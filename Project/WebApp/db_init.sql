-- main user table
CREATE TABLE IF NOT EXISTS users (
	uuid /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
	username TEXT NOT NULL,
	encrypted_passkey TEXT NOT NULL,
    creation_timestamp DATETIME NULL,
	active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS user_actions (
    action_id INTEGER NOT NULL PRIMARY KEY,
    action_name TEXT NOT NULL UNIQUE
);

INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (1, 'CREATE');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (2, 'DEACTIVATE');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (3, 'LOGIN');
INSERT OR IGNORE INTO user_actions (action_id, action_name) VALUES (4, 'LOGOFF');

CREATE TABLE IF NOT EXISTS user_logs(
    log_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    uuid INTEGER NOT NULL REFERENCES users(uuid),
    log_action_id INTEGER NOT NULL REFERENCES user_actions(action_id),
    timestamp DATETIME NOT NULL
);

-- only usernames for active accounts require uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_usernames
  	ON users(username)
  	WHERE active = 1;

-- contains extra information about the users
CREATE TABLE IF NOT EXISTS user_heuristics (
    uuid INTEGER PRIMARY KEY REFERENCES users(uuid),
    articles_read_count INTEGER NOT NULL DEFAULT 0,
    articles_liked_count INTEGER NOT NULL DEFAULT 0,
    articles_disliked_count INTEGER NOT NULL DEFAULT 0,
    CHECK (articles_read_count >= 0),
    CHECK (articles_liked_count >= 0),
    CHECK (articles_disliked_count >= 0)
);

-- contains entries for users reading, liking, and disliking articles
CREATE TABLE IF NOT EXISTS article_interactions (
    uuid INTEGER NOT NULL REFERENCES users(uuid),
    article_id INTEGER NOT NULL REFERENCES articles(article_id),
    liked BOOLEAN NOT NULL DEFAULT 0,
    disliked BOOLEAN NOT NULL DEFAULT 0,
    read BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (uuid, article_id)
);

-- main article table
CREATE TABLE IF NOT EXISTS articles (
    article_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    active BOOLEAN NOT NULL DEFAULT 1,
	title TEXT NOT NULL,
	author TEXT NULL,
	publish_date DATETIME NULL,
	submitted_date DATETIME NOT NULL,
	submitter_uuid INTEGER REFERENCES users(UUID),
	path TEXT NOT NULL,
    like_count INTEGER NOT NULL DEFAULT 0,
    CHECK (like_count >= 0)
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
    genre_name TEXT NULL DEFAULT NULL
);

-- contains entries for if an article is associated with a genre
CREATE TABLE IF NOT EXISTS article_genres (
	article_id INTEGER NOT NULL REFERENCES articles(article_id),
	genre_id INTEGER NOT NULL REFERENCES genres(genre_id),
	PRIMARY KEY (article_id, genre_id)
);

-- DIR STRUCTURE
-- /evanr/
-- -- database.sqlite3
-- -- articles/
-- -- -- <article_id>.txt
-- -- summaries/
-- -- -- <article_id>_sum.txt