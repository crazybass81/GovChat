# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Primitive structures for use when interacting with crypto material managers.

.. versionadded:: 1.3.0
"""

import attr
import six

from ..identifiers import Algorithm, CommitmentPolicy
from ..internal.utils.streams import ROStream
from ..structures import DataKey


@attr.s(hash=False)
class EncryptionMaterialsRequest:
    """Request object to provide to a crypto material manager's `get_encryption_materials` method.

    .. versionadded:: 1.3.0

    .. warning::
        If plaintext_rostream seek position is modified, it must be returned before leaving method.

    :param dict encryption_context: Encryption context passed to underlying master key provider and master keys
    :param int frame_length: Frame length to be used while encrypting stream
    :param plaintext_rostream: Source plaintext read-only stream (optional)
    :type plaintext_rostream: aws_encryption_sdk.internal.utils.streams.ROStream
    :param algorithm: Algorithm passed to underlying master key provider and master keys (optional)
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param int plaintext_length: Length of source plaintext (optional)
    """

    encryption_context = attr.ib(validator=attr.validators.instance_of(dict))
    frame_length = attr.ib(validator=attr.validators.instance_of(six.integer_types))
    commitment_policy = attr.ib(
        default=CommitmentPolicy.FORBID_ENCRYPT_ALLOW_DECRYPT,
        validator=attr.validators.optional(attr.validators.instance_of(CommitmentPolicy)),
    )
    plaintext_rostream = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(ROStream))
    )
    algorithm = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(Algorithm))
    )
    plaintext_length = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(six.integer_types)),
    )


@attr.s(hash=False)
class EncryptionMaterials:
    """Encryption materials returned by a crypto material manager's `get_encryption_materials` method.

    .. versionadded:: 1.3.0

    :param algorithm: Algorithm to use for encrypting message
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param data_encryption_key: Plaintext data key to use for encrypting message
    :type data_encryption_key: aws_encryption_sdk.structures.DataKey
    :param encrypted_data_keys: List of encrypted data keys
    :type encrypted_data_keys: list of `aws_encryption_sdk.structures.EncryptedDataKey`
    :param dict encryption_context: Encryption context tied to `encrypted_data_keys`
    :param bytes signing_key: Encoded signing key
    """

    algorithm = attr.ib(validator=attr.validators.instance_of(Algorithm))
    data_encryption_key = attr.ib(validator=attr.validators.instance_of(DataKey))
    encrypted_data_keys = attr.ib(validator=attr.validators.instance_of(set))
    encryption_context = attr.ib(validator=attr.validators.instance_of(dict))
    signing_key = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(bytes))
    )


@attr.s(hash=False)
class DecryptionMaterialsRequest:
    """Request object to provide to a crypto material manager's `decrypt_materials` method.

    .. versionadded:: 1.3.0

    :param algorithm: Algorithm to provide to master keys for underlying decrypt requests
    :type algorithm: aws_encryption_sdk.identifiers.Algorithm
    :param encrypted_data_keys: Set of encrypted data keys
    :type encrypted_data_keys: set of `aws_encryption_sdk.structures.EncryptedDataKey`
    :param dict encryption_context: Encryption context to provide to master keys for underlying decrypt requests
    """

    algorithm = attr.ib(validator=attr.validators.instance_of(Algorithm))
    encrypted_data_keys = attr.ib(validator=attr.validators.instance_of(set))
    encryption_context = attr.ib(validator=attr.validators.instance_of(dict))
    commitment_policy = attr.ib(
        default=CommitmentPolicy.FORBID_ENCRYPT_ALLOW_DECRYPT,
        validator=attr.validators.optional(attr.validators.instance_of(CommitmentPolicy)),
    )


@attr.s(hash=False)
class DecryptionMaterials:
    """Decryption materials returned by a crypto material manager's `decrypt_materials` method.

    .. versionadded:: 1.3.0

    :param data_key: Plaintext data key to use with message decryption
    :type data_key: aws_encryption_sdk.structures.DataKey
    :param bytes verification_key: Raw signature verification key
    """

    data_key = attr.ib(validator=attr.validators.instance_of(DataKey))
    verification_key = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(bytes))
    )
