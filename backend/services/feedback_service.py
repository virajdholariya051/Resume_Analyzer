"""
Feedback service - user reviews, bug reports, feature requests, support tickets.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import Feedback, User


VALID_CATEGORIES = ["Review", "Bug", "Feature", "Ticket"]
VALID_STATUSES = ["Open", "Resolved", "Closed"]


class FeedbackService:
    """Service for managing user feedback."""

    def submit(self, user_id: Optional[int], category: str, subject: str,
               message: str, rating: Optional[int] = None) -> Dict:
        """Create a new feedback entry."""
        if category not in VALID_CATEGORIES:
            return {"success": False, "message": "Invalid feedback category."}
        if not message:
            return {"success": False, "message": "Message is required."}

        db = get_db()
        try:
            fb = Feedback(
                user_id=user_id,
                category=category,
                subject=subject or None,
                message=message,
                rating=rating,
                status="Open",
            )
            db.add(fb)
            db.commit()
            return {"success": True, "message": "Feedback submitted. Thank you!"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error submitting feedback: {e}"}
        finally:
            db.close()

    def get_by_category(self, category: str) -> List[Dict]:
        """Return feedback entries for a category, newest first."""
        db = get_db()
        try:
            rows = (
                db.query(Feedback)
                .filter(Feedback.category == category)
                .order_by(Feedback.created_at.desc())
                .all()
            )
            user_ids = {r.user_id for r in rows if r.user_id}
            names = {}
            if user_ids:
                for u in db.query(User).filter(User.user_id.in_(user_ids)).all():
                    names[u.user_id] = u.name
            return [self._to_dict(r, names) for r in rows]
        finally:
            db.close()

    def _to_dict(self, r: Feedback, names: Dict) -> Dict:
        return {
            "feedback_id": r.feedback_id,
            "user_id": r.user_id,
            "user_name": names.get(r.user_id, "Anonymous"),
            "category": r.category,
            "subject": r.subject or "",
            "message": r.message,
            "rating": r.rating,
            "status": r.status,
            "admin_reply": r.admin_reply or "",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A",
        }

    def update_status(self, feedback_id: int, status: str) -> Dict:
        """Update the status of a feedback entry."""
        if status not in VALID_STATUSES:
            return {"success": False, "message": "Invalid status."}
        db = get_db()
        try:
            fb = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
            if not fb:
                return {"success": False, "message": "Feedback not found."}
            fb.status = status
            db.commit()
            return {"success": True, "message": f"Marked as {status}."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error: {e}"}
        finally:
            db.close()

    def reply(self, feedback_id: int, reply: str) -> Dict:
        """Add an admin reply to a feedback entry."""
        db = get_db()
        try:
            fb = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
            if not fb:
                return {"success": False, "message": "Feedback not found."}
            fb.admin_reply = reply
            if fb.status == "Open":
                fb.status = "Resolved"
            db.commit()
            return {"success": True, "message": "Reply saved."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error: {e}"}
        finally:
            db.close()

    def delete(self, feedback_id: int) -> Dict:
        """Delete a feedback entry."""
        db = get_db()
        try:
            fb = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
            if not fb:
                return {"success": False, "message": "Feedback not found."}
            db.delete(fb)
            db.commit()
            return {"success": True, "message": "Feedback deleted."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error: {e}"}
        finally:
            db.close()

    def get_counts(self) -> Dict[str, int]:
        """Return counts per category and open tickets."""
        db = get_db()
        try:
            rows = db.query(Feedback).all()
            counts = {c: 0 for c in VALID_CATEGORIES}
            open_count = 0
            for r in rows:
                counts[r.category] = counts.get(r.category, 0) + 1
                if r.status == "Open":
                    open_count += 1
            counts["open"] = open_count
            counts["total"] = len(rows)
            return counts
        finally:
            db.close()
