import os

from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)


pg_url = os.environ.get("PG_URL")

app.debug = False
app.config['SQLALCHEMY_DATABASE_URI'] ='{pg_url}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False

db = SQLAlchemy(app)

class Judges(db.Model):
    __tablename__ = 'judges'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    hash = db.Column(db.Text())

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("name"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html")
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")