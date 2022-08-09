import os
import psycopg2
import psycopg2.extras

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
            return render_template("login.html", message="Please log in to access.")
        return (f(*args, **kwargs))
    return check_login


def errorpage(message, sendto):
    return render_template("errorpage.html", message=message, sendto=sendto)


@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    cur.execute("""SELECT * FROM seasons""")
    rows = cur.fetchall()
    cur.execute("""SELECT * FROM tournaments""")
    cols = cur.fetchall()
    session["selected_season"] = None
    return render_template("judgehome.html", rows=rows, cols=cols)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        user_name = request.form.get("name")
        if not user_name or not request.form.get("password"):
            return errorpage(message="Please enter a username and password.", sendto="login")
        cur.execute("""SELECT * FROM judges WHERE judge_name = %(user_name)s""", {'user_name': user_name})
        rows = cur.fetchall()
        if (len(rows) != 1) or not check_password_hash(rows[0]["pass_hash"], request.form.get("password")):
            return errorpage(message="The username or password was not found.", sendto="login")
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
            return errorpage(sendto="newjudge", message="Please fill out all fields.")
        name = request.form.get("name")
        pw = request.form.get("password")
        confirm = request.form.get("confirmation")

        cur.execute("""SELECT * FROM judges WHERE judge_name = %(name)s""", {'name': name})
        rows = cur.fetchall()
        if len(rows) > 0:
            return errorpage(sendto="newjudge", message="A judge account with this name already exists.")
        if pw != confirm:
            return errorpage(sendto="newjudge", message="Passwords did not match.")
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
            return errorpage(sendto="newcompetitor", message="Please fill out all fields.")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        cur.execute("""SELECT * FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname': fname, 'lname': lname})
        rows = cur.fetchall()
        if len(rows) > 0:
            return errorpage(sendto="newcompetitor", message="A competitor with this name already exists.")
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
            return errorpage(sendto="newseason", message="Please fill out all fields.")
        season = request.form.get("season")
        yearof = request.form.get("year")
        discipline = request.form.get("discipline")
        startdate = request.form.get("startdate")
        cur.execute("""SELECT season_id FROM seasons WHERE season = %(season)s AND yearof = %(yearof)s AND discipline = %(discipline)s""", {'season': season, 'yearof': yearof, 'discipline':discipline})
        list = cur.fetchall()
        if len(list) > 0:
            return errorpage(sendto="newseason", message="A {season} {yearof} {discipline} season already exists.".format(season=season, yearof=yearof, discipline=discipline))
        cur.execute("""INSERT INTO seasons (season, yearof, discipline, startdate) VALUES (%(season)s, %(yearof)s, %(discipline)s, %(startdate)s)""", {'season': season, 'yearof': yearof, 'discipline': discipline, 'startdate': startdate})
        conn.commit()
        return redirect("/")
    else:
        return render_template("newseason.html")


@app.route("/seasonview")
@login_required
def seasonview():
    if request.args.get("season"):
        sess = request.args.get("season")
        session["selected_season"] = sess
    elif session["selected_season"]:
        sess = session["selected_season"]
    else:
        return errorpage(sendto="/", message="You must select a season.")
    cur.execute("""SELECT * FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
    rows = cur.fetchall()
    if len(rows) != 1:
        return errorpage(sendto="/", message="You must select a valid season.")
    cur.execute("""SELECT competitor_first_name, competitor_last_name FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE season_id = %(sess)s""", {'sess':sess})
    players = cur.fetchall()
    return render_template("seasonview.html", rows=rows, players=players)


@app.route("/newtournament", methods=["GET", "POST"])
@login_required
def newtournament():
    if request.method == "POST":
        if not request.form.get("name") or not request.form.get("discipline") or not request.form.get("date"):
            return errorpage(sendto="newtournament", message="Please fill in all fields.")
        name = request.form.get("name")
        discipline = request.form.get("discipline")
        date = request.form.get("date")

        cur.execute("""INSERT INTO tournaments (tournament_name, discipline, tournament_date) VALUES (%(name)s, %(discipline)s, %(date)s)""", {'name': name, 'discipline': discipline, 'date': date})
        conn.commit()
        return redirect("/")
    else:
        return render_template("newtournament.html")


@app.route("/tournamentview")
@login_required
def tournamentview():
    if request.args.get("tournament"):
        sess = request.args.get("tournament")
        session["selected_season"] = sess
    elif session["selected_season"]:
        sess = session["selected_season"]
    else:
        return errorpage(sendto="/", message="You must select a tournament.")
    cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
    cols = cur.fetchall()
    if len(cols) != 1:
        return errorpage(sendto="/", message="You must select a valid tournament.")
    cur.execute("""SELECT competitor_first_name, competitor_last_name FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE tournament_id = %(sess)s""", {'sess':sess})
    players = cur.fetchall()
    return render_template("tournamentview.html", cols=cols, players=players)


@app.route("/enrollcompetitor", methods=["GET", "POST"])
@login_required
def enrollcompetitor():
    sess = session["selected_season"]
    isseason = False
    cur.execute("""SELECT * FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
    rows = cur.fetchall()
    if len(rows) == 1:
        isseason = True
    if not isseason:
        cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
        cols = cur.fetchall()


    if request.method == "POST":
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")
        cur.execute("""SELECT competitor_id FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname':fname, 'lname':lname})
        comp = cur.fetchall()
        if len(comp) != 1:
            return errorpage(sendto="enrollcompetitor", message="That competitor does not exist.")
        compid = comp[0][0]
        if isseason:
            sid = rows[0]["season_id"]
            cur.execute("""SELECT season_id FROM enrollment WHERE competitor_id = %(compid)s""", {'compid':compid})
            check = cur.fetchall()
            for each in check:
                if sid == each[0]:
                    return errorpage(sendto="enrollcompetitor", message="That competitor is already enrolled in this season.")
            cur.execute("""INSERT INTO enrollment (competitor_id, season_id) VALUES (%(compid)s, %(sid)s)""", {'compid':compid, 'sid':sid})
            conn.commit()
            return redirect("/seasonview")
        else:
            tid = cols[0]["tournament_id"]
            cur.execute("""SELECT tournament_id FROM enrollment WHERE competitor_id = %(compid)s""", {'compid':compid})
            check = cur.fetchall()
            for each in check:
                if tid == each[0]:
                    return errorpage(sendto="enrollcompetitor", message="That competitor is already enrolled in this tournament.")
            cur.execute("""INSERT INTO enrollment (competitor_id, tournament_id) VALUES (%(compid)s, %(tid)s)""", {'compid':compid, 'tid':tid})
            conn.commit()
            return redirect("/tournamentview")

    if isseason:
        result = "{} {} {} season".format(rows[0]['season'], rows[0]['yearof'], rows[0]['discipline'])
    else:
        result = "{} {} tournament on {}".format(cols[0]['tournament_name'], cols[0]['discipline'], cols[0]['tournament_date'])
    return render_template("enrollcompetitor.html", result=result)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)