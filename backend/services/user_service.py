"""
User service for managing user accounts, profiles, and privileged operations.

All privileged operations (creating Admins/Recruiters, changing roles,
enabling/disabling, resetting passwords, deletion) verify on the backend that
the acting user is an Admin, and write an entry to the audit log.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import User
from backend.auth.auth_service import hash_password, validate_password_strength
from backend.services.audit_service import AuditService


VALID_ROLES = ["Job Seeker", "Recruiter", "Admin"]
PRIVILEGED_ROLES = ["Recruiter", "Admin"]


class UserService:
    """Service class for user operations."""

    def __init__(self):
        self.audit = AuditService()

    # ------------------------------------------------------------------ #
    # Backend authorization guard
    # ------------------------------------------------------------------ #
    def _verify_admin(self, db, admin_id: int) -> bool:
        """Return True only if admin_id corresponds to an active Admin user."""
        if not admin_id:
            return False
        admin = db.query(User).filter(User.user_id == admin_id).first()
        return bool(admin and admin.role == "Admin" and getattr(admin, "is_active", True))

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #
    def get_all_users(self, role: Optional[str] = None) -> List[Dict]:
        """Get all users, optionally filtered by role."""
        db = get_db()
        try:
            query = db.query(User)
            if role:
                query = query.filter(User.role == role)
            users = query.order_by(User.created_at.desc()).all()
            return [self._to_dict(u) for u in users]
        finally:
            db.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a user by ID."""
        db = get_db()
        try:
            u = db.query(User).filter(User.user_id == user_id).first()
            return self._to_dict(u) if u else None
        finally:
            db.close()

    def _to_dict(self, u: User) -> Dict:
        return {
            "user_id": u.user_id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "phone": u.phone or "",
            "is_active": getattr(u, "is_active", True),
            "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A",
        }

    def get_user_count(self) -> int:
        """Get total number of users."""
        db = get_db()
        try:
            return db.query(User).count()
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Self-service profile update (used by Profile page)
    # ------------------------------------------------------------------ #
    def update_user(self, user_id: int, name: str = None, phone: str = None, password: str = None) -> Dict:
        """Update own profile (name, phone, password)."""
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
                strength = validate_password_strength(password)
                if not strength["valid"]:
                    return {"success": False, "message": strength["message"]}
                user.password = hash_password(password)

            db.commit()
            return {"success": True, "message": "Profile updated successfully!"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating profile: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Privileged: create Admin / Recruiter
    # ------------------------------------------------------------------ #
    def create_privileged_user(self, admin_id: int, name: str, email: str,
                               password: str, phone: str, role: str) -> Dict:
        """
        Create an Admin or Recruiter account. Only callable by an existing Admin.
        """
        if role not in PRIVILEGED_ROLES:
            return {"success": False, "message": "This method can only create Admin or Recruiter accounts."}

        if not name or not email or not password:
            return {"success": False, "message": "Name, email, and password are required."}

        strength = validate_password_strength(password)
        if not strength["valid"]:
            return {"success": False, "message": strength["message"]}

        db = get_db()
        try:
            if not self._verify_admin(db, admin_id):
                return {"success": False, "message": "Access denied. Admin privileges required."}

            if db.query(User).filter(User.email == email).first():
                return {"success": False, "message": "Email already registered."}

            user = User(
                name=name,
                email=email,
                password=hash_password(password),
                phone=phone or None,
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            self.audit.log(admin_id, f"Created {role} account ({email})", user.user_id)
            return {"success": True, "message": f"{role} account created successfully!", "user_id": user.user_id}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error creating account: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Privileged: change role
    # ------------------------------------------------------------------ #
    def change_role(self, admin_id: int, user_id: int, new_role: str) -> Dict:
        """Change a user's role. Only callable by an existing Admin."""
        if new_role not in VALID_ROLES:
            return {"success": False, "message": f"Invalid role. Allowed: {', '.join(VALID_ROLES)}"}

        db = get_db()
        try:
            if not self._verify_admin(db, admin_id):
                return {"success": False, "message": "Access denied. Admin privileges required."}

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}

            if user.user_id == admin_id:
                return {"success": False, "message": "You cannot change your own role."}

            old_role = user.role
            if old_role == new_role:
                return {"success": False, "message": "User already has this role."}

            # Prevent removing the last active admin
            if old_role == "Admin" and new_role != "Admin":
                active_admins = db.query(User).filter(
                    User.role == "Admin", User.is_active == True  # noqa: E712
                ).count()
                if active_admins <= 1:
                    return {"success": False, "message": "Cannot demote the last remaining Admin."}

            user.role = new_role
            db.commit()

            self.audit.log(admin_id, f"Changed role of {user.email}: {old_role} -> {new_role}", user_id)
            return {"success": True, "message": f"Role changed from {old_role} to {new_role}."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error changing role: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Privileged: enable / disable
    # ------------------------------------------------------------------ #
    def set_active(self, admin_id: int, user_id: int, active: bool) -> Dict:
        """Enable or disable a user account. Only callable by an existing Admin."""
        db = get_db()
        try:
            if not self._verify_admin(db, admin_id):
                return {"success": False, "message": "Access denied. Admin privileges required."}

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}

            if user.user_id == admin_id and not active:
                return {"success": False, "message": "You cannot disable your own account."}

            # Prevent disabling the last active admin
            if user.role == "Admin" and not active:
                active_admins = db.query(User).filter(
                    User.role == "Admin", User.is_active == True  # noqa: E712
                ).count()
                if active_admins <= 1:
                    return {"success": False, "message": "Cannot disable the last remaining Admin."}

            user.is_active = active
            db.commit()

            action = "Enabled" if active else "Disabled"
            self.audit.log(admin_id, f"{action} account {user.email}", user_id)
            return {"success": True, "message": f"Account {action.lower()} successfully."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating account: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Privileged: reset password
    # ------------------------------------------------------------------ #
    def reset_password(self, admin_id: int, user_id: int, new_password: str) -> Dict:
        """Reset another user's password. Only callable by an existing Admin."""
        strength = validate_password_strength(new_password)
        if not strength["valid"]:
            return {"success": False, "message": strength["message"]}

        db = get_db()
        try:
            if not self._verify_admin(db, admin_id):
                return {"success": False, "message": "Access denied. Admin privileges required."}

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}

            user.password = hash_password(new_password)
            db.commit()

            self.audit.log(admin_id, f"Reset password for {user.email}", user_id)
            return {"success": True, "message": "Password reset successfully."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error resetting password: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Privileged: delete
    # ------------------------------------------------------------------ #
    def delete_user(self, user_id: int, admin_id: Optional[int] = None) -> Dict:
        """
        Delete a user account. Only callable by an existing Admin.

        Guards:
        - Admins cannot delete their own account.
        - The last remaining active Admin cannot be deleted.
        """
        db = get_db()
        try:
            if not self._verify_admin(db, admin_id):
                return {"success": False, "message": "Access denied. Admin privileges required."}

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found."}

            if user.user_id == admin_id:
                return {"success": False, "message": "You cannot delete your own account."}

            if user.role == "Admin":
                active_admins = db.query(User).filter(
                    User.role == "Admin", User.is_active == True  # noqa: E712
                ).count()
                if active_admins <= 1:
                    return {"success": False, "message": "Cannot delete the last remaining Admin."}

            email = user.email
            db.delete(user)
            db.commit()

            self.audit.log(admin_id, f"Deleted account {email}", user_id)
            return {"success": True, "message": "User deleted successfully."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting user: {str(e)}"}
        finally:
            db.close()
