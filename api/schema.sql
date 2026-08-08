CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS movies;

CREATE TABLE movies (
    id              INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    overview        TEXT NOT NULL,
    genres          TEXT[] NOT NULL DEFAULT '{}',
    year            SMALLINT,
    runtime         SMALLINT,
    vote_average    REAL,
    vote_count      INTEGER,
    embed_text      TEXT NOT NULL,
    embedding       VECTOR(1536) NOT NULL
);

-- Filter support

CREATE INDEX moives_vote_count_idx ON movies (vote_count DESC);
CREATE INDEX movies_year_idx       ON movies (year);