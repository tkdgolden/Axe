from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.debug = False
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://aitqeogodbgmfm:03f15e7e90089ce3fd408a2bceb1fede8257af98d0a7a24819d20305a47b39c0@ec2-3-218-171-44.compute-1.amazonaws.com:5432/dc4jn4js71cvkk'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False

db = SQLAlchemy(app)

@app.route("/")
def index():
    if not session.get("name"):
        return render_template("index.html")
    return render_template("judgehome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("name")
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")