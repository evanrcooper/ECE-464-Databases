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

-- contains extra information about the users
CREATE TABLE IF NOT EXISTS user_heuristics (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id),
    articles_read_count INTEGER NOT NULL DEFAULT 0,
    articles_liked_count INTEGER NOT NULL DEFAULT 0,
    articles_disliked_count INTEGER NOT NULL DEFAULT 0,
    CHECK (articles_read_count >= 0),
    CHECK (articles_liked_count >= 0),
    CHECK (articles_disliked_count >= 0)
);

-- main article table
CREATE TABLE IF NOT EXISTS articles (
    article_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    active BOOLEAN NOT NULL DEFAULT 1,
	title TEXT NOT NULL,
	authors_str TEXT NULL,
	publish_date DATETIME NULL,
	submitter_user_id INTEGER REFERENCES users(user_id),
	path TEXT NOT NULL,
    like_count INTEGER NOT NULL DEFAULT 0,
    CHECK (like_count >= 0),
    CHECK (active in (0, 1))
);

-- contains entries for users reading, liking, and disliking articles
CREATE TABLE IF NOT EXISTS article_interactions (
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    article_id INTEGER NOT NULL REFERENCES articles(article_id),
    like_or_dislike INTEGER NOT NULL DEFAULT 0,
    like_timestamp DATETIME NULL DEFAULT NULL,
    read BOOLEAN NOT NULL DEFAULT 0,
    read_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- most recent read
    CHECK (read in (0, 1)),
    CHECK (like_or_dislike in (-1, 0, 1)),
    PRIMARY KEY (user_id, article_id)
);

-- holds information about the articles like text summaries and vector encodings
CREATE TABLE IF NOT EXISTS article_heuristics (
    article_id INTEGER PRIMARY KEY REFERENCES articles(article_id),
    summary_path TEXT NULL DEFAULT NULL,
    vector BLOB NULL DEFAULT NULL
);

-- indexes all genres (aka keywords)
CREATE TABLE IF NOT EXISTS genres (
    genre_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    genre_name TEXT NOT NULL UNIQUE
);

CREATE UNIQUE INDEX IF NOT EXISTS genre_name_index ON genres (genre_name);

-- contains entries for if an article is associated with a genre
CREATE TABLE IF NOT EXISTS article_genres (
	article_id INTEGER NOT NULL REFERENCES articles(article_id),
	genre_id INTEGER NOT NULL REFERENCES genres(genre_id),
	PRIMARY KEY (article_id, genre_id)
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

-- DIR STRUCTURE
-- /evanr/
-- -- database.sqlite3
-- -- articles/
-- -- -- <article_id>.txt
-- -- summaries/
-- -- -- <article_id>_sum.txt