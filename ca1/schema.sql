-- DROP TABLE IF EXISTS movies;

-- CREATE TABLE movies (
--     id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
--     title TEXT NOT NULL,
--     synopsis TEXT NOT NULL,
--     date TEXT NOT NULL,
--     runtime INTEGER NOT NULL,
--     poster TEXT NOT NULL,
--     poster_src TEXT NOT NULL
-- );

-- INSERT INTO movies (title, synopsis, date, runtime, poster, poster_src)
-- VALUES
-- ("Oppenheimer", "The story of J. Robert Oppenheimer and the creation of the atomic bomb.", "2023-07-21", 180, "oppenheimer.jpg", "Sergi Viladesau on Unsplash"),
-- ("Barbie", "Barbie and Ken leave Barbie Land for the real world.", "2023-07-21", 114, "barbie.jpg", "Elena Mishlanova on Unsplash")
-- ;



-- DROP TABLE IF EXISTS users;

-- CREATE TABLE users (
--     username TEXT NOT NULL PRIMARY KEY,
--     password TEXT NOT NULL,
--     admin INTEGER NOT NULL
-- );



-- DROP TABLE IF EXISTS genres;

-- CREATE TABLE genres (
--     id id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL
-- );

-- INSERT INTO genres (name)
-- VALUES
-- ("Drama"),
-- ("History"),
-- ("Biography"),
-- ("Adventure"),
-- ("Comedy"),
-- ("Fantasy")
-- ;



-- DROP TABLE IF EXISTS movie_genres;

-- CREATE TABLE movie_genres (
--     movie_id INTEGER NOT NULL,
--     genre_id INTEGER NOT NULL,
--     PRIMARY KEY (movie_id, genre_id),
--     FOREIGN KEY (movie_id) REFERENCES movies(id),
--     FOREIGN KEY (genre_id) REFERENCES genres(id)
-- );

-- INSERT INTO movie_genres
-- VALUES
-- (1, 1),
-- (1, 2),
-- (1, 3),
-- (2, 4),
-- (2, 5),
-- (2, 6)
-- ;



-- DROP TABLE IF EXISTS ratings;

-- CREATE TABLE ratings (
--     username TEXT,
--     movie_id INTEGER NOT NULL,
--     score INTEGER,
--     review TEXT,
--     PRIMARY KEY (username, movie_id),
--     FOREIGN KEY (username) REFERENCES users(username),
--     FOREIGN KEY (movie_id) REFERENCES movies(id)
-- );

-- INSERT INTO ratings
-- VALUES
-- ("benny", 1, 5, "It was OK"),
-- ("betty", 1, 10, "Great"),
-- ("benny", 2, 3, "Bad"),
-- ("betty", 2, 7, "Good")
-- ;



-- DROP TABLE IF EXISTS lists;

-- CREATE TABLE lists (
--     id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
--     username TEXT NOT NULL,
--     list_name TEXT NOT NULL,
--     public INTEGER NOT NULL,
--     FOREIGN KEY (username) REFERENCES users(username)
-- );

-- INSERT INTO lists (username, list_name, public)
-- VALUES 
-- ("betty", "Betty's Favourites", 1),
-- ("benny", "Benny's Favourites", 0)
-- ;



-- DROP TABLE IF EXISTS list_items;

-- CREATE TABLE list_items (
--     list_id INTEGER NOT NULL,
--     movie_id INTEGER NOT NULL,
--     PRIMARY KEY (list_id, movie_id),
--     FOREIGN KEY (list_id) REFERENCES lists(id),
--     FOREIGN KEY (movie_id) REFERENCES movies(id)
-- );

-- INSERT INTO list_items
-- VALUES
-- (1, 1),
-- (1, 2),
-- (2, 1)
-- ;