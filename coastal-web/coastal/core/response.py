import json
from django.http import HttpResponse


class JsonResponse(HttpResponse):
    def __init__(self, data=None, status=0, message="ok"):
        res_data = {
            'status': status,
            'message': message,
            'result': data,
        }
        super(JsonResponse, self).__init__(content=json.dumps(res_data), content_type='application/json')


STATUS_404 = 404
