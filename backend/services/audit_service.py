"""
Audit log service for recording and retrieving sensitive administrative actions.
"""

from typing import List, Dict, Optional
from database.database import get_db
from database.schema import AuditLog, User


class AuditService:
    """Service for writing and reading the audit log."""

    def log(self, admin_id: Optional[int], action: str, target_user_id: Optional[int] = None,
            ip_address: Optional[str] = None) -> None:
        """Record an administrative action. Best-effort; never raises to the caller."""
        db = get_db()
        try:
            entry = AuditLog(
                admin_id=admin_id, action=action,
                target_user_id=target_user_id, ip_address=ip_address,
            )
            db.add(entry)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def get_logs(self, limit: int = 200) -> List[Dict]:
        """Return recent audit log entries (most recent first), with admin names resolved."""
        db = get_db()
        try:
            logs = (
                db.query(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            # Resolve admin names
            admin_ids = {l.admin_id for l in logs if l.admin_id}
            names = {}
            if admin_ids:
                for u in db.query(User).filter(User.user_id.in_(admin_ids)).all():
                    names[u.user_id] = u.name

            return [
                {
                    "log_id": l.log_id,
                    "admin_id": l.admin_id,
                    "admin_name": names.get(l.admin_id, "System" if l.admin_id is None else f"User #{l.admin_id}"),
                    "action": l.action,
                    "target_user_id": l.target_user_id,
                    "ip_address": getattr(l, "ip_address", None) or "-",
                    "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A",
                }
                for l in logs
            ]
        finally:
            db.close()
