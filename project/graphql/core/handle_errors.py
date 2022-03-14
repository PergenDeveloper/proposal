from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ValidationError,
)
import graphene

from .utils.error_codes import get_error_code_from_error
from .utils.common import snake_to_camel_case


def validation_error_to_error_type(
    validation_error: ValidationError, error_type_class
) -> list:
    """Convert a ValidationError into a list of Error types."""
    err_list = []
    error_class_fields = set(error_type_class._meta.fields.keys())
    if hasattr(validation_error, "error_dict"):
        # convert field errors
        for field, field_errors in validation_error.error_dict.items():
            field = None if field == NON_FIELD_ERRORS else snake_to_camel_case(field)
            for err in field_errors:
                error = error_type_class(
                    field=field,
                    message=err.messages[0],
                    code=get_error_code_from_error(err),
                )
                attach_error_params(error, err.params, error_class_fields)
                err_list.append(error)
    else:
        # convert non-field errors
        for err in validation_error.error_list:
            error = error_type_class(
                message=err.messages[0],
                code=get_error_code_from_error(err),
            )
            attach_error_params(error, err.params, error_class_fields)
            err_list.append(error)
    return err_list


def get_error_fields(error_type_class):
    error_field = graphene.Field(
        graphene.List(
            graphene.NonNull(error_type_class),
            description="List of errors that occurred executing the mutation.",
        ),
        default_value=[],
        required=True,
    )
    return {"errors": error_field}


def attach_error_params(error, params: dict, error_class_fields: set):
    if not params:
        return {}
    # If some of the params key overlap with error class fields
    # attach param value to the error
    error_fields_in_params = set(params.keys()) & error_class_fields
    for error_field in error_fields_in_params:
        setattr(error, error_field, params[error_field])