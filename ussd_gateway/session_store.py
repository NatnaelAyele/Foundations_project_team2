import time

SESSIONS = {}

SESSION_MAX_AGE_SECONDS = 300


def touch(session_key):
    """
    Marks a session as recently used so the sweeper does not remove it.
    Called on every USSD request for that session.
    """
    session = SESSIONS.get(session_key)
    if session is not None:
        session["last_seen"] = time.time()


def sweep_expired(max_age_seconds=SESSION_MAX_AGE_SECONDS):
    """
    Removes abandoned sessions (farmer closed the simulator/phone
    without pressing 0). Without this, a long-running server slowly
    accumulates dead session dictionaries forever.
    """
    now = time.time()
    expired_keys = [
        key
        for key, session in SESSIONS.items()
        if now - session.get("last_seen", now) > max_age_seconds
    ]
    for key in expired_keys:
        SESSIONS.pop(key, None)
    return len(expired_keys)


def reset_state():
    """Clear all active sessions (used before a fresh demo/test)."""
    SESSIONS.clear()