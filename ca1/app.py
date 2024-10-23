#You can login to one of the existing accounts below, or register a new account by clicking the link in the top right

#Accounts

#Username: admin
#Password: jWkd139PF8cI

#The admin account can use the admin tools, which can be accessed from the home page when logged in as an admin, or at "/admin"

#Username: betty
#Password: MqIP3PTv27ou

#Username: benny
#Password: 123

from flask import Flask, render_template, session, g, redirect, url_for, request, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from database import get_db, close_db
from movies import get_movie_info, get_movie_list, get_recommendations
from forms import *
import os

UPLOAD_FOLDER = os.getcwd() + "/static/posters"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.teardown_appcontext(close_db)

@app.before_request
def get_username():
    g.user = session.get("username", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect( url_for("login", next=request.url) )
        return view(*args, **kwargs)
    return wrapped_view

def admin_tools(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (g.user,)).fetchone()
        if user["admin"] == 0:
            return render_template("error.html", error="This page is for administrators only.", title="Admin Only")
        return view(*args, **kwargs)
    return wrapped_view

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", error="Page Not Found", title="Not Found"), 404



## Main Pages

#Shows a welcome message, the top 10 movies, and, if logged in, movie reccommendations for the user
@app.route("/")
def index():
    db = get_db()
    movies = get_movie_list(commands="ORDER BY avg_score DESC LIMIT 5")
    if g.user:
        recs = get_recommendations()
        user = db.execute("SELECT * FROM users WHERE username = ?", (g.user,)).fetchone()
    else:
        recs = None
        user = None
    return render_template("index.html", movies=movies, recs=recs, user=user, title="Home")

#Shows a list of all movies and genres
@app.route("/browse")
def browse():
    db = get_db()
    movies = get_movie_list(commands="ORDER BY date DESC")
    genres = db.execute("SELECT * FROM genres").fetchall()
    return render_template("browse.html", movies=movies, genres=genres, title="Browse Movies")

#Allows the user to search for movies
@app.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    movies = None
    if form.validate_on_submit():
        search = "%" + form.query.data.strip() + "%"
        get_db()
        movies = get_movie_list(where="AND title LIKE ?", values=(search,))
    return render_template("search.html", form=form, movies=movies, title="Search")

#Allows the user to search for movies, with more options
@app.route("/advanced_search", methods=["GET", "POST"])
def advanced_search():
    db = get_db()
    genres = db.execute("SELECT * FROM genres").fetchall()
    form = AdvancedSearchForm()
    form.genre.choices += [(genre["id"], genre["name"]) for genre in genres]
    movies = None
    if form.validate_on_submit():
        #Builds an SQL query based on the options chosen by the user
        search = "%" + form.search_term.data.strip() + "%"
        where = "AND title LIKE ? "
        commands = ""
        values = (search,)
        min_date = form.min_date.data
        max_date = form.max_date.data
        min_score = form.min_score.data
        max_score = form.max_score.data
        genre = form.genre.data
        
        if min_date:
            where += "AND date >= ? "
            values += (min_date,)
        if max_date:
            where += "AND date <= ? "
            values += (max_date,)
        if genre != "":
            where += "AND movies.id IN (SELECT movie_id FROM movie_genres WHERE genre_id = ?) "
            values += (genre,)
        
        if min_score and max_score and min_score < max_score:
            commands += "HAVING avg_score >= ? AND avg_score <= ? "
            values += ( float(min_score), )
            values += ( float(max_score), )
        elif min_score:
            commands += "HAVING avg_score >= ? "
            values += ( float(min_score), )
        elif max_score:
            commands += "HAVING avg_score <= ? "
            values += ( float(max_score), )

        commands += "ORDER BY "
        sort1 = form.sort1.data
        sort1_order = form.sort1_order.data
        sort2 = form.sort2.data
        sort2_order = form.sort2_order.data
        commands += sort1
        if sort1_order == "Descending":
            commands += " DESC"
        if sort2 != "":
            commands += ", " + sort2
            if sort2_order == "Descending":
                commands += " DESC"

        movies = get_movie_list(where=where, commands=commands, values=values)
    return render_template("advanced_search.html", form=form, movies=movies, title="Advanced Search")



## Movies

#Shows information about a certain movie and allows the user to submit a rating/review for it
@app.route("/movie/<movie_id>", methods=["GET", "POST"])
def movie_page(movie_id):
    db = get_db()
    
    form = RatingForm()
    existing_rating = db.execute("SELECT * FROM ratings WHERE username = ? AND movie_id = ?", (g.user, movie_id)).fetchone()
    if form.validate_on_submit():
        score = form.score.data
        review = form.review.data
        if existing_rating is None:
            db.execute("INSERT INTO ratings VALUES (?, ?, ?, ?);", (g.user, movie_id, score, review))
        else:
            db.execute("UPDATE ratings SET score = ?, review = ? WHERE username = ? AND movie_id = ?;", (score, review, g.user, movie_id))
        db.commit()
    elif existing_rating is not None:
        #Autofill the form with the data of the user's existing rating of the movie
        form.score.data = str(existing_rating["score"])
        form.review.data = existing_rating["review"]

    movie = get_movie_info(movie_id)
    if movie is None:
        return render_template("error.html", error="This movie is not in our database.", title="Not Found"), 404

    return render_template("movie_page.html", movie=movie, form=form, title=movie["info"]["title"])

#Removes the user's rating for the movie
@app.route("/remove_rating/<movie_id>", methods=["GET", "POST"])
@login_required
def remove_rating(movie_id):
    form = ConfirmationForm2()
    db = get_db()
    if form.validate_on_submit():
        db.execute("DELETE FROM ratings WHERE username = ? AND movie_id = ?;", (g.user, movie_id))
        db.commit()
        return redirect( url_for("movie_page", movie_id=movie_id) )
    rating = db.execute("SELECT * FROM ratings WHERE username = ? AND movie_id = ?", (g.user, movie_id)).fetchone()
    if rating is None:
        return redirect( url_for("movie_page", movie_id=movie_id) )
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    return render_template("remove_rating.html", movie=movie, rating=rating, form=form, title="Delete Rating")

#Shows a list of movies that are of a certain genre
@app.route("/genre/<genre_id>")
def genre_page(genre_id):
    db = get_db()
    info = db.execute("SELECT * FROM genres WHERE id = ?", (genre_id,)).fetchone()
    if info is None:
        return render_template("error.html", error="This genre does not exist.", title="Not Found"), 404
    page_genre = info["name"]
    movies = get_movie_list(where="AND movies.id IN (SELECT movie_id FROM movie_genres WHERE genre_id = ?)", values=(genre_id,))
    return render_template("genre_page.html", page_genre=page_genre, movies=movies, title=page_genre + " Movies")



## Lists

#Shows information about a list of movies, and allows the user to change its settings if it is their list
@app.route("/list/<list_id>", methods=["GET", "POST"])
def list_page(list_id):
    db = get_db()
    form = ListSettingsForm()
    message = ""
    list = db.execute("SELECT * FROM lists WHERE id = ?", (list_id,)).fetchone()
    if form.validate_on_submit() and g.user == list["username"]:
        name = form.name.data
        visibility = form.visibility.data
        #If a list is private, it will not be shown on the user's page when other users view it, and other users will not be able to see the list
        db.execute("UPDATE lists SET list_name = ?, public = ? WHERE id = ?", (name, visibility, list_id))
        db.commit()
        message = "List updated successfully."
        list = db.execute("SELECT * FROM lists WHERE id = ?", (list_id,)).fetchone()    #Update list information to be shown on page
        
    if list is None:
        return render_template("error.html", error="This list does not exist.", title="Not Found"), 404
    if list["public"] == 0 and g.user != list["username"]:
        return render_template("error.html", error="This list is private.", title="Private")
    form.name.data = list["list_name"]
    form.visibility.data = str(list["public"])
    
    movies = get_movie_list(where="AND movies.id IN (SELECT movie_id FROM list_items WHERE list_id = ?)", values=(list_id,))
    return render_template("/lists/list_page.html", form=form, list=list, movies=movies, message=message, title=list["list_name"])

#Allows the user to create a new list
@app.route("/create_list", methods=["GET", "POST"])
@login_required
def create_list():
    form = ListSettingsForm()
    if form.validate_on_submit():
        name = form.name.data
        visibility = form.visibility.data
        db = get_db()
        db.execute("INSERT INTO lists (username, list_name, public) VALUES (?, ?, ?)", (g.user, name, visibility))
        db.commit()
        return redirect( url_for("user_page", username=g.user) )
    return render_template("/lists/create_list.html", form=form, title="Create A List")

#Allows the user to delete a list
@app.route("/delete_list/<list_id>", methods=["GET", "POST"])
@login_required
def delete_list(list_id):
    db = get_db()
    list = db.execute("SELECT * FROM lists WHERE id = ?", (list_id,)).fetchone()
    if list is None:
        return render_template("error.html", error="This list does not exist.", title="Not Found"), 404
    if list["username"] != g.user:
        return render_template("error.html", error="This list is not associated with your account.", title="Error")
    form = ConfirmationForm2()
    if form.validate_on_submit():
        db.execute("DELETE FROM list_items WHERE list_id = ?", (list_id,))
        db.execute("DELETE FROM lists WHERE id = ?", (list_id,))
        db.commit()
        return redirect( url_for("user_page", username=g.user) )
    return render_template("/lists/delete_list.html", list=list, form=form, title="Delete List")

#Allows the user to add a movie to a list
@app.route("/add_to_list/<movie_id>", methods=["GET", "POST"])
@login_required
def add_to_list(movie_id):
    db = get_db()
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if movie is None:
        return render_template("error.html", error="This movie is not in our database.", title="Not Found"), 404

    lists = db.execute("""
                        SELECT *
                        FROM lists
                        WHERE username = ?
                        AND NOT EXISTS (
                            SELECT *
                            FROM list_items
                            WHERE list_id = lists.id AND username = ? AND movie_id = ?
                        )
                       """, (g.user, g.user, movie_id)).fetchall()
    list_ids = [str(list["id"]) for list in lists]
    form = ListAddForm()
    form.list.choices = [(list["id"], list["list_name"]) for list in lists]
    
    list_id = form.list.data
    if form.validate_on_submit() and list_id in list_ids:     #Ensure list belongs to user
        db.execute("INSERT INTO list_items VALUES (?, ?)", (list_id, movie_id))
        db.commit()
        return redirect( url_for("list_page", list_id=list_id) )
    return render_template("/lists/add_to_list.html", movie=movie, form=form, title="Add to List")

#Allows the user to remove a movie from a list
@app.route("/remove_from_list/<list_id>", methods=["GET", "POST"])
@login_required
def remove_from_list(list_id):
    db = get_db()
    list = db.execute("SELECT * FROM lists WHERE id = ?", (list_id,)).fetchone()
    if list is None:
        return render_template("error.html", error="This list does not exist.", title="Not Found"), 404
    if list["username"] != g.user:
        return render_template("error.html", error="This list is not associated with your account.", title="Error")
    
    form = ListRemoveForm()
    movies = db.execute("SELECT * FROM movies JOIN list_items ON movies.id = list_items.movie_id WHERE list_id = ?", (list_id,)).fetchall()
    form.movie.choices = [(movie["id"], movie["title"] + " (" + movie["date"][0:4] + ")") for movie in movies]      #Title (Year)
    if form.validate_on_submit():
        movie_id = form.movie.data
        db.execute("DELETE FROM list_items WHERE list_id = ? AND movie_id = ?", (list_id, movie_id))
        db.commit()
        return redirect( url_for("list_page", list_id=list_id) )
    return render_template("/lists/remove_from_list.html", list=list, form=form, title="Remove From List")



## User Accounts

#Shows information about the user
@app.route("/user/<username>")
def user_page(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None:
        return render_template("error.html", error="This user does not exist.", title="Not Found"), 404
    lists = db.execute("SELECT * FROM lists WHERE username = ? AND (public = 1 OR username = ?)", (username, g.user)).fetchall()
    ratings = db.execute("""
                            SELECT *
                            FROM ratings JOIN movies
                            ON ratings.movie_id = movies.id
                            WHERE username = ?
                         """, (username,)).fetchall()
    return render_template("user_page.html", username=username, lists=lists, ratings=ratings, title=username)

#Shows the user information about their viewing habits
@app.route("/stats")
@login_required
def stats():
    db = get_db()
    movies = db.execute("""
                        SELECT COUNT(*) as no_movies, SUM(movies.runtime) AS total_time, AVG(ratings.score) AS avg_score
                        FROM movies JOIN ratings
                        ON movies.id = ratings.movie_id
                        WHERE ratings.username = ?
                        """, (g.user,)).fetchone()
    if movies["no_movies"] == 0:
        return render_template("stats_none.html", title="Stats")
    genres = db.execute("""
                        SELECT genres.id, genres.name, COUNT(*) AS no_movies, SUM(movies.runtime) AS total_time, AVG(ratings.score) AS avg_score
                        FROM genres JOIN movie_genres JOIN movies JOIN ratings
                        ON genres.id = movie_genres.genre_id AND movie_genres.movie_id = movies.id AND movie_genres.movie_id = ratings.movie_id
                        WHERE ratings.username = ?
                        GROUP BY genres.id
                        ORDER BY avg_score DESC, genres.id
                        LIMIT 10
                        """, (g.user,)).fetchall()
    return render_template("stats.html", movies=movies, genres=genres, title="Stats")

#Allows the user to create a new account
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        form.username.data = form.username.data.lower()
        username = form.username.data
        db = get_db()
        conflict_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if conflict_user is not None:
            form.username.errors.append("Username is taken.")
        else:
            password = generate_password_hash(form.password.data)
            db.execute("INSERT INTO users VALUES (?, ?, 0);", (username, password))
            list_name = username.capitalize() + "'s Favourites"
            db.execute("INSERT INTO lists (username, list_name, public) VALUES (?, ?, 1)", (username, list_name))
            db.commit()
            session.clear()
            session["username"] = username
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("/accounts/register.html", form=form, title="Register")

#Allows the user to login to their account
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None:
            form.username.errors.append("No such user.")
        elif not check_password_hash(user["password"], password):
            form.password.errors.append("Password is incorrect.")
        else:
            session.clear()
            session["username"] = username
            next_page = request.args.get("next")
            if next_page == "profile":
                return redirect( url_for("user_page", username=username) )
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("/accounts/login.html", form=form, title="Login")

#Logs the user out of their account
@app.route("/logout")
def logout():
    session.clear()
    return redirect( url_for("index") )

#Allows the user to change their password or delete their account
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = ChangePasswordForm()
    message = ""
    if form.validate_on_submit():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (g.user,)).fetchone()
        old_password = form.old_password.data
        if not check_password_hash(user["password"], old_password):
            form.old_password.errors.append("Current password is incorrect.")
        else:
            new_password = generate_password_hash(form.new_password.data)
            db.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, g.user))
            db.commit()
            message = "Password updated successfully."
    return render_template("/accounts/account.html", form=form, message=message, title="My Account")

#Allows the user to delete their account
@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    form = ConfirmationForm1()
    if form.validate_on_submit():
        db = get_db()
        db.execute("DELETE FROM ratings WHERE username = ?", (g.user,))
        db.execute("DELETE FROM list_items WHERE list_id IN (SELECT id FROM lists WHERE username = ?)", (g.user,))
        db.execute("DELETE FROM lists WHERE username = ?", (g.user,))
        db.execute("DELETE FROM users WHERE username = ?", (g.user,))
        db.commit()
        session.clear()
        return redirect( url_for("index") )
    return render_template("/accounts/delete_account.html", form=form, title="Delete Account")



## Admin Tools

#Main page for the admin tools
@app.route("/admin")
@login_required
@admin_tools
def admin():
    return render_template("admin/admin.html", title="Admin Tools")

#Shows a list of all movies, from which the admin can choose one to edit the details of
@app.route("/admin/edit_movie")
@login_required
@admin_tools
def edit_movie_options():
    db = g.db       #"get_db" is already called in "admin_tools"
    movies = db.execute("SELECT * FROM movies").fetchall()
    return render_template("admin/edit_movie_options.html", movies=movies, title="Edit Movie Info")

#Allows the admin to edit the details of a movie
@app.route("/admin/edit_movie/<movie_id>", methods=["GET", "POST"])
@login_required
@admin_tools
def edit_movie(movie_id):
    form = MovieInfoForm()
    form.poster.choices = os.listdir( os.getcwd() + "/static/posters" )
    db = g.db

    if form.validate_on_submit():
        values = (form.title.data, form.synopsis.data, form.date.data, form.runtime.data, form.poster.data, form.poster_src.data, movie_id)
        db.execute("""
                    UPDATE movies
                    SET title = ?, synopsis = ?, date = ?, runtime = ?, poster = ?, poster_src = ?
                    WHERE id = ?
                   """, values)
        db.commit()
        movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
        message = "Movie updated successfully."
    else:
        movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
        if movie is None:
            return render_template("error.html", error="This movie is not in our database.", title="Not Found"), 404
        #Autofill the form with the current details of the movie
        form.title.data = movie["title"]
        form.synopsis.data = movie["synopsis"]
        form.date.data = datetime.strptime(movie["date"], "%Y-%m-%d")
        form.runtime.data = movie["runtime"]
        form.poster.data = movie["poster"]
        form.poster_src.data = movie["poster_src"]
        message = ""

    return render_template("admin/edit_movie.html", form=form, movie=movie, message=message, title="Edit Movie Info")

#Allows the admin to add a new movie
@app.route("/admin/add_movie", methods=["GET", "POST"])
@login_required
@admin_tools
def add_movie():
    form = MovieInfoForm()
    form.poster.choices = os.listdir( os.getcwd() + "/static/posters" )
    if form.validate_on_submit():
        db = g.db
        values = (form.title.data, form.synopsis.data, form.date.data, form.runtime.data, form.poster.data, form.poster_src.data)
        db.execute("""
                    INSERT INTO movies (title, synopsis, date, runtime, poster, poster_src)
                    VALUES
                    (?, ?, ?, ?, ?, ?)
                   """, values)
        id = db.execute("SELECT MAX(id) FROM movies").fetchone()[0]
        db.execute("INSERT INTO ratings VALUES (NULL, ?, NULL, '')", (id,))       #This ensures that the movie will appear in the browse page and in other lists
        db.commit()
        return redirect( url_for("assign_genres", movie_id=id) )        #Redirects to the page for assigning genres to the newly created movie
    return render_template("admin/add_movie.html", form=form, title="Add Movie")

#Shows a list of all movies, from which the admin can choose one to delete
@app.route("/admin/delete_movie")
@login_required
@admin_tools
def delete_movie_options():
    db = g.db
    movies = db.execute("SELECT * FROM movies").fetchall()
    return render_template("admin/delete_movie_options.html", movies=movies, title="Delete Movie")

#Allows the admin to delete a movie from the database
@app.route("/admin/delete_movie/<movie_id>", methods=["GET", "POST"])
@login_required
@admin_tools
def delete_movie(movie_id):
    form = ConfirmationForm1()
    db = g.db
    if form.validate_on_submit():
        db.execute("DELETE FROM list_items where movie_id = ?", (movie_id,))
        db.execute("DELETE FROM movie_genres where movie_id = ?", (movie_id,))
        db.execute("DELETE FROM ratings where movie_id = ?", (movie_id,))
        db.execute("DELETE FROM movies where id = ?", (movie_id,))
        db.commit()
        return redirect( url_for("admin") )
    else:
        movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
        if movie is None:
            return render_template("error.html", error="This movie is not in our database.", title="Not Found"), 404
        return render_template("/admin/delete_movie.html", form=form, movie=movie, title="Delete Movie")

#Allows the admin to add a new genre
@app.route("/admin/add_genre", methods=["GET", "POST"])
@login_required
@admin_tools
def add_genre():
    form = GenreForm()
    message = ""
    if form.validate_on_submit():
        name = form.name.data
        db = g.db
        db.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        db.commit()
        form.name.data = ""
        message = "Genre added successfully."
    return render_template("/admin/add_genre.html", form=form, message=message, title="Add Genre")

#Allows the admin to delete a genre from the database
@app.route("/admin/delete_genre", methods=["GET", "POST"])
@login_required
@admin_tools
def delete_genre():
    db = g.db
    genres = db.execute("SELECT * FROM genres").fetchall()
    form = DeleteGenreForm()
    form.genre.choices += [(genre["id"], genre["name"]) for genre in genres]
    if form.validate_on_submit():
        genre_id = form.genre.data
        db.execute("DELETE FROM movie_genres WHERE genre_id = ?", (genre_id,))
        db.execute("DELETE FROM genres WHERE id =?", (genre_id,))
        db.commit()
        return redirect( url_for("admin") )
    return render_template("/admin/delete_genre.html", form=form, title="Delete Genre")

#Shows a list of all genres, from which the admin can choose one to edit the details of
@app.route("/admin/edit_genre")
@login_required
@admin_tools
def edit_genre_options():
    db = g.db
    genres = db.execute("SELECT * FROM genres").fetchall()
    return render_template("admin/edit_genre_options.html", genres=genres, title="Edit Genre")

#Allows the admin to edit the details of a genre
@app.route("/admin/edit_genre/<genre_id>", methods=["GET", "POST"])
@login_required
@admin_tools
def edit_genre(genre_id):
    db = g.db
    form = GenreForm()
    genre = None
    if form.validate_on_submit():
        name = form.name.data
        db.execute("UPDATE genres SET name = ? WHERE id = ?", (name, genre_id))
        db.commit()
        message = "Genre updated successfully."
    else:
        genre = db.execute("SELECT * FROM genres WHERE id = ?", (genre_id,)).fetchone()
        if genre is None:
            return render_template("error.html", error="This genre does not exist.", title="Not Found"), 404
        form.name.data = genre["name"]
        message = ""
    return render_template("/admin/edit_genre.html", genre=genre, form=form, message=message, title="Edit Genre")

#Shows a list of all movies, from which the admin can choose one to assign genres to
@app.route("/admin/assign_genres")
@login_required
@admin_tools
def assign_genres_options():
    db = g.db
    movies = db.execute("SELECT * FROM movies").fetchall()
    return render_template("admin/assign_genres_options.html", movies=movies, title="Assign Genres")

#Allows the admin to assign genres to a movie
@app.route("/admin/assign_genres/<movie_id>", methods=["GET", "POST"])
@login_required
@admin_tools
def assign_genres(movie_id):
    db = g.db
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if movie is None:
        return render_template("error.html", error="This movie is not in our database.", title="Not Found"), 404
    form = AssignGenresForm()
    message = ""
    genres = db.execute("SELECT * FROM genres").fetchall()
    genre_choices = [(genre["id"], genre["name"]) for genre in genres]
    form.genre1.choices = genre_choices
    form.genre2.choices = genre_choices
    form.genre3.choices = genre_choices

    if form.validate_on_submit():
        if len( set((form.genre1.data, form.genre2.data, form.genre3.data)) ) == 3:     #Checks if the admin picked three distinct genres
            values = (movie_id, form.genre1.data, movie_id, form.genre2.data, movie_id, form.genre3.data)
            db.execute("DELETE FROM movie_genres WHERE movie_id = ?", (movie_id,))
            db.execute("""
                        INSERT INTO movie_genres
                        VALUES
                        (?, ?),
                        (?, ?),
                        (?, ?)
                       """, values)
            db.commit()
            message = "Movie updated successfully."
        else:
            form.genre1.errors.append("The three genres must be distinct.")
    elif len(genre_choices) >= 3:
            #Autofill the form with three distinct genres
            form.genre1.data = str(genre_choices[0][0])
            form.genre2.data = str(genre_choices[1][0])
            form.genre3.data = str(genre_choices[2][0])

    current_genres = db.execute("""
                                SELECT *
                                FROM movie_genres JOIN genres
                                ON movie_genres.genre_id = genres.id
                                WHERE movie_genres.movie_id = ?
                                """, (movie_id,)).fetchall()

    return render_template("admin/assign_genres.html", movie=movie, current_genres=current_genres, genres=genres, message=message, form=form, title="Assign Genres")

#The following two functions were taken from the Flask documentation
#https://flask.palletsprojects.com/en/2.3.x/patterns/fileuploads/
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/admin/upload_poster", methods=["GET", "POST"])
@login_required
@admin_tools
def upload_poster():
    message = ""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            message = "Poster uploaded successfully."
    return render_template("/admin/upload_poster.html", message=message, title="Upload Poster")
