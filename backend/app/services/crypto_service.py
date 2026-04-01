import base64
import hashlib

from cryptography.fernet import Fernet

from ..config import settings


_key_material = hashlib.sha256(settings.encryption_key.encode('utf-8')).digest()
FERNET_KEY = base64.urlsafe_b64encode(_key_material)
fernet = Fernet(FERNET_KEY)


def encrypt(value: str) -> str:
    return fernet.encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt(value: str) -> str:
    return fernet.decrypt(value.encode('utf-8')).decode('utf-8')
