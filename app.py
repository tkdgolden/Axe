import os
import psycopg2
import psycopg2.extras
import sys

from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
debug = True
print("initiated the app with a name of:", __name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)

try:
    SECRET = os.environ["SECRET"]
    print("Heroku db access")
except:
    SECRET = os.environ["DATABASE_URL"]
    print("local db access")

try:
    conn = psycopg2.connect(SECRET)
except:
    print("Unable to connect to database")

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return (f(*args, **kwargs))
    return check_login


@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    return render_template("judgehome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        user_name = request.form.get("name")
        if not user_name or not request.form.get("password"):
            return render_template("login.html")
        cur.execute("""SELECT * FROM judges WHERE judge_name = %(user_name)s""", {'user_name': user_name})
        rows = cur.fetchall()
        if (len(rows) != 1) or not check_password_hash(rows[0]["pass_hash"], request.form.get("password")):
            return render_template("login.html")
        session["user_id"] = rows[0]['judge_id']
        session["name"] = rows[0]["judge_name"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session["user_id"] = None
    session["name"] = None
    session["selected_season"] = None
    return redirect("/")

@app.route("/newjudge", methods=["GET", "POST"])
@login_required
def newjudge():
    if request.method == "POST":
        if not request.form.get("name") or not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("newjudge.html")
        name = request.form.get("name")
        pw = request.form.get("password")
        confirm = request.form.get("confirmation")

        cur.execute("""SELECT * FROM judges WHERE judge_name = %(name)s""", {'name': name})
        rows = cur.fetchall()
        if len(rows) > 0:
            return render_template("newjudge.html")
        if pw != confirm:
            return render_template("newjudge.html")
        pwhash = generate_password_hash(pw)
        cur.execute("""INSERT INTO judges(judge_name, pass_hash) VALUES (%(name)s, %(pwhash)s)""", {'name': name, 'pwhash': pwhash})
        conn.commit()
        return redirect("/")
    else:
        return render_template("newjudge.html")


@app.route("/newcompetitor", methods=["GET", "POST"])
@login_required
def newcompetitor():
    if request.method == "POST":
        if not request.form.get("firstname") or not request.form.get("lastname"):
            return render_template("newcompetitor.html")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        cur.execute("""SELECT * FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname': fname, 'lname': lname})
        rows = cur.fetchall()
        if len(rows) > 0:
            return render_template("newcompetitor.html")
        cur.execute("""INSERT INTO competitors (competitor_first_name, competitor_last_name) VALUES (%(fname)s, %(lname)s)""", {'fname': fname, 'lname': lname})
        conn.commit()
        return redirect("/")
    else:
        return render_template("newcompetitor.html")


@app.route("/newseason", methods=["GET", "POST"])
@login_required
def newseason():
    if request.method == "POST":
        if not request.form.get("season") or not request.form.get("year") or not request.form.get("discipline") or not request.form.get("startdate"):
            return render_template("newseason.html")
        season = request.form.get("season")
        yearof = request.form.get("year")
        discipline = request.form.get("discipline")
        startdate = request.form.get("startdate")

        cur.execute("""INSERT INTO seasons (season, yearof, discipline, startdate) VALUES (%(season)s, %(yearof)s, %(discipline)s, %(startdate)s)""", {'season': season, 'yearof': yearof, 'discipline': discipline, 'startdate': startdate})
        conn.commit()
        return redirect("/")
    else:
        return render_template("newseason.html")


@app.route("/seasonview")
@login_required
def seasonview():
    session["selected_season"] = request.form.get("selectedseason")
    if session.get("selected_season") is None:
        return render_template("/")
    else:
        return render_template("seasonview.html")

@app.route("/leaveseason")
@login_required
def leaveseason():
    session["selected_season"] = None
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)