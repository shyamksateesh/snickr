-- ─────────────────────────────────────────────────────────────
-- Snickr Schema
-- CS 6083 Principles of Database Systems — NYU Tandon Spring 2026
-- Shyam Krishna Sateesh — ss20355
-- ─────────────────────────────────────────────────────────────

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    nickname      VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Workspace ─────────────────────────────────────────────────
CREATE TABLE workspace (
    workspace_id SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    creator_id   INT          NOT NULL REFERENCES users(user_id),
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Workspace Admin ───────────────────────────────────────────
CREATE TABLE workspace_admin (
    workspace_id INT       NOT NULL REFERENCES workspace(workspace_id),
    user_id      INT       NOT NULL REFERENCES users(user_id),
    granted_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- ── Workspace Member ──────────────────────────────────────────
CREATE TABLE workspace_member (
    workspace_id INT       NOT NULL REFERENCES workspace(workspace_id),
    user_id      INT       NOT NULL REFERENCES users(user_id),
    is_active    BOOLEAN   NOT NULL DEFAULT TRUE,
    joined_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- ── Workspace Invitation ──────────────────────────────────────
CREATE TABLE workspace_invitation (
    invitation_id SERIAL PRIMARY KEY,
    workspace_id  INT         NOT NULL REFERENCES workspace(workspace_id),
    inviter_id    INT         NOT NULL REFERENCES users(user_id),
    invitee_id    INT         NOT NULL REFERENCES users(user_id),
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'accepted', 'declined')),
    invited_at    TIMESTAMP   NOT NULL DEFAULT NOW(),
    responded_at  TIMESTAMP,
    UNIQUE (workspace_id, invitee_id)
);

-- ── Channel ───────────────────────────────────────────────────
CREATE TABLE channel (
    channel_id   SERIAL PRIMARY KEY,
    workspace_id INT         NOT NULL REFERENCES workspace(workspace_id),
    name         VARCHAR(100) NOT NULL,
    channel_type VARCHAR(10) NOT NULL
                 CHECK (channel_type IN ('public', 'private', 'direct')),
    creator_id   INT         NOT NULL REFERENCES users(user_id),
    created_at   TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── Channel Member ────────────────────────────────────────────
CREATE TABLE channel_member (
    channel_id INT       NOT NULL REFERENCES channel(channel_id),
    user_id    INT       NOT NULL REFERENCES users(user_id),
    joined_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (channel_id, user_id)
);

-- ── Channel Invitation ────────────────────────────────────────
CREATE TABLE channel_invitation (
    invitation_id SERIAL PRIMARY KEY,
    channel_id    INT         NOT NULL REFERENCES channel(channel_id),
    inviter_id    INT         NOT NULL REFERENCES users(user_id),
    invitee_id    INT         NOT NULL REFERENCES users(user_id),
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'accepted', 'declined')),
    invited_at    TIMESTAMP   NOT NULL DEFAULT NOW(),
    responded_at  TIMESTAMP,
    UNIQUE (channel_id, invitee_id)
);

-- ── Message ───────────────────────────────────────────────────
CREATE TABLE message (
    message_id SERIAL PRIMARY KEY,
    channel_id INT       NOT NULL REFERENCES channel(channel_id),
    sender_id  INT       NOT NULL REFERENCES users(user_id),
    body       TEXT      NOT NULL,
    posted_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Verify ───────────────────────────────────────────────────
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
