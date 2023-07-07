import random
from user_management.models import UserGateWeb3Account
from cryptography.fernet import Fernet
from django.conf import settings
from urllib.parse import urlparse
import hashlib
import base64
import pytz




utc=pytz.UTC

sys_random = random.SystemRandom()

def get_random_string(k=35):
    letters = "abcdefghiklmnopqrstuvwwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    return ''.join(sys_random.choices(letters, k=k))


from eth_account import Account


def getOrCreateWeb3Acoount(user):
    if UserGateWeb3Account.objects.filter(user=user).exists():
        return UserGateWeb3Account.objects.get(user=user)
    # create one
    Account.enable_unaudited_hdwallet_features()
    acct, mnemonic = Account.create_with_mnemonic()
    w3_acc = UserGateWeb3Account(
        user = user,
        address = acct.address,
        private_key = encrypt_message(acct.key.hex()),
        mnemonic = encrypt_message(mnemonic)
    )
    w3_acc.save()
    return w3_acc



def generate_fernet_key():
    return Fernet.generate_key()


def encrypt_message(message, secret_key=settings.MSG_SECRET_KEY):
    # Create a Fernet key from the secret key
    fernet_key = Fernet(secret_key)
    
    # Encrypt the message
    encrypted_message = fernet_key.encrypt(message.encode('utf-8'))
    
    return encrypted_message.decode('utf-8')

def decrypt_message(encrypted_message, secret_key=settings.MSG_SECRET_KEY):
    # Create a Fernet key from the secret key
    fernet_key = Fernet(secret_key)
    
    # Decrypt the message
    decrypted_message = fernet_key.decrypt(encrypted_message).decode('utf-8')
    
    return decrypted_message


def intOrZero(string):
    try:
        return int(string)
    except Exception as e:
        return 0
    


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def bytesToString(b: bytes):
    return base64.b64encode(b).decode('utf-8')

def stringToBytes(s: str):
    return base64.b64decode(s.encode('utf-8'))

