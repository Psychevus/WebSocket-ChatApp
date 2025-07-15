import base64
import pytest
from ChatApp import kms


def test_generate_and_decrypt_data_key(settings, kms_client):
    kms_client.generate_data_key.return_value = {
        "Plaintext": b"plain",
        "CiphertextBlob": b"cipher",
    }
    plaintext, ciphertext = kms.generate_data_key()
    assert plaintext == b"plain"
    assert ciphertext == base64.b64encode(b"cipher").decode()
    kms_client.generate_data_key.assert_called_with(KeyId=settings.KMS_KEY_ID, KeySpec="AES_256")

    kms_client.decrypt.return_value = {"Plaintext": b"plain"}
    result = kms.decrypt_data_key(ciphertext)
    assert result == b"plain"
    kms_client.decrypt.assert_called_with(CiphertextBlob=b"cipher")


def test_generate_data_key_missing_setting(monkeypatch, kms_client, settings):
    settings.KMS_KEY_ID = None
    with pytest.raises(ValueError):
        kms.generate_data_key()
