# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import annotations

import binascii
import re
import sys
import typing
import warnings
from collections.abc import Iterable, Iterator

from cryptography import utils
from cryptography.hazmat.bindings._rust import x509 as rust_x509
from cryptography.x509.oid import NameOID, ObjectIdentifier


class _ASN1Type(utils.Enum):
    BitString = 3
    OctetString = 4
    UTF8String = 12
    NumericString = 18
    PrintableString = 19
    T61String = 20
    IA5String = 22
    UTCTime = 23
    GeneralizedTime = 24
    VisibleString = 26
    UniversalString = 28
    BMPString = 30


_ASN1_TYPE_TO_ENUM = {i.value: i for i in _ASN1Type}
_NAMEOID_DEFAULT_TYPE: dict[ObjectIdentifier, _ASN1Type] = {
    NameOID.COUNTRY_NAME: _ASN1Type.PrintableString,
    NameOID.JURISDICTION_COUNTRY_NAME: _ASN1Type.PrintableString,
    NameOID.SERIAL_NUMBER: _ASN1Type.PrintableString,
    NameOID.DN_QUALIFIER: _ASN1Type.PrintableString,
    NameOID.EMAIL_ADDRESS: _ASN1Type.IA5String,
    NameOID.DOMAIN_COMPONENT: _ASN1Type.IA5String,
}

# Type alias
_OidNameMap = typing.Mapping[ObjectIdentifier, str]
_NameOidMap = typing.Mapping[str, ObjectIdentifier]

#: Short attribute names from RFC 4514:
#: https://tools.ietf.org/html/rfc4514#page-7
_NAMEOID_TO_NAME: _OidNameMap = {
    NameOID.COMMON_NAME: "CN",
    NameOID.LOCALITY_NAME: "L",
    NameOID.STATE_OR_PROVINCE_NAME: "ST",
    NameOID.ORGANIZATION_NAME: "O",
    NameOID.ORGANIZATIONAL_UNIT_NAME: "OU",
    NameOID.COUNTRY_NAME: "C",
    NameOID.STREET_ADDRESS: "STREET",
    NameOID.DOMAIN_COMPONENT: "DC",
    NameOID.USER_ID: "UID",
}
_NAME_TO_NAMEOID = {v: k for k, v in _NAMEOID_TO_NAME.items()}

_NAMEOID_LENGTH_LIMIT = {
    NameOID.COUNTRY_NAME: (2, 2),
    NameOID.JURISDICTION_COUNTRY_NAME: (2, 2),
    NameOID.COMMON_NAME: (1, 64),
}


def _escape_dn_value(val: str | bytes) -> str:
    """Escape special characters in RFC4514 Distinguished Name value."""

    if not val:
        return ""

    # RFC 4514 Section 2.4 defines the value as being the # (U+0023) character
    # followed by the hexadecimal encoding of the octets.
    if isinstance(val, bytes):
        return "#" + binascii.hexlify(val).decode("utf8")

    # See https://tools.ietf.org/html/rfc4514#section-2.4
    val = val.replace("\\", "\\\\")
    val = val.replace('"', '\\"')
    val = val.replace("+", "\\+")
    val = val.replace(",", "\\,")
    val = val.replace(";", "\\;")
    val = val.replace("<", "\\<")
    val = val.replace(">", "\\>")
    val = val.replace("\0", "\\00")

    if val[0] in ("#", " "):
        val = "\\" + val
    if val[-1] == " ":
        val = val[:-1] + "\\ "

    return val


def _unescape_dn_value(val: str) -> str:
    if not val:
        return ""

    # See https://tools.ietf.org/html/rfc4514#section-3

    # special = escaped / SPACE / SHARP / EQUALS
    # escaped = DQUOTE / PLUS / COMMA / SEMI / LANGLE / RANGLE
    def sub(m):
        val = m.group(1)
        # Regular escape
        if len(val) == 1:
            return val
        # Hex-value scape
        return chr(int(val, 16))

    return _RFC4514NameParser._PAIR_RE.sub(sub, val)


NameAttributeValueType = typing.TypeVar(
    "NameAttributeValueType",
    typing.Union[str, bytes],
    str,
    bytes,
    covariant=True,
)


class NameAttribute(typing.Generic[NameAttributeValueType]):
    def __init__(
        self,
        oid: ObjectIdentifier,
        value: NameAttributeValueType,
        _type: _ASN1Type | None = None,
        *,
        _validate: bool = True,
    ) -> None:
        if not isinstance(oid, ObjectIdentifier):
            raise TypeError("oid argument must be an ObjectIdentifier instance.")
        if _type == _ASN1Type.BitString:
            if oid != NameOID.X500_UNIQUE_IDENTIFIER:
                raise TypeError("oid must be X500_UNIQUE_IDENTIFIER for BitString type.")
            if not isinstance(value, bytes):
                raise TypeError("value must be bytes for BitString")
        else:
            if not isinstance(value, str):
                raise TypeError("value argument must be a str")

        length_limits = _NAMEOID_LENGTH_LIMIT.get(oid)
        if length_limits is not None:
            min_length, max_length = length_limits
            assert isinstance(value, str)
            c_len = len(value.encode("utf8"))
            if c_len < min_length or c_len > max_length:
                msg = (
                    f"Attribute's length must be >= {min_length} and "
                    f"<= {max_length}, but it was {c_len}"
                )
                if _validate is True:
                    raise ValueError(msg)
                else:
                    warnings.warn(msg, stacklevel=2)

        # The appropriate ASN1 string type varies by OID and is defined across
        # multiple RFCs including 2459, 3280, and 5280. In general UTF8String
        # is preferred (2459), but 3280 and 5280 specify several OIDs with
        # alternate types. This means when we see the sentinel value we need
        # to look up whether the OID has a non-UTF8 type. If it does, set it
        # to that. Otherwise, UTF8!
        if _type is None:
            _type = _NAMEOID_DEFAULT_TYPE.get(oid, _ASN1Type.UTF8String)

        if not isinstance(_type, _ASN1Type):
            raise TypeError("_type must be from the _ASN1Type enum")

        self._oid = oid
        self._value: NameAttributeValueType = value
        self._type: _ASN1Type = _type

    @property
    def oid(self) -> ObjectIdentifier:
        return self._oid

    @property
    def value(self) -> NameAttributeValueType:
        return self._value

    @property
    def rfc4514_attribute_name(self) -> str:
        """
        The short attribute name (for example "CN") if available,
        otherwise the OID dotted string.
        """
        return _NAMEOID_TO_NAME.get(self.oid, self.oid.dotted_string)

    def rfc4514_string(self, attr_name_overrides: _OidNameMap | None = None) -> str:
        """
        Format as RFC4514 Distinguished Name string.

        Use short attribute name if available, otherwise fall back to OID
        dotted string.
        """
        attr_name = attr_name_overrides.get(self.oid) if attr_name_overrides else None
        if attr_name is None:
            attr_name = self.rfc4514_attribute_name

        return f"{attr_name}={_escape_dn_value(self.value)}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NameAttribute):
            return NotImplemented

        return self.oid == other.oid and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.oid, self.value))

    def __repr__(self) -> str:
        return f"<NameAttribute(oid={self.oid}, value={self.value!r})>"


class RelativeDistinguishedName:
    def __init__(self, attributes: Iterable[NameAttribute]):
        attributes = list(attributes)
        if not attributes:
            raise ValueError("a relative distinguished name cannot be empty")
        if not all(isinstance(x, NameAttribute) for x in attributes):
            raise TypeError("attributes must be an iterable of NameAttribute")

        # Keep list and frozenset to preserve attribute order where it matters
        self._attributes = attributes
        self._attribute_set = frozenset(attributes)

        if len(self._attribute_set) != len(attributes):
            raise ValueError("duplicate attributes are not allowed")

    def get_attributes_for_oid(
        self,
        oid: ObjectIdentifier,
    ) -> list[NameAttribute[str | bytes]]:
        return [i for i in self if i.oid == oid]

    def rfc4514_string(self, attr_name_overrides: _OidNameMap | None = None) -> str:
        """
        Format as RFC4514 Distinguished Name string.

        Within each RDN, attributes are joined by '+', although that is rarely
        used in certificates.
        """
        return "+".join(attr.rfc4514_string(attr_name_overrides) for attr in self._attributes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelativeDistinguishedName):
            return NotImplemented

        return self._attribute_set == other._attribute_set

    def __hash__(self) -> int:
        return hash(self._attribute_set)

    def __iter__(self) -> Iterator[NameAttribute]:
        return iter(self._attributes)

    def __len__(self) -> int:
        return len(self._attributes)

    def __repr__(self) -> str:
        return f"<RelativeDistinguishedName({self.rfc4514_string()})>"


class Name:
    @typing.overload
    def __init__(self, attributes: Iterable[NameAttribute]) -> None: ...

    @typing.overload
    def __init__(self, attributes: Iterable[RelativeDistinguishedName]) -> None: ...

    def __init__(
        self,
        attributes: Iterable[NameAttribute | RelativeDistinguishedName],
    ) -> None:
        attributes = list(attributes)
        if all(isinstance(x, NameAttribute) for x in attributes):
            self._attributes = [
                RelativeDistinguishedName([typing.cast(NameAttribute, x)]) for x in attributes
            ]
        elif all(isinstance(x, RelativeDistinguishedName) for x in attributes):
            self._attributes = typing.cast(typing.List[RelativeDistinguishedName], attributes)
        else:
            raise TypeError(
                "attributes must be a list of NameAttribute or a list RelativeDistinguishedName"
            )

    @classmethod
    def from_rfc4514_string(
        cls,
        data: str,
        attr_name_overrides: _NameOidMap | None = None,
    ) -> Name:
        return _RFC4514NameParser(data, attr_name_overrides or {}).parse()

    def rfc4514_string(self, attr_name_overrides: _OidNameMap | None = None) -> str:
        """
        Format as RFC4514 Distinguished Name string.
        For example 'CN=foobar.com,O=Foo Corp,C=US'

        An X.509 name is a two-level structure: a list of sets of attributes.
        Each list element is separated by ',' and within each list element, set
        elements are separated by '+'. The latter is almost never used in
        real world certificates. According to RFC4514 section 2.1 the
        RDNSequence must be reversed when converting to string representation.
        """
        return ",".join(
            attr.rfc4514_string(attr_name_overrides) for attr in reversed(self._attributes)
        )

    def get_attributes_for_oid(
        self,
        oid: ObjectIdentifier,
    ) -> list[NameAttribute[str | bytes]]:
        return [i for i in self if i.oid == oid]

    @property
    def rdns(self) -> list[RelativeDistinguishedName]:
        return self._attributes

    def public_bytes(self, backend: typing.Any = None) -> bytes:
        return rust_x509.encode_name_bytes(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Name):
            return NotImplemented

        return self._attributes == other._attributes

    def __hash__(self) -> int:
        # TODO: this is relatively expensive, if this looks like a bottleneck
        # for you, consider optimizing!
        return hash(tuple(self._attributes))

    def __iter__(self) -> Iterator[NameAttribute]:
        for rdn in self._attributes:
            yield from rdn

    def __len__(self) -> int:
        return sum(len(rdn) for rdn in self._attributes)

    def __repr__(self) -> str:
        rdns = ",".join(attr.rfc4514_string() for attr in self._attributes)
        return f"<Name({rdns})>"


class _RFC4514NameParser:
    _OID_RE = re.compile(r"(0|([1-9]\d*))(\.(0|([1-9]\d*)))+")
    _DESCR_RE = re.compile(r"[a-zA-Z][a-zA-Z\d-]*")

    _PAIR = r"\\([\\ #=\"\+,;<>]|[\da-zA-Z]{2})"
    _PAIR_RE = re.compile(_PAIR)
    _LUTF1 = r"[\x01-\x1f\x21\x24-\x2A\x2D-\x3A\x3D\x3F-\x5B\x5D-\x7F]"
    _SUTF1 = r"[\x01-\x21\x23-\x2A\x2D-\x3A\x3D\x3F-\x5B\x5D-\x7F]"
    _TUTF1 = r"[\x01-\x1F\x21\x23-\x2A\x2D-\x3A\x3D\x3F-\x5B\x5D-\x7F]"
    _UTFMB = rf"[\x80-{chr(sys.maxunicode)}]"
    _LEADCHAR = rf"{_LUTF1}|{_UTFMB}"
    _STRINGCHAR = rf"{_SUTF1}|{_UTFMB}"
    _TRAILCHAR = rf"{_TUTF1}|{_UTFMB}"
    _STRING_RE = re.compile(
        rf"""
        (
            ({_LEADCHAR}|{_PAIR})
            (
                ({_STRINGCHAR}|{_PAIR})*
                ({_TRAILCHAR}|{_PAIR})
            )?
        )?
        """,
        re.VERBOSE,
    )
    _HEXSTRING_RE = re.compile(r"#([\da-zA-Z]{2})+")

    def __init__(self, data: str, attr_name_overrides: _NameOidMap) -> None:
        self._data = data
        self._idx = 0

        self._attr_name_overrides = attr_name_overrides

    def _has_data(self) -> bool:
        return self._idx < len(self._data)

    def _peek(self) -> str | None:
        if self._has_data():
            return self._data[self._idx]
        return None

    def _read_char(self, ch: str) -> None:
        if self._peek() != ch:
            raise ValueError
        self._idx += 1

    def _read_re(self, pat) -> str:
        match = pat.match(self._data, pos=self._idx)
        if match is None:
            raise ValueError
        val = match.group()
        self._idx += len(val)
        return val

    def parse(self) -> Name:
        """
        Parses the `data` string and converts it to a Name.

        According to RFC4514 section 2.1 the RDNSequence must be
        reversed when converting to string representation. So, when
        we parse it, we need to reverse again to get the RDNs on the
        correct order.
        """

        if not self._has_data():
            return Name([])

        rdns = [self._parse_rdn()]

        while self._has_data():
            self._read_char(",")
            rdns.append(self._parse_rdn())

        return Name(reversed(rdns))

    def _parse_rdn(self) -> RelativeDistinguishedName:
        nas = [self._parse_na()]
        while self._peek() == "+":
            self._read_char("+")
            nas.append(self._parse_na())

        return RelativeDistinguishedName(nas)

    def _parse_na(self) -> NameAttribute:
        try:
            oid_value = self._read_re(self._OID_RE)
        except ValueError:
            name = self._read_re(self._DESCR_RE)
            oid = self._attr_name_overrides.get(name, _NAME_TO_NAMEOID.get(name))
            if oid is None:
                raise ValueError
        else:
            oid = ObjectIdentifier(oid_value)

        self._read_char("=")
        if self._peek() == "#":
            value = self._read_re(self._HEXSTRING_RE)
            value = binascii.unhexlify(value[1:]).decode()
        else:
            raw_value = self._read_re(self._STRING_RE)
            value = _unescape_dn_value(raw_value)

        return NameAttribute(oid, value)
