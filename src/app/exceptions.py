from pydantic.errors import PydanticErrorCodes


class DispatchException(Exception):
    pass


class DispatchPluginException(DispatchException):
    pass


class NotFoundError(PydanticErrorCodes):
    code = "not_found"
    msg_template = "{msg}"


class FieldNotFoundError(PydanticErrorCodes):
    code = "not_found.field"
    msg_template = "{msg}"


class ModelNotFoundError(PydanticErrorCodes):
    code = "not_found.model"
    msg_template = "{msg}"


class ExistsError(PydanticErrorCodes):
    code = "exists"
    msg_template = "{msg}"


class InvalidConfigurationError(PydanticErrorCodes):
    code = "invalid.configuration"
    msg_template = "{msg}"


class InvalidFilterError(PydanticErrorCodes):
    code = "invalid.filter"
    msg_template = "{msg}"


class InvalidUsernameError(PydanticErrorCodes):
    code = "invalid.username"
    msg_template = "{msg}"


class InvalidPasswordError(PydanticErrorCodes):
    code = "invalid.password"
    msg_template = "{msg}"
