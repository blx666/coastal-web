from functools import wraps

from django.utils.decorators import available_attrs
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response


def login_required(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return CoastalJsonResponse(status=response.STATUS_1100)
    return _wrapped_view