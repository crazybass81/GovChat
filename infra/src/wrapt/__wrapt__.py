import os

from .wrappers import (
    BoundFunctionWrapper,
    CallableObjectProxy,
    FunctionWrapper,
    ObjectProxy,
    PartialCallableObjectProxy,
    _FunctionWrapperBase,
)

try:
    if not os.environ.get("WRAPT_DISABLE_EXTENSIONS"):
        from ._wrappers import (
            BoundFunctionWrapper,
            CallableObjectProxy,
            FunctionWrapper,
            ObjectProxy,
            PartialCallableObjectProxy,
            _FunctionWrapperBase,
        )

except ImportError:
    pass
