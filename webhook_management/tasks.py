
from backend.celery import app
from user_management.models import User, UserGateWeb3Account
from django.conf import settings
from celery import shared_task
import datetime
import os
import json
from moralis import evm_api
from payment.models import Invoice, RefundTransaction, PayoutTransaction, BlockchainTransaction
from web3.auto import w3
from backend.helpers import utc, encrypt_message, stringToBytes, decrypt_message
from backend.services.EVM import EVM
from webhook_management.models import WebHookSecret, WebHookRequest
import requests



def webhook_request(event:str, data:dict, user_id:int):
    if event in WebHookRequest.EVENT_TYPES_LIST:
        for wh in WebHookSecret.objects.filter(user__id = user_id,enabled=True):
            data.update({"event": event})
            
            if data.get("metadata", None) is None:
                data.update({"metadata": {}})
                if data.get("invoice_id", None) is not None:
                    if Invoice.objects.filter(id=data["invoice_id"]).exists():
                        inv = Invoice.objects.get(id=data["invoice_id"])
                        if inv.metadata:
                            data["metadata"] = inv.metadata
                
            
            data = encrypt_message(json.dumps(data), stringToBytes(wh.sec_key))
            data = {"data": data}
            whr = WebHookRequest(
                webhook = wh,
                event_type = event,
                request_data = data,
            )
            whr.save()
            send_webhook_request.delay(whr.id)
    else:
        print("webhook event not supported")


@shared_task(bind=True)
def send_webhook_request(self, webhook_request_id:int):
    print("processing webhook request")
    whr = WebHookRequest.objects.get(id=webhook_request_id)
    wh = whr.webhook
    whr.request_status = "PROCESSING"
    whr.save()
    whr.request_sent_at = datetime.datetime.now()
    try:
        response = requests.post(wh.endpoint, json=whr.request_data)
        whr.response_status_code = response.status_code
        if response.status_code == 200:
            whr.request_status = "SUCCESSFUL"
        else:
            whr.request_status = "FAILED"
        whr.save()
    except Exception as e:
        whr.request_status = "FAILED"
        whr.save()
        return {"message": "error", "error": str(e)}
    
    
def test_webhook_request(webhook_id:int, payload:str):
    print("processing webhook request")
    wh = WebHookSecret.objects.get(id=webhook_id)
    data = json.loads(decrypt_message(payload, stringToBytes(wh.sec_key)))
    return data

    

 

