"""
Authentication service providing password hashing, verification, and session management.
"""

import bcrypt
import streamlit as st
from typing import Optional
from database.database import get_db
from database.schema import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength.

    Requirements: at least 8 characters, with at least one letter and one digit.

    Returns:
        dict with 'valid' boolean and 'message' string.
    """
    if not password or len(password) < 8:
        return {"valid": False, "message": "Password must be at least 8 characters long."}
    if not any(c.isalpha() for c in password):
        return {"valid": False, "message": "Password must contain at least one letter."}
    if not any(c.isdigit() for c in password):
        return {"valid": False, "message": "Password must contain at least one number."}
    return {"valid": True, "message": "Password is strong."}


def register_user(name: str, email: str, password: str, phone: str = "", role: str = "Job Seeker") -> dict:
    """
    Register a new public user.

    SECURITY: Public registration may only create "Job Seeker" or "Recruiter"
    accounts. Any attempt to register as "Admin" (or any unrecognized value) is
    forced down to "Job Seeker". Admin accounts can only be created by an
    existing Admin through the Admin Management module.

    Returns:
        dict with 'success' boolean and 'message' string.
    """
    db = get_db()
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "message": "Email already registered."}

        # Validate inputs
        if not name or not email or not password:
            return {"success": False, "message": "Name, email, and password are required."}

        strength = validate_password_strength(password)
        if not strength["valid"]:
            return {"success": False, "message": strength["message"]}

        # SECURITY: whitelist self-service roles; never allow public Admin creation.
        allowed_public_roles = {"Job Seeker", "Recruiter"}
        forced_role = role if role in allowed_public_roles else "Job Seeker"

        hashed_pw = hash_password(password)
        user = User(
            name=name,
            email=email,
            password=hashed_pw,
            phone=phone,
            role=forced_role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"success": True, "message": "Registration successful!", "user_id": user.user_id}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Registration failed: {str(e)}"}
    finally:
        db.close()


def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user.
    
    Returns:
        dict with 'success' boolean, 'message' string, and 'user' data.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"success": False, "message": "Invalid email or password."}

        if not verify_password(password, user.password):
            return {"success": False, "message": "Invalid email or password."}

        # Block disabled accounts
        if getattr(user, "is_active", True) is False:
            return {"success": False, "message": "Your account has been disabled. Contact an administrator."}

        return {
            "success": True,
            "message": "Login successful!",
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone,
            },
        }
    except Exception as e:
        return {"success": False, "message": f"Login failed: {str(e)}"}
    finally:
        db.close()


def set_session(user_data: dict) -> None:
    """Store user data in Streamlit session state."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_data


def get_current_user() -> Optional[dict]:
    """Get the currently authenticated user from session."""
    if st.session_state.get("authenticated"):
        return st.session_state.get("user")
    return None


def logout() -> None:
    """Clear the user session."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


def is_authenticated() -> bool:
    """Check if a user is currently authenticated."""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if the current user has admin role."""
    user = get_current_user()
    if user:
        return user.get("role") == "Admin"
    return False


def is_recruiter() -> bool:
    """Check if the current user has recruiter role."""
    user = get_current_user()
    if user:
        return user.get("role") == "Recruiter"
    return False


def get_role() -> str:
    """Return the current user's role, or an empty string if not logged in."""
    user = get_current_user()
    return user.get("role", "") if user else ""
