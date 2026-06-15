import pytest
from services.utils import decoder


class TestDecoder:
    def test_utf8(self):
        assert decoder("café".encode("utf-8")) == "café"

    def test_utf8_bom(self):
        assert decoder("café".encode("utf-8-sig")) == "café"

    def test_latin1(self):
        assert decoder("café".encode("latin-1")) == "café"

    def test_ascii(self):
        assert decoder(b"hello world") == "hello world"

    def test_empty(self):
        assert decoder(b"") == ""

    def test_returns_string_for_arbitrary_bytes(self):
        # Le fallback latin-1 avec errors=replace garantit un retour str
        result = decoder(b"\xff\xfe\x00\x48")
        assert isinstance(result, str)

    def test_utf8_multiline(self):
        content = "première ligne\ndeuxième ligne\n".encode("utf-8")
        result = decoder(content)
        assert "première" in result
        assert "deuxième" in result
