CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  state TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  next_action_at DATETIME
);

INSERT OR IGNORE INTO meta (key, value) VALUES ('last_processed_timestamp', '0');
