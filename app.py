import os
import psycopg2

from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)


DATABASE_URL = os.environ['DATABASE_URL']

app.debug = False
app.config['SQLALCHEMY_DATABASE_URI'] ='DATABASE_URL'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if not session.get("user_id"):
        return render_template("index.html")
    return render_template("judgehome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("name") or not request.form.get("password"):
            return render_template("login.html")
        result = db.select([judges]).where(judges.c.judge_name == request.form.get("name"))
        if (len(result) != 1) or (request.form.get("password") != judges[0]["pass_hash"]):
            return render_template("login.html")
        session["user_id"] = judges[0]["judge_id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")
