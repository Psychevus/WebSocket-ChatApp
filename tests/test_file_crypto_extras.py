import os
import tempfile

import pytest

from ChatApp import file_crypto


class DummyEncryptor:
    def __init__(self):
        self.tag = b't' * 16

    def update(self, data):
        raise RuntimeError('boom')

    def finalize(self):
        pass


class DummyCipherEnc:
    def __init__(self, *a, **k):
        pass

    def encryptor(self):
        return DummyEncryptor()


class DummyDecryptor:
    def update(self, data):
        return data

    def finalize_with_tag(self, tag):
        raise RuntimeError('bad tag')


class DummyCipherDec:
    def __init__(self, *a, **k):
        pass

    def decryptor(self):
        return DummyDecryptor()


def test_encrypt_file_cleanup_on_error(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, 'plain')
        enc = os.path.join(tmp, 'enc')
        with open(plain, 'wb') as fh:
            fh.write(b'data')

        monkeypatch.setattr(file_crypto, 'Cipher', DummyCipherEnc)
        with pytest.raises(RuntimeError):
            file_crypto.encrypt_file(plain, enc, 'pw')
        assert not os.path.exists(enc)


def test_decrypt_file_too_small():
    with tempfile.TemporaryDirectory() as tmp:
        infile = os.path.join(tmp, 'small')
        outfile = os.path.join(tmp, 'out')
        with open(infile, 'wb') as fh:
            fh.write(b'123')
        with pytest.raises(ValueError):
            file_crypto.decrypt_file(infile, outfile, 'pw')


def test_decrypt_file_cleanup_on_error(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, 'plain')
        enc = os.path.join(tmp, 'enc')
        dec = os.path.join(tmp, 'dec')
        with open(plain, 'wb') as fh:
            fh.write(b'secret data')
        file_crypto.encrypt_file(plain, enc, 'pw')

        monkeypatch.setattr(file_crypto, 'Cipher', DummyCipherDec)
        with pytest.raises(RuntimeError):
            file_crypto.decrypt_file(enc, dec, 'pw')
        assert not os.path.exists(dec)

class StopEarlyFile:
    def __init__(self, fh):
        self._fh = fh
        self.calls = 0

    def __enter__(self):
        self._fh.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._fh.__exit__(exc_type, exc, tb)

    def read(self, size=-1):
        self.calls += 1
        data = self._fh.read(size)
        if self.calls > 3:
            return b''
        return data

    def __getattr__(self, item):
        return getattr(self._fh, item)


def test_decrypt_file_breaks_on_short_read(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, 'plain')
        enc = os.path.join(tmp, 'enc')
        dec = os.path.join(tmp, 'dec')
        with open(plain, 'wb') as fh:
            fh.write(b'some data to encrypt')
        file_crypto.encrypt_file(plain, enc, 'pw')

        real_open = open

        def bad_open(path, mode='rb', *args, **kwargs):
            fh = real_open(path, mode, *args, **kwargs)
            if path == enc and 'rb' in mode:
                return StopEarlyFile(fh)
            return fh

        import builtins
        monkeypatch.setattr(builtins, 'open', bad_open)
        with pytest.raises(Exception):
            file_crypto.decrypt_file(enc, dec, 'pw', chunk_size=1)
        assert not os.path.exists(dec)
