from cryptography.fernet import Fernet

from config import settings


if settings.fernet_key:
    _fernet = Fernet(settings.fernet_key.encode())
else:
    generated_key = Fernet.generate_key()
    _fernet = Fernet(generated_key)


def encrypt_value(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
