# utils.py

from cryptography.fernet import Fernet

# Generate a key and save it securely
key = b'your-32-byte-encryption-key'  # Replace with your generated key
cipher = Fernet(key)


def encrypt_price(price: float) -> bytes:
    return cipher.encrypt(str(price).encode())


def decrypt_price(encrypted_price: bytes) -> float:
    return float(cipher.decrypt(encrypted_price).decode())
