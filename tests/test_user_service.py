"""Unit tests for UserService privileged operations and authorization."""

from backend.services.user_service import UserService


def test_non_admin_cannot_create_privileged_user(job_seeker_id):
    svc = UserService()
    res = svc.create_privileged_user(
        job_seeker_id, "New Rec", "denied_rec@example.com", "Password1", "", "Recruiter"
    )
    assert res["success"] is False
    assert "access denied" in res["message"].lower()


def test_admin_creates_recruiter(admin_id):
    svc = UserService()
    res = svc.create_privileged_user(
        admin_id, "Made Rec", "made_rec@example.com", "Password1", "", "Recruiter"
    )
    assert res["success"] is True


def test_cannot_create_job_seeker_via_privileged(admin_id):
    svc = UserService()
    res = svc.create_privileged_user(
        admin_id, "Seeker", "bad_seeker@example.com", "Password1", "", "Job Seeker"
    )
    assert res["success"] is False


def test_create_privileged_weak_password(admin_id):
    svc = UserService()
    res = svc.create_privileged_user(
        admin_id, "Weak", "weakpriv@example.com", "weak", "", "Recruiter"
    )
    assert res["success"] is False


def test_change_role_requires_admin(job_seeker_id, make_user):
    svc = UserService()
    target = make_user("Target", "target_role@example.com", "Password1")
    res = svc.change_role(job_seeker_id, target, "Recruiter")
    assert res["success"] is False


def test_admin_change_role(admin_id, make_user):
    svc = UserService()
    target = make_user("Promote", "promote_me@example.com", "Password1")
    res = svc.change_role(admin_id, target, "Recruiter")
    assert res["success"] is True
    assert svc.get_user_by_id(target)["role"] == "Recruiter"


def test_admin_cannot_change_own_role(admin_id):
    svc = UserService()
    res = svc.change_role(admin_id, admin_id, "Job Seeker")
    assert res["success"] is False


def test_disable_and_enable_user(admin_id, make_user):
    svc = UserService()
    target = make_user("Toggle", "toggle_me@example.com", "Password1")
    off = svc.set_active(admin_id, target, False)
    assert off["success"] is True
    assert svc.get_user_by_id(target)["is_active"] is False
    on = svc.set_active(admin_id, target, True)
    assert on["success"] is True


def test_reset_password(admin_id, make_user):
    svc = UserService()
    target = make_user("Resettable", "reset_me@example.com", "Password1")
    res = svc.reset_password(admin_id, target, "NewPass123")
    assert res["success"] is True
    from backend.auth.auth_service import login_user
    assert login_user("reset_me@example.com", "NewPass123")["success"] is True


def test_delete_user(admin_id, make_user):
    svc = UserService()
    target = make_user("Deletable", "delete_me@example.com", "Password1")
    res = svc.delete_user(target, admin_id=admin_id)
    assert res["success"] is True
    assert svc.get_user_by_id(target) is None


def test_admin_cannot_delete_self(admin_id):
    svc = UserService()
    res = svc.delete_user(admin_id, admin_id=admin_id)
    assert res["success"] is False
