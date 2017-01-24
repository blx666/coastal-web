from django.contrib import admin
from coastal.apps.message.models import Dialogue, Message


admin.site.register(Dialogue)
admin.site.register(Message)