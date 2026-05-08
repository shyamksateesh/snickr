"""
db.py — Database connection and helper utilities for Snickr.

All queries use psycopg2 parameterized queries (%s placeholders) to prevent
SQL injection. The connection is opened per-request via get_db() and closed
via close_db(), both registered with Flask's app context.
"""

import psycopg2
import psycopg2.extras
from flask import g
import os
from dotenv import load_dotenv

# ── Connection config ──────────────────────────────────────────────────────────

load_dotenv()

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME", "snickr"),
    "user":     os.getenv("DB_USER", "shyam"),
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db():
    """Return the per-request database connection (opens once per request)."""
    if "db" not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
        g.db.autocommit = False  # explicit transactions everywhere
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ── Generic query helpers ──────────────────────────────────────────────────────

def query_one(sql, params=()):
    """Execute SQL and return a single row as a dict, or None."""
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def query_all(sql, params=()):
    """Execute SQL and return all rows as a list of dicts."""
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def execute(sql, params=()):
    """Execute a write query (INSERT/UPDATE/DELETE). Does NOT commit."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params)


def execute_returning(sql, params=()):
    """Execute an INSERT ... RETURNING and return the first row as a dict."""
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


# ── User queries ───────────────────────────────────────────────────────────────

def get_user_by_username(username):
    return query_one(
        "SELECT * FROM users WHERE username = %s", (username,)
    )


def get_user_by_id(user_id):
    return query_one(
        "SELECT * FROM users WHERE user_id = %s", (user_id,)
    )


def get_user_by_email(email):
    return query_one(
        "SELECT * FROM users WHERE email = %s", (email,)
    )


def create_user(email, username, nickname, password_hash):
    return execute_returning(
        """
        INSERT INTO users (email, username, nickname, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id
        """,
        (email, username, nickname, password_hash),
    )


# ── Workspace queries ──────────────────────────────────────────────────────────

def get_workspaces_for_user(user_id):
    """Return all workspaces the user is an active member of."""
    return query_all(
        """
        SELECT w.workspace_id, w.name, w.description, w.created_at,
               u.username AS creator_username,
               EXISTS (
                   SELECT 1 FROM workspace_admin wa
                   WHERE wa.workspace_id = w.workspace_id AND wa.user_id = %s
               ) AS is_admin
        FROM workspace w
        JOIN workspace_member wm ON wm.workspace_id = w.workspace_id
        JOIN users u ON u.user_id = w.creator_id
        WHERE wm.user_id = %s AND wm.is_active = TRUE
        ORDER BY w.created_at DESC
        """,
        (user_id, user_id),
    )


def get_workspace_by_id(workspace_id):
    return query_one(
        "SELECT * FROM workspace WHERE workspace_id = %s", (workspace_id,)
    )


def is_workspace_member(workspace_id, user_id):
    row = query_one(
        """
        SELECT 1 FROM workspace_member
        WHERE workspace_id = %s AND user_id = %s AND is_active = TRUE
        """,
        (workspace_id, user_id),
    )
    return row is not None


def is_workspace_admin(workspace_id, user_id):
    row = query_one(
        """
        SELECT 1 FROM workspace_admin
        WHERE workspace_id = %s AND user_id = %s
        """,
        (workspace_id, user_id),
    )
    return row is not None


def create_workspace(name, description, creator_id):
    """
    TRANSACTION: Insert workspace, then insert creator into
    workspace_member AND workspace_admin atomically.
    """
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO workspace (name, description, creator_id)
                VALUES (%s, %s, %s)
                RETURNING workspace_id
                """,
                (name, description, creator_id),
            )
            workspace_id = cur.fetchone()["workspace_id"]

            cur.execute(
                """
                INSERT INTO workspace_member (workspace_id, user_id)
                VALUES (%s, %s)
                """,
                (workspace_id, creator_id),
            )

            cur.execute(
                """
                INSERT INTO workspace_admin (workspace_id, user_id)
                VALUES (%s, %s)
                """,
                (workspace_id, creator_id),
            )
        conn.commit()
        return workspace_id
    except Exception:
        conn.rollback()
        raise


def get_workspace_members(workspace_id):
    return query_all(
        """
        SELECT u.user_id, u.username, u.nickname, u.email, wm.joined_at,
               EXISTS (
                   SELECT 1 FROM workspace_admin wa
                   WHERE wa.workspace_id = %s AND wa.user_id = u.user_id
               ) AS is_admin
        FROM workspace_member wm
        JOIN users u ON u.user_id = wm.user_id
        WHERE wm.workspace_id = %s AND wm.is_active = TRUE
        ORDER BY u.username
        """,
        (workspace_id, workspace_id),
    )


def get_workspace_admins(workspace_id):
    return query_all(
        """
        SELECT u.user_id, u.username, u.email
        FROM workspace_admin wa
        JOIN users u ON u.user_id = wa.user_id
        WHERE wa.workspace_id = %s
        ORDER BY u.username
        """,
        (workspace_id,),
    )


def grant_admin(workspace_id, user_id):
    """Grant admin rights to an existing active workspace member."""
    conn = get_db()
    try:
        execute(
            """
            INSERT INTO workspace_admin (workspace_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (workspace_id, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def invite_to_workspace(workspace_id, inviter_id, invitee_id):
    """Insert a pending workspace invitation (idempotent on duplicate)."""
    execute(
        """
        INSERT INTO workspace_invitation (workspace_id, inviter_id, invitee_id)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (workspace_id, inviter_id, invitee_id),
    )
    get_db().commit()


def get_pending_workspace_invitations(user_id):
    return query_all(
        """
        SELECT wi.invitation_id, w.name AS workspace_name,
               u.username AS inviter_username, wi.invited_at
        FROM workspace_invitation wi
        JOIN workspace w ON w.workspace_id = wi.workspace_id
        JOIN users u ON u.user_id = wi.inviter_id
        WHERE wi.invitee_id = %s AND wi.status = 'pending'
        ORDER BY wi.invited_at DESC
        """,
        (user_id,),
    )


def respond_workspace_invitation(invitation_id, user_id, accept: bool):
    """
    TRANSACTION: Update invitation status; if accepting, insert into
    workspace_member atomically.
    """
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE workspace_invitation
                SET status = %s, responded_at = NOW()
                WHERE invitation_id = %s AND invitee_id = %s AND status = 'pending'
                RETURNING workspace_id
                """,
                ("accepted" if accept else "declined", invitation_id, user_id),
            )
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                return False

            if accept:
                cur.execute(
                    """
                    INSERT INTO workspace_member (workspace_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT (workspace_id, user_id) DO UPDATE SET is_active = TRUE
                    """,
                    (row["workspace_id"], user_id),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise


# ── Channel queries ────────────────────────────────────────────────────────────

def get_channels_for_workspace(workspace_id, user_id):
    """
    Return channels visible to the user in this workspace:
    - All public channels in the workspace
    - Private channels where the user is a member
    - Direct channels where the user is a member
    """
    return query_all(
        """
        SELECT c.channel_id, c.name, c.channel_type, c.created_at,
               u.username AS creator_username,
               EXISTS (
                   SELECT 1 FROM channel_member cm2
                   WHERE cm2.channel_id = c.channel_id AND cm2.user_id = %s
               ) AS is_member
        FROM channel c
        JOIN users u ON u.user_id = c.creator_id
        WHERE c.workspace_id = %s
          AND (
              c.channel_type = 'public'
              OR EXISTS (
                  SELECT 1 FROM channel_member cm
                  WHERE cm.channel_id = c.channel_id AND cm.user_id = %s
              )
          )
        ORDER BY c.channel_type, c.name
        """,
        (user_id, workspace_id, user_id),
    )


def get_channel_by_id(channel_id):
    return query_one(
        "SELECT * FROM channel WHERE channel_id = %s", (channel_id,)
    )


def is_channel_member(channel_id, user_id):
    row = query_one(
        "SELECT 1 FROM channel_member WHERE channel_id = %s AND user_id = %s",
        (channel_id, user_id),
    )
    return row is not None


def create_channel(workspace_id, name, channel_type, creator_id):
    """
    TRANSACTION: Create channel and add creator as member atomically.
    Enforces that creator is an active workspace member.
    """
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Authorization check
            cur.execute(
                """
                SELECT 1 FROM workspace_member
                WHERE workspace_id = %s AND user_id = %s AND is_active = TRUE
                """,
                (workspace_id, creator_id),
            )
            if cur.fetchone() is None:
                raise PermissionError("User is not an active workspace member.")

            cur.execute(
                """
                INSERT INTO channel (workspace_id, name, channel_type, creator_id)
                VALUES (%s, %s, %s, %s)
                RETURNING channel_id
                """,
                (workspace_id, name, channel_type, creator_id),
            )
            channel_id = cur.fetchone()["channel_id"]

            cur.execute(
                "INSERT INTO channel_member (channel_id, user_id) VALUES (%s, %s)",
                (channel_id, creator_id),
            )
        conn.commit()
        return channel_id
    except Exception:
        conn.rollback()
        raise


def join_public_channel(channel_id, user_id):
    """Add a user directly to a public channel (no invitation needed)."""
    conn = get_db()
    try:
        execute(
            """
            INSERT INTO channel_member (channel_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (channel_id, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_channel_members(channel_id):
    return query_all(
        """
        SELECT u.user_id, u.username, u.nickname
        FROM channel_member cm
        JOIN users u ON u.user_id = cm.user_id
        WHERE cm.channel_id = %s
        ORDER BY u.username
        """,
        (channel_id,),
    )


def invite_to_channel(channel_id, inviter_id, invitee_id):
    execute(
        """
        INSERT INTO channel_invitation (channel_id, inviter_id, invitee_id)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (channel_id, inviter_id, invitee_id),
    )
    get_db().commit()


def get_pending_channel_invitations(user_id):
    return query_all(
        """
        SELECT ci.invitation_id, c.name AS channel_name, c.channel_type,
               w.name AS workspace_name,
               u.username AS inviter_username, ci.invited_at
        FROM channel_invitation ci
        JOIN channel c ON c.channel_id = ci.channel_id
        JOIN workspace w ON w.workspace_id = c.workspace_id
        JOIN users u ON u.user_id = ci.inviter_id
        WHERE ci.invitee_id = %s AND ci.status = 'pending'
        ORDER BY ci.invited_at DESC
        """,
        (user_id,),
    )


def respond_channel_invitation(invitation_id, user_id, accept: bool):
    """
    TRANSACTION: Update channel invitation status; if accepting, insert
    into channel_member atomically.
    """
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE channel_invitation
                SET status = %s, responded_at = NOW()
                WHERE invitation_id = %s AND invitee_id = %s AND status = 'pending'
                RETURNING channel_id
                """,
                ("accepted" if accept else "declined", invitation_id, user_id),
            )
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                return False

            if accept:
                cur.execute(
                    """
                    INSERT INTO channel_member (channel_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (row["channel_id"], user_id),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise


# ── Message queries ────────────────────────────────────────────────────────────

def get_messages_in_channel(channel_id):
    return query_all(
        """
        SELECT m.message_id, m.body, m.posted_at,
               u.username, u.nickname
        FROM message m
        JOIN users u ON u.user_id = m.sender_id
        WHERE m.channel_id = %s
        ORDER BY m.posted_at ASC
        """,
        (channel_id,),
    )


def post_message(channel_id, sender_id, body):
    execute(
        """
        INSERT INTO message (channel_id, sender_id, body)
        VALUES (%s, %s, %s)
        """,
        (channel_id, sender_id, body),
    )
    get_db().commit()


def search_messages(user_id, keyword):
    """
    Return all messages containing keyword that are accessible to user_id.
    Accessibility = user is a member of both the workspace and the channel.
    (Query 7 from Project 1, parameterized.)
    """
    return query_all(
        """
        SELECT c.name AS channel_name, c.channel_id,
               w.name AS workspace_name, w.workspace_id,
               m.body, m.posted_at, u.username AS sender_username
        FROM message m
        JOIN channel c ON c.channel_id = m.channel_id
        JOIN workspace w ON w.workspace_id = c.workspace_id
        JOIN users u ON u.user_id = m.sender_id
        JOIN workspace_member wm ON wm.workspace_id = c.workspace_id
            AND wm.user_id = %s AND wm.is_active = TRUE
        JOIN channel_member cm ON cm.channel_id = m.channel_id
            AND cm.user_id = %s
        WHERE m.body ILIKE %s
        ORDER BY m.posted_at DESC
        """,
        (user_id, user_id, f"%{keyword}%"),
    )
