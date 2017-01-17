from coastal.api.support.forms import HelpCenterForm
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response


def sent_message(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = HelpCenterForm(request.POST)
    if form.is_valid():
        form.save()
        data = {'send': 'success'}
    else:
        data = {'send': 'failed'}
    return CoastalJsonResponse(data)
