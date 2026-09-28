"""
Tests for the version logic in app/config.py.

Verifies that:
1. The fallback version is returned when git is unavailable.
2. The version string matches the expected format when git IS available.
3. The version is surfaced via the Settings object.
"""
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


def test_version_format_with_git_available():
    """When git returns a commit count, the version must be Version <count>."""
    from app.config import get_settings

    # Patch subprocess to return a known commit count
    with patch("subprocess.check_output", return_value=b"105\n") as mock_cmd:
        settings = get_settings()

    assert settings.app_version == "Version 105", (
        f"Expected 'Version 105', got '{settings.app_version}'"
    )


def test_version_fallback_when_git_unavailable():
    """When git is not available (e.g., Docker without .git), the fallback version is used."""
    from app.config import get_settings

    with patch("subprocess.check_output", side_effect=FileNotFoundError("git not found")):
        settings = get_settings()

    assert settings.app_version == "Version Unknown", (
        f"Expected fallback 'Version Unknown', got '{settings.app_version}'"
    )


def test_version_fallback_when_not_a_git_repo():
    """When git exits with an error (no repo), fallback is used."""
    from app.config import get_settings

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(128, "git", stderr=b"not a git repo"),
    ):
        settings = get_settings()

    assert settings.app_version == "Version Unknown", (
        f"Expected fallback 'Version Unknown', got '{settings.app_version}'"
    )


def test_version_is_not_empty():
    """The version should never be empty or None."""
    from app.config import get_settings

    settings = get_settings()
    assert settings.app_version
    assert settings.app_version.startswith("Version "), (
        f"Version should start with 'Version ', got: {settings.app_version}"
    )


def test_version_format_regex():
    """Version must match 'Version <count>' pattern or 'Version Unknown'."""
    import re
    from app.config import get_settings

    settings = get_settings()
    pattern = r"^Version (\d+|Unknown)$"
    assert re.match(pattern, settings.app_version), (
        f"Version '{settings.app_version}' does not match expected format 'Version <N>'"
    )
