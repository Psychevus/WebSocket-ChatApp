"""Helper utilities for retrieving tenant encryption keys from AWS KMS."""

from __future__ import annotations

import base64
from typing import Tuple

import boto3
from django.conf import settings

_kms_client = None


def get_kms_client():
    """Return a cached boto3 KMS client."""
    global _kms_client
    if _kms_client is None:
        region = getattr(settings, "AWS_REGION", "us-east-1")
        _kms_client = boto3.client("kms", region_name=region)
    return _kms_client


def generate_data_key() -> Tuple[bytes, str]:
    """Generate a data key using the configured CMK.

    Returns the plaintext key and the base64 encoded ciphertext blob so that the
    ciphertext can be stored alongside encrypted data.
    """
    key_id = getattr(settings, "KMS_KEY_ID", None)
    if not key_id:
        raise ValueError("KMS_KEY_ID is not configured")

    client = get_kms_client()
    response = client.generate_data_key(KeyId=key_id, KeySpec="AES_256")
    plaintext = response["Plaintext"]
    ciphertext = base64.b64encode(response["CiphertextBlob"]).decode("utf-8")
    return plaintext, ciphertext


def decrypt_data_key(ciphertext_b64: str) -> bytes:
    """Decrypt a base64 encoded ciphertext blob and return the plaintext key."""
    client = get_kms_client()
    ciphertext = base64.b64decode(ciphertext_b64)
    response = client.decrypt(CiphertextBlob=ciphertext)
    return response["Plaintext"]
