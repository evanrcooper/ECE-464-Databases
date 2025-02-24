-- main user table
CREATE TABLE IF NOT EXISTS users (
	uuid /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
	username TEXT NOT NULL,
	display_name TEXT NOT NULL,
	encrypted_passkey TEXT NOT NULL,
	active BOOLEAN NOT NULL DEFAULT 1,
);

-- only usernames for active accounts require uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_usernames
  	ON users(username)
  	WHERE active = 1;

-- contains extra information about the users
CREATE TABLE IF NOT EXISTS user_heuristics (
    uuid INTEGER PRIMARY KEY FOREIGN KEY users(uuid),
    articles_read_count INTEGER NOT NULL DEFAULT 0,
    articles_liked_count INTEGER NOT NULL DEFAULT 0,
    articles_disliked_count INTEGER NOT NULL DEFAULT 0,
    CHECK (articles_read_count >= 0),
    CHECK (articles_liked_count >= 0),
    CHECK (articles_disliked_count >= 0),
);

-- contains entries for users reading, liking, and disliking articles
CREATE TABLE IF NOT EXISTS article_interactions (
    uuid INTEGER FOREIGN KEY users(uuid),
    article_id INTEGER FOREIGN KEY articles(article_id),
    (article_id, genre_id) PRIMARY KEY,
    like BOOLEAN NOT NULL DEFAULT 0,
    dislike BOOLEAN NOT NULL DEFAULT 0,
    read BOOLEAN NOT NULL DEFAULT 0,
);

-- main article table
CREATE TABLE IF NOT EXISTS articles (
    article_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    active BOOLEAN NOT NULL DEFAULT 1,
	title TEXT NOT NULL,
	author TEXT NULL,
	publish_date DATETIME NULL,
	submitted_date DATETIME NOT NULL,
	submitter_uuid INTEGER FOREIGN KEY users(UUID),
	path TEXT NOT NULL,
    like_count INTEGER NOT NULL DEFAULT 0,
    CHECK (like_count >= 0),
);

-- holds information about the articles like text summaries and vector encodings
CREATE TABLE IF NOT EXISTS article_heuristics (
    article_id INTEGER PRIMARY KEY FOREIGN KEY articles(article_id),
    summary_path TEXT NULL DEFAULT NULL,
    vector BLOB NULL DEFAULT NULL,
);

-- indexes all genres (aka keywords)
CREATE TABLE genres (
    genre_id /* AUTOINCREMENT */ INTEGER PRIMARY KEY, -- https://www.sqlite.org/autoinc.html
    genre_name TEXT NULL DEFAULT NULL,
);

-- contains entries for if an article is associated with a genre
CREATE TABLE article_genres (
	article_id INTEGER NOT NULL FOREIGN KEY articles(article_id),
	genre_id INTEGER NOT NULL FOREIGN KEY genres(genre_id),
	(article_id, genre_id) PRIMARY KEY,
);

-- DIR STRUCTURE
-- /evanr/
-- -- database.sqlite3
-- -- articles/
-- -- -- article_id.txt
-- -- summaries/
-- -- -- article_id_sum.txt