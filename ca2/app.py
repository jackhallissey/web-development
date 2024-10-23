from flask import Flask, render_template, url_for, session, g, redirect, request
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db
from forms import *

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.teardown_appcontext(close_db)

CHEATS_USED = {"false" : 0, "true" : 1}

@app.before_request
def get_username():
    g.user = session.get("username", None)
    if not g.user and "results" not in session:
        session["results"] = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/attribution")
def attribution():
    return render_template("attribution.html")

def get_stats():
    if g.user:
        db = get_db()
        results = db.execute("SELECT * FROM game_results WHERE user = ? ORDER BY id DESC LIMIT 5", (g.user,)).fetchall()
        stats = db.execute("""SELECT SUM(score), AVG(score), AVG(levels)
                              FROM game_results
                              WHERE cheats = 0 AND user = ?""", (g.user,)).fetchone()
        for stat in stats:
            if stat is None:
                stats = None
                break
    else:
        results = reversed(session["results"][-5:])
        stats = None
    return results, stats

@app.route("/play")
def play():
    results, stats = get_stats()
    return render_template("play.html", results=results, stats=stats)

#Used with XMLHttpRequest
@app.route("/stats")
def stats():
    results, stats = get_stats()
    return render_template("stats.html", results=results, stats=stats)

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
            session["username"] = username
            if session["results"]:
                return redirect( url_for("add_results") )
            else:
                return redirect( url_for("play") )
    return render_template("login.html", form=form)

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
            db.execute("INSERT INTO users VALUES (?, ?);", (username, password))
            db.commit()
            session["username"] = username
            if session["results"]:
                return redirect( url_for("add_results") )
            else:
                return redirect( url_for("play") )
    return render_template("register.html", form=form)

@app.route("/logout")
def logout():
    session["username"] = None
    return redirect( url_for("play") )

@app.route("/add_results", methods=["GET", "POST"])
def add_results():
    if not g.user or not session["results"]:
        return redirect( url_for("play") )
    form = AddResultsForm()
    if form.validate_on_submit():
        if form.choice.data == "Yes":
            for result in session["results"]:
                score = int(result["score"])
                levels = int(result["levels"])
                cheats = int(result["cheats"])

                db = get_db()
                db.execute("""INSERT INTO game_results (user, score, levels, cheats)
                            VALUES (?, ?, ?, ?)""", (g.user, score, levels, cheats))
                db.commit()
        session["results"] = []
        return redirect( url_for("play") )
    
    results = reversed(session["results"])
    return render_template("add_results.html", form=form, results=results)

@app.route("/lb")
def lb():
    db = get_db()
    lb = db.execute("""SELECT user, SUM(score), AVG(score), AVG(levels)
                       FROM game_results
                       WHERE cheats = 0
                       GROUP BY user
                       ORDER BY AVG(score) DESC""").fetchall()
    r = range( len(lb) )
    return render_template("lb.html", lb=lb, r=r)

#Used with XMLHttpRequest
@app.route("/store_result", methods=["POST"])
def store_result():
    result = request.form
    
    if g.user:
        score = int(result["score"])
        levels = int(result["levels"])
        cheats = CHEATS_USED[result["cheats"]]

        db = get_db()
        db.execute("""INSERT INTO game_results (user, score, levels, cheats)
                VALUES (?, ?, ?, ?)""", (g.user, score, levels, cheats))
        db.commit()
    else:
        result = dict(result)
        result["cheats"] = CHEATS_USED[result["cheats"]]
        session["results"].append(result)
    
    return "success"

#Used with XMLHttpRequest
@app.route("/clear_results", methods=["POST"])
def clear_results():
    if g.user:
        db = get_db()
        db.execute("DELETE FROM game_results WHERE user = ?", (g.user,))
        db.commit()
    else:
        session["results"] = []

    return "success"