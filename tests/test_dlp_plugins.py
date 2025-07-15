from ChatApp import dlp_plugins


def test_nightfall_scan(monkeypatch):
    result = dlp_plugins.nightfall_scan("hello")
    assert result is True


def test_google_dlp_scan(monkeypatch):
    class DummyResponse:
        class result:
            findings = []
    class DummyClient:
        def inspect_content(self, parent, item):
            return DummyResponse()
    monkeypatch.setitem(__import__('sys').modules, 'google.cloud.dlp_v2', type('m',(object,),{'DlpServiceClient': lambda: DummyClient()}))
    result = dlp_plugins.google_dlp_scan("hi")
    assert result is True
