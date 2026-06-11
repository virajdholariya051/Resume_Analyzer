"""
User service for managing user accounts and profiles.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import User
from backend.auth.auth_service import hash_password


class UserService:
    """Service class for user operations."""

    def get_all_users(self) -> List[Dict]:
        """Get all users (admin function)."""
        db = get_db()
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()
            return [
                {
                    "user_id": u.user_id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "phone": u.phone or "N/A",
                    "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A",
                }
                for u in users
            ]
        finally:
            db.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a user by ID."""
        db = get_db()
        try:
            u = db.query(User).filter(User.user_id == user_id).first()
            if u:
                return {
                    "user_id": u.user_id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "phone": u.phone or "",
                    "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A",
                }
            return None
        finally:
            db.close()

    def update_user(self, user_id: int, name: str = None, phone: str = None, password: str = None) -> Dict:
        """Update user profile."""
        db = get_db()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}

            if name:
                user.name = name
            if phone is not None:
                user.phone = phone
            if password:
                user.password = hash_password(password)

            db.commit()
            return {"success": True, "message": "Profile updated successfully!"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating profile: {str(e)}"}
        finally:
            db.close()

    def delete_user(self, user_id: int) -> Dict:
        """Delete a user account."""
        db = get_db()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}
            if user.role == "Admin":
                return {"success": False, "message": "Cannot delete admin user."}

            db.delete(user)
            db.commit()
            return {"success": True, "message": "User deleted successfully."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting user: {str(e)}"}
        finally:
            db.close()

    def get_user_count(self) -> int:
        """Get total number of users."""
        db = get_db()
        try:
            return db.query(User).count()
        finally:
            db.close()
