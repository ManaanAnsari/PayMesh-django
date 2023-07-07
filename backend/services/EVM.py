from web3 import Web3
from payment.models import SupportedNetwork
from backend.helpers import decrypt_message
from backend.abi import getABI
from decimal import Decimal


class EVM:
    def __init__(self,network:SupportedNetwork):
        self.w3 = None
        if network.url:
            try:
                self.w3 = Web3(Web3.HTTPProvider(network.url))
            except Exception as e:
                print(e)
    
    def checksum_address(self,address):
        return  self.w3.to_checksum_address(address)
    
    def native_get_balance(self,address):
        address = self.checksum_address(address)
        if self.w3:
            balance_wei = self.w3.eth.get_balance(address)
            balance_ether = self.w3.from_wei(balance_wei, 'ether')
            balance_ether = float(balance_ether)
            return balance_ether
        return None
    
    def erc20_get_balance(self,address,contract_address):
        abi = getABI("ERC20")
        address = self.checksum_address(address)
        contract_address = self.checksum_address(contract_address)
        if abi is not None:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            # Call the balanceOf function on the ERC20 contract
            balance = contract.functions.balanceOf(address).call()
            # Convert the balance to a human-readable format
            token_decimals = contract.functions.decimals().call()
            balance_readable = balance / (10 ** token_decimals)
            return balance_readable
        return None

    def erc20_get_decimals(self,contract_address):
        abi = getABI("ERC20")
        contract_address = self.checksum_address(contract_address)
        
        if abi is not None:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            token_decimals = contract.functions.decimals().call()
            return token_decimals  
        return None  
    
    
    def native_transfer(self,from_address:str,from_private_key_enc:str,to_address:str,amount_ether:float):
        from_address = self.checksum_address(from_address)
        to_address = self.checksum_address(to_address)
        
        if self.w3:
            acc_balance = self.native_get_balance(from_address)
            if acc_balance:
                print(acc_balance, amount_ether)
                if acc_balance > amount_ether:
                    # Decrypt the private key string
                    private_key = decrypt_message(from_private_key_enc)
                    # Build the transaction object
                    value_wei = self.w3.to_wei(amount_ether, 'ether')
                    # Estimate the gas limit
                    gas_limit = self.w3.eth.estimate_gas({'to': to_address, 'value': value_wei})
                    # Estimate the gas price
                    gas_price = self.w3.eth.gas_price
                    # Get the account nonce for the sender account
                    nonce = self.w3.eth.get_transaction_count(from_address)

                    transaction = {
                        'to': to_address,  # Recipient's address
                        'value': value_wei,  # Amount of Ether to transfer
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'nonce': nonce,
                    }
                    if (self.w3.to_wei(acc_balance, 'ether') - (gas_limit * gas_price)) >0: 

                        try:
                            # Sign the transaction with the sender's private key
                            signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key)
                            # Send the signed transaction to the Ethereum network
                            transaction_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
                            # Wait for the transaction to be mined
                            transaction_receipt = self.w3.eth.wait_for_transaction_receipt(transaction_hash,timeout=600)

                            # Check the transaction status
                            if transaction_receipt.status == 1:
                                return True, {"message": "Transaction successful.", "transaction_hash": transaction_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                            else:
                                return False, {"message": "Transaction failed.", "transaction_hash": transaction_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                        except Exception as e:
                            print(e)
                            return False, {"message": "Transaction failed error: "+str(e), "error": str(e)}
                    else:
                        return False, {"message": "Insufficient balance for gas."}
                else:
                    return False, {"message": "Insufficient balance."}
            else:
                return False, {"message": "Invalid network."}
        else:
            return False, {"message": "Invalid network."}
        
    
    
    def erc20_transfer(self,from_address:str,from_private_key_enc:str,to_address:str,amount_ether:float,contract_address:str):
        from_address = self.checksum_address(from_address)
        to_address = self.checksum_address(to_address)
        contract_address = self.checksum_address(contract_address)
        
        if self.w3:
            abi = getABI("ERC20")
            if abi is not None:
                acc_balance = self.erc20_get_balance(from_address,contract_address)
                if acc_balance:
                    if acc_balance >= amount_ether:
                        contract = self.w3.eth.contract(address=contract_address, abi=abi)
                        private_key = decrypt_message(from_private_key_enc)
                        token_decimals = self.erc20_get_decimals(contract_address)
                        if token_decimals is not None:
                            # Amount of tokens to transfer
                            token_amount = int(Decimal(str(amount_ether)) * (10**token_decimals))  
                            # Encode the function call to transfer tokens
                            transfer_data = contract.encodeABI(fn_name='transfer', args=[to_address, token_amount])
                            # Build the transaction object
                            print(token_amount,acc_balance)
                            transaction = {
                                'from': from_address,
                                'to': contract_address,
                                'nonce': self.w3.eth.get_transaction_count(from_address),
                                'data': transfer_data,
                            }
                            transaction['gas'] =  self.w3.eth.estimate_gas(transaction)
                            transaction['gasPrice'] = self.w3.eth.gas_price
                            native_bal = self.native_get_balance(from_address)
                            if native_bal:
                                if (self.w3.to_wei(native_bal, 'ether') - (transaction['gas'] * transaction['gasPrice'])) >0: 
                                    try:
                                        signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key)
                                        transaction_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
                                        transaction_receipt = self.w3.eth.wait_for_transaction_receipt(transaction_hash,timeout=600)

                                        if transaction_receipt.status == 1:
                                            return True, {"message": "Transaction successful.", "transaction_hash": transaction_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                                        else:
                                            return False, {"message": "Transaction failed.", "transaction_hash": transaction_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                                    except Exception as e:
                                        print(e)
                                        return False, {"message": "Transaction failed.", "error": str(e)}
                                else:
                                    return False, {"message": "Insufficient balance for gas."}
                            else:
                                return False, {"message": "Invalid native network."}
                        else:
                            return False, {"message": "Invalid token decimals"}
                    else:
                        return False, {"message": "Insufficient balance."}
                else:
                    return False, {"message": "unable to get balance."}
            else:
                return False, {"message": "Invalid abi."}
        else:
            return False, {"message": "Invalid network."}
                        
                        
    def close_wallet(self,from_address,from_private_key_enc, to_address):
        from_address = self.checksum_address(from_address)
        to_address = self.checksum_address(to_address)
        
        if self.w3:
            private_key = decrypt_message(from_private_key_enc)
            # Get the current balance of the sender's address
            balance = self.w3.eth.get_balance(from_address)
            # Estimate the gas limit
            gas_limit = self.w3.eth.estimate_gas({'to': to_address, 'value': balance})
            # Estimate the gas price
            gas_price = self.w3.eth.gas_price
            amount_to_transfer = balance - (gas_limit * gas_price)

            if amount_to_transfer > 0:
                # Set up the transaction parameters
                transaction = {
                    'to': to_address,  # Recipient's address
                    'value': amount_to_transfer,  # Amount of Ether to transfer
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(from_address),
                }
                try:
                    # Sign the transaction with the private key
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
                    # Send the signed transaction
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    transaction_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash,timeout=600)
                    
                    if transaction_receipt.status == 1:
                        return True, {"message": "Transaction successful.", "transaction_hash": tx_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                    else:
                        return False, {"message": "Transaction failed.", "transaction_hash": tx_hash.hex(), "transaction_receipt": str(transaction_receipt)}
                except Exception as e:
                    print(e)
                    return False, {"message": "Transaction failed.", "error": str(e)}
            else:
                return False, {"message": "Insufficient balance."}
        else:
            return False, {"message": "Invalid network."}
        
                
        
                    

