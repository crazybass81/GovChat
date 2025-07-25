"""
AWS SSM Parameter retrieval and caching utility
"""

from __future__ import annotations

import logging
import os
import warnings
from typing import TYPE_CHECKING, Any, Literal, overload

import boto3
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import (
    resolve_max_age,
    resolve_truthy_env_var_choice,
    slice_dictionary,
)
from aws_lambda_powertools.utilities.parameters.base import (
    BaseProvider,
    transform_value,
)
from aws_lambda_powertools.utilities.parameters.constants import (
    DEFAULT_MAX_AGE_SECS,
    DEFAULT_PROVIDERS,
    SSM_PARAMETER_TIER,
    SSM_PARAMETER_TYPES,
)
from aws_lambda_powertools.utilities.parameters.exceptions import (
    GetParameterError,
    SetParameterError,
)
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parameters.types import TransformOptions
    from botocore.config import Config
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_ssm.type_defs import GetParametersResultTypeDef, PutParameterResultTypeDef

logger = logging.getLogger(__name__)


class SSMProvider(BaseProvider):
    """
    AWS Systems Manager Parameter Store Provider

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to create a boto3_client from
    boto3_client: SSMClient, optional
            Boto3 SSM Client to use, boto3_session will be ignored if both are provided

    Example
    -------
    **Retrieves a parameter value from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> value = ssm_provider.get("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from Systems Manager Parameter Store in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> ssm_provider = SSMProvider(config=config)
        >>>
        >>> value = ssm_provider.get("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves multiple parameter values from Systems Manager Parameter Store using a path prefix**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> values = ssm_provider.get_multiple("/my/path/prefix")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        /my/path/prefix/a   Parameter value a
        /my/path/prefix/b   Parameter value b
        /my/path/prefix/c   Parameter value c

    **Retrieves multiple parameter values from Systems Manager Parameter Store passing options to the SDK call**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> values = ssm_provider.get_multiple("/my/path/prefix", MaxResults=10)
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        /my/path/prefix/a   Parameter value a
        /my/path/prefix/b   Parameter value b
        /my/path/prefix/c   Parameter value c
    """

    _MAX_GET_PARAMETERS_ITEM = 10
    _ERRORS_KEY = "_errors"

    def __init__(
        self,
        config: Config | None = None,
        boto_config: Config | None = None,
        boto3_session: boto3.session.Session | None = None,
        boto3_client: SSMClient | None = None,
    ):
        """
        Initialize the SSM Parameter Store client
        """
        if config:
            warnings.warn(
                message="The 'config' parameter is deprecated in V3 and will be removed in V4. "
                "Please use 'boto_config' instead.",
                category=PowertoolsDeprecationWarning,
                stacklevel=2,
            )

        if boto3_client is None:
            boto3_session = boto3_session or boto3.session.Session()
            boto3_client = boto3_session.client("ssm", config=boto_config or config)
        self.client = boto3_client

        super().__init__(client=self.client)

    def get_multiple(  # type: ignore[override]
        self,
        path: str,
        max_age: int | None = None,
        transform: TransformOptions = None,
        raise_on_transform_error: bool = False,
        decrypt: bool | None = None,
        force_fetch: bool = False,
        recursive: bool = False,
        **sdk_options,
    ) -> dict[str, str] | dict[str, bytes] | dict[str, dict]:
        """
        Retrieve multiple parameters based on a path prefix

        Parameters
        ----------
        path: str
            Parameter path used to retrieve multiple parameters
        max_age: int, optional
            Maximum age of the cached value
        transform: str, optional
            Optional transformation of the parameter value. Supported values
            are "json" for JSON strings, "binary" for base 64 encoded
            values or "auto" which looks at the attribute key to determine the type.
        raise_on_transform_error: bool, optional
            Raises an exception if any transform fails, otherwise this will
            return a None value for each transform that failed
        force_fetch: bool, optional
            Force update even before a cached item has expired, defaults to False
        recursive: bool, optional
            If this should retrieve the parameter values recursively or not
        sdk_options: dict, optional
            Arguments that will be passed directly to the underlying API call

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve parameter values for
            a given path.
        TransformParameterError
            When the parameter provider fails to transform a parameter value.
        """

        # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
        max_age = resolve_max_age(
            env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
        )

        # If decrypt is not set, resolve it from the environment variable, defaulting to False
        decrypt = resolve_truthy_env_var_choice(
            env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
            choice=decrypt,
        )

        sdk_options["decrypt"] = decrypt
        sdk_options["recursive"] = recursive

        return super().get_multiple(
            path, max_age, transform, force_fetch, raise_on_transform_error, **sdk_options
        )

    # We break Liskov substitution principle due to differences in signatures of this method and superclass get method
    # We ignore mypy error, as changes to the signature here or in a superclass is a breaking change to users
    def get(  # type: ignore[override]
        self,
        name: str,
        max_age: int | None = None,
        transform: TransformOptions = None,
        decrypt: bool | None = None,
        force_fetch: bool = False,
        **sdk_options,
    ) -> str | bytes | dict | None:
        """
        Retrieve a parameter value or return the cached value

        Parameters
        ----------
        name: str
            Parameter name
        max_age: int, optional
            Maximum age of the cached value
        transform: str
            Optional transformation of the parameter value. Supported values
            are "json" for JSON strings and "binary" for base 64 encoded
            values.
        decrypt: bool, optional
            If the parameter value should be decrypted
        force_fetch: bool, optional
            Force update even before a cached item has expired, defaults to False
        sdk_options: dict, optional
            Arguments that will be passed directly to the underlying API call

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve a parameter value for
            a given name.
        TransformParameterError
            When the parameter provider fails to transform a parameter value.
        """

        # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
        max_age = resolve_max_age(
            env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
        )

        # If decrypt is not set, resolve it from the environment variable, defaulting to False
        decrypt = resolve_truthy_env_var_choice(
            env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
            choice=decrypt,
        )

        # Add to `decrypt` sdk_options to we can have an explicit option for this
        sdk_options["decrypt"] = decrypt

        return super().get(name, max_age, transform, force_fetch, **sdk_options)

    @overload
    def set(
        self,
        name: str,
        value: list[str],
        *,
        overwrite: bool = False,
        description: str = "",
        parameter_type: Literal["StringList"] = "StringList",
        tier: Literal["Standard", "Advanced", "Intelligent-Tiering"] = "Standard",
        kms_key_id: str | None = "None",
        **sdk_options,
    ): ...

    @overload
    def set(
        self,
        name: str,
        value: str,
        *,
        overwrite: bool = False,
        description: str = "",
        parameter_type: Literal["SecureString"] = "SecureString",
        tier: Literal["Standard", "Advanced", "Intelligent-Tiering"] = "Standard",
        kms_key_id: str,
        **sdk_options,
    ): ...

    @overload
    def set(
        self,
        name: str,
        value: str,
        *,
        overwrite: bool = False,
        description: str = "",
        parameter_type: Literal["String"] = "String",
        tier: Literal["Standard", "Advanced", "Intelligent-Tiering"] = "Standard",
        kms_key_id: str | None = None,
        **sdk_options,
    ): ...

    def set(
        self,
        name: str,
        value: str | list[str],
        *,
        overwrite: bool = False,
        description: str = "",
        parameter_type: SSM_PARAMETER_TYPES = "String",
        tier: SSM_PARAMETER_TIER = "Standard",
        kms_key_id: str | None = None,
        **sdk_options,
    ) -> PutParameterResultTypeDef:
        """
        Sets a parameter in AWS Systems Manager Parameter Store.

        Parameters
        ----------
        name: str
            The fully qualified name includes the complete hierarchy of the parameter name and name.
        value: str
            The parameter value
        overwrite: bool, optional
            If the parameter value should be overwritten, False by default
        description: str, optional
            The description of the parameter
        parameter_type: str, optional
            Type of the parameter.  Allowed values are String, StringList, and SecureString
        tier: str, optional
            The parameter tier to use. Allowed values are Standard, Advanced, and Intelligent-Tiering
        kms_key_id: str, optional
            The KMS key id to use to encrypt the parameter
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Parameter Store get_parameter API call

        Raises
        ------
        SetParameterError
            When the parameter provider fails to retrieve a parameter value for
            a given name.

        URLs:
        -------
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/put_parameter.html

        Example
        -------
        **Sets a parameter value from Systems Manager Parameter Store**

            >>> from aws_lambda_powertools.utilities import parameters
            >>>
            >>> response = parameters.set_parameter(name="/my/example/parameter", value="More Powertools")
            >>>
            >>> print(response)
            123

        Returns
        -------
        PutParameterResultTypeDef
            The dict returned by boto3.
        """
        opts = {
            "Name": name,
            "Value": value,
            "Overwrite": overwrite,
            "Type": parameter_type,
            "Tier": tier,
            "Description": description,
            **sdk_options,
        }

        if kms_key_id:
            opts["KeyId"] = kms_key_id

        try:
            return self.client.put_parameter(**opts)
        except Exception as exc:
            raise SetParameterError(f"Error setting parameter - {str(exc)}") from exc

    def _get(self, name: str, decrypt: bool = False, **sdk_options) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store

        Parameters
        ----------
        name: str
            Parameter name
        decrypt: bool, optional
            If the parameter value should be decrypted
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Parameter Store get_parameter API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["Name"] = name
        sdk_options["WithDecryption"] = decrypt

        return self.client.get_parameter(**sdk_options)["Parameter"]["Value"]

    def _get_multiple(
        self,
        path: str,
        decrypt: bool | None = None,
        recursive: bool = False,
        **sdk_options,
    ) -> dict[str, str]:
        """
        Retrieve multiple parameter values from AWS Systems Manager Parameter Store

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        decrypt: bool, optional
            If the parameter values should be decrypted
        recursive: bool, optional
            If this should retrieve the parameter values recursively or not
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Parameter Store get_parameters_by_path API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["Path"] = path
        sdk_options["WithDecryption"] = decrypt
        sdk_options["Recursive"] = recursive

        parameters = {}
        for page in self.client.get_paginator("get_parameters_by_path").paginate(**sdk_options):
            for parameter in page.get("Parameters", []):
                # Standardize the parameter name
                # The parameter name returned by SSM will contain the full path.
                # However, for readability, we should return only the part after
                # the path.
                name = parameter["Name"]
                if name.startswith(path):
                    name = name[len(path) :]
                name = name.lstrip("/")

                parameters[name] = parameter["Value"]

        return parameters

    # NOTE: When bandwidth permits, allocate a week to refactor to lower cognitive load
    def get_parameters_by_name(
        self,
        parameters: dict[str, dict],
        transform: TransformOptions = None,
        decrypt: bool | None = None,
        max_age: int | None = None,
        raise_on_error: bool = True,
    ) -> dict[str, str] | dict[str, bytes] | dict[str, dict]:
        """
        Retrieve multiple parameter values by name from SSM or cache.

        Raise_on_error decides on error handling strategy:

        - A) Default to fail-fast. Raises GetParameterError upon any error
        - B) Gracefully aggregate all parameters that failed under "_errors" key

        It transparently uses GetParameter and/or GetParameters depending on decryption requirements.

                                    ┌────────────────────────┐
                                ┌───▶  Decrypt entire batch  │─────┐
                                │   └────────────────────────┘     │     ┌────────────────────┐
                                │                                  ├─────▶ GetParameters API  │
        ┌──────────────────┐    │   ┌────────────────────────┐     │     └────────────────────┘
        │   Split batch    │─── ┼──▶│ No decryption required │─────┘
        └──────────────────┘    │   └────────────────────────┘
                                │                                        ┌────────────────────┐
                                │   ┌────────────────────────┐           │  GetParameter API  │
                                └──▶│Decrypt some but not all│───────────▶────────────────────┤
                                    └────────────────────────┘           │ GetParameters API  │
                                                                         └────────────────────┘

        Parameters
        ----------
        parameters: dict[str, dict]
            List of parameter names, and any optional overrides
        transform: str, optional
            Transforms the content from a JSON object ('json') or base64 binary string ('binary')
        decrypt: bool, optional
            If the parameter values should be decrypted
        max_age: int, optional
            Maximum age of the cached value
        raise_on_error: bool
            Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve a parameter value for a given name.

            When "_errors" reserved key is in parameters to be fetched from SSM.
        """

        # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
        max_age = resolve_max_age(
            env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
        )

        # If decrypt is not set, resolve it from the environment variable, defaulting to False
        decrypt = resolve_truthy_env_var_choice(
            env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
            choice=decrypt,
        )

        # Init potential batch/decrypt batch responses and errors
        batch_ret: dict[str, Any] = {}
        decrypt_ret: dict[str, Any] = {}
        batch_err: list[str] = []
        decrypt_err: list[str] = []
        response: dict[str, Any] = {}

        # NOTE: We fail early to avoid unintended graceful errors being replaced with their '_errors' param values
        self._raise_if_errors_key_is_present(parameters, self._ERRORS_KEY, raise_on_error)

        batch_params, decrypt_params = self._split_batch_and_decrypt_parameters(
            parameters, transform, max_age, decrypt
        )

        # NOTE: We need to find out whether all parameters must be decrypted or not to know which API to use
        ## Logic:
        ##
        ## GetParameters API -> When decrypt is used for all parameters in the the batch
        ## GetParameter  API -> When decrypt is used for one or more in the batch

        if len(decrypt_params) != len(parameters):
            decrypt_ret, decrypt_err = self._get_parameters_by_name_with_decrypt_option(
                decrypt_params, raise_on_error
            )
            batch_ret, batch_err = self._get_parameters_batch_by_name(
                batch_params, raise_on_error, decrypt=False
            )
        else:
            batch_ret, batch_err = self._get_parameters_batch_by_name(
                decrypt_params, raise_on_error, decrypt=True
            )

        # Fail-fast disabled, let's aggregate errors under "_errors" key so they can handle gracefully
        if not raise_on_error:
            response[self._ERRORS_KEY] = [*decrypt_err, *batch_err]

        return {**response, **batch_ret, **decrypt_ret}

    def _get_parameters_by_name_with_decrypt_option(
        self,
        batch: dict[str, dict],
        raise_on_error: bool,
    ) -> tuple[dict, list]:
        response: dict[str, Any] = {}
        errors: list[str] = []

        # Decided for single-thread as it outperforms in 128M and 1G + reduce timeout risk
        # see: https://github.com/aws-powertools/powertools-lambda-python/issues/1040#issuecomment-1299954613
        for parameter, options in batch.items():
            try:
                response[parameter] = self.get(
                    parameter, options["max_age"], options["transform"], options["decrypt"]
                )
            except GetParameterError:
                if raise_on_error:
                    raise
                errors.append(parameter)
                continue

        return response, errors

    def _get_parameters_batch_by_name(
        self,
        batch: dict[str, dict],
        raise_on_error: bool = True,
        decrypt: bool = False,
    ) -> tuple[dict, list]:
        """Slice batch and fetch parameters using GetParameters by max permitted"""
        errors: list[str] = []

        # Fetch each possible batch param from cache and return if entire batch is cached
        cached_params = self._get_parameters_by_name_from_cache(batch)
        if len(cached_params) == len(batch):
            return cached_params, errors

        # Slice batch by max permitted GetParameters call
        batch_ret, errors = self._get_parameters_by_name_in_chunks(
            batch, cached_params, raise_on_error, decrypt
        )

        return {**cached_params, **batch_ret}, errors

    def _get_parameters_by_name_from_cache(self, batch: dict[str, dict]) -> dict[str, Any]:
        """Fetch each parameter from batch that hasn't been expired"""
        cache = {}
        for name, options in batch.items():
            cache_key = (name, options["transform"])
            if self.has_not_expired_in_cache(cache_key):
                cache[name] = self.store[cache_key].value

        return cache

    def _get_parameters_by_name_in_chunks(
        self,
        batch: dict[str, dict],
        cache: dict[str, Any],
        raise_on_error: bool,
        decrypt: bool = False,
    ) -> tuple[dict, list]:
        """Take out differences from cache and batch, slice it and fetch from SSM"""
        response: dict[str, Any] = {}
        errors: list[str] = []

        diff = {key: value for key, value in batch.items() if key not in cache}

        for chunk in slice_dictionary(data=diff, chunk_size=self._MAX_GET_PARAMETERS_ITEM):
            response, possible_errors = self._get_parameters_by_name(
                parameters=chunk,
                raise_on_error=raise_on_error,
                decrypt=decrypt,
            )
            response.update(response)
            errors.extend(possible_errors)

        return response, errors

    def _get_parameters_by_name(
        self,
        parameters: dict[str, dict],
        raise_on_error: bool = True,
        decrypt: bool = False,
    ) -> tuple[dict[str, Any], list[str]]:
        """Use SSM GetParameters to fetch parameters, hydrate cache, and handle partial failure

        Parameters
        ----------
        parameters : dict[str, dict]
            Parameters to fetch
        raise_on_error : bool, optional
            Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

        Returns
        -------
        dict[str, Any]
            Retrieved parameters as key names and their values

        Raises
        ------
        GetParameterError
            When one or more parameters failed on fetching, and raise_on_error is enabled
        """
        ret: dict[str, Any] = {}
        batch_errors: list[str] = []
        parameter_names = list(parameters.keys())

        # All params in the batch must be decrypted
        # we return early if we hit an unrecoverable exception like InvalidKeyId/InternalServerError
        # everything else should technically be recoverable as GetParameters is non-atomic
        try:
            if decrypt:
                response = self.client.get_parameters(Names=parameter_names, WithDecryption=True)
            else:
                response = self.client.get_parameters(Names=parameter_names)
        except (self.client.exceptions.InvalidKeyId, self.client.exceptions.InternalServerError):
            return ret, parameter_names

        batch_errors = self._handle_any_invalid_get_parameter_errors(response, raise_on_error)
        transformed_params = self._transform_and_cache_get_parameters_response(
            response, parameters, raise_on_error
        )

        return transformed_params, batch_errors

    def _transform_and_cache_get_parameters_response(
        self,
        api_response: GetParametersResultTypeDef,
        parameters: dict[str, Any],
        raise_on_error: bool = True,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {}

        for parameter in api_response["Parameters"]:
            name = parameter["Name"]
            value = parameter["Value"]
            options = parameters[name]
            transform = options.get("transform")

            # NOTE: If transform is set, we do it before caching to reduce number of operations
            if transform:
                value = transform_value(name, value, transform, raise_on_error)  # type: ignore

            _cache_key = (name, options["transform"])
            self.add_to_cache(key=_cache_key, value=value, max_age=options["max_age"])

            response[name] = value

        return response

    @staticmethod
    def _handle_any_invalid_get_parameter_errors(
        api_response: GetParametersResultTypeDef,
        raise_on_error: bool = True,
    ) -> list[str]:
        """GetParameters is non-atomic. Failures don't always reflect in exceptions so we need to collect."""
        failed_parameters = api_response["InvalidParameters"]
        if failed_parameters:
            if raise_on_error:
                raise GetParameterError(f"Failed to fetch parameters: {failed_parameters}")

            return failed_parameters

        return []

    @staticmethod
    def _split_batch_and_decrypt_parameters(
        parameters: dict[str, dict],
        transform: TransformOptions,
        max_age: int,
        decrypt: bool,
    ) -> tuple[dict[str, dict], dict[str, dict]]:
        """Split parameters that can be fetched by GetParameters vs GetParameter

        Parameters
        ----------
        parameters : dict[str, dict]
            Parameters containing names as key and optional config override as value
        transform : TransformOptions
            Transform configuration
        max_age : int
            How long to cache a parameter for
        decrypt : bool
            Whether to use KMS to decrypt a parameter

        Returns
        -------
        tuple[dict[str, dict], dict[str, dict]]
            GetParameters and GetParameter parameters dict along with their overrides/globals merged
        """
        batch_parameters: dict[str, dict] = {}
        decrypt_parameters: dict[str, Any] = {}

        for parameter, options in parameters.items():
            # NOTE: TypeDict later
            _overrides = options or {}
            _overrides["transform"] = _overrides.get("transform") or transform

            # These values can be falsy (False, 0)
            if "decrypt" not in _overrides:
                _overrides["decrypt"] = decrypt

            if "max_age" not in _overrides:
                _overrides["max_age"] = max_age

            # NOTE: Split parameters who have decrypt OR have it global
            if _overrides["decrypt"]:
                decrypt_parameters[parameter] = _overrides
            else:
                batch_parameters[parameter] = _overrides

        return batch_parameters, decrypt_parameters

    @staticmethod
    def _raise_if_errors_key_is_present(
        parameters: dict, reserved_parameter: str, raise_on_error: bool
    ):
        """Raise GetParameterError if fail-fast is disabled and '_errors' key is in parameters batch"""
        if not raise_on_error and reserved_parameter in parameters:
            raise GetParameterError(
                f"You cannot fetch a parameter named '{reserved_parameter}' in graceful error mode.",
            )


@overload
def get_parameter(
    name: str,
    transform: None = None,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str: ...


@overload
def get_parameter(
    name: str,
    transform: Literal["json"],
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> dict: ...


@overload
def get_parameter(
    name: str,
    transform: Literal["binary"],
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str | bytes | dict: ...


@overload
def get_parameter(
    name: str,
    transform: Literal["auto"],
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> bytes: ...


def get_parameter(
    name: str,
    transform: TransformOptions = None,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str | bytes | dict:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    name: str
        Name of the parameter
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    decrypt: bool, optional
        If the parameter values should be decrypted
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int, optional
        Maximum age of the cached value
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Parameter Store get_parameter API call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Retrieves a parameter value from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> value = get_parameter("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value and decodes it using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> value = get_parameter("/my/parameter", transform='binary')
        >>>
        >>> print(value)
        My parameter value
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(
        env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
    )

    # If decrypt is not set, resolve it from the environment variable, defaulting to False
    decrypt = resolve_truthy_env_var_choice(
        env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
        choice=decrypt,
    )

    return DEFAULT_PROVIDERS["ssm"].get(
        name=name,
        max_age=max_age,
        transform=transform,
        force_fetch=force_fetch,
        decrypt=decrypt,
        **sdk_options,
    )


@overload
def get_parameters(
    path: str,
    transform: None = None,
    recursive: bool = True,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    raise_on_transform_error: bool = False,
    **sdk_options,
) -> dict[str, str]: ...


@overload
def get_parameters(
    path: str,
    transform: Literal["json"],
    recursive: bool = True,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    raise_on_transform_error: bool = False,
    **sdk_options,
) -> dict[str, dict]: ...


@overload
def get_parameters(
    path: str,
    transform: Literal["binary"],
    recursive: bool = True,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    raise_on_transform_error: bool = False,
    **sdk_options,
) -> dict[str, bytes]: ...


@overload
def get_parameters(
    path: str,
    transform: Literal["auto"],
    recursive: bool = True,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    raise_on_transform_error: bool = False,
    **sdk_options,
) -> dict[str, str] | dict[str, bytes] | dict[str, dict]: ...


def get_parameters(
    path: str,
    transform: TransformOptions = None,
    recursive: bool = True,
    decrypt: bool | None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    raise_on_transform_error: bool = False,
    **sdk_options,
) -> dict[str, str] | dict[str, bytes] | dict[str, dict]:
    """
    Retrieve multiple parameter values from AWS Systems Manager (SSM) Parameter Store

    For readability, we strip the path prefix name in the response.

    Parameters
    ----------
    path: str
        Path to retrieve the parameters
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    recursive: bool, optional
        If this should retrieve the parameter values recursively or not, defaults to True
    decrypt: bool, optional
        If the parameter values should be decrypted
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int, optional
        Maximum age of the cached value
    raise_on_transform_error: bool, optional
        Raises an exception if any transform fails, otherwise this will
        return a None value for each transform that failed
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Parameter Store get_parameters_by_path API call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve parameter values for
        a given path.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Retrieves parameter values from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> values = get_parameters("/my/path/prefix")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        config              Parameter value (/my/path/prefix/config)
        webhook/config      Parameter value (/my/path/prefix/webhook/config)

    **Retrieves parameter values and decodes them using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> values = get_parameters("/my/path/prefix", transform='binary')
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(
        env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
    )

    # If decrypt is not set, resolve it from the environment variable, defaulting to False
    decrypt = resolve_truthy_env_var_choice(
        env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
        choice=decrypt,
    )

    return DEFAULT_PROVIDERS["ssm"].get_multiple(
        path=path,
        max_age=max_age,
        transform=transform,
        raise_on_transform_error=raise_on_transform_error,
        force_fetch=force_fetch,
        recursive=recursive,
        decrypt=decrypt,
        **sdk_options,
    )


def set_parameter(
    name: str,
    value: str,
    *,  # force keyword arguments
    overwrite: bool = False,
    description: str = "",
    parameter_type: SSM_PARAMETER_TYPES = "String",
    tier: SSM_PARAMETER_TIER = "Standard",
    kms_key_id: str | None = None,
    **sdk_options,
) -> PutParameterResultTypeDef:
    """
    Sets a parameter in AWS Systems Manager Parameter Store.

    Parameters
    ----------
    name: str
        The fully qualified name includes the complete hierarchy of the parameter name and name.
    value: str
        The parameter value
    overwrite: bool, optional
        If the parameter value should be overwritten, False by default
    description: str, optional
        The description of the parameter
    parameter_type: str, optional
        Type of the parameter.  Allowed values are String, StringList, and SecureString
    tier: str, optional
        The parameter tier to use. Allowed values are Standard, Advanced, and Intelligent-Tiering
    kms_key_id: str, optional
        The KMS key id to use to encrypt the parameter
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Parameter Store get_parameter API call

    Raises
    ------
    SetParameterError
        When attempting to set a parameter fails.

    URLs:
    -------
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/put_parameter.html

    Example
    -------
    **Sets a parameter value from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> response = parameters.set_parameter(name="/my/example/parameter", value="More Powertools")
        >>>
        >>> print(response)
        123

    Returns
    -------
    PutParameterResultTypeDef
        The dict returned by boto3.
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].set(
        name,
        value,
        parameter_type=parameter_type,
        overwrite=overwrite,
        tier=tier,
        description=description,
        kms_key_id=kms_key_id,
        **sdk_options,
    )


@overload
def get_parameters_by_name(
    parameters: dict[str, dict],
    transform: None = None,
    decrypt: bool | None = None,
    max_age: int | None = None,
    raise_on_error: bool = True,
) -> dict[str, str]: ...


@overload
def get_parameters_by_name(
    parameters: dict[str, dict],
    transform: Literal["binary"],
    decrypt: bool | None = None,
    max_age: int | None = None,
    raise_on_error: bool = True,
) -> dict[str, bytes]: ...


@overload
def get_parameters_by_name(
    parameters: dict[str, dict],
    transform: Literal["json"],
    decrypt: bool | None = None,
    max_age: int | None = None,
    raise_on_error: bool = True,
) -> dict[str, dict[str, Any]]: ...


@overload
def get_parameters_by_name(
    parameters: dict[str, dict],
    transform: Literal["auto"],
    decrypt: bool | None = None,
    max_age: int | None = None,
    raise_on_error: bool = True,
) -> dict[str, str] | dict[str, dict]: ...


def get_parameters_by_name(
    parameters: dict[str, Any],
    transform: TransformOptions = None,
    decrypt: bool | None = None,
    max_age: int | None = None,
    raise_on_error: bool = True,
) -> dict[str, str] | dict[str, bytes] | dict[str, dict]:
    """
    Retrieve multiple parameter values by name from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    parameters: dict[str, Any]
        List of parameter names, and any optional overrides
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    decrypt: bool, optional
        If the parameter values should be decrypted
    max_age: int, optional
        Maximum age of the cached value
    raise_on_error: bool, optional
        Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

    Example
    -------

    **Retrieves multiple parameters from distinct paths from Systems Manager Parameter Store**

        from aws_lambda_powertools.utilities.parameters import get_parameters_by_name

        params = {
            "/param": {},
            "/json": {"transform": "json"},
            "/binary": {"transform": "binary"},
            "/no_cache": {"max_age": 0},
            "/api_key": {"decrypt": True},
        }

        values = get_parameters_by_name(parameters=params)
        for param_name, value in values.items():
            print(f"{param_name}: {value}")

        # "/param": value
        # "/json": value
        # "/binary": value
        # "/no_cache": value
        # "/api_key": value

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    """

    # NOTE: Decided against using multi-thread due to single-thread outperforming in 128M and 1G + timeout risk
    # see: https://github.com/aws-powertools/powertools-lambda-python/issues/1040#issuecomment-1299954613

    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(
        env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age
    )

    # If decrypt is not set, resolve it from the environment variable, defaulting to False
    decrypt = resolve_truthy_env_var_choice(
        env=os.getenv(constants.PARAMETERS_SSM_DECRYPT_ENV, "false"),
        choice=decrypt,
    )

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get_parameters_by_name(
        parameters=parameters,
        max_age=max_age,
        transform=transform,
        decrypt=decrypt,
        raise_on_error=raise_on_error,
    )
