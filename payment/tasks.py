
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
from backend.helpers import utc
from backend.services.EVM import EVM
from webhook_management.tasks import webhook_request


# @app.task(bind=True)
@shared_task(bind=True)
def test_foo(self,test_str="hello world"):
    print(test_str)
    return test_str

def getMoralisSupportedChains():
    return ['eth', 'goerli', 'sepolia', 'polygon', 'mumbai', 'bsc', 'bsc testnet', 'avalanche', 'fantom', 'cronos', 'palm', 'arbitrum']




@shared_task(bind=True)
def mark_expired_invoices(self):
    # get all the invoices to check
    invs = Invoice.objects.filter(status="CREATED")
    for inv in invs:
        if (inv.created_at + datetime.timedelta(minutes=inv.expiry_mins)) < datetime.datetime.now().replace(tzinfo=utc):
            inv.status = "EXPIRED"
            inv.save()
            # send webhook event INVOICE_EXPIRED
            webhook_request("INVOICE_EXPIRED", {"invoice_id":inv.id}, inv.receiver.id)
            


@shared_task(bind=True)
def moralis_invoice_status(self,inv_id):
    inv = Invoice.objects.get(pk=inv_id)
    if (inv.created_at + datetime.timedelta(minutes=inv.expiry_mins)) < datetime.datetime.now().replace(tzinfo=utc):
        inv.status = "EXPIRED"
        inv.save()
        # send webhook event INVOICE_EXPIRED
        webhook_request("INVOICE_EXPIRED", {"invoice_id":inv.id}, inv.receiver.id)
        return False
    if inv.status == "CREATED":
        inv.status = "PROCESSING"
        inv.save()
        if w3.is_address(inv.token.contract_address):
            if inv.token.network.network_name in getMoralisSupportedChains():
                params = {
                    "wallet_addresses": [inv.payment_account_address],
                    "chain": inv.token.network.network_name,
                    "limit":1
                }
                print(params)
                result = evm_api.token.get_erc20_transfers(
                    api_key=settings.MORALIS_API_KEY,
                    params=params,
                )
                if len(result['result']):
                    for res in result["result"]:
                        print(res["contract_address"] , inv.token.contract_address)
                        if w3.to_checksum_address(res["contract_address"]) == w3.to_checksum_address(inv.token.contract_address):
                            if float(res.get("value_decimal",0)) == inv.amount:
                                print("paid!")
                                inv.status = "SUCCESSFUL"
                                inv.customer_address = res["from_wallet"]
                                inv.amount_paid = inv.amount
                                inv.transacrion_details = json.dumps(res)
                                inv.message = "payment successful"
                                inv.save()
                                # send event INVOICE_SUCCESSFUL
                                webhook_request("INVOICE_SUCCESSFUL", {"invoice_id":inv.id}, inv.receiver.id)
                                pt = PayoutTransaction(
                                    invoice=inv,
                                    amount_to_pay = inv.amount
                                    # fee_amount = inv.amount * settings.TRX_FEES_PERC,
                                    # fee_perc = settings.TRX_FEES_PERC
                                )
                                pt.save()
                                return True
                            else:
                                print("amount missmatch")
                                inv.amount_paid = float(res["value_decimal"])
                                inv.customer_address = res["from_wallet"]
                                inv.transacrion_details = json.dumps(res)
                                inv.message = "amount missmatch"
                                inv.status = "FAILED"
                                inv.save()
                                # send webhook INVOICE_FAILED
                                webhook_request("INVOICE_FAILED", {"invoice_id":inv.id,"message":inv.message}, inv.receiver.id)
                                rt = RefundTransaction(
                                    invoice=inv,
                                    amount_to_pay = inv.amount_paid
                                    # fee_amount = inv.amount_paid * settings.REFUND_FEES_PERC,
                                    # fee_perc = settings.REFUND_FEES_PERC
                                )
                                rt.save()
                                inv.message = "amount missmatched refund issued id:#"+str(rt.id)
                                inv.save()
                                # return the amount to the user (after charging a fee)
                                return False
                        else:
                            # mark it as failed
                            inv.status = "FAILED"
                            inv.message = "some different token was paid!"
                            print("some different token was paid!")
                            inv.save()
                            webhook_request("INVOICE_FAILED", {"invoice_id":inv.id,"message":inv.message}, inv.receiver.id)
                            # send webhook INVOICE_FAILED
                            # todo : flag it for review and support team
                            return False
                # else:
                #     print("not paid yet!")
            else:
                inv.message = "not a supported chain"
                inv.status = "UNDER_REVIEW"
                # send webhook INVOICE_UNDER_REVIEW
                inv.save()
                webhook_request("INVOICE_UNDER_REVIEW", {"invoice_id":inv.id,"message":inv.message}, inv.receiver.id)
                print("not a supported chain")
        else:
            inv.message = "not a valid token address"
            inv.status = "UNDER_REVIEW"
            # send webhook INVOICE_UNDER_REVIEW
            inv.save()
            webhook_request("INVOICE_UNDER_REVIEW", {"invoice_id":inv.id,"message":inv.message}, inv.receiver.id)
            print("not a valid token address")
        inv.status = "CREATED"
        inv.save()


# moralis to check status
@shared_task(bind=True)
def check_status(self):
    # get all the invoices to check
    invs = Invoice.objects.filter(status="CREATED")
    for inv in invs:
        moralis_invoice_status.delay(inv.id)
        
        
@shared_task(bind=True)
def process_payout_trx(self, trx_id):
    trx = PayoutTransaction.objects.get(pk=trx_id)
    if trx.status == "CREATED":
        trx.status = "PROCESSING"
        trx.save()
        web3_obj = EVM(trx.invoice.token.network)
        if web3_obj.w3:
            # get the user trx account
            # check its balance 
            user = trx.invoice.receiver
            if UserGateWeb3Account.objects.filter(user=user,address_type = "EVM").exists():
                gate_acc = UserGateWeb3Account.objects.filter(user=user,address_type = "EVM").last()
                # check balance here itself
                native_bal = web3_obj.native_get_balance(gate_acc.address)
                print(native_bal)
                if native_bal:
                    if native_bal>0.01:
                        # transfer the amount to the invoice account for gas fees
                        gas_trx_status,gas_trx_data = web3_obj.native_transfer(gate_acc.address, gate_acc.private_key, trx.invoice.payment_account_address, 0.01)
                        bt = BlockchainTransaction(
                            status = "SUCCESSFUL" if gas_trx_status else "FAILED",
                            transaction_type = "GAS",
                            payout_transaction = trx,
                            message = gas_trx_data.get("message",None),
                            network = trx.invoice.token.network,
                            user = user,
                            transaction_hash = gas_trx_data.get("transaction_hash",None),
                            transacrion_details = json.dumps(gas_trx_data.get("transaction_receipt",{}))
                        )
                        bt.save()
                        if gas_trx_status:
                            # transfer the token from the invoice account to the user account
                            erc_20_trx_status, erc_20_trx_data = web3_obj.erc20_transfer(
                                from_address=trx.invoice.payment_account_address, 
                                from_private_key_enc=trx.invoice.payment_account_address_private_key, 
                                # todo: chenge to users address
                                to_address=gate_acc.address, 
                                amount_ether=trx.amount_to_pay,
                                contract_address=trx.invoice.token.contract_address
                            )
                            bt = BlockchainTransaction(
                                status = "SUCCESSFUL" if erc_20_trx_status else "FAILED",
                                transaction_type = "ERC20",
                                payout_transaction = trx,
                                message = erc_20_trx_data.get("message",None),
                                network = trx.invoice.token.network,
                                user = user,
                                transaction_hash = erc_20_trx_data.get("transaction_hash",None),
                                transacrion_details = json.dumps(erc_20_trx_data.get("transaction_receipt",{}))
                            )
                            bt.save()
                            if erc_20_trx_status:
                                # todo: transfer the fees to the platform account
                                # transfer the remaining native bal back to the trx account
                                close_wallet_trx_status, close_wallet_trx_data = web3_obj.close_wallet(
                                    from_address=trx.invoice.payment_account_address,
                                    from_private_key_enc=trx.invoice.payment_account_address_private_key,
                                    to_address=gate_acc.address
                                )
                                
                                bt = BlockchainTransaction(
                                    status = "SUCCESSFUL" if close_wallet_trx_status else "FAILED",
                                    transaction_type = "CLOSE_WALLET",
                                    payout_transaction = trx,
                                    message = close_wallet_trx_data.get("message",None),
                                    network = trx.invoice.token.network,
                                    user = user,
                                    transaction_hash = close_wallet_trx_data.get("transaction_hash",None),
                                    transacrion_details = json.dumps(close_wallet_trx_data.get("transaction_receipt",{}))
                                )
                                bt.save()
                                
                                if close_wallet_trx_status:
                                    # update the trx status
                                    trx.status = "SUCCESSFUL"
                                    # webhook PAYOUT_SUCCESSFUL
                                    trx.save()
                                    webhook_request("PAYOUT_SUCCESSFUL", {"invoice_id":trx.invoice.id}, trx.invoice.receiver.id)
                                    return True
                                else:
                                    trx.status = "FAILED"
                                    trx.message = close_wallet_trx_data.get("message",None)
                                    trx.save()
                                    # webhook PAYOUT_FAILED
                                    webhook_request("PAYOUT_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                            else:
                                trx.status = "FAILED"
                                trx.message = erc_20_trx_data.get("message",None)
                                trx.save()
                                # webhook PAYOUT_FAILED
                                webhook_request("PAYOUT_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                        else:
                            trx.status = "FAILED"
                            trx.message = gas_trx_data.get("message",None)
                            trx.save()
                            # webhook PAYOUT_FAILED
                            webhook_request("PAYOUT_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                    else:
                        trx.status = "CREATED"
                        trx.message = "eth balance is less than 0.01"
                        trx.save()
                else:
                    trx.status = "CREATED"
                    trx.message = "eth balance is less than 0.01"
                    trx.save()
            else:
                trx.status = "FAILED"
                trx.message = "user has no web3 account"
                trx.save()
                # webhook PAYOUT_FAILED
                webhook_request("PAYOUT_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
        else:
            trx.status = "FAILED"
            trx.message = "no valid web3 connection"
            trx.save()
            # webhook PAYOUT_FAILED
            webhook_request("PAYOUT_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                
    
    
@shared_task(bind=True)
def process_payout(self):
    print("processing payout")
    trxs = PayoutTransaction.objects.filter(status="CREATED")
    for trx in trxs:
        process_payout_trx.delay(trx.id)
        

@shared_task(bind=True)
def process_refund_trx(self, trx_id):
    trx = RefundTransaction.objects.get(pk=trx_id)
    if trx.status == "CREATED":
        trx.status = "PROCESSING"
        trx.save()
        if trx.invoice.customer_address is not None and trx.invoice.amount_paid:
            web3_obj = EVM(trx.invoice.token.network)
            if web3_obj.w3:
                # get the user trx account
                # check its balance 
                user = trx.invoice.receiver
                if UserGateWeb3Account.objects.filter(user=user,address_type = "EVM").exists():
                    gate_acc = UserGateWeb3Account.objects.filter(user=user,address_type = "EVM").last()
                    # check balance here itself
                    native_bal = web3_obj.native_get_balance(gate_acc.address)
                    print(native_bal)
                    if native_bal:
                        if native_bal>0.01:
                            # transfer the amount to the invoice account for gas fees
                            gas_trx_status,gas_trx_data = web3_obj.native_transfer(gate_acc.address, gate_acc.private_key, trx.invoice.payment_account_address, 0.01)
                            bt = BlockchainTransaction(
                                status = "SUCCESSFUL" if gas_trx_status else "FAILED",
                                transaction_type = "GAS",
                                refund_transaction = trx,
                                message = gas_trx_data.get("message",None),
                                network = trx.invoice.token.network,
                                user = user,
                                transaction_hash = gas_trx_data.get("transaction_hash",None),
                                transacrion_details = json.dumps(gas_trx_data.get("transaction_receipt",{}))
                            )
                            bt.save()
                            if gas_trx_status:
                                # transfer the token from the invoice account to the user account
                                erc_20_trx_status, erc_20_trx_data = web3_obj.erc20_transfer(
                                    from_address=trx.invoice.payment_account_address, 
                                    from_private_key_enc=trx.invoice.payment_account_address_private_key, 
                                    # todo: chenge to users address
                                    to_address=trx.invoice.customer_address, 
                                    amount_ether=trx.invoice.amount_paid,
                                    contract_address=trx.invoice.token.contract_address
                                )
                                bt = BlockchainTransaction(
                                    status = "SUCCESSFUL" if erc_20_trx_status else "FAILED",
                                    transaction_type = "ERC20",
                                    refund_transaction = trx,
                                    message = erc_20_trx_data.get("error",None) if erc_20_trx_data.get("error",None) else erc_20_trx_data.get("message",None),
                                    network = trx.invoice.token.network,
                                    user = user,
                                    transaction_hash = erc_20_trx_data.get("transaction_hash",None),
                                    transacrion_details = json.dumps(erc_20_trx_data.get("transaction_receipt",{}))
                                )
                                bt.save()
                                if erc_20_trx_status:
                                    # todo: transfer the fees to the platform account
                                    # transfer the remaining native bal back to the trx account
                                    close_wallet_trx_status, close_wallet_trx_data = web3_obj.close_wallet(
                                        from_address=trx.invoice.payment_account_address,
                                        from_private_key_enc=trx.invoice.payment_account_address_private_key,
                                        to_address=gate_acc.address
                                    )
                                    
                                    bt = BlockchainTransaction(
                                        status = "SUCCESSFUL" if close_wallet_trx_status else "FAILED",
                                        transaction_type = "CLOSE_WALLET",
                                        refund_transaction = trx,
                                        message = close_wallet_trx_data.get("message",None),
                                        network = trx.invoice.token.network,
                                        user = user,
                                        transaction_hash = close_wallet_trx_data.get("transaction_hash",None),
                                        transacrion_details = json.dumps(close_wallet_trx_data.get("transaction_receipt",{}))
                                    )
                                    bt.save()
                                    
                                    if close_wallet_trx_status:
                                        # update the trx status
                                        trx.status = "SUCCESSFUL"
                                        trx.save()
                                        # webhook REFUND_SUCCESSFUL
                                        webhook_request("REFUND_SUCCESSFUL", {"invoice_id":trx.invoice.id}, trx.invoice.receiver.id)
                                        return True
                                    else:
                                        trx.status = "FAILED"
                                        trx.message = close_wallet_trx_data.get("message",None)
                                        trx.save()
                                        # webhook REFUND_FAILED
                                        webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)

                                else:
                                    trx.status = "FAILED"
                                    trx.message = erc_20_trx_data.get("message",None)
                                    trx.save()
                                    # webhook REFUND_FAILED
                                    webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                            else:
                                trx.status = "FAILED"
                                trx.message = gas_trx_data.get("message",None)
                                trx.save()
                                # webhook REFUND_FAILED
                                webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
                        else:
                            trx.status = "CREATED"
                            trx.message = "eth balance is less than 0.01"
                            trx.save()
                    else:
                        trx.status = "CREATED"
                        trx.message = "eth balance is less than 0.01"
                        trx.save()
                else:
                    trx.status = "FAILED"
                    trx.message = "user has no web3 account"
                    trx.save()
                    # webhook REFUND_FAILED
                    webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
            else:
                trx.status = "FAILED"
                trx.message = "no valid web3 connection"
                trx.save()
                # webhook REFUND_FAILED
                webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)
        else:
            trx.status = "FAILED"
            trx.message = "customer address or amount paid is missing"
            trx.save()
            # webhook REFUND_FAILED
            webhook_request("REFUND_FAILED", {"invoice_id":trx.invoice.id,"message":trx.message}, trx.invoice.receiver.id)


@shared_task(bind=True)
def process_refund(self):
    print("processing refund")
    trxs = RefundTransaction.objects.filter(status="CREATED")
    for trx in trxs:
        process_refund_trx.delay(trx.id)
    

    

 

