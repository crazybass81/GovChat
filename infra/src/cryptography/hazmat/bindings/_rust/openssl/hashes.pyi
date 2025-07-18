# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

import typing

from cryptography.hazmat.primitives import hashes
from cryptography.utils import Buffer

class Hash(hashes.HashContext):
    def __init__(self, algorithm: hashes.HashAlgorithm, backend: typing.Any = None) -> None: ...
    @property
    def algorithm(self) -> hashes.HashAlgorithm: ...
    def update(self, data: Buffer) -> None: ...
    def finalize(self) -> bytes: ...
    def copy(self) -> Hash: ...

def hash_supported(algorithm: hashes.HashAlgorithm) -> bool: ...

class XOFHash:
    def __init__(self, algorithm: hashes.ExtendableOutputFunction) -> None: ...
    @property
    def algorithm(self) -> hashes.ExtendableOutputFunction: ...
    def update(self, data: Buffer) -> None: ...
    def squeeze(self, length: int) -> bytes: ...
    def copy(self) -> XOFHash: ...
