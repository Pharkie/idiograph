-- Idiograph's feedback notes, one row a note. Run once, from this folder:
--   wrangler d1 execute idiograph-feedback --remote --file schema.sql
-- `at` is the collector's own clock in ISO form, UTC. `ip_hash` is the SHA-256 of the sender's IP
-- and the IP_SALT secret, so no raw IP is ever stored.
CREATE TABLE IF NOT EXISTS notes (
  id       INTEGER PRIMARY KEY,
  at       TEXT NOT NULL,
  text     TEXT NOT NULL,
  contact  TEXT NOT NULL DEFAULT '',
  version  TEXT NOT NULL DEFAULT '',
  platform TEXT NOT NULL DEFAULT '',
  screen   TEXT NOT NULL DEFAULT '',
  agent    TEXT NOT NULL DEFAULT '',
  ip_hash  TEXT NOT NULL
);

-- the hourly limit counts a sender's notes by the hash and the time
CREATE INDEX IF NOT EXISTS notes_by_sender ON notes (ip_hash, at);
