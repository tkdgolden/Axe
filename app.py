# to keep database credentials secure
from distutils.log import error
import os
from sqlite3 import Timestamp
# to connect to postgresql
import psycopg2
# to be able to run sql code in the app
import psycopg2.extras
# flask framework for lots of things that make apps easy
from flask import Flask, render_template, request, session, redirect
# to store session variables
from flask_session import Session
# to hash and unhash judge passwords
from werkzeug.security import check_password_hash, generate_password_hash
# to create my own login_required wrap function
from functools import wraps
# to get today's date
from datetime import date
# to calculate date differences
import datetime


#initiate app
app = Flask(__name__)


# app settings
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)


# find database credentials
try:
    SECRET = os.environ["SECRET"]
    print("Heroku db access")
except:
    SECRET = os.environ["DATABASE_URL"]
    print("local db access")


# connect to database
try:
    conn = psycopg2.connect(SECRET)
except:
    print("Unable to connect to database")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


possible_scores = [0,1,2,3,6]


# function to output error message and send the user back to what they were attempting so they can try again
def errorpage(message, sendto):
    return render_template("errorpage.html", message=message, sendto=sendto)


# check that user is logged in
def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if session.get("user_id") is None:
            return errorpage(sendto="login", message="Please log in to access.")
        return (f(*args, **kwargs))
    return check_login


# index page if not logged in, judgehome if they are
@app.route("/")
def index():
    # clears from any season or tournament being selected
    session["selected_season"] = None

    # not logged in:
    if session.get("user_id") is None:
        return render_template("index.html")

    # logged in:
    # loads seasons and tournaments for dropdowns in judge home page
    # Filter out seasons and tournaments that are finished
    cur.execute("""SELECT * FROM seasons""")
    rows = cur.fetchall()
    today = date.today()
    seasonarchive = []
    for each in rows:
        enddate = each["startdate"] + datetime.timedelta(days=70)
        if (enddate < today):
            seasonarchive.append(each)
    for each in seasonarchive:
        rows.remove(each)
    cur.execute("""SELECT * FROM tournaments""")
    cols = cur.fetchall()
    tournamentarchive = []
    for each in cols:
        enddate = each["tournament_date"]  + datetime.timedelta(days=1)
        if (enddate < today):
            tournamentarchive.append(each)
    for each in tournamentarchive:
        cols.remove(each)

    # sends available season and tournament info to page to be displayed
    return render_template("judgehome.html", rows=rows, cols=cols)


# a login form, validated, variables put in session and / reloaded
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # after form submission
    if request.method == "POST":
        user_name = request.form.get("name")

        # check for blank fields
        if not user_name or not request.form.get("password"):
            return errorpage(message="Please enter a username and password.", sendto="login")
        
        # pull judge accounts from database
        cur.execute("""SELECT * FROM judges WHERE judge_name = %(user_name)s""", {'user_name': user_name})
        rows = cur.fetchall()

        # check if the judge doesnt exist, or the given password doesnt hash
        if (len(rows) != 1) or not check_password_hash(rows[0]["pass_hash"], request.form.get("password")):
            return errorpage(message="The username or password was not found.", sendto="login")

        # save judge info in session
        session["user_id"] = rows[0]['judge_id']
        session["name"] = rows[0]["judge_name"]
        return redirect("/")

    # the form:
    return render_template("login.html")


# clears session variables, reloads /
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


# validates form to create a new judge
@app.route("/newjudge", methods=["GET", "POST"])
@login_required
def newjudge():

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("name") or not request.form.get("password") or not request.form.get("confirmation"):
            return errorpage(sendto="newjudge", message="Please fill out all fields.")
        name = request.form.get("name")
        pw = request.form.get("password")
        confirm = request.form.get("confirmation")

        # check for that judge already existing
        cur.execute("""SELECT * FROM judges WHERE judge_name = %(name)s""", {'name': name})
        rows = cur.fetchall()
        if len(rows) > 0:
            return errorpage(sendto="newjudge", message="A judge account with this name already exists.")

        # check they entered the password twice the same
        if pw != confirm:
            return errorpage(sendto="newjudge", message="Passwords did not match.")

        # generate and store password hash
        pwhash = generate_password_hash(pw)
        cur.execute("""INSERT INTO judges(judge_name, pass_hash) VALUES (%(name)s, %(pwhash)s)""", {'name': name, 'pwhash': pwhash})
        conn.commit()
        return redirect("/")

    # the form:
    else:
        return render_template("newjudge.html")


# validates form to create a new competitor
@app.route("/newcompetitor", methods=["GET", "POST"])
@login_required
def newcompetitor():

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("firstname") or not request.form.get("lastname"):
            return errorpage(sendto="newcompetitor", message="Please fill out all fields.")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        # check if that competitor already exists
        cur.execute("""SELECT * FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname': fname, 'lname': lname})
        rows = cur.fetchall()
        if len(rows) > 0:
            return errorpage(sendto="newcompetitor", message="A competitor with this name already exists.")

        # add competitor to database
        cur.execute("""INSERT INTO competitors (competitor_first_name, competitor_last_name) VALUES (%(fname)s, %(lname)s)""", {'fname': fname, 'lname': lname})
        conn.commit()
        return redirect("/")
    
    # the form:
    else:
        return render_template("newcompetitor.html")


# form and validation to create a new season
@app.route("/newseason", methods=["GET", "POST"])
@login_required
def newseason():

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("season") or not request.form.get("year") or not request.form.get("discipline") or not request.form.get("startdate"):
            return errorpage(sendto="newseason", message="Please fill out all fields.")
        season = request.form.get("season")
        yearof = request.form.get("year")
        discipline = request.form.get("discipline")
        startdate = request.form.get("startdate")

        # check that the season doesnt exist already
        cur.execute("""SELECT season_id FROM seasons WHERE season = %(season)s AND yearof = %(yearof)s AND discipline = %(discipline)s""", {'season': season, 'yearof': yearof, 'discipline':discipline})
        list = cur.fetchall()
        if len(list) > 0:
            return errorpage(sendto="newseason", message="A {season} {yearof} {discipline} season already exists.".format(season=season, yearof=yearof, discipline=discipline))
        
        # put the season in the database
        cur.execute("""INSERT INTO seasons (season, yearof, discipline, startdate) VALUES (%(season)s, %(yearof)s, %(discipline)s, %(startdate)s)""", {'season': season, 'yearof': yearof, 'discipline': discipline, 'startdate': startdate})
        conn.commit()
        return redirect("/")

    # the form:
    else:
        return render_template("newseason.html")


# will show one selected season and links to enroll players, judge matches, all enrolled players, and recent matches
# TODO suggested matches, create a match from player name button, recent matches
@app.route("/seasonview")
@login_required
def seasonview():

    session["array_competitor_ids"] = None

    # get the selected season to be displayed
    if request.args.get("season"):
        sess = request.args.get("season")
        session["selected_season"] = sess
    elif session["selected_season"]:
        sess = session["selected_season"]
    else:
        return errorpage(sendto="/", message="You must select a season.")

    # get that season's info from database
    cur.execute("""SELECT * FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
    rows = cur.fetchall()
    if len(rows) != 1:
        return errorpage(sendto="/", message="You must select a valid season.")

    # get competitor info from database
    cur.execute("""SELECT * FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE season_id = %(sess)s""", {'sess':sess})
    players = cur.fetchall()

    cur.execute("""SELECT * FROM matches WHERE season_id = %(sess)s""", {'sess':sess})
    logged_matches = cur.fetchall()

    print(logged_matches)
    # send that info on to the page to be displayed
    return render_template("seasonview.html", rows=rows, players=players, logged_matches=logged_matches)


# form and validation for scoring a match
@app.route("/scorematch", methods=["GET", "POST"])
@login_required
def scorematch():

    # after form submission
    if request.method == "POST":

        # check all required fields were submitted
        if not request.form.get("p1t1") or not request.form.get("p2t1") or not request.form.get("p1t2") or not request.form.get("p2t2") or not request.form.get("p1t3") or not request.form.get("p2t3") or not request.form.get("p1t4") or not request.form.get("p2t4") or not request.form.get("p1t5") or not request.form.get("p2t5") or not request.form.get("p1t6") or not request.form.get("p2t6") or not request.form.get("p1t7") or not request.form.get("p2t7") or not request.form.get("p1t8") or not request.form.get("p2t8") or not request.form.get("sequence"):
            return errorpage(sendto="scorematch", message="THE APOCALYPSE, your match was submitted incompletely, and therefore wasn't saved.")
        
        # current timestamp
        ts = datetime.datetime.now()
        
        # record the randomly generated sequence
        sequence = request.form.get("sequence")

        # take form inputs and save them as integers with names that ironically cant have integers or it messes with the postgresql command
        # the try except handles drop and fault scores
        try:
            pAtone = int(request.form.get("p1t1"))
        except ValueError:
            pAtone = 0
        try:
            pBtone = int(request.form.get("p2t1"))
        except ValueError:
            pBtone = 0
        try:
            pAttwo = int(request.form.get("p1t2"))
        except ValueError:
            pAttwo = 0
        try:
            pBttwo = int(request.form.get("p2t2"))
        except ValueError:
            pBttwo = 0
        try:
            pAtthree = int(request.form.get("p1t3"))
        except ValueError:
            pAtthree = 0
        try:
            pBtthree = int(request.form.get("p2t3"))
        except ValueError:
            pBtthree = 0
        try:
            pAtfour = int(request.form.get("p1t4"))
        except ValueError:
            pAtfour = 0
        try:
            pBtfour = int(request.form.get("p2t4"))
        except ValueError:
            pBtfour = 0
        try:
            pAtfive = int(request.form.get("p1t5"))
        except ValueError:
            pAtfive = 0
        try:
            pBtfive = int(request.form.get("p2t5"))
        except ValueError:
            pBtfive = 0
        try:
            pAtsix = int(request.form.get("p1t6"))
        except ValueError:
            pAtsix = 0
        try:
            pBtsix = int(request.form.get("p2t6"))
        except ValueError:
            pBtsix = 0
        try:
            pAtseven = int(request.form.get("p1t7"))
        except ValueError:
            pAtseven = 0
        try:
            pBtseven = int(request.form.get("p2t7"))
        except ValueError:
            pBtseven = 0
        try:
            pAteight = int(request.form.get("p1t8"))
        except ValueError:
            pAteight = 0
        try:
            pBteight = int(request.form.get("p2t8"))
        except ValueError:
            pBteight = 0

        # store all quickthrow points
        q1 = request.form.get("q1")
        q2 = request.form.get("q2")
        q3 = request.form.get("q3")
        q4 = request.form.get("q4")
        q5 = request.form.get("q5")
        q6 = request.form.get("q6")
        q7 = request.form.get("q7")
        q8 = request.form.get("q8")

        # iterate through the quicktrow points to count the points per player
        qs = [q1, q2, q3, q4, q5, q6, q7, q8]
        pAqt = 0;
        pBqt = 0;
        for each in qs:
            if each == "p1":
                pAqt += 1
            elif each == "p2":
                pBqt += 1

        # iterate through all the throw scores to make sure nobody hacked the html
        allscores = [pAtone, pAttwo, pAtthree, pAtfour, pAtfive, pAtsix, pAtseven, pAteight, pBtone, pBttwo, pBtthree, pBtfour, pBtfive, pBtsix, pBtseven, pBteight]
        for each in allscores:
            if each not in possible_scores:
                return errorpage(message="someone tried to hack your form.", sendto="seasonview")

        # sum each players score
        pAtotal = pAtone + pAttwo + pAtthree + pAtfour + pAtfive + pAtsix + pAtseven + pAteight + pAqt
        pBtotal = pBtone + pBttwo + pBtthree + pBtfour + pBtfive + pBtsix + pBtseven + pBteight + pBqt

        # compare scores and record winner ids
        winner = ""
        if pAtotal > pBtotal:
            winner = session["array_competitor_ids"][0]
        elif pAtotal < pBtotal:
            winner = session["array_competitor_ids"][1]
        else:
            if not request.form.get("winner"):
                return errorpage(message="No Tiebreaker selected, scores NOT recoreded.", sendto="seasonview")
            winner = request.form.get("winner")

        # get player ids
        playerA = session["array_competitor_ids"][0]
        playerB = session["array_competitor_ids"][1]

        # determine win boolean for each player
        if winner == playerA:
            pAwin = True
            pBwin = False
        else:
            pBwin = True
            pAwin = False

        # get session values to be stored
        sess = session["selected_season"]
        judge = session["user_id"]

        # get season, tournament, and discipline values from database
        cur.execute("""SELECT tournament_id, discipline FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
        cols = cur.fetchall()
        if len(cols) == 0:
            t = None
            s = sess
            cur.execute("""SELECT discipline FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
            dis = cur.fetchall()
            discipline = dis[0]["discipline"]
        else:
            t = sess
            s = None
            discipline = cols[0]["discipline"]

        # three database inserts: one to matches, and one for each player into scores
        try:

            # insert into matches, returns primary key match id for use in scores inserts
            cur.execute("""INSERT INTO matches (player_1_id, player_2_id, season_id, tournament_id, winner_id, player1total, player2total, discipline, judge_id, dt) VALUES (%(playerA)s, %(playerB)s, %(s)s, %(t)s, %(winner)s, %(pAtotal)s, %(pBtotal)s, %(discipline)s, %(judge)s, %(ts)s) RETURNING match_id""", {'playerA': playerA, 'playerB': playerB, 's': s, 't': t, 'winner': winner, 'pAtotal': pAtotal, 'pBtotal': pBtotal, 'discipline': discipline, 'judge': judge, 'ts': ts})
            m = cur.fetchall()
            conn.commit()
            mid = m[0][0]

            # inserts into scores for each player
            cur.execute("""INSERT INTO scores (competitor_id, match_id, quick_points, seq, throw1, throw2, throw3, throw4, throw5, throw6, throw7, throw8, total, won) VALUES (%(playerA)s, %(mid)s, %(pAqt)s, %(sequence)s, %(pAtone)s, %(pAttwo)s, %(pAtthree)s, %(pAtfour)s, %(pAtfive)s, %(pAtsix)s, %(pAtseven)s, %(pAteight)s, %(pAtotal)s, %(pAwin)s)""", {'playerA': playerA, 'mid': mid, 'pAqt': pAqt, 'sequence': sequence, 'pAtone': pAtone, 'pAttwo': pAttwo, 'pAtthree': pAtthree, 'pAtfour': pAtfour, 'pAtfive': pAtfive, 'pAtsix': pAtsix, 'pAtseven': pAtseven, 'pAteight': pAteight, 'pAtotal': pAtotal, 'pAwin': pAwin})
            conn.commit()
            cur.execute("""INSERT INTO scores (competitor_id, match_id, quick_points, seq, throw1, throw2, throw3, throw4, throw5, throw6, throw7, throw8, total, won) VALUES (%(playerB)s, %(mid)s, %(pBqt)s, %(sequence)s, %(pBtone)s, %(pBttwo)s, %(pBtthree)s, %(pBtfour)s, %(pBtfive)s, %(pBtsix)s, %(pBtseven)s, %(pBteight)s, %(pBtotal)s, %(pBwin)s)""", {'playerB': playerB, 'mid': mid, 'pBqt': pBqt, 'sequence': sequence, 'pBtone': pBtone, 'pBttwo': pBttwo, 'pBtthree': pBtthree, 'pBtfour': pBtfour, 'pBtfive': pBtfive, 'pBtsix': pBtsix, 'pBtseven': pBtseven, 'pBteight': pBteight, 'pBtotal': pBtotal, 'pBwin': pBwin})
            conn.commit()
        
        # error if the inserts fail
        except:
            return errorpage(message="DATABASE INSERT FAILED, SCORES NOT RECORDED", sendto="seasonview")

        # clear the selected competitors from session
        session["array_competitor_ids"] = None

        # redirect to current season
        return redirect("seasonview")

    # the form:
    else:

        # take the selected competitors from season view or tournament view page
        session["array_competitor_ids"] = request.args.getlist("competitor_selection")
        
        # make an array with those competitors and their information from competitor database table
        array_competitors = []
        for each in session["array_competitor_ids"]:
            cur.execute("""SELECT * FROM competitors WHERE competitor_id = %(each)s""", {'each':each})
            array_competitors.append(cur.fetchall())

        # send competitor info to scorematch form
        return render_template("scorematch.html", array_competitors=array_competitors, possible_scores=possible_scores)


# form and validation for creating a new tournament
@app.route("/newtournament", methods=["GET", "POST"])
@login_required
def newtournament():

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("name") or not request.form.get("discipline") or not request.form.get("date"):
            return errorpage(sendto="newtournament", message="Please fill in all fields.")
        name = request.form.get("name")
        discipline = request.form.get("discipline")
        date = request.form.get("date")

        # check that the tournament doesnt exist already
        cur.execute("""SELECT tournament_id FROM tournaments WHERE tournament_name = %(name)s AND discipline = %(discipline)s AND tournament_date = %(date)s""", {'name': name, 'discipline': discipline, 'date': date})
        list = cur.fetchall()
        if len(list) > 0:
            return errorpage(sendto="newtournament", message="A {name} {discipline} tournament on {date} already exists.".format(name=name, discipline=discipline, date=date))
        
        # put the new tournament into the database
        cur.execute("""INSERT INTO tournaments (tournament_name, discipline, tournament_date) VALUES (%(name)s, %(discipline)s, %(date)s)""", {'name': name, 'discipline': discipline, 'date': date})
        conn.commit()
        return redirect("/")

    # the form:
    else:
        return render_template("newtournament.html")


# will show a link to add players, all players, recent matches, and create a match
# TODO suggested matches, create a match from player name button, recent matches
@app.route("/tournamentview")
@login_required
def tournamentview():

    session["array_competitor_ids"] = None

    # find the selected tournament
    if request.args.get("tournament"):
        sess = request.args.get("tournament")
        session["selected_season"] = sess
    elif session["selected_season"]:
        sess = session["selected_season"]
    else:
        return errorpage(sendto="/", message="You must select a tournament.")

    # get the tournament info from database
    cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
    cols = cur.fetchall()
    if len(cols) != 1:
        return errorpage(sendto="/", message="You must select a valid tournament.")

    # get competitor info from database
    cur.execute("""SELECT competitor_first_name, competitor_last_name FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE tournament_id = %(sess)s""", {'sess':sess})
    players = cur.fetchall()

    # send info to page to be displayed
    return render_template("tournamentview.html", cols=cols, players=players)


# form and validation for adding an already existing player to an already existing season or tournament
@app.route("/enrollcompetitor", methods=["GET", "POST"])
@login_required
def enrollcompetitor():

    # determine if a season or tournament is selected
    sess = session["selected_season"]
    isseason = False
    cur.execute("""SELECT * FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
    rows = cur.fetchall()
    returnlink = None
    if len(rows) == 1:
        isseason = True
        returnlink = "seasonview"
    if not isseason:
        cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
        cols = cur.fetchall()
        returnlink = "tournamentview"

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("firstname") or not request.form.get("lastname"):
            return errorpage(sendto="enrollcompetitor", message="Please fill out all fields.")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        # check if the competitor exists
        cur.execute("""SELECT competitor_id FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname':fname, 'lname':lname})
        comp = cur.fetchall()
        if len(comp) != 1:
            return errorpage(sendto="enrollcompetitor", message="That competitor does not exist.")

        # check if the competitor is already enrolled in the selected season or tournament
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

    # sending data to the form page
    if isseason:
        result = "{} {} {} season".format(rows[0]['season'], rows[0]['yearof'], rows[0]['discipline'])
    else:
        result = "{} {} tournament on {}".format(cols[0]['tournament_name'], cols[0]['discipline'], cols[0]['tournament_date'])

    # the form:
    return render_template("enrollcompetitor.html", result=result, returnlink=returnlink)


# archive page to access expired seasons and tournaments
@app.route("/archive")
@login_required
def archive():

    # loads archived seasons and tournaments
    cur.execute("""SELECT * FROM seasons""")
    rows = cur.fetchall()
    today = date.today()
    seasonarchive = []
    for each in rows:
        enddate = each["startdate"] + datetime.timedelta(days=70)
        if (enddate < today):
            seasonarchive.append(each)
    cur.execute("""SELECT * FROM tournaments""")
    cols = cur.fetchall()
    tournamentarchive = []
    for each in cols:
        enddate = each["tournament_date"] + datetime.timedelta(days=1)
        if (enddate < today):
            tournamentarchive.append(each)

     # sends available season and tournament info to page to be displayed
    return render_template("archive.html", seasonarchive=seasonarchive, tournamentarchive=tournamentarchive)

