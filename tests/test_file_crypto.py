import os
import tempfile

from ChatApp.file_crypto import encrypt_file, decrypt_file


def _roundtrip(data: bytes, password: str = "pass"):
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, "plain.bin")
        enc = os.path.join(tmp, "enc.bin")
        dec = os.path.join(tmp, "dec.bin")
        with open(plain, "wb") as fh:
            fh.write(data)
        encrypt_file(plain, enc, password)
        decrypt_file(enc, dec, password)
        with open(dec, "rb") as fh:
            return fh.read()


def test_encrypt_decrypt_empty_file():
    assert _roundtrip(b"") == b""


def test_encrypt_decrypt_small_file():
    data = b"hello world" * 5
    assert _roundtrip(data) == data


def test_encrypt_decrypt_large_file():
    data = os.urandom(1024 * 1024)  # 1MB
    assert _roundtrip(data) == data
