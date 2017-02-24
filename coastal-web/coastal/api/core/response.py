from django.http import JsonResponse as CoreJsonResponse

STATUS_400 = 400
STATUS_404 = 404
STATUS_405 = 405
STATUS_1100 = 1100
STATUS_1000 = 1000
STATUS_1101 = 1101
STATUS_1200 = 1200
STATUS_1300 = 1300
STATUS_1500 = 1500
STATUS_1301 = 1301

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
    STATUS_1101: 'Please verify your profile info.',

    # 1200-1299 sns
    STATUS_1200: 'Endpoint is disabled.',

    # 1300-1399 Book Rental
    STATUS_1300: 'Sorry, this time has been booked by others. Please select any other time.',
    STATUS_1301: 'Sorry, the listing is unpublished.',

    # 1500-1599 Payment
    STATUS_1500: 'You have paid already.',
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
