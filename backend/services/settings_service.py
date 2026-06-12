"""
System settings service - read/write configurable key/value settings.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import SystemSetting


class SettingsService:
    """Service for managing configurable system settings."""

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return a single setting value by key."""
        db = get_db()
        try:
            s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            return s.value if s else default
        finally:
            db.close()

    def get_by_category(self, category: str) -> List[Dict]:
        """Return all settings within a category."""
        db = get_db()
        try:
            rows = db.query(SystemSetting).filter(SystemSetting.category == category).all()
            return [{"key": r.key, "value": r.value, "category": r.category} for r in rows]
        finally:
            db.close()

    def get_all(self) -> Dict[str, str]:
        """Return all settings as a dict."""
        db = get_db()
        try:
            return {s.key: s.value for s in db.query(SystemSetting).all()}
        finally:
            db.close()

    def set(self, key: str, value: str) -> Dict:
        """Create or update a setting."""
        db = get_db()
        try:
            s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if s:
                s.value = value
            else:
                s = SystemSetting(key=key, value=value)
                db.add(s)
            db.commit()
            return {"success": True, "message": "Setting saved."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error saving setting: {e}"}
        finally:
            db.close()

    def set_many(self, values: Dict[str, str]) -> Dict:
        """Bulk update several settings."""
        db = get_db()
        try:
            for key, value in values.items():
                s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
                if s:
                    s.value = str(value)
                else:
                    db.add(SystemSetting(key=key, value=str(value)))
            db.commit()
            return {"success": True, "message": "Settings updated."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating settings: {e}"}
        finally:
            db.close()
