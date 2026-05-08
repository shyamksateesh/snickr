"""
app.py — Snickr Flask application.

Session management: Flask's built-in signed cookie session stores user_id.
All routes that require login use the @login_required decorator.
Passwords are hashed with werkzeug's generate_password_hash / check_password_hash.
All DB queries go through db.py and use psycopg2 parameterized queries.
All template output is auto-escaped by Jinja2 (XSS protection by default).
"""

from functools import wraps
import os
from dotenv import load_dotenv

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import db as database

app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")

# Register DB teardown
app.teardown_appcontext(database.close_db)


# ── Auth helpers ───────────────────────────────────────────────────────────────
    
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" in session:
        return database.get_user_by_id(session["user_id"])
    return None


# ── Root ───────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("workspaces"))
    return redirect(url_for("login"))


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("workspaces"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")

        # Basic validation
        if not email or not username or not password:
            flash("Email, username, and password are required.", "error")
            return render_template("auth/register.html")

        if len(username) > 50:
            flash("Username must be 50 characters or fewer.", "error")
            return render_template("auth/register.html")

        if database.get_user_by_email(email):
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html")

        if database.get_user_by_username(username):
            flash("That username is already taken.", "error")
            return render_template("auth/register.html")

        password_hash = generate_password_hash(password)
        row = database.create_user(email, username, nickname or None, password_hash)
        database.get_db().commit()

        session["user_id"] = row["user_id"]
        flash(f"Welcome to Snickr, {username}!", "success")
        return redirect(url_for("workspaces"))

    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("workspaces"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = database.get_user_by_username(username)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html")

        session.clear()
        session["user_id"] = user["user_id"]
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(url_for("workspaces"))

    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("login"))


# ── Workspace routes ───────────────────────────────────────────────────────────

@app.route("/workspaces")
@login_required
def workspaces():
    user = current_user()
    user_workspaces = database.get_workspaces_for_user(session["user_id"])
    pending_ws = database.get_pending_workspace_invitations(session["user_id"])
    pending_ch = database.get_pending_channel_invitations(session["user_id"])
    return render_template(
        "workspace/list.html",
        user=user,
        workspaces=user_workspaces,
        pending_workspace_count=len(pending_ws),
        pending_channel_count=len(pending_ch),
    )


@app.route("/workspaces/create", methods=["GET", "POST"])
@login_required
def create_workspace():
    user = current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Workspace name is required.", "error")
            return render_template("workspace/create.html", user=user)

        if len(name) > 100:
            flash("Workspace name must be 100 characters or fewer.", "error")
            return render_template("workspace/create.html", user=user)

        ws_id = database.create_workspace(name, description or None, session["user_id"])
        flash(f"Workspace '{name}' created!", "success")
        return redirect(url_for("workspace_detail", workspace_id=ws_id))

    return render_template("workspace/create.html", user=user)


@app.route("/workspaces/<int:workspace_id>")
@login_required
def workspace_detail(workspace_id):
    user = current_user()
    ws = database.get_workspace_by_id(workspace_id)
    if ws is None:
        flash("Workspace not found.", "error")
        return redirect(url_for("workspaces"))

    if not database.is_workspace_member(workspace_id, session["user_id"]):
        flash("You are not a member of that workspace.", "error")
        return redirect(url_for("workspaces"))

    channels = database.get_channels_for_workspace(workspace_id, session["user_id"])
    members = database.get_workspace_members(workspace_id)
    is_admin = database.is_workspace_admin(workspace_id, session["user_id"])

    return render_template(
        "workspace/detail.html",
        user=user,
        workspace=ws,
        channels=channels,
        members=members,
        is_admin=is_admin,
    )


@app.route("/workspaces/<int:workspace_id>/grant-admin", methods=["POST"])
@login_required
def grant_admin(workspace_id):
    # Only existing admins can grant admin rights
    if not database.is_workspace_admin(workspace_id, session["user_id"]):
        flash("Only workspace admins can grant admin rights.", "error")
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    username = request.form.get("username", "").strip()
    target = database.get_user_by_username(username)

    if target is None:
        flash(f"No user found with username '{username}'.", "error")
    elif not database.is_workspace_member(workspace_id, target["user_id"]):
        flash(f"{username} is not a member of this workspace.", "error")
    elif database.is_workspace_admin(workspace_id, target["user_id"]):
        flash(f"{username} is already an admin.", "warning")
    else:
        database.grant_admin(workspace_id, target["user_id"])
        flash(f"{username} is now an admin.", "success")

    return redirect(url_for("workspace_detail", workspace_id=workspace_id))


@app.route("/workspaces/<int:workspace_id>/invite", methods=["POST"])
@login_required
def invite_to_workspace(workspace_id):
    ws = database.get_workspace_by_id(workspace_id)
    if ws is None or not database.is_workspace_admin(workspace_id, session["user_id"]):
        flash("Only workspace admins can send invitations.", "error")
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    invitee_username = request.form.get("username", "").strip()
    invitee = database.get_user_by_username(invitee_username)

    if invitee is None:
        flash(f"No user found with username '{invitee_username}'.", "error")
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    if database.is_workspace_member(workspace_id, invitee["user_id"]):
        flash(f"{invitee_username} is already a member.", "warning")
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    database.invite_to_workspace(workspace_id, session["user_id"], invitee["user_id"])
    flash(f"Invitation sent to {invitee_username}.", "success")
    return redirect(url_for("workspace_detail", workspace_id=workspace_id))


# ── Channel routes ─────────────────────────────────────────────────────────────

@app.route("/workspaces/<int:workspace_id>/channels/create", methods=["GET", "POST"])
@login_required
def create_channel(workspace_id):
    user = current_user()
    ws = database.get_workspace_by_id(workspace_id)

    if ws is None or not database.is_workspace_member(workspace_id, session["user_id"]):
        flash("You must be a workspace member to create channels.", "error")
        return redirect(url_for("workspaces"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        channel_type = request.form.get("channel_type", "public")

        if not name:
            flash("Channel name is required.", "error")
            return render_template("channel/create.html", user=user, workspace=ws)

        if channel_type not in ("public", "private", "direct"):
            flash("Invalid channel type.", "error")
            return render_template("channel/create.html", user=user, workspace=ws)

        if len(name) > 100:
            flash("Channel name must be 100 characters or fewer.", "error")
            return render_template("channel/create.html", user=user, workspace=ws)

        try:
            ch_id = database.create_channel(workspace_id, name, channel_type, session["user_id"])
        except PermissionError as e:
            flash(str(e), "error")
            return render_template("channel/create.html", user=user, workspace=ws)

        # If direct channel, invite the second user immediately
        if channel_type == "direct":
            other_username = request.form.get("direct_user", "").strip()
            other_user = database.get_user_by_username(other_username)
            if other_user is None:
                flash("Direct channel created, but that user wasn't found.", "warning")
            elif not database.is_workspace_member(workspace_id, other_user["user_id"]):
                flash("That user is not a workspace member.", "warning")
            else:
                database.invite_to_channel(ch_id, session["user_id"], other_user["user_id"])

        flash(f"Channel '#{name}' created!", "success")
        return redirect(url_for("channel_detail", channel_id=ch_id))

    return render_template("channel/create.html", user=user, workspace=ws)


@app.route("/channels/<int:channel_id>")
@login_required
def channel_detail(channel_id):
    user = current_user()
    ch = database.get_channel_by_id(channel_id)

    if ch is None:
        flash("Channel not found.", "error")
        return redirect(url_for("workspaces"))

    ws = database.get_workspace_by_id(ch["workspace_id"])

    # Must be workspace member
    if not database.is_workspace_member(ch["workspace_id"], session["user_id"]):
        flash("You are not a member of this workspace.", "error")
        return redirect(url_for("workspaces"))

    # For non-public channels, must also be channel member
    if ch["channel_type"] != "public":
        if not database.is_channel_member(channel_id, session["user_id"]):
            flash("You are not a member of this channel.", "error")
            return redirect(url_for("workspace_detail", workspace_id=ch["workspace_id"]))

    is_member = database.is_channel_member(channel_id, session["user_id"])
    messages = database.get_messages_in_channel(channel_id) if is_member else []
    members = database.get_channel_members(channel_id)
    ws_members = database.get_workspace_members(ch["workspace_id"])

    return render_template(
        "channel/detail.html",
        user=user,
        channel=ch,
        workspace=ws,
        messages=messages,
        members=members,
        ws_members=ws_members,
        is_member=is_member,
    )


@app.route("/channels/<int:channel_id>/join", methods=["POST"])
@login_required
def join_channel(channel_id):
    ch = database.get_channel_by_id(channel_id)
    if ch is None or ch["channel_type"] != "public":
        flash("You can only join public channels directly.", "error")
        return redirect(url_for("workspaces"))

    if not database.is_workspace_member(ch["workspace_id"], session["user_id"]):
        flash("You must be a workspace member first.", "error")
        return redirect(url_for("workspaces"))

    database.join_public_channel(channel_id, session["user_id"])
    flash(f"You joined #{ch['name']}!", "success")
    return redirect(url_for("channel_detail", channel_id=channel_id))


@app.route("/channels/<int:channel_id>/post", methods=["POST"])
@login_required
def post_message(channel_id):
    ch = database.get_channel_by_id(channel_id)
    if ch is None:
        flash("Channel not found.", "error")
        return redirect(url_for("workspaces"))

    if not database.is_channel_member(channel_id, session["user_id"]):
        flash("You are not a member of this channel.", "error")
        return redirect(url_for("channel_detail", channel_id=channel_id))

    body = request.form.get("body", "").strip()
    if not body:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("channel_detail", channel_id=channel_id))

    database.post_message(channel_id, session["user_id"], body)
    return redirect(url_for("channel_detail", channel_id=channel_id))


@app.route("/channels/<int:channel_id>/invite", methods=["POST"])
@login_required
def invite_to_channel(channel_id):
    ch = database.get_channel_by_id(channel_id)
    if ch is None:
        flash("Channel not found.", "error")
        return redirect(url_for("workspaces"))

    if not database.is_channel_member(channel_id, session["user_id"]):
        flash("Only channel members can send invitations.", "error")
        return redirect(url_for("channel_detail", channel_id=channel_id))

    invitee_username = request.form.get("username", "").strip()
    invitee = database.get_user_by_username(invitee_username)

    if invitee is None:
        flash(f"No user found with username '{invitee_username}'.", "error")
    elif not database.is_workspace_member(ch["workspace_id"], invitee["user_id"]):
        flash(f"{invitee_username} is not a member of this workspace.", "error")
    elif database.is_channel_member(channel_id, invitee["user_id"]):
        flash(f"{invitee_username} is already in this channel.", "warning")
    else:
        database.invite_to_channel(channel_id, session["user_id"], invitee["user_id"])
        flash(f"Invitation sent to {invitee_username}.", "success")

    return redirect(url_for("channel_detail", channel_id=channel_id))


# ── Invitations ────────────────────────────────────────────────────────────────

@app.route("/invitations")
@login_required
def invitations():
    user = current_user()
    ws_invites = database.get_pending_workspace_invitations(session["user_id"])
    ch_invites = database.get_pending_channel_invitations(session["user_id"])
    return render_template(
        "invitations.html",
        user=user,
        workspace_invitations=ws_invites,
        channel_invitations=ch_invites,
    )


@app.route("/invitations/<int:invitation_id>/respond", methods=["POST"])
@login_required
def respond_workspace_invitation(invitation_id):
    action = request.form.get("action")
    accept = action == "accept"
    database.respond_workspace_invitation(invitation_id, session["user_id"], accept)
    flash("Invitation accepted!" if accept else "Invitation declined.", "success" if accept else "info")
    return redirect(url_for("invitations"))


@app.route("/channel-invitations/<int:invitation_id>/respond", methods=["POST"])
@login_required
def respond_channel_invitation(invitation_id):
    action = request.form.get("action")
    accept = action == "accept"
    database.respond_channel_invitation(invitation_id, session["user_id"], accept)
    flash("Invitation accepted!" if accept else "Invitation declined.", "success" if accept else "info")
    return redirect(url_for("invitations"))


# ── Search ─────────────────────────────────────────────────────────────────────

@app.route("/search")
@login_required
def search():
    user = current_user()
    keyword = request.args.get("q", "").strip()
    results = []
    if keyword:
        results = database.search_messages(session["user_id"], keyword)
    return render_template("search.html", user=user, keyword=keyword, results=results)


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)