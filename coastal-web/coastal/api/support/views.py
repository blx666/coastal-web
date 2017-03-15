from coastal.api.support.forms import HelpCenterForm
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response
from coastal.api import defines as defs


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


def setting(request):
    data = {
        'expire_time': defs.EXPIRATION_TIME,
        'expire_time_display': '%s hours' % defs.EXPIRATION_TIME,
    }
    return CoastalJsonResponse(data)
