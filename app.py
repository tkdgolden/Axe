import os
import psycopg2
import psycopg2.extras

from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)

app.debug = True

try:
    SECRET = os.environ["SECRET"]
except:
    SECRET = os.environ["DATABASE_URL"]

print(SECRET)

try:
    conn = psycopg2.connect(SECRET)
except:
    print("Unable to connect to database")

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


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
        cur.execute("""SELECT * FROM judges WHERE judge_name = '%s'""" % user_name)
        rows = cur.fetchall()
        print(rows)
        if (len(rows) != 1) or (request.form.get("password") != rows[0]["pass_hash"]):
            return render_template("login.html")
        session["user_id"] = rows[0]['judge_id']
        session["name"] = rows[0]["judge_name"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    session["user_id"] = None
    return redirect("/")
