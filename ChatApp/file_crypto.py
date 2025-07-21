from __future__ import annotations

import os
from typing import Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


_CHUNK_SIZE = 4096
_SALT_SIZE = 16
_NONCE_SIZE = 12
_TAG_SIZE = 16


def _derive_key(password: Union[str, bytes], salt: bytes) -> bytes:
    """Derive a 256-bit key from the given password and salt."""
    if isinstance(password, str):
        password = password.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend(),
    )
    return kdf.derive(password)


def encrypt_file(
    in_path: str,
    out_path: str,
    password: Union[str, bytes],
    chunk_size: int = _CHUNK_SIZE,
) -> None:
    """Encrypt ``in_path`` to ``out_path`` using AES-GCM.

    The output file layout is ``salt`` + ``nonce`` + ciphertext + ``tag``. Data
    is processed in chunks so large files do not need to be fully loaded into
    memory.
    """
    salt = os.urandom(_SALT_SIZE)
    key = _derive_key(password, salt)
    nonce = os.urandom(_NONCE_SIZE)
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend(),
    )
    encryptor = cipher.encryptor()

    try:
        with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
            fout.write(salt)
            fout.write(nonce)
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break
                data = encryptor.update(chunk)
                if data:
                    fout.write(data)
            encryptor.finalize()
            fout.write(encryptor.tag)
    except Exception:
        if os.path.exists(out_path):
            os.remove(out_path)
        raise


def decrypt_file(
    in_path: str,
    out_path: str,
    password: Union[str, bytes],
    chunk_size: int = _CHUNK_SIZE,
) -> None:
    """Decrypt ``in_path`` to ``out_path`` verifying the authentication tag."""
    total_size = os.path.getsize(in_path)
    if total_size < _SALT_SIZE + _NONCE_SIZE + _TAG_SIZE:
        raise ValueError("Ciphertext too small")

    with open(in_path, "rb") as fin:
        salt = fin.read(_SALT_SIZE)
        nonce = fin.read(_NONCE_SIZE)
        key = _derive_key(password, salt)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()

        ciphertext_len = total_size - _SALT_SIZE - _NONCE_SIZE - _TAG_SIZE
        remaining = ciphertext_len
        try:
            with open(out_path, "wb") as fout:
                while remaining > 0:
                    chunk = fin.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    data = decryptor.update(chunk)
                    if data:
                        fout.write(data)
                tag = fin.read(_TAG_SIZE)
                decryptor.finalize_with_tag(tag)
        except Exception:
            if os.path.exists(out_path):
                os.remove(out_path)
            raise
