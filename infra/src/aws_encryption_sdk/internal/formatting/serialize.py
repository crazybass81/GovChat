# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Components for handling AWS Encryption SDK message serialization."""

import logging
import struct

import aws_encryption_sdk.internal.defaults
import aws_encryption_sdk.internal.formatting.encryption_context
from aws_encryption_sdk.exceptions import SerializationError
from aws_encryption_sdk.identifiers import (
    ContentAADString,
    EncryptionType,
    SequenceIdentifier,
    SerializationVersion,
)
from aws_encryption_sdk.internal.crypto.encryption import encrypt
from aws_encryption_sdk.internal.crypto.iv import frame_iv, header_auth_iv
from aws_encryption_sdk.internal.str_ops import to_bytes
from aws_encryption_sdk.structures import EncryptedDataKey, MasterKeyInfo

_LOGGER = logging.getLogger(__name__)


def serialize_encrypted_data_key(encrypted_data_key):
    """Serializes an encrypted data key.

    .. versionadded:: 1.3.0

    :param encrypted_data_key: Encrypted data key to serialize
    :type encrypted_data_key: aws_encryption_sdk.structures.EncryptedDataKey
    :returns: Serialized encrypted data key
    :rtype: bytes
    """
    encrypted_data_key_format = (
        ">"  # big endian
        "H"  # key provider ID length
        "{provider_id_len}s"  # key provider ID
        "H"  # key info length
        "{provider_info_len}s"  # key info
        "H"  # encrypted data key length
        "{enc_data_key_len}s"  # encrypted data key
    )
    return struct.pack(
        encrypted_data_key_format.format(
            provider_id_len=len(encrypted_data_key.key_provider.provider_id),
            provider_info_len=len(encrypted_data_key.key_provider.key_info),
            enc_data_key_len=len(encrypted_data_key.encrypted_data_key),
        ),
        len(encrypted_data_key.key_provider.provider_id),
        to_bytes(encrypted_data_key.key_provider.provider_id),
        len(encrypted_data_key.key_provider.key_info),
        to_bytes(encrypted_data_key.key_provider.key_info),
        len(encrypted_data_key.encrypted_data_key),
        encrypted_data_key.encrypted_data_key,
    )


def _serialize_header_v1(header, signer=None):
    """Serializes a header object for messages with SerializationVersion.V1.

    :param header: Header to serialize
    :type header: aws_encryption_sdk.structures.MessageHeader
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized header
    :rtype: bytes
    """
    ec_serialized = (
        aws_encryption_sdk.internal.formatting.encryption_context.serialize_encryption_context(
            header.encryption_context
        )
    )
    header_start_format = (
        ">"  # big endian
        "B"  # version
        "B"  # type
        "H"  # algorithm ID
        "16s"  # message ID
        "H"  # encryption context length
        f"{len(ec_serialized)}s"  # serialized encryption context
    )
    header_bytes = bytearray()
    header_bytes.extend(
        struct.pack(
            header_start_format,
            header.version.value,
            header.type.value,
            header.algorithm.algorithm_id,
            header.message_id,
            len(ec_serialized),
            ec_serialized,
        )
    )

    serialized_data_keys = bytearray()
    for data_key in header.encrypted_data_keys:
        serialized_data_keys.extend(serialize_encrypted_data_key(data_key))

    header_bytes.extend(struct.pack(">H", len(header.encrypted_data_keys)))
    header_bytes.extend(serialized_data_keys)

    header_close_format = (
        ">"  # big endian
        "B"  # content type (no framing vs framing)
        "4x"  # reserved (formerly content AAD length)
        "B"  # nonce/IV length, this applies to all IVs in this message
        "I"  # frame length
    )
    header_bytes.extend(
        struct.pack(
            header_close_format,
            header.content_type.value,
            header.algorithm.iv_len,
            header.frame_length,
        )
    )
    output = bytes(header_bytes)
    if signer is not None:
        signer.update(output)
    return output


def _serialize_header_v2(header, signer=None):
    """Serializes a header object for messages with SerializationVersion.V2.

    :param header: Header to serialize
    :type header: aws_encryption_sdk.structures.MessageHeader
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized header
    :rtype: bytes
    """
    ec_serialized = (
        aws_encryption_sdk.internal.formatting.encryption_context.serialize_encryption_context(
            header.encryption_context
        )
    )
    header_start_format = (
        ">"  # big endian
        "B"  # version
        "H"  # algorithm ID
        "32s"  # message ID
        "H"  # encryption context length
        f"{len(ec_serialized)}s"  # serialized encryption context
    )
    header_bytes = bytearray()
    header_bytes.extend(
        struct.pack(
            header_start_format,
            header.version.value,
            header.algorithm.algorithm_id,
            header.message_id,
            len(ec_serialized),
            ec_serialized,
        )
    )

    serialized_data_keys = bytearray()
    for data_key in header.encrypted_data_keys:
        serialized_data_keys.extend(serialize_encrypted_data_key(data_key))

    header_bytes.extend(struct.pack(">H", len(header.encrypted_data_keys)))
    header_bytes.extend(serialized_data_keys)

    header_bytes.extend(struct.pack(">B", header.content_type.value))
    header_bytes.extend(struct.pack(">I", header.frame_length))

    if header.algorithm.is_committing():
        algorithm_suite_data_length = header.algorithm.algorithm_suite_data_length()
        header_bytes.extend(
            struct.pack(f">{algorithm_suite_data_length}s", header.commitment_key)
        )

    output = bytes(header_bytes)
    if signer is not None:
        signer.update(output)
    return output


def serialize_header(header, signer=None):
    """Serializes a header object.

    :param header: Header to serialize
    :type header: aws_encryption_sdk.structures.MessageHeader
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized header
    :rtype: bytes
    """
    if header.version == SerializationVersion.V1:
        return _serialize_header_v1(header, signer)
    elif header.version == SerializationVersion.V2:
        return _serialize_header_v2(header, signer)
    else:
        raise SerializationError(f"Unrecognized message format version: {header.version}")


def _serialize_header_auth_v1(algorithm, header, data_encryption_key, signer=None):
    """Creates serialized header authentication data for messages in serialization version V1.

    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes header: Serialized message header
    :param bytes data_encryption_key: Data key with which to encrypt message
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.Signer
    :returns: Serialized header authentication data
    :rtype: bytes
    """
    header_auth = encrypt(
        algorithm=algorithm,
        key=data_encryption_key,
        plaintext=b"",
        associated_data=header,
        iv=header_auth_iv(algorithm),
    )
    output = struct.pack(
        f">{algorithm.iv_len}s{algorithm.tag_len}s",
        header_auth.iv,
        header_auth.tag,
    )
    if signer is not None:
        signer.update(output)
    return output


def _serialize_header_auth_v2(algorithm, header, data_encryption_key, signer=None):
    """Creates serialized header authentication data for messages in serialization version V2.

    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes header: Serialized message header
    :param bytes data_encryption_key: Data key with which to encrypt message
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.Signer
    :returns: Serialized header authentication data
    :rtype: bytes
    """
    header_auth = encrypt(
        algorithm=algorithm,
        key=data_encryption_key,
        plaintext=b"",
        associated_data=header,
        iv=header_auth_iv(algorithm),
    )
    output = struct.pack(
        f">{algorithm.tag_len}s",
        header_auth.tag,
    )
    if signer is not None:
        signer.update(output)
    return output


def serialize_header_auth(version, algorithm, header, data_encryption_key, signer=None):
    """Creates serialized header authentication data.

    :param version: The serialization version of the message
    :type version: int
    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes header: Serialized message header
    :param bytes data_encryption_key: Data key with which to encrypt message
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.Signer
    :returns: Serialized header authentication data
    :rtype: bytes
    """
    if version == SerializationVersion.V1:
        return _serialize_header_auth_v1(algorithm, header, data_encryption_key, signer)
    elif version == SerializationVersion.V2:
        return _serialize_header_auth_v2(algorithm, header, data_encryption_key, signer)
    else:
        raise SerializationError(f"Unrecognized message format version: {version}")


def serialize_non_framed_open(algorithm, iv, plaintext_length, signer=None):
    """Serializes the opening block for a non-framed message body.

    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes iv: IV value used to encrypt body
    :param int plaintext_length: Length of plaintext (and thus ciphertext) in body
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized body start block
    :rtype: bytes
    """
    body_start_format = (f">{algorithm.iv_len}sQ")  # nonce (IV)  # content length
    body_start = struct.pack(body_start_format, iv, plaintext_length)
    if signer:
        signer.update(body_start)
    return body_start


def serialize_non_framed_close(tag, signer=None):
    """Serializes the closing block for a non-framed message body.

    :param bytes tag: Auth tag value from body encryptor
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized body close block
    :rtype: bytes
    """
    body_close = struct.pack(f"{len(tag)}s", tag)
    if signer:
        signer.update(body_close)
    return body_close


def serialize_frame(
    algorithm,
    plaintext,
    message_id,
    data_encryption_key,
    frame_length,
    sequence_number,
    is_final_frame,
    signer=None,
):
    """Receives a message plaintext, breaks off a frame, encrypts and serializes
    the frame, and returns the encrypted frame and the remaining plaintext.

    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes plaintext: Source plaintext to encrypt and serialize
    :param bytes message_id: Message ID
    :param bytes data_encryption_key: Data key with which to encrypt message
    :param int frame_length: Length of the framed data
    :param int sequence_number: Sequence number for frame to be generated
    :param bool is_final_frame: Boolean stating whether or not this frame is a final frame
    :param signer: Cryptographic signer object (optional)
    :type signer: aws_encryption_sdk.Signer
    :returns: Serialized frame and remaining plaintext
    :rtype: tuple of bytes
    :raises SerializationError: if number of frames is too large
    """
    if sequence_number < 1:
        raise SerializationError("Frame sequence number must be greater than 0")
    if sequence_number > aws_encryption_sdk.internal.defaults.MAX_FRAME_COUNT:
        raise SerializationError("Max frame count exceeded")
    if is_final_frame:
        content_string = ContentAADString.FINAL_FRAME_STRING_ID
    else:
        content_string = ContentAADString.FRAME_STRING_ID
    frame_plaintext = plaintext[:frame_length]
    frame_ciphertext = encrypt(
        algorithm=algorithm,
        key=data_encryption_key,
        plaintext=frame_plaintext,
        associated_data=aws_encryption_sdk.internal.formatting.encryption_context.assemble_content_aad(
            message_id=message_id,
            aad_content_string=content_string,
            seq_num=sequence_number,
            length=len(frame_plaintext),
        ),
        iv=frame_iv(algorithm, sequence_number),
    )
    plaintext = plaintext[frame_length:]
    if is_final_frame:
        _LOGGER.debug("Serializing final frame")
        packed_frame = struct.pack(
            f">II{algorithm.iv_len}sI{len(frame_ciphertext.ciphertext)}s{algorithm.auth_len}s",
            SequenceIdentifier.SEQUENCE_NUMBER_END.value,
            sequence_number,
            frame_ciphertext.iv,
            len(frame_ciphertext.ciphertext),
            frame_ciphertext.ciphertext,
            frame_ciphertext.tag,
        )
    else:
        _LOGGER.debug("Serializing frame")
        packed_frame = struct.pack(
            f">I{algorithm.iv_len}s{frame_length}s{algorithm.auth_len}s",
            sequence_number,
            frame_ciphertext.iv,
            frame_ciphertext.ciphertext,
            frame_ciphertext.tag,
        )
    if signer is not None:
        signer.update(packed_frame)
    return packed_frame, plaintext


def serialize_footer(signer):
    """Uses the signer object which has been used to sign the message to generate
    the signature, then serializes that signature.

    :param signer: Cryptographic signer object
    :type signer: aws_encryption_sdk.internal.crypto.Signer
    :returns: Serialized footer
    :rtype: bytes
    """
    footer = b""
    if signer is not None:
        signature = signer.finalize()
        footer = struct.pack(
            f">H{len(signature)}s", len(signature), signature
        )
    return footer


def serialize_raw_master_key_prefix(raw_master_key):
    """Produces the prefix that a RawMasterKey will always use for the
    key_info value of keys which require additional information.

    :param raw_master_key: RawMasterKey for which to produce a prefix
    :type raw_master_key: aws_encryption_sdk.key_providers.raw.RawMasterKey
    :returns: Serialized key_info prefix
    :rtype: bytes
    """
    if (
        raw_master_key.config.wrapping_key.wrapping_algorithm.encryption_type
        is EncryptionType.ASYMMETRIC
    ):
        return to_bytes(raw_master_key.key_id)
    return struct.pack(
        f">{len(raw_master_key.key_id)}sII",
        to_bytes(raw_master_key.key_id),
        # Tag Length is stored in bits, not bytes
        raw_master_key.config.wrapping_key.wrapping_algorithm.algorithm.tag_len * 8,
        raw_master_key.config.wrapping_key.wrapping_algorithm.algorithm.iv_len,
    )


def serialize_wrapped_key(key_provider, wrapping_algorithm, wrapping_key_id, encrypted_wrapped_key):
    """Serializes EncryptedData into a Wrapped EncryptedDataKey.

    :param key_provider: Info for Wrapping MasterKey
    :type key_provider: aws_encryption_sdk.structures.MasterKeyInfo
    :param wrapping_algorithm: Wrapping Algorithm with which to wrap plaintext_data_key
    :type wrapping_algorithm: aws_encryption_sdk.identifiers.WrappingAlgorithm
    :param bytes wrapping_key_id: Key ID of wrapping MasterKey
    :param encrypted_wrapped_key: Encrypted data key
    :type encrypted_wrapped_key: aws_encryption_sdk.internal.structures.EncryptedData
    :returns: Wrapped EncryptedDataKey
    :rtype: aws_encryption_sdk.structures.EncryptedDataKey
    """
    if encrypted_wrapped_key.iv is None:
        key_info = wrapping_key_id
        key_ciphertext = encrypted_wrapped_key.ciphertext
    else:
        key_info = struct.pack(
            f">{len(wrapping_key_id)}sII{wrapping_algorithm.algorithm.iv_len}s",
            to_bytes(wrapping_key_id),
            len(encrypted_wrapped_key.tag) * 8,  # Tag Length is stored in bits, not bytes
            wrapping_algorithm.algorithm.iv_len,
            encrypted_wrapped_key.iv,
        )
        key_ciphertext = encrypted_wrapped_key.ciphertext + encrypted_wrapped_key.tag
    return EncryptedDataKey(
        key_provider=MasterKeyInfo(provider_id=key_provider.provider_id, key_info=key_info),
        encrypted_data_key=key_ciphertext,
    )
