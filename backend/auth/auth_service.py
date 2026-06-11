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


def register_user(name: str, email: str, password: str, phone: str = "", role: str = "Job Seeker") -> dict:
    """
    Register a new user.
    
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
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters."}

        # Create user
        hashed_pw = hash_password(password)
        user = User(
            name=name,
            email=email,
            password=hashed_pw,
            phone=phone,
            role=role,
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
