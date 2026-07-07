"""Unit tests for authentication: hashing, validation, registration, login."""

import pytest
from backend.auth.auth_service import (
    hash_password,
    verify_password,
    validate_password_strength,
    register_user,
    login_user,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


@pytest.mark.parametrize("password,valid", [
    ("short1", False),        # too short
    ("allletters", False),    # no digit
    ("12345678", False),      # no letter
    ("Password1", True),      # ok
    ("", False),              # empty
])
def test_validate_password_strength(password, valid):
    assert validate_password_strength(password)["valid"] is valid


def test_register_user_success():
    res = register_user("Alice", "alice_reg@example.com", "Password1")
    assert res["success"] is True
    assert "user_id" in res


def test_register_duplicate_email():
    register_user("Bob", "dup_reg@example.com", "Password1")
    res = register_user("Bob2", "dup_reg@example.com", "Password1")
    assert res["success"] is False
    assert "already registered" in res["message"].lower()


def test_register_weak_password_rejected():
    res = register_user("Weak", "weak_reg@example.com", "weak")
    assert res["success"] is False


def test_register_admin_role_is_downgraded():
    """SECURITY: public registration must never create an Admin."""
    res = register_user("Sneaky", "sneaky_reg@example.com", "Password1", role="Admin")
    assert res["success"] is True
    login = login_user("sneaky_reg@example.com", "Password1")
    assert login["user"]["role"] == "Job Seeker"


def test_register_recruiter_role_allowed():
    res = register_user("Rec", "selfrec_reg@example.com", "Password1", role="Recruiter")
    assert res["success"] is True
    login = login_user("selfrec_reg@example.com", "Password1")
    assert login["user"]["role"] == "Recruiter"


def test_login_invalid_password():
    register_user("Carol", "carol_login@example.com", "Password1")
    res = login_user("carol_login@example.com", "WrongPass1")
    assert res["success"] is False


def test_login_unknown_email():
    res = login_user("nobody_here@example.com", "Password1")
    assert res["success"] is False


def test_login_success_returns_user():
    register_user("Dave", "dave_login@example.com", "Password1")
    res = login_user("dave_login@example.com", "Password1")
    assert res["success"] is True
    assert res["user"]["email"] == "dave_login@example.com"
