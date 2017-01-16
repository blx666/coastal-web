from coastal.api.support.forms import HelpCenterForm
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response


def sent_message(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    try:
        form = HelpCenterForm(request.POST)
        form.save()
    except:
        data = {'send': 'failed'}
        return CoastalJsonResponse(data)
    data = {'send': 'success'}
    return CoastalJsonResponse(data)
