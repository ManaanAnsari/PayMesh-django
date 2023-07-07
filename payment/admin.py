from django.contrib import admin
from payment.models import SupportedChain, SupportedNetwork, SupportedToken, Invoice, PayoutTransaction, RefundTransaction, BlockchainTransaction

# Register your models here.

admin.site.register(SupportedChain)
admin.site.register(SupportedNetwork)
admin.site.register(SupportedToken)
admin.site.register(Invoice)
admin.site.register(PayoutTransaction)
admin.site.register(RefundTransaction)
admin.site.register(BlockchainTransaction)



