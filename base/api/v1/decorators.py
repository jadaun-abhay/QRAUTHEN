from typing import Any

from drf_spectacular.utils import extend_schema, OpenApiResponse

from base.api.v1.constants import success_status_mapping

# Write your decorators here


def extend_schema_response(type: Any | None):
    def wrapper(func):
        method = getattr(func, "__name__")
        status_code = success_status_mapping.get(method)
        return extend_schema(
            responses={
                status_code: OpenApiResponse(
                    response=type,
                    description="Indicates that the operation is successfull.",
                )
            }
        )(func)

    return wrapper
