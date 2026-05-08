-- ─────────────────────────────────────────────────────────────
-- Snickr Sample Data — Realistic Tech Startup Scenario
-- Run in psql: \i seed.sql
-- Assumes tables are empty (run TRUNCATE ... RESTART IDENTITY CASCADE first)
-- ─────────────────────────────────────────────────────────────

-- ── Users (8 people at a startup) ────────────────────────────
INSERT INTO users (email, username, nickname, password_hash) VALUES
('priya.sharma@axiomhq.io',   'priya',   'Priya',   'pbkdf2:sha256:260000$placeholder$aaa'),
('marcus.chen@axiomhq.io',    'marcus',  'Marc',    'pbkdf2:sha256:260000$placeholder$bbb'),
('sofia.reyes@axiomhq.io',    'sofia',   'Sof',     'pbkdf2:sha256:260000$placeholder$ccc'),
('dan.kowalski@axiomhq.io',   'dan',     'Dan',     'pbkdf2:sha256:260000$placeholder$ddd'),
('aisha.okonkwo@axiomhq.io',  'aisha',   'Aisha',   'pbkdf2:sha256:260000$placeholder$eee'),
('liam.nakamura@axiomhq.io',  'liam',    'Liam',    'pbkdf2:sha256:260000$placeholder$fff'),
('elena.petrov@axiomhq.io',   'elena',   'Ellie',   'pbkdf2:sha256:260000$placeholder$ggg'),
('raj.patel@axiomhq.io',      'raj',     'Raj',     'pbkdf2:sha256:260000$placeholder$hhh');

-- ── Workspaces ────────────────────────────────────────────────
INSERT INTO workspace (name, description, creator_id) VALUES
('Axiom HQ',      'Main workspace for the Axiom engineering team', 1),
('Design Studio', 'UI/UX design team workspace',                   3);

-- ── Workspace Admins ─────────────────────────────────────────
INSERT INTO workspace_admin (workspace_id, user_id) VALUES
(1, 1),  -- priya admins Axiom HQ
(1, 2),  -- marcus co-admins Axiom HQ
(2, 3);  -- sofia admins Design Studio

-- ── Workspace Members ─────────────────────────────────────────
INSERT INTO workspace_member (workspace_id, user_id, is_active) VALUES
(1, 1, TRUE),
(1, 2, TRUE),
(1, 3, TRUE),
(1, 4, TRUE),
(1, 5, TRUE),
(1, 6, TRUE),
(2, 3, TRUE),
(2, 5, TRUE),
(2, 7, TRUE);

-- ── Channels ──────────────────────────────────────────────────
INSERT INTO channel (workspace_id, name, channel_type, creator_id) VALUES
(1, 'general',      'public',  1),   -- ch 1
(1, 'engineering',  'public',  2),   -- ch 2
(1, 'releases',     'public',  1),   -- ch 3
(1, 'hiring',       'private', 1),   -- ch 4
(1, 'priya-marcus', 'direct',  1),   -- ch 5
(2, 'general',      'public',  3),   -- ch 6
(2, 'design-review','private', 3);   -- ch 7

-- ── Channel Members ───────────────────────────────────────────
INSERT INTO channel_member (channel_id, user_id) VALUES
-- #general (workspace 1) — everyone
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
-- #engineering — eng team
(2, 2), (2, 4), (2, 6),
-- #releases — everyone
(3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
-- #hiring — admins only
(4, 1), (4, 2),
-- #priya-marcus — direct
(5, 1), (5, 2),
-- Design Studio #general
(6, 3), (6, 5), (6, 7),
-- Design Studio #design-review
(7, 3), (7, 5);

-- ── Messages — #general (channel 1) ──────────────────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(1, 1, 'Good morning everyone! Quick reminder — sprint planning kicks off at 10am today. See you all there 🚀', NOW() - INTERVAL '6 days'),
(1, 2, 'On it. I''ll have the velocity chart pulled up before we start.', NOW() - INTERVAL '6 days' + INTERVAL '4 minutes'),
(1, 4, 'Can we add the auth refactor to the backlog? Been meaning to bring it up.', NOW() - INTERVAL '6 days' + INTERVAL '9 minutes'),
(1, 1, 'Absolutely Dan, add it as a ticket and we''ll slot it in.', NOW() - INTERVAL '6 days' + INTERVAL '13 minutes'),
(1, 3, 'Hey all — I''ll be dropping the updated design tokens into Figma this afternoon. Will ping when ready.', NOW() - INTERVAL '5 days'),
(1, 5, 'Just wrapped the onboarding flow wireframes. Sharing in #design-review for feedback.', NOW() - INTERVAL '5 days' + INTERVAL '2 hours'),
(1, 6, 'Deployed the new API gateway to staging. Latency is down 40% compared to last week — pretty happy with this.', NOW() - INTERVAL '4 days'),
(1, 2, 'Nice work Liam! What was the main bottleneck you fixed?', NOW() - INTERVAL '4 days' + INTERVAL '8 minutes'),
(1, 6, 'Connection pooling was the main culprit. Each request was spinning up a new connection. Fixed that and it flew.', NOW() - INTERVAL '4 days' + INTERVAL '15 minutes'),
(1, 4, 'That''s a huge win. Should we document this in the runbook?', NOW() - INTERVAL '4 days' + INTERVAL '22 minutes'),
(1, 1, 'Yes please Dan — add it to the engineering wiki when you get a chance.', NOW() - INTERVAL '4 days' + INTERVAL '30 minutes'),
(1, 2, 'Team — heads up that we''re doing a code freeze from 5pm Friday until Monday morning ahead of the v2.1 release.', NOW() - INTERVAL '3 days'),
(1, 3, 'Got it. I''ll make sure all design assets are finalized by Thursday EOD then.', NOW() - INTERVAL '3 days' + INTERVAL '11 minutes'),
(1, 5, 'Same — all UI specs will be locked by Thursday.', NOW() - INTERVAL '3 days' + INTERVAL '20 minutes'),
(1, 1, 'Perfect. This release is going to be a big one. Really proud of what the team has built 💪', NOW() - INTERVAL '3 days' + INTERVAL '35 minutes'),
(1, 4, 'Quick update — auth refactor PR is up for review. 847 lines changed but I think it''s clean. Would love a second pair of eyes.', NOW() - INTERVAL '2 days'),
(1, 2, 'On it, will review this afternoon.', NOW() - INTERVAL '2 days' + INTERVAL '5 minutes'),
(1, 6, 'I''ll take a look too Dan.', NOW() - INTERVAL '2 days' + INTERVAL '8 minutes'),
(1, 1, 'Happy Friday everyone! Great sprint. Enjoy the weekend 🎉', NOW() - INTERVAL '1 day'),
(1, 3, 'Happy Friday! 🙌', NOW() - INTERVAL '1 day' + INTERVAL '3 minutes');

-- ── Messages — #engineering (channel 2) ──────────────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(2, 2, 'Switching our CI pipeline from Jenkins to GitHub Actions. Should cut build times significantly. PR up for review.', NOW() - INTERVAL '5 days'),
(2, 4, 'Finally! Jenkins has been a pain. I''ll review the workflow files today.', NOW() - INTERVAL '5 days' + INTERVAL '15 minutes'),
(2, 6, 'One thing to watch — make sure the secrets are properly scoped in the Actions config. Happy to help with that part.', NOW() - INTERVAL '5 days' + INTERVAL '28 minutes'),
(2, 2, 'Good call Liam. I''ll add you as a reviewer on the PR.', NOW() - INTERVAL '5 days' + INTERVAL '35 minutes'),
(2, 4, 'PR approved. Clean setup Marcus. Build time went from 8 min to 2:40 on my test run.', NOW() - INTERVAL '4 days'),
(2, 2, 'Merged. Thanks both. Keeping an eye on the first few prod runs.', NOW() - INTERVAL '4 days' + INTERVAL '10 minutes'),
(2, 6, 'Database migration for the user preferences table is ready. Anyone have bandwidth to review before I run it on staging?', NOW() - INTERVAL '3 days'),
(2, 4, 'Send it over, I''ll take a look.', NOW() - INTERVAL '3 days' + INTERVAL '7 minutes'),
(2, 6, 'Shared the migration script in the PR. Main change is adding a jsonb column for preference storage — more flexible than the current approach.', NOW() - INTERVAL '3 days' + INTERVAL '20 minutes'),
(2, 4, 'Reviewed — looks solid. One suggestion: add an index on the user_id column for the new table. Will speed up lookups.', NOW() - INTERVAL '3 days' + INTERVAL '45 minutes'),
(2, 6, 'Great catch — added. Running on staging now.', NOW() - INTERVAL '3 days' + INTERVAL '55 minutes'),
(2, 2, 'Staging migration successful. Promoting to prod tomorrow morning.', NOW() - INTERVAL '2 days');

-- ── Messages — #releases (channel 3) ─────────────────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(3, 1, 'Cutting the v2.1 release branch today. Feature freeze is now in effect. Bug fixes only from here.', NOW() - INTERVAL '3 days'),
(3, 2, 'Release notes draft is in Notion — please review and add anything I''ve missed.', NOW() - INTERVAL '3 days' + INTERVAL '1 hour'),
(3, 3, 'Added the design system updates to the release notes. Also attached the updated changelog.', NOW() - INTERVAL '2 days'),
(3, 4, 'Auth refactor is merged and tested. Ready for release.', NOW() - INTERVAL '2 days' + INTERVAL '3 hours'),
(3, 6, 'API gateway improvements are in. Staging has been stable for 48 hours.', NOW() - INTERVAL '1 day'),
(3, 1, 'v2.1 is LIVE 🎉 Great work everyone. Monitoring dashboards look clean.', NOW() - INTERVAL '12 hours'),
(3, 2, 'Smooth release! Zero rollbacks. This is what good engineering looks like 🙌', NOW() - INTERVAL '11 hours'),
(3, 5, 'The new onboarding UI is getting great feedback already. Users are completing setup 30% faster.', NOW() - INTERVAL '10 hours');

-- ── Messages — #hiring (channel 4, private) ───────────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(4, 1, 'We have two strong candidates for the senior backend role. Scheduling final rounds for next week.', NOW() - INTERVAL '4 days'),
(4, 2, 'I interviewed candidate A yesterday — really strong systems design instincts. Would be a great fit for the infra work.', NOW() - INTERVAL '4 days' + INTERVAL '2 hours'),
(4, 1, 'Agreed. Let''s make sure we move fast — they mentioned they have another offer pending.', NOW() - INTERVAL '4 days' + INTERVAL '2 hours 15 minutes'),
(4, 2, 'Offer letter going out today. Fingers crossed 🤞', NOW() - INTERVAL '3 days'),
(4, 1, 'They accepted! Starting in three weeks. Super excited to have them join.', NOW() - INTERVAL '2 days'),
(4, 2, 'Excellent news! I''ll set up their onboarding doc and workspace access.', NOW() - INTERVAL '2 days' + INTERVAL '10 minutes');

-- ── Messages — #priya-marcus direct (channel 5) ───────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(5, 1, 'Hey Marcus — can you take point on the investor update deck this week? I''m swamped with the release.', NOW() - INTERVAL '4 days'),
(5, 2, 'Of course, I''ll have a draft ready by Wednesday.', NOW() - INTERVAL '4 days' + INTERVAL '5 minutes'),
(5, 1, 'Thank you. Focus on the growth metrics and the v2.1 highlights. Those are the strongest story right now.', NOW() - INTERVAL '4 days' + INTERVAL '10 minutes'),
(5, 2, 'Draft is in Google Drive — link in your email. Let me know if you want to walk through it.', NOW() - INTERVAL '2 days'),
(5, 1, 'Just reviewed — this is excellent. Really clear narrative. Minor edits left in comments.', NOW() - INTERVAL '2 days' + INTERVAL '3 hours'),
(5, 2, 'Updated based on your comments. Ready to send whenever you are.', NOW() - INTERVAL '1 day');

-- ── Messages — Design Studio #general (channel 6) ─────────────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(6, 3, 'Welcome to the Design Studio workspace! This is our home for all things design. Let''s keep it creative 🎨', NOW() - INTERVAL '7 days'),
(6, 5, 'Excited to be here! Just finished the onboarding flow — sharing in #design-review for feedback.', NOW() - INTERVAL '6 days'),
(6, 7, 'New brand color palette is ready for review. I''ve uploaded the swatches to Figma.', NOW() - INTERVAL '5 days'),
(6, 3, 'Love the direction Elena. The teal and slate combo is really working.', NOW() - INTERVAL '5 days' + INTERVAL '1 hour'),
(6, 7, 'Thanks! Made some tweaks based on accessibility contrast checks — all colors now pass WCAG AA.', NOW() - INTERVAL '4 days'),
(6, 5, 'Component library update is live in Figma. Added 12 new variants to the button component.', NOW() - INTERVAL '3 days'),
(6, 3, 'Great work everyone. Design is looking really cohesive for v2.1 🙌', NOW() - INTERVAL '2 days');

-- ── Messages — Design Studio #design-review (channel 7) ───────
INSERT INTO message (channel_id, sender_id, body, posted_at) VALUES
(7, 5, 'Sharing the onboarding flow for review. Three screens: welcome, workspace setup, and first channel join. Feedback welcome!', NOW() - INTERVAL '6 days'),
(7, 3, 'Really clean Aisha. One thought — the CTA button on screen 2 could be more prominent. Maybe full width?', NOW() - INTERVAL '6 days' + INTERVAL '30 minutes'),
(7, 5, 'Good call. Updated — full width button feels much stronger. Also bumped the font size on the headline.', NOW() - INTERVAL '5 days'),
(7, 3, 'Perfect. This is ready to hand off to engineering. Great work!', NOW() - INTERVAL '5 days' + INTERVAL '15 minutes');

-- ── Workspace Invitations ─────────────────────────────────────
INSERT INTO workspace_invitation (workspace_id, inviter_id, invitee_id, status, invited_at, responded_at) VALUES
(1, 1, 7, 'pending', NOW() - INTERVAL '1 day', NULL),
(2, 3, 4, 'pending', NOW() - INTERVAL '2 days', NULL);

-- ── Channel Invitations ───────────────────────────────────────
INSERT INTO channel_invitation (channel_id, inviter_id, invitee_id, status, invited_at, responded_at) VALUES
(4, 1, 3, 'declined', NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'),
(7, 3, 6, 'pending',  NOW() - INTERVAL '1 day',  NULL);

-- ── Done ──────────────────────────────────────────────────────
SELECT 'Users:'      AS table_name, COUNT(*) FROM users
UNION ALL SELECT 'Workspaces:', COUNT(*) FROM workspace
UNION ALL SELECT 'Channels:',   COUNT(*) FROM channel
UNION ALL SELECT 'Messages:',   COUNT(*) FROM message
UNION ALL SELECT 'Members:',    COUNT(*) FROM workspace_member;
