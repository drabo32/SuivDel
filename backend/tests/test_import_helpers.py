import pytest
from datetime import date
from services.import_init import _normalize, _find_col, _parse_float, _parse_date


class TestNormalize:
    def test_strips_whitespace(self):
        assert _normalize("  hello  ") == "hello"

    def test_collapses_internal_spaces(self):
        assert _normalize("hello   world") == "hello world"

    def test_replaces_newline(self):
        assert _normalize("hello\nworld") == "hello world"

    def test_empty(self):
        assert _normalize("") == ""

    def test_already_clean(self):
        assert _normalize("clean") == "clean"


class TestFindCol:
    def test_exact_match(self):
        header = ["Code", "Libelle", "Budget"]
        assert _find_col(header, "Code") == 0

    def test_second_alias(self):
        header = ["Autre chose", "Ref. Aha Master feature"]
        assert _find_col(header, "inexistant", "Ref. Aha Master feature") == 1

    def test_case_insensitive(self):
        header = ["CODE AHA"]
        assert _find_col(header, "code aha") == 0

    def test_not_found(self):
        header = ["Code", "Libelle"]
        assert _find_col(header, "Budget") is None

    def test_normalizes_header_whitespace(self):
        # Les en-têtes avec espaces multiples sont normalisés avant comparaison
        header = ["RAF  DEV  M"]
        assert _find_col(header, "RAF DEV M") == 0


class TestParseFloat:
    def test_integer_string(self):
        assert _parse_float("42") == 42.0

    def test_decimal_comma(self):
        assert _parse_float("3,14") == pytest.approx(3.14)

    def test_decimal_dot(self):
        assert _parse_float("3.14") == pytest.approx(3.14)

    def test_space_separator(self):
        assert _parse_float("1 234") == 1234.0

    def test_empty_string(self):
        assert _parse_float("") is None

    def test_none(self):
        assert _parse_float(None) is None

    def test_invalid(self):
        assert _parse_float("abc") is None

    def test_whitespace_only(self):
        assert _parse_float("   ") is None


class TestParseDate:
    def test_iso_format(self):
        assert _parse_date("2025-01-15") == date(2025, 1, 15)

    def test_french_format(self):
        assert _parse_date("15/01/2025") == date(2025, 1, 15)

    def test_excel_serial(self):
        # Série Excel 45028 = 2023-04-12 (vérifié via datetime(1899,12,30)+timedelta(45028))
        result = _parse_date("45028")
        assert isinstance(result, date)
        assert result == date(2023, 4, 12)

    def test_excel_serial_small_ignored(self):
        # Valeur <= 1000 n'est pas traitée comme série Excel → None
        assert _parse_date("999") is None

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_none(self):
        assert _parse_date(None) is None

    def test_invalid(self):
        assert _parse_date("pas-une-date") is None

    def test_strips_whitespace(self):
        assert _parse_date("  2025-06-01  ") == date(2025, 6, 1)
