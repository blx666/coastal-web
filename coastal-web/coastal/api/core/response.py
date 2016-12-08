import json
from django.http import HttpResponse
from django.http import JsonResponse as CoreJsonResponse

STATUS_CODE = {
    0: 'ok',

    # The following codes are error codes
    # 0-999 Http Remain Status Code
    400: 'Request Params Error',
    404: 'The record is not found.',
    405: 'The request method is not allowed.',

    # 1000-1099 Account Register & Login
    1000: 'The username and password are not matched.',
}


class CoastalJsonResponse(CoreJsonResponse):
    def __init__(self, data=None, status=0, message=''):
        if not message:
            message = STATUS_CODE.get(status, status > 0 and 'error' or 'ok')

        res_data = {
            'status': status,
            'message': message,
            'result': data,
        }
        super(CoastalJsonResponse, self).__init__(res_data)


class JsonResponse(HttpResponse):
    def __init__(self, data=None, status=0, message="ok"):
        res_data = {
            'status': status,
            'message': message,
            'result': data,
        }
        super(JsonResponse, self).__init__(content=json.dumps(res_data), content_type='application/json')

