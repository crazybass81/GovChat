# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Public data structures for aws_encryption_sdk."""

import attr
import six


@attr.s(hash=True)
class EncryptedData:
    """Holds encrypted data.

    :param bytes iv: Initialization Vector
    :param bytes ciphertext: Ciphertext
    :param bytes tag: Encryption tag
    """

    iv = attr.ib(hash=True, validator=attr.validators.optional(attr.validators.instance_of(bytes)))
    ciphertext = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    tag = attr.ib(hash=True, validator=attr.validators.optional(attr.validators.instance_of(bytes)))


@attr.s(hash=True)
class MessageHeaderAuthentication:
    """Deserialized message header authentication

    :param bytes iv: Initialization Vector
    :param bytes tag: Encryption Tag
    """

    iv = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    tag = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))


@attr.s(hash=True)
class MessageFrameBody:
    """Deserialized message frame

    :param bytes iv: Initialization Vector
    :param bytes ciphertext: Ciphertext
    :param bytes tag: Encryption Tag
    :param int sequence_number: Frame sequence number
    :param bool final_frame: Identifies final frames
    """

    iv = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    ciphertext = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    tag = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    sequence_number = attr.ib(hash=True, validator=attr.validators.instance_of(six.integer_types))
    final_frame = attr.ib(hash=True, validator=attr.validators.instance_of(bool))


@attr.s(hash=True)
class MessageNoFrameBody:
    """Deserialized message body with no framing

    :param bytes iv: Initialization Vector
    :param bytes ciphertext: Ciphertext
    :param bytes tag: Encryption Tag
    """

    iv = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    ciphertext = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    tag = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
    sequence_number = 1
    final_frame = True  # Never used, but set here to provide a consistent API with MessageFrameBody


@attr.s(hash=True)
class MessageFooter:
    """Deserialized message footer

    :param bytes signature: Message signature
    """

    signature = attr.ib(hash=True, validator=attr.validators.instance_of(bytes))
