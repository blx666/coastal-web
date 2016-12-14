from django.http import JsonResponse as CoreJsonResponse

STATUS_400 = 400
STATUS_404 = 404
STATUS_405 = 405
STATUS_1100 = 1100
STATUS_1000 = 1000

STATUS_CODE = {
    0: 'ok',

    # The following codes are error codes
    # 0-999 Http Remain Status Code
    STATUS_400: 'Request Params Error',
    STATUS_404: 'The record is not found.',
    STATUS_405: 'The request method is not allowed.',

    # 1000-1099 Account Register & Login
    STATUS_1000: 'The username and password are not matched.',
    STATUS_1100: 'The user is not login.',
}


class CoastalJsonResponse(CoreJsonResponse):
    def __init__(self, data=None, status=0, message=''):
        if not message:
            message = STATUS_CODE.get(status, 'error')

        res_data = {
            'status': status,
            'message': message,
            'result': data,
        }
        super(CoastalJsonResponse, self).__init__(res_data)
