-- CREATE EXTENSION IF NOT EXISTS vector;

-- main user table
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
	user_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
	username TEXT NOT NULL,
	encrypted_passkey TEXT NOT NULL,
	active BOOLEAN NOT NULL DEFAULT 1,
    CHECK (active in (0, 1))
);

-- only usernames for active accounts require uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_usernames
  	ON users(username)
  	WHERE active = 1;

-- main article table
CREATE TABLE IF NOT EXISTS articles (
    article_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    active BOOLEAN NOT NULL DEFAULT 1,
	title TEXT NOT NULL,
	authors_str TEXT NULL,
	publish_day INTEGER NULL,
	publish_month INTEGER NULL,
	publish_year INTEGER NULL,
	submitter_user_id INTEGER REFERENCES users(user_id),
    submitted_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (active in (0, 1))
);

-- holds information about the articles like text summaries and vector encodings
CREATE TABLE IF NOT EXISTS article_heuristics (
    article_id INTEGER PRIMARY KEY REFERENCES articles(article_id),
    summary_path TEXT NULL DEFAULT NULL,
    vector BLOB NULL DEFAULT NULL
);

-- log user actions
CREATE TABLE IF NOT EXISTS user_actions (
    action_id INTEGER NOT NULL PRIMARY KEY,
    action_name TEXT NOT NULL UNIQUE
);

INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (1, 'CREATE');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (2, 'DEACTIVATE');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (3, 'LOGIN');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (4, 'LOGOUT');

CREATE TABLE IF NOT EXISTS user_logs(
    log_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    log_action_id INTEGER NOT NULL REFERENCES user_actions(action_id),
    log_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- log article actions
CREATE TABLE IF NOT EXISTS article_actions (
    action_id INTEGER NOT NULL PRIMARY KEY,
    action_name TEXT NOT NULL UNIQUE
);

INSERT OR IGNORE INTO article_actions (action_id, action_name) VALUES (1, 'CREATE');
INSERT OR IGNORE INTO article_actions (action_id, action_name) VALUES (2, 'DELETE');
INSERT OR IGNORE INTO article_actions (action_id, action_name) VALUES (3, 'GENERATE_SUMMARY');

CREATE TABLE IF NOT EXISTS article_logs(
    log_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    article_id INTEGER NOT NULL REFERENCES articles(article_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    log_action_id INTEGER NOT NULL REFERENCES article_actions(action_id),
    log_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_reads (
    read_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    read_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

-- DIR STRUCTURE
-- /evanr/
-- -- database.sqlite3
-- -- articles/
-- -- -- <article_id>.txt
-- -- summaries/
-- -- -- <article_id>_sum.txt