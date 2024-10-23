#These functions are called in app.py. They build SQL queries from the parameters given, execute them, and return the results

from flask import g
from datetime import datetime

def get_movie_info(id):
    movie = {}
    db = g.db

    movie["info"] = db.execute("SELECT * FROM movies WHERE id = ?", (id,)).fetchone()
    if movie["info"] is None:
        return None

    movie["score"] = db.execute("SELECT AVG(score) FROM ratings WHERE movie_id = ?", (id,)).fetchone()[0]
    movie["genres"] = db.execute("""
                                    SELECT *
                                    FROM movie_genres JOIN genres
                                    ON movie_genres.genre_id = genres.id
                                    WHERE movie_genres.movie_id = ?
                                   """, (id,)).fetchall()
    movie["ratings"] = db.execute("""
                                    SELECT * FROM ratings
                                    WHERE movie_id = ? AND username IS NOT NULL
                                    ORDER BY
                                        CASE
                                            WHEN username = ? THEN 1
                                            ELSE 2
                                        END
                                    """, (id, g.user)).fetchall()
                                    #'ORDER BY' adapted from the following page: https://stackoverflow.com/questions/18725941/mysql-order-by-best-match
    
    date = movie["info"]["date"]
    movie["date"] = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y').lstrip("0")
    #Adapted from the following page: https://stackoverflow.com/questions/14524322/how-to-convert-a-date-string-to-different-format

    runtime = movie["info"]["runtime"]
    movie["runtime"] = str(runtime // 60) + "h"
    if runtime % 60 != 0:
        movie["runtime"] += " " + str(runtime % 60) + "m"

    if g.user:
        movie["lists"] = db.execute("""
                                        SELECT lists.id, lists.list_name
                                        FROM lists JOIN list_items
                                        ON lists.id = list_items.list_id
                                        WHERE
                                            lists.username = ? AND
                                            list_items.movie_id = ?
                                      """, (g.user, id)).fetchall()

    return movie



def get_movie_list(**kwargs):
    query = """SELECT
    movies.*,
    AVG(ratings.score) AS avg_score,
    g1.*,
    g2.*,
    g3.*
FROM
    movies JOIN
    ratings JOIN
    movie_genres AS mg1 JOIN
    genres AS g1 JOIN
    movie_genres AS mg2 JOIN
    genres AS g2 JOIN
    movie_genres AS mg3 JOIN
    genres AS g3
ON
    movies.id = ratings.movie_id AND
    movies.id = mg1.movie_id AND
    movies.id = mg2.movie_id AND
    movies.id = mg3.movie_id AND
    g1.id = mg1.genre_id AND
    g2.id = mg2.genre_id AND
    g3.id = mg3.genre_id
WHERE
    g1.id < g2.id AND
    g2.id < g3.id"""

    if "where" in kwargs:
        query += " " + kwargs["where"]

    query += " GROUP BY movies.id"

    if "commands" in kwargs:
        query += " " + kwargs["commands"]

    db = g.db
    if "values" in kwargs:
        results = db.execute(query, kwargs["values"]).fetchall()
    else:
        results = db.execute(query).fetchall()

    return results

def get_recommendations():
    recs_query = """AND
        movies.id IN (
            SELECT DISTINCT m.id
            FROM movies AS m JOIN movie_genres
            ON m.id = movie_genres.movie_id
            WHERE
                movie_genres.genre_id IN (
                    SELECT movie_genres.genre_id
                    FROM movie_genres JOIN ratings
                    ON movie_genres.movie_id = ratings.movie_id
                    WHERE ratings.username = ?
                    GROUP BY movie_genres.genre_id
                    HAVING AVG(ratings.score) >= 5.0
                    ORDER BY AVG(ratings.score) DESC
                    LIMIT 5
                ) AND
                NOT EXISTS (
                    SELECT *
                    FROM ratings
                    WHERE movie_id = m.id AND username = ?
                )
            LIMIT 5
        )
    """

    return get_movie_list(where=recs_query, values=(g.user, g.user))