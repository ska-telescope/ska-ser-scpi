"""This module tests the package version."""
import ska_ser_scpi


def test_version() -> None:
    """Test that the package version is as expected."""
    assert ska_ser_scpi.__version__ == "0.5.1"
