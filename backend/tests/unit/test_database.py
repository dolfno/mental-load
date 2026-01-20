"""Unit tests for database infrastructure."""

import pytest

from src.infrastructure.database import TursoConnection, TursoCursor


class TestTursoConnectionURLConstruction:
    """Test that TursoConnection handles various URL formats correctly."""

    def test_standard_libsql_url(self):
        """Standard libsql:// URL should be converted to https://."""
        conn = TursoConnection("libsql://db-name.turso.io", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_url_with_trailing_slash(self):
        """URLs with trailing slash should have it stripped."""
        conn = TursoConnection("libsql://db-name.turso.io/", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_url_with_multiple_trailing_slashes(self):
        """URLs with multiple trailing slashes should have them stripped."""
        conn = TursoConnection("libsql://db-name.turso.io///", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_url_with_path_already_included(self):
        """URLs that already include /v2/pipeline should have it removed."""
        conn = TursoConnection("libsql://db-name.turso.io/v2/pipeline", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_url_with_path_and_trailing_slash(self):
        """URLs with path and trailing slash should be handled correctly."""
        conn = TursoConnection("libsql://db-name.turso.io/v2/pipeline/", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_https_url_passthrough(self):
        """https:// URLs should work without modification."""
        conn = TursoConnection("https://db-name.turso.io", "token")
        assert conn.base_url == "https://db-name.turso.io"

    def test_aws_region_url(self):
        """URLs with AWS region should be preserved correctly."""
        conn = TursoConnection("libsql://aivin-dolfno.aws-eu-west-1.turso.io", "token")
        assert conn.base_url == "https://aivin-dolfno.aws-eu-west-1.turso.io"

    def test_final_api_url_is_correct(self):
        """The final API URL should always be correct regardless of input format."""
        test_cases = [
            "libsql://db.turso.io",
            "libsql://db.turso.io/",
            "libsql://db.turso.io/v2/pipeline",
            "libsql://db.turso.io/v2/pipeline/",
            "https://db.turso.io",
        ]

        for url in test_cases:
            conn = TursoConnection(url, "token")
            api_url = f"{conn.base_url}/v2/pipeline"
            assert api_url == "https://db.turso.io/v2/pipeline", f"Failed for input: {url}"


class TestTursoCursorTypeParsing:
    """Test that TursoCursor correctly parses Turso API response types."""

    def test_parses_integer_values(self):
        """Integer type should be converted to Python int."""
        result = {
            "response": {
                "result": {
                    "cols": [{"name": "id"}, {"name": "count"}],
                    "rows": [
                        [{"type": "integer", "value": "42"}, {"type": "integer", "value": "0"}]
                    ]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        assert rows[0]["id"] == 42
        assert isinstance(rows[0]["id"], int)
        assert rows[0]["count"] == 0
        assert isinstance(rows[0]["count"], int)

    def test_integer_zero_is_falsy(self):
        """Integer 0 should be falsy when used as boolean (the autocomplete bug)."""
        result = {
            "response": {
                "result": {
                    "cols": [{"name": "autocomplete"}],
                    "rows": [[{"type": "integer", "value": "0"}]]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        # This was the bug: bool("0") == True, but bool(0) == False
        assert rows[0]["autocomplete"] == 0
        assert bool(rows[0]["autocomplete"]) is False

    def test_parses_float_values(self):
        """Float type should be converted to Python float."""
        result = {
            "response": {
                "result": {
                    "cols": [{"name": "price"}],
                    "rows": [[{"type": "float", "value": "19.99"}]]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        assert rows[0]["price"] == 19.99
        assert isinstance(rows[0]["price"], float)

    def test_parses_null_values(self):
        """Null type should be converted to Python None."""
        result = {
            "response": {
                "result": {
                    "cols": [{"name": "optional_field"}],
                    "rows": [[{"type": "null", "value": None}]]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        assert rows[0]["optional_field"] is None

    def test_parses_text_values(self):
        """Text type should remain as string."""
        result = {
            "response": {
                "result": {
                    "cols": [{"name": "name"}],
                    "rows": [[{"type": "text", "value": "hello"}]]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        assert rows[0]["name"] == "hello"
        assert isinstance(rows[0]["name"], str)

    def test_parses_mixed_row(self):
        """A row with mixed types should be parsed correctly."""
        result = {
            "response": {
                "result": {
                    "cols": [
                        {"name": "id"},
                        {"name": "name"},
                        {"name": "is_active"},
                        {"name": "score"},
                        {"name": "deleted_at"}
                    ],
                    "rows": [[
                        {"type": "integer", "value": "1"},
                        {"type": "text", "value": "Test Task"},
                        {"type": "integer", "value": "1"},
                        {"type": "float", "value": "95.5"},
                        {"type": "null", "value": None}
                    ]]
                }
            }
        }
        cursor = TursoCursor(result)
        rows = cursor.fetchall()

        assert rows[0]["id"] == 1
        assert rows[0]["name"] == "Test Task"
        assert rows[0]["is_active"] == 1
        assert bool(rows[0]["is_active"]) is True
        assert rows[0]["score"] == 95.5
        assert rows[0]["deleted_at"] is None
