import pytest
from config import get_env_var

def test_get_env_var_returns_value(monkeypatch):
    monkeypatch.setenv("DUMMY_VAR", "secret_value")
    assert get_env_var("DUMMY_VAR") == "secret_value"

def test_get_env_var_raises_error(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(EnvironmentError, match="Missing required environment variable: MISSING_VAR"):
        get_env_var("MISSING_VAR")
