"""Simple test to verify test framework is working."""

def test_simple():
    """Simple test that should pass."""
    assert True


def test_exit_codes_import():
    """Test that we can import ExitCodes."""
    from src.policy_dq.cli import ExitCodes
    assert ExitCodes.SUCCESS == 0
    assert ExitCodes.VALIDATION_FAILED == 1