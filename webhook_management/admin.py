from django.contrib import admin
from webhook_management.models import WebHookRequest, WebHookSecret
# Register your models here.

admin.site.register(WebHookRequest)
admin.site.register(WebHookSecret)

