# ruff: noqa: FA100
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Union

from aws_lambda_powertools.event_handler.openapi.compat import model_rebuild
from aws_lambda_powertools.event_handler.openapi.exceptions import SchemaValidationError
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, model_validator

MODEL_CONFIG_ALLOW = ConfigDict(extra="allow")
MODEL_CONFIG_IGNORE = ConfigDict(extra="ignore")

"""
The code defines Pydantic models for the various OpenAPI objects like OpenAPI, PathItem, Operation, Parameter etc.
These models can be used to parse OpenAPI JSON/YAML files into Python objects, or generate OpenAPI from Python data.
"""


class OpenAPIExtensions(BaseModel):
    """
    This class serves as a Pydantic proxy model to add OpenAPI extensions.

    OpenAPI extensions are arbitrary fields, so we remove openapi_extensions when dumping
    and add only the provided value in the schema.
    """

    openapi_extensions: Optional[Dict[str, Any]] = None

    # If the 'openapi_extensions' field is present in the 'values' dictionary,
    # And if the extension starts with x- (must respect the RFC)
    # update the 'values' dictionary with the contents of 'openapi_extensions',
    # and then remove the 'openapi_extensions' field from the 'values' dictionary
    model_config = {"extra": "allow"}

    @model_validator(mode="before")
    def serialize_openapi_extension_v2(self):
        if isinstance(self, dict) and self.get("openapi_extensions"):
            openapi_extension_value = self.get("openapi_extensions")

            for extension_key in openapi_extension_value:
                if not str(extension_key).startswith("x-"):
                    raise SchemaValidationError("An OpenAPI extension key must start with x-")

            self.update(openapi_extension_value)
            self.pop("openapi_extensions", None)

        return self


# https://swagger.io/specification/#contact-object
class Contact(BaseModel):
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    email: Optional[str] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#license-object
class License(BaseModel):
    name: str
    identifier: Optional[str] = None
    url: Optional[AnyUrl] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#info-object
class Info(BaseModel):
    title: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None  # noqa: A003
    version: str
    summary: Optional[str] = None

    model_config = MODEL_CONFIG_IGNORE


# https://swagger.io/specification/#server-variable-object
class ServerVariable(BaseModel):
    enum: Annotated[Optional[List[str]], Field(min_length=1)] = None
    default: str
    description: Optional[str] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#server-object
class Server(OpenAPIExtensions):
    url: Union[AnyUrl, str]
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#reference-object
class Reference(BaseModel):
    ref: str = Field(alias="$ref")


# https://swagger.io/specification/#discriminator-object
class Discriminator(BaseModel):
    propertyName: str
    mapping: Optional[Dict[str, str]] = None


# https://swagger.io/specification/#xml-object
class XML(BaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    prefix: Optional[str] = None
    attribute: Optional[bool] = None
    wrapped: Optional[bool] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#external-documentation-object
class ExternalDocumentation(BaseModel):
    description: Optional[str] = None
    url: AnyUrl

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#schema-object
class Schema(BaseModel):
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-json-schema-core-vocabu
    # Core Vocabulary
    schema_: Optional[str] = Field(default=None, alias="$schema")
    vocabulary: Optional[str] = Field(default=None, alias="$vocabulary")
    id: Optional[str] = Field(default=None, alias="$id")  # noqa: A003
    anchor: Optional[str] = Field(default=None, alias="$anchor")
    dynamicAnchor: Optional[str] = Field(default=None, alias="$dynamicAnchor")
    ref: Optional[str] = Field(default=None, alias="$ref")
    dynamicRef: Optional[str] = Field(default=None, alias="$dynamicRef")
    defs: Optional[Dict[str, "SchemaOrBool"]] = Field(default=None, alias="$defs")
    comment: Optional[str] = Field(default=None, alias="$comment")
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-a-vocabulary-for-applying-s
    # A Vocabulary for Applying Subschemas
    allOf: Optional[List["SchemaOrBool"]] = None
    anyOf: Optional[List["SchemaOrBool"]] = None
    oneOf: Optional[List["SchemaOrBool"]] = None
    not_: Optional["SchemaOrBool"] = Field(default=None, alias="not")
    if_: Optional["SchemaOrBool"] = Field(default=None, alias="if")
    then: Optional["SchemaOrBool"] = None
    else_: Optional["SchemaOrBool"] = Field(default=None, alias="else")
    dependentSchemas: Optional[Dict[str, "SchemaOrBool"]] = None
    prefixItems: Optional[List["SchemaOrBool"]] = None
    # MAINTENANCE: uncomment and remove below when deprecating Pydantic v1
    # MAINTENANCE: It generates a list of schemas for tuples, before prefixItems was available
    # MAINTENANCE: items: Optional["SchemaOrBool"] = None
    items: Optional[Union["SchemaOrBool", List["SchemaOrBool"]]] = None
    contains: Optional["SchemaOrBool"] = None
    properties: Optional[Dict[str, "SchemaOrBool"]] = None
    patternProperties: Optional[Dict[str, "SchemaOrBool"]] = None
    additionalProperties: Optional["SchemaOrBool"] = None
    propertyNames: Optional["SchemaOrBool"] = None
    unevaluatedItems: Optional["SchemaOrBool"] = None
    unevaluatedProperties: Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-structural
    # A Vocabulary for Structural Validation
    type: Optional[str] = None  # noqa: A003
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None
    multipleOf: Optional[float] = Field(default=None, gt=0)
    maximum: Optional[float] = None
    exclusiveMaximum: Optional[float] = None
    minimum: Optional[float] = None
    exclusiveMinimum: Optional[float] = None
    maxLength: Optional[int] = Field(default=None, ge=0)
    minLength: Optional[int] = Field(default=None, ge=0)
    pattern: Optional[str] = None
    maxItems: Optional[int] = Field(default=None, ge=0)
    minItems: Optional[int] = Field(default=None, ge=0)
    uniqueItems: Optional[bool] = None
    maxContains: Optional[int] = Field(default=None, ge=0)
    minContains: Optional[int] = Field(default=None, ge=0)
    maxProperties: Optional[int] = Field(default=None, ge=0)
    minProperties: Optional[int] = Field(default=None, ge=0)
    required: Optional[List[str]] = None
    dependentRequired: Optional[Dict[str, Set[str]]] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-vocabularies-for-semantic-c
    # Vocabularies for Semantic Content With "format"
    format: Optional[str] = None  # noqa: A003
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-the-conten
    # A Vocabulary for the Contents of String-Encoded Data
    contentEncoding: Optional[str] = None
    contentMediaType: Optional[str] = None
    contentSchema: Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    # A Vocabulary for Basic Meta-Data Annotations
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    deprecated: Optional[bool] = None
    readOnly: Optional[bool] = None
    writeOnly: Optional[bool] = None
    examples: Optional[List["Example"]] = None
    # Ref: OpenAPI 3.0.0: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.0.md#schema-object
    # Schema Object
    discriminator: Optional[Discriminator] = None
    xml: Optional[XML] = None
    externalDocs: Optional[ExternalDocumentation] = None

    model_config = MODEL_CONFIG_ALLOW


# Ref: https://json-schema.org/draft/2020-12/json-schema-core.html#name-json-schema-documents
# A JSON Schema MUST be an object or a boolean.
SchemaOrBool = Union[Schema, bool]


# https://swagger.io/specification/#example-object
class Example(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Optional[Any] = None
    externalValue: Optional[AnyUrl] = None

    model_config = MODEL_CONFIG_ALLOW


class ParameterInType(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


# https://swagger.io/specification/#encoding-object
class Encoding(BaseModel):
    contentType: Optional[str] = None
    headers: Optional[Dict[str, Union["Header", Reference]]] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#media-type-object
class MediaType(BaseModel):
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    encoding: Optional[Dict[str, Encoding]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#parameter-object
class ParameterBase(BaseModel):
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    # Serialization rules for simple scenarios
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = None
    schema_: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    # Serialization rules for more complex scenarios
    content: Optional[Dict[str, MediaType]] = None

    model_config = MODEL_CONFIG_ALLOW


class Parameter(ParameterBase):
    name: str
    in_: ParameterInType = Field(alias="in")


class Header(ParameterBase):
    pass


# https://swagger.io/specification/#request-body-object
class RequestBody(BaseModel):
    description: Optional[str] = None
    content: Dict[str, MediaType]
    required: Optional[bool] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#link-object
class Link(BaseModel):
    operationRef: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[Dict[str, Union[Any, str]]] = None
    requestBody: Optional[Union[Any, str]] = None
    description: Optional[str] = None
    server: Optional[Server] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#response-object
class Response(BaseModel):
    description: str
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    content: Optional[Dict[str, MediaType]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#tag-object
class Tag(BaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#operation-object
class Operation(OpenAPIExtensions):
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Optional[List[Union[Parameter, Reference]]] = None
    requestBody: Optional[Union[RequestBody, Reference]] = None
    # Using Any for Specification Extensions
    responses: Optional[Dict[int, Union[Response, Any]]] = None
    callbacks: Optional[Dict[str, Union[Dict[str, "PathItem"], Reference]]] = None
    deprecated: Optional[bool] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    servers: Optional[List[Server]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#path-item-object
class PathItem(BaseModel):
    ref: Optional[str] = Field(default=None, alias="$ref")
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None
    servers: Optional[List[Server]] = None
    parameters: Optional[List[Union[Parameter, Reference]]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#security-scheme-object
class SecuritySchemeType(Enum):
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"


class SecurityBase(OpenAPIExtensions):
    type_: SecuritySchemeType = Field(alias="type")
    description: Optional[str] = None

    model_config = {"extra": "allow", "populate_by_name": True}


class APIKeyIn(Enum):
    query = "query"
    header = "header"
    cookie = "cookie"


class APIKey(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.apiKey, alias="type")
    in_: APIKeyIn = Field(alias="in")
    name: str


class HTTPBase(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.http, alias="type")
    scheme: str


class HTTPBearer(HTTPBase):
    scheme: Literal["bearer"] = "bearer"
    bearerFormat: Optional[str] = None


class OAuthFlow(BaseModel):
    refreshUrl: Optional[str] = None
    scopes: Dict[str, str] = {}

    model_config = MODEL_CONFIG_ALLOW


class OAuthFlowImplicit(OAuthFlow):
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlow):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlow):
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    authorizationUrl: str
    tokenUrl: str


class OAuthFlows(BaseModel):
    implicit: Optional[OAuthFlowImplicit] = None
    password: Optional[OAuthFlowPassword] = None
    clientCredentials: Optional[OAuthFlowClientCredentials] = None
    authorizationCode: Optional[OAuthFlowAuthorizationCode] = None

    model_config = MODEL_CONFIG_ALLOW


class OAuth2(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.oauth2, alias="type")
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.openIdConnect,
        alias="type",
    )
    openIdConnectUrl: str


SecurityScheme = Union[APIKey, HTTPBase, OAuth2, OpenIdConnect, HTTPBearer]


# https://swagger.io/specification/#components-object
class Components(BaseModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]] = None
    responses: Optional[Dict[str, Union[Response, Reference]]] = None
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None
    examples: Optional[Dict[str, Union[Example, Reference]]] = None
    requestBodies: Optional[Dict[str, Union[RequestBody, Reference]]] = None
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    securitySchemes: Optional[Dict[str, Union[SecurityScheme, Reference]]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None
    # Using Any for Specification Extensions
    callbacks: Optional[Dict[str, Union[Dict[str, PathItem], Reference, Any]]] = None
    pathItems: Optional[Dict[str, Union[PathItem, Reference]]] = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#openapi-object
class OpenAPI(OpenAPIExtensions):
    openapi: str
    info: Info
    jsonSchemaDialect: Optional[str] = None
    servers: Optional[List[Server]] = None
    # Using Any for Specification Extensions
    paths: Optional[Dict[str, Union[PathItem, Any]]] = None
    webhooks: Optional[Dict[str, Union[PathItem, Reference]]] = None
    components: Optional[Components] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None

    model_config = MODEL_CONFIG_ALLOW


model_rebuild(Schema)
model_rebuild(Operation)
model_rebuild(Encoding)
