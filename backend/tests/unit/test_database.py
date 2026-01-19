"""Unit tests for database infrastructure."""

import pytest

from src.infrastructure.database import TursoConnection


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
