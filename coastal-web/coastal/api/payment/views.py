from coastal.api.core.decorators import login_required
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.payment.stripe import add_card, get_card_list


@login_required
def stripe_add_card(request):
    """
    Add credit card for stripe payment
    :param request: request.POST data {"token": "tok_19UiVAIwZ8ZTWo9bF8Z6L6Ua"}
    :return:
    """
    try:
        add_card(request.user, request.POST.get('token'))
    except Exception:
        CoastalJsonResponse({"add_card": "failed"})

    return CoastalJsonResponse({
        "add_card": "success",
        "card_list": get_card_list(request.user)
    })
