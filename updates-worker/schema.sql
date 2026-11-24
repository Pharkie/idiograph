-- Idiograph's updates list. Run once, from this folder (README.md, Setting it up):
--   wrangler d1 execute idiograph-updates --remote --file schema.sql
-- Times are the Worker's own clock in ISO form, UTC.

-- One row an address. `email` is trimmed and lower-cased, and unique. `status` is pending until the
-- link in the confirmation email is used, then confirmed. `consent` is the version of the wording the
-- person saw (for example updates-2026-11-23), `source` site or app, `version` the app's version for
-- a sign-up from the app. `token_hash` is the SHA-256 of the newest confirmation link's token and the
-- CONFIRM_SALT secret, null once confirmed; `ip_hash` the SHA-256 of the sign-up's IP and IP_SALT,
-- null once confirmed. AUTOINCREMENT, so an id is never given again and an old unsubscribe link,
-- which is worked out from the id, can never reach someone else's row.
CREATE TABLE IF NOT EXISTS subscribers (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  email        TEXT NOT NULL,
  status       TEXT NOT NULL CHECK (status IN ('pending', 'confirmed')),
  source       TEXT NOT NULL DEFAULT '',
  version      TEXT NOT NULL DEFAULT '',
  consent      TEXT NOT NULL,
  created_at   TEXT NOT NULL,
  confirmed_at TEXT,
  token_hash   TEXT,
  ip_hash      TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS subscribers_email ON subscribers (email);
CREATE INDEX IF NOT EXISTS subscribers_token ON subscribers (token_hash);
CREATE INDEX IF NOT EXISTS subscribers_pending ON subscribers (status, created_at);

-- One row a sign-up the Worker acted on, for the limits alone: the SHA-256 of the address and of the
-- IP, each with IP_SALT, never either itself. `held` is '' when a confirmation email went out, or why
-- none did: 'ip' (that IP's ten an hour), 'address' (that address's hourly or daily limit), 'cap'
-- (the day's 100 in all), 'confirmed' (already on the list) or 'failed' (SES did not take it, so it
-- counts towards no limit). A sign-up takes its row in one statement that counts and inserts at once
-- (worker.js, signUp). The cron deletes rows over 2 days old.
CREATE TABLE IF NOT EXISTS sends (
  id         INTEGER PRIMARY KEY,
  email_hash TEXT NOT NULL,
  ip_hash    TEXT NOT NULL,
  at         TEXT NOT NULL,
  held       TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS sends_by_email ON sends (email_hash, at);
CREATE INDEX IF NOT EXISTS sends_by_ip ON sends (ip_hash, at);
CREATE INDEX IF NOT EXISTS sends_by_time ON sends (at);

-- The relay watch's seen counts (worker.js, relayWatch), kept by the hourly cron. `key` is
-- where|status|date (worker or project, the invocation's status, the UTC day) with `n` the non-success
-- invocations seen that day, or one of two markers with an empty `day`: _baselined (the first run has
-- been) and _fails (analytics queries failed this many runs in a row). Counts, statuses and dates only.
-- The hourly run deletes rows for days before yesterday.
CREATE TABLE IF NOT EXISTS relay_watch (
  key TEXT PRIMARY KEY,
  n   INTEGER NOT NULL,
  day TEXT NOT NULL DEFAULT ''
);
