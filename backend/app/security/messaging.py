from base64 import b64decode

import rsa


def encrypt_contact(contents: str, public_key: str):
    return rsa.encrypt(contents.encode(), rsa.PublicKey._load_pkcs1_pem(b64decode(public_key)))