"""
AI/NLP request logging service for the AI Analysis Center monitoring dashboard.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import AILog


class AILogService:
    """Service for recording and querying AI analysis logs."""

    def log(self, user_id: Optional[int], resume_id: Optional[int], action: str,
            status: str = "success", processing_ms: int = 0, message: str = "") -> None:
        """Record an AI/NLP request. Best-effort; never raises to caller."""
        db = get_db()
        try:
            db.add(AILog(
                user_id=user_id,
                resume_id=resume_id,
                action=action,
                status=status,
                processing_ms=processing_ms,
                message=message,
            ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def get_logs(self, limit: int = 200, status: Optional[str] = None) -> List[Dict]:
        """Return recent AI logs, optionally filtered by status."""
        db = get_db()
        try:
            query = db.query(AILog)
            if status:
                query = query.filter(AILog.status == status)
            logs = query.order_by(AILog.created_at.desc()).limit(limit).all()
            return [self._to_dict(l) for l in logs]
        finally:
            db.close()

    def _to_dict(self, l: AILog) -> Dict:
        return {
            "ai_log_id": l.ai_log_id,
            "user_id": l.user_id,
            "resume_id": l.resume_id,
            "action": l.action,
            "status": l.status,
            "processing_ms": l.processing_ms or 0,
            "message": l.message or "",
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "N/A",
        }

    def get_stats(self) -> Dict:
        """Aggregate AI monitoring statistics."""
        db = get_db()
        try:
            logs = db.query(AILog).all()
            total = len(logs)
            success = sum(1 for l in logs if l.status == "success")
            failed = total - success
            avg_ms = round(sum(l.processing_ms or 0 for l in logs) / total) if total else 0

            # Most used actions
            action_counts: Dict[str, int] = {}
            for l in logs:
                action_counts[l.action] = action_counts.get(l.action, 0) + 1
            most_used = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)

            return {
                "total_requests": total,
                "successful": success,
                "failed": failed,
                "success_rate": round((success / total) * 100, 1) if total else 0.0,
                "avg_processing_ms": avg_ms,
                "most_used": most_used,
            }
        finally:
            db.close()
