# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Public data structures for aws_encryption_sdk."""

import attr
import aws_encryption_sdk.identifiers
import six
from aws_encryption_sdk.internal.str_ops import to_bytes, to_str


@attr.s(hash=True)
class MessageHeader:
    # pylint: disable=too-many-instance-attributes
    """Deserialized message header object.

    :param version: Message format version, per spec
    :type version: aws_encryption_sdk.identifiers.SerializationVersion
    :param type: Message content type, per spec
    :type type: aws_encryption_sdk.identifiers.ObjectType
    :param algorithm: Algorithm to use for encryption
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param bytes message_id: Message ID
    :param dict encryption_context: Dictionary defining encryption context
    :param encrypted_data_keys: Encrypted data keys
    :type encrypted_data_keys: set of :class:`aws_encryption_sdk.structures.EncryptedDataKey`
    :param content_type: Message content framing type (framed/non-framed)
    :type content_type: aws_encryption_sdk.identifiers.ContentType
    :param bytes content_aad_length: empty
    :param int header_iv_length: Bytes in Initialization Vector value found in header
    :param int frame_length: Length of message frame in bytes
    """

    version = attr.ib(
        hash=True,
        validator=attr.validators.instance_of(aws_encryption_sdk.identifiers.SerializationVersion),
    )
    algorithm = attr.ib(
        hash=True, validator=attr.validators.instance_of(aws_encryption_sdk.identifiers.Algorithm)
    )
    message_id = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    encryption_context = attr.ib(hash=True, validator=attr.validators.instance_of(dict))
    encrypted_data_keys = attr.ib(hash=True, validator=attr.validators.instance_of(set))
    content_type = attr.ib(
        hash=True, validator=attr.validators.instance_of(aws_encryption_sdk.identifiers.ContentType)
    )
    frame_length = attr.ib(hash=True, validator=attr.validators.instance_of(six.integer_types))

    # Only present in SerializationVersion.V1
    type = attr.ib(
        hash=True,
        default=None,
        validator=attr.validators.optional(
            attr.validators.instance_of(aws_encryption_sdk.identifiers.ObjectType)
        ),
    )
    content_aad_length = attr.ib(
        hash=True,
        default=None,
        validator=attr.validators.optional(
            attr.validators.optional(attr.validators.instance_of(six.integer_types))
        ),
    )
    header_iv_length = attr.ib(
        hash=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(six.integer_types)),
    )

    # Only present in SerializationVersion.V2 with certain algorithm suites
    commitment_key = attr.ib(
        hash=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(bytes)),
    )


@attr.s(hash=True)
class MasterKeyInfo:
    """Contains information necessary to identify a Master Key.

    :param str provider_id: MasterKey provider_id value
    :param bytes key_info: MasterKey key_info value
    """

    provider_id = attr.ib(
        hash=True,
        validator=attr.validators.instance_of((six.string_types, bytes)),
        converter=to_str,
    )
    key_info = attr.ib(
        hash=True,
        validator=attr.validators.instance_of((six.string_types, bytes)),
        converter=to_bytes,
    )


@attr.s(hash=True)
class RawDataKey:
    """Hold only the unencrypted copy of a data key.

    :param key_provider: Key Provider information
    :type key_provider: aws_encryption_sdk.structures.MasterKeyInfo
    :param bytes data_key: Plaintext data key
    """

    key_provider = attr.ib(hash=True, validator=attr.validators.instance_of(MasterKeyInfo))
    data_key = attr.ib(hash=True, repr=False, validator=attr.validators.instance_of(bytes))


@attr.s(hash=True)
class DataKey:
    """Holds both the encrypted and unencrypted copies of a data key.

    :param key_provider: Key Provider information
    :type key_provider: aws_encryption_sdk.structures.MasterKeyInfo
    :param bytes data_key: Plaintext data key
    :param bytes encrypted_data_key: Encrypted data key
    """

    key_provider = attr.ib(hash=True, validator=attr.validators.instance_of(MasterKeyInfo))
    data_key = attr.ib(hash=True, repr=False, validator=attr.validators.instance_of(bytes))
    encrypted_data_key = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))


@attr.s(hash=True)
class EncryptedDataKey:
    """Holds only the encrypted copy of a data key.

    :param key_provider: Key Provider information
    :type key_provider: aws_encryption_sdk.structures.MasterKeyInfo
    :param bytes encrypted_data_key: Encrypted data key
    """

    key_provider = attr.ib(hash=True, validator=attr.validators.instance_of(MasterKeyInfo))
    encrypted_data_key = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
