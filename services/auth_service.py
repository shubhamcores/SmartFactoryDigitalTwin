"""
Authentication and Authorization Service for FactoryTwin 
Enforces Role-Based Access Control (RBAC), session management, password hashing,
and route protection decorators for Administrators and Operators.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection
from services.audit_service import log_audit_event

def authenticate_user(username: str, password_candidate: str, ip_address: str = "127.0.0.1") -> dict:
    """Validate user credentials against SQLite users table and record audit log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, password_hash, role, full_name, email
        FROM users
        WHERE username = ?
    """, (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user["password_hash"], password_candidate):
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
        conn.commit()
        conn.close()

        user_dict = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
            "email": user["email"]
        }
        log_audit_event(user["id"], user["username"], "LOGIN_SUCCESS", ip_address, f"Role: {user['role']}")
        return user_dict

    conn.close()
    log_audit_event(None, username, "LOGIN_FAILED", ip_address, "Invalid username or password candidate")
    return None

def login_required(f):
    """Decorator ensuring that user is logged into an active session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please authenticate.", "status": 401}), 401
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator strictly restricting endpoint access to Administrators."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required", "status": 401}), 401
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            log_audit_event(
                session.get("user_id"),
                session.get("username", "Unknown"),
                "UNAUTHORIZED_ACCESS_ATTEMPT",
                request.remote_addr,
                f"Attempted access to restricted admin endpoint: {request.path}"
            )
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Forbidden: Administrator privileges required.", "status": 403}), 403
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Retrieve current session user dictionary."""
    if "user_id" in session:
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role"),
            "full_name": session.get("full_name")
        }
    return None
