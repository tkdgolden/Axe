# to keep database credentials secure
from distutils.log import error
import os
# to connect to postgresql
import psycopg2
# to be able to run sql code in the app
import psycopg2.extras
# flask framework for lots of things that make apps easy
from flask import Flask, render_template, request, session, redirect, jsonify
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

import json




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


possible_scores = [0,1,2,3,4,6,12]

# when compared against a sorted list of players, it sets the matches so that players are seeded correctly
bracket_A_seed_order = [0,1]
bracket_B_seed_order = [0,3,1,2]
bracket_C_seed_order = [0,7,3,4,2,5,1,6]
bracket_D_seed_order = [0,15,7,8,3,12,4,11,1,14,6,9,2,13,5,10]
bracket_E_seed_order = [0,31,15,16,8,23,7,24,3,28,12,19,11,20,4,27,1,30,14,17,9,22,6,25,2,29,13,18,10,21,5,26]
bracket_F_seed_order = [0,63,31,32,16,47,15,48,8,55,23,40,24,39,7,56,3,60,28,35,19,44,12,51,11,52,20,43,27,36,4,59,1,62,30,33,17,46,14,49,9,54,22,41,25,38,6,57,2,61,29,34,18,45,13,50,10,53,21,42,26,37,5,58]

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
    session["selected_tournament"] = None

    # not logged in:
    if session.get("user_id") is None:
        player_list = render_player_stats()

        cur.execute("""SELECT * FROM seasons""")
        rows = cur.fetchall()

        cur.execute("""SELECT * FROM tournaments""")
        cols = cur.fetchall()

        return render_template("index.html", player_list=player_list, rows=rows, cols=cols)

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
    session["selected_tournament"] = None

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

    # clear session values
    session["array_competitor_ids"] = None
    session["selected_tournament"] = None

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

    # TODO display completed matches
    cur.execute("""SELECT * FROM matches WHERE season_id = %(sess)s""", {'sess':sess})
    logged_matches = cur.fetchall()

    # send that info on to the page to be displayed
    return render_template("seasonview.html", rows=rows, players=players, logged_matches=logged_matches)


# create match used only from seasons, in tournaments matches are created when the round is created
@app.route("/creatematch")
@login_required
def creatematch():

    # make sure there is a valid season selected
    if session["selected_season"]:
        session["array_competitor_ids"] = request.args.getlist("competitor_selection")
    else:
        return errorpage(sendto="/", message="Create match is only for seasons.")
        
    # make an array with those competitors and their information from competitor database table
    array_competitors = []
    for each in session["array_competitor_ids"]:
        cur.execute("""SELECT * FROM competitors WHERE competitor_id = %(each)s""", {'each':each})
        array_competitors.append(cur.fetchall()[0])

    # get player ids
    playerA = session["array_competitor_ids"][0]
    playerB = session["array_competitor_ids"][1]

    # get session values to be stored
    sess = session["selected_season"]

    # insert into matches, returns primary key match id for use in scores inserts
    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, season_id) VALUES (%(playerA)s, %(playerB)s, %(sess)s) RETURNING match_id""", {'playerA': playerA, 'playerB': playerB, 'sess': sess})
    match = cur.fetchall()
    conn.commit()
    session["match_id"] = match[0][0]

    # send competitor info to scorematch form
    return render_template("scorematch.html", array_competitors=array_competitors, possible_scores=possible_scores)




# form and validation for scoring a match
@app.route("/scorematch", methods=["POST"])
@login_required
def scorematch():

    # after form submission
    if request.method == "POST":

        match_id = session["match_id"]
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
            if winner == session["array_competitor_ids"][0]:
                pAtotal += 1
            elif winner == session["array_competitor_ids"][1]:
                pBtotal += 1

        # get player ids
        playerA = session["array_competitor_ids"][0]
        playerB = session["array_competitor_ids"][1]

        # determine win boolean for each player
        if winner == session["array_competitor_ids"][0]:
            pAwin = True
            pBwin = False
        else:
            pBwin = True
            pAwin = False

        # determine season or tournament, get discipline values
        if session["selected_season"]:
            sess = session["selected_season"]
            cur.execute("""SELECT discipline FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
            cols = cur.fetchall()
            view = 'season'
        else:
            sess = session["selected_tournament"]
            cur.execute("""SELECT discipline FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
            cols = cur.fetchall()
            view = 'tournament'
        judge = session["user_id"]
        discipline = cols[0]

        # three database inserts: one to matches, and one for each player into scores
        try:
            # insert into matches, returns primary key match id for use in scores inserts
            cur.execute("""UPDATE matches SET winner_id = %(winner)s, player1total = %(pAtotal)s, player2total = %(pBtotal)s, discipline = %(discipline)s, judge_id = %(judge)s, dt = %(ts)s WHERE match_id = %(match_id)s""", {'winner': winner, 'pAtotal': pAtotal, 'pBtotal': pBtotal, 'discipline': discipline, 'judge': judge, 'ts': ts, 'match_id': match_id})
            conn.commit()


            # inserts into scores for each player
            cur.execute("""INSERT INTO scores (competitor_id, match_id, quick_points, seq, throw1, throw2, throw3, throw4, throw5, throw6, throw7, throw8, total, won) VALUES (%(playerA)s, %(match_id)s, %(pAqt)s, %(sequence)s, %(pAtone)s, %(pAttwo)s, %(pAtthree)s, %(pAtfour)s, %(pAtfive)s, %(pAtsix)s, %(pAtseven)s, %(pAteight)s, %(pAtotal)s, %(pAwin)s)""", {'playerA': playerA, 'match_id': match_id, 'pAqt': pAqt, 'sequence': sequence, 'pAtone': pAtone, 'pAttwo': pAttwo, 'pAtthree': pAtthree, 'pAtfour': pAtfour, 'pAtfive': pAtfive, 'pAtsix': pAtsix, 'pAtseven': pAtseven, 'pAteight': pAteight, 'pAtotal': pAtotal, 'pAwin': pAwin})
            conn.commit()


            cur.execute("""INSERT INTO scores (competitor_id, match_id, quick_points, seq, throw1, throw2, throw3, throw4, throw5, throw6, throw7, throw8, total, won) VALUES (%(playerB)s, %(match_id)s, %(pBqt)s, %(sequence)s, %(pBtone)s, %(pBttwo)s, %(pBtthree)s, %(pBtfour)s, %(pBtfive)s, %(pBtsix)s, %(pBtseven)s, %(pBteight)s, %(pBtotal)s, %(pBwin)s)""", {'playerB': playerB, 'match_id': match_id, 'pBqt': pBqt, 'sequence': sequence, 'pBtone': pBtone, 'pBttwo': pBttwo, 'pBtthree': pBtthree, 'pBtfour': pBtfour, 'pBtfive': pBtfive, 'pBtsix': pBtsix, 'pBtseven': pBtseven, 'pBteight': pBteight, 'pBtotal': pBtotal, 'pBwin': pBwin})
            conn.commit()

        
        # error if the inserts fail
        except:
            return errorpage(message="DATABASE INSERT FAILED, SCORES NOT RECORDED", sendto="seasonview")

        # clear the selected competitors from session
        session["array_competitor_ids"] = None

        # redirect to current season/ tournament
        if (view == 'season'):
            return redirect("seasonview")
        elif (view == 'tournament'):
            return redirect("tournamentview")




# form and validation for creating a new tournament
@app.route("/newtournament", methods=["GET", "POST"])
@login_required
def newtournament():
    session["selected_season"] = None

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("name") or not request.form.get("discipline") or not request.form.get("date") or not request.form.get("double_elimination"):
            return errorpage(sendto="newtournament", message="Please fill in all fields.")
        name = request.form.get("name")
        discipline = request.form.get("discipline")
        date = request.form.get("date")
        double_elimination = request.form.get("double_eliminaiton")

        # check that the tournament doesnt exist already
        cur.execute("""SELECT tournament_id FROM tournaments WHERE tournament_name = %(name)s AND discipline = %(discipline)s AND tournament_date = %(date)s""", {'name': name, 'discipline': discipline, 'date': date})
        list = cur.fetchall()
        if len(list) > 0:
            return errorpage(sendto="newtournament", message="A {name} {discipline} tournament on {date} already exists.".format(name=name, discipline=discipline, date=date))
        
        # put the new tournament into the database
        cur.execute("""INSERT INTO tournaments (tournament_name, discipline, tournament_date, double_elimination) VALUES (%(name)s, %(discipline)s, %(date)s, %(double_elimination)s)""", {'name': name, 'discipline': discipline, 'date': date, 'double_elimination': double_elimination})
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
    session["selected_season"] = None

    # get the selected tournament to be displayed
    if request.args.get("tournament"):
        sess = request.args.get("tournament")
        session["selected_tournament"] = sess
    elif session["selected_tournament"]:
        sess = session["selected_tournament"]
    else:
        return errorpage(sendto="/", message="You must select a tournament.")

    # calls refreshtournament function
    results = refreshtournament()
    players = results[0]

    # cols is tournament info
    cols = results[1][0]
    match_info = []
    player_info = []

    # if there is a round started
    if (results[2]):
        round_info = results[2][0]

        # counting the number of matches
        count = 0

        # for each competitor in the bye competitors list
        for each in round_info[1]:

            # if it is a real competitor and not a placeholder for a bye
            if each != 0:

                # add the word bye to be read by the javascript
                match_info.append("bye")

                # add the player info
                for x in players:
                    if x[0] == each:
                        player_id = x[0]
                        player_first_name = x[1]
                        player_last_name = x[2]
                        player_info = [player_id, player_first_name, player_last_name]
                match_info.append(player_info)
            
            # if there is no bye (0), there must be a match
            else:
                # get the match id
                match = round_info[2][count]

                # get the match info
                cur.execute("""SELECT player_1_id, player_2_id, winner_id FROM matches WHERE match_id = %(match)s""", {'match': match})
                two_competitors = cur.fetchall()[0]
                
                # if the round has no winner
                if two_competitors[2] == None:

                    # add the word match to be read by the javascript
                    match_count = ["match", match]
                    match_info.append(match_count)

                    # add each competitor info
                    iteration = 0
                    while iteration < 2:
                        competitor = two_competitors[iteration]
                        for x in players:
                            if x[0] == competitor:
                                player_id = x[0]
                                player_first_name = x[1]
                                player_last_name = x[2]
                                player_info = [player_id, player_first_name, player_last_name]
                        match_info.append(player_info)
                        iteration += 1
                
                # if the round is already complete
                else:

                    # add completed match to be read by the javascript
                    completed_match = ["completed", match]
                    match_info.append(completed_match)

                    # add each competitor info
                    iteration = 0
                    while iteration < 2:
                        competitor = two_competitors[iteration]
                        for x in players:
                            if x[0] == competitor:
                                player_id = x[0]
                                player_first_name = x[1]
                                player_last_name = x[2]
                                player_info = [player_id, player_first_name, player_last_name]
                        match_info.append(player_info)
                        iteration += 1
                count += 1

    # send info to page to be displayed
    return render_template("tournamentview.html", cols=cols, players=players, match_info=match_info)


# updates tournament data for a variety of routes
def refreshtournament():

    # clear session info
    session["selected_season"] = None
    session["current_round"] = None

    # find the selected tournament
    if request.args.get("tournament"):
        sess = request.args.get("tournament")
        session["selected_tournament"] = sess
    elif session["selected_tournament"]:
        sess = session["selected_tournament"]
    else:
        return errorpage(sendto="/", message="You must select a tournament.")
    
    # get the tournament info from database
    cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})
    cols = cur.fetchall()
    if len(cols) != 1:
        return errorpage(sendto="/", message="You must select a valid tournament.")
    
    # get competitor info from database
    cur.execute("""SELECT competitors.competitor_id, competitor_first_name, competitor_last_name FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE tournament_id = %(sess)s""", {'sess':sess})
    players = cur.fetchall()

    # get the current round id from the tournament info
    round_id = cols[0][5]

    # get the round info
    cur.execute("""SELECT * FROM rounds WHERE round_id = %(round_id)s""", {'round_id': round_id})
    round_info = cur.fetchall()

    # returns players and cols (tournament info) to the route that called refresh
    return players, cols, round_info


# will seed players in first round, change tournament status to started
@app.route("/begintournament")
@login_required
def begintournament():

    # clear session info
    session["selected_season"] = None
    
    # find the selected tournament
    if request.args.get("tournament"):
        sess = request.args.get("tournament")
        session["selected_tournament"] = sess
    elif session["selected_tournament"]:
        sess = session["selected_tournament"]
    else:
        return errorpage(sendto="/", message="You must select a tournament.")

    # calls refreshtournament function
    results = refreshtournament()

    players = results[0]

    # tournament info
    cols = results[1]
    tournamentid = cols[0]["tournament_id"]

    # put just the player ids into a list
    playerids = []
    for each in players:
        playerids.append(each[0])

    # find the number of players
    playercount = len(playerids)

    # using all scores from all players, sort them by highest average score
    cur.execute("""SELECT competitor_id FROM scores WHERE competitor_id = ANY(%(playerids)s) GROUP BY competitor_id ORDER BY AVG(COALESCE(total, 0)) DESC""", {'playerids':playerids})
    rows = cur.fetchall()
    sortedplayers = []
    for each in rows:
        sortedplayers.append(each[0])
    for each in playerids:
        if each not in sortedplayers:
            sortedplayers.append(each)

    # handle too big or too small tournaments
    if playercount < 2:
        return errorpage(sendto="newtournament", message="Tournaments can have 2 to 64 players.")
    elif playercount > 64:
        return errorpage(sendto="newtournament", message="Tournaments can have 2 to 64 players.")

    # dont allow any more players to be added to the tournament
    cur.execute("""UPDATE tournaments SET enrollment_open = FALSE WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournamentid})

    # create the first round
    createround(sortedplayers, tournamentid)

    return tournamentview()


# takes a list of sorted players and a tournament and places player into matches, gives them byes appropriately
@login_required
def createround(sorted_players, tournamentid):

    # clears session info
    session["selected_season"] = None

    matches_array = []
    bye_array = []
    playerone = None
    playertwo = None
    sortedplayers = list(sorted_players)
    playercount = len(sorted_players)
    tournamentid = tournamentid

    if playercount < 2:
        return errorpage(sendto="tournamentview", message="Tournaments must include at least two players.")

    # starts at round A
    elif playercount == 2:
        which_round = "A"

        # create matches
        for each in bracket_A_seed_order:
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                playertwo = sortedplayers[each]
                cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                conn.commit()
                match_id = cur.fetchall()[0][0]
                matches_array.append(match_id)

        # there will be no byes by default for this smallest round
        bye_array = [0]

    # starts at round B
    elif playercount < 5:
        which_round = "B"

        # handle not full seeding
        if playercount < 4:
            sortedplayers.append(0)

        # create matches
        for each in bracket_B_seed_order:
            match_id = None
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                if sortedplayers[each]:
                    playertwo = sortedplayers[each]
                    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                    conn.commit()
                    match_id = cur.fetchall()[0][0]
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(playerone)
                playerone = None
                playertwo = None

    # starts at round C
    elif playercount < 9:
        which_round = "C"

        # handle not full seeding
        bye_array = []
        count = playercount
        while count < 8:
            sortedplayers.append(0)
            count += 1
        
        # create matches
        for each in bracket_C_seed_order:
            match_id = None
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                if sortedplayers[each]:
                    playertwo = sortedplayers[each]
                    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                    conn.commit()
                    match_id = cur.fetchall()[0][0]
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(playerone)
                playerone = None
                playertwo = None

    # starts at round D
    elif playercount < 17:
        which_round = "D"

        # handle not full seeding
        bye_array = []
        count = playercount
        while count < 16:
            sortedplayers.append(0)
            count += 1
        
        # create matches
        for each in bracket_D_seed_order:
            match_id = None
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                if sortedplayers[each]:
                    playertwo = sortedplayers[each]
                    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                    conn.commit()
                    match_id = cur.fetchall()[0][0]
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(playerone)
                playerone = None
                playertwo = None

    # starts at round E
    elif playercount <33:
        which_round = "E"

        # handle not full seeding
        bye_array = []
        count = playercount
        while count < 32:
            sortedplayers.append(0)
            count += 1
        
        # create matches
        for each in bracket_E_seed_order:
            match_id = None
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                if sortedplayers[each]:
                    playertwo = sortedplayers[each]
                    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                    conn.commit()
                    match_id = cur.fetchall()[0][0]
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(playerone)
                playerone = None
                playertwo = None

    # starts at round F
    elif playercount <65:
        which_round = "F"

        # handle not full seeding
        bye_array = []
        count = playercount
        while count < 32:
            sortedplayers.append(0)
            count += 1
        
        # create matches
        for each in bracket_F_seed_order:
            match_id = None
            if playerone is None:
                playerone = sortedplayers[each]
            else:
                if sortedplayers[each]:
                    playertwo = sortedplayers[each]
                    cur.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(playerone)s, %(playertwo)s, %(tournament_id)s) RETURNING match_id""", {'playerone': playerone, 'playertwo': playertwo, 'tournament_id': tournamentid})
                    conn.commit()
                    match_id = cur.fetchall()[0][0]
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(playerone)
                playerone = None
                playertwo = None

    # insert round entry to database
    cur.execute("""INSERT INTO rounds (tournament_id, matches, round_id, bye_competitors, which_round) VALUES (%(tournament_id)s, %(matches_array)s, nextval('round_increment'), %(bye_array)s, %(which_round)s) RETURNING round_id""", {'tournament_id': tournamentid, 'matches_array': matches_array, 'bye_array': bye_array, 'which_round': which_round})
    conn.commit()
    round_id = cur.fetchall()[0][0]

    # set the current round in the tounament info and session
    cur.execute("""UPDATE tournaments SET current_round = %(round_id)s WHERE tournament_id = %(tournament_id)s""", {'round_id': round_id, 'tournament_id': tournamentid})
    conn.commit()
    session["current_round"] = round_id

    return tournamentview()


# given the current tournament, sets player list for next round by taking previous bye players and winners from previous round
@app.route("/nextround")
@login_required
def nextround():

    # clear session values
    session["selected_seaon"] = None

    # get current tournament
    tournament = session["selected_tournament"]

    # get previous round id from tournament info
    cur.execute("""SELECT current_round FROM tournaments WHERE tournament_id = %(tournament)s""", {'tournament': tournament})
    
    # get previous round info
    previous_round = cur.fetchall()[0][0]
    cur.execute("""SELECT * FROM rounds WHERE round_id = %(previous_round)s""", {'previous_round': previous_round})
    previous_round_info = cur.fetchall()[0]

    # prepares a sorted list for the next round by taking all players with byes and winners in the previous round 
    player_id_array = []
    count = 0
    for each in previous_round_info[1]:
        if each != 0:
            player_id_array.append(each)
        else:
            match = previous_round_info[2][count]
            cur.execute("""SELECT winner_id FROM matches WHERE match_id = %(match)s""", {'match': match})
            winner_id = cur.fetchall()[0][0]
            player_id_array.append(winner_id)
            count += 1

    return createround(player_id_array, tournament)


@app.route("/editmatch")
@login_required
def editmatch():
    
    match_id = request.args.get("match")

    # make sure there is a valid tournament selected
    if not session["selected_tournament"]:
        return errorpage(sendto="/", message="Create match is only for seasons.")

    # get match info
    cur.execute("""SELECT * FROM matches WHERE match_id = %(match_id)s""", {'match_id': match_id})
    match_info = cur.fetchall()[0]

    player_one_info = [match_info[1]]
    player_two_info = [match_info[2]]

    session["array_competitor_ids"] = [match_info[1], match_info[2]]

    # get player info
    cur.execute("""SELECT competitor_first_name, competitor_last_name FROM competitors WHERE competitor_id = %(match_info[1])s""", {'match_info[1]': match_info[1]})
    p1info = cur.fetchall()[0]
    player_one_info.append(p1info["competitor_first_name"])
    player_one_info.append(p1info["competitor_last_name"])
    cur.execute("""SELECT competitor_first_name, competitor_last_name FROM competitors WHERE competitor_id = %(match_info[2])s""", {'match_info[2]': match_info[2]})
    p2info = cur.fetchall()[0]
    player_two_info.append(p2info["competitor_first_name"])
    player_two_info.append(p2info["competitor_last_name"])


    # store match id in session
    session["match_id"] = match_id

    # store players in array
    array_competitors = [player_one_info, player_two_info]

    # send competitor info to scorematch form
    return render_template("scorematch.html", array_competitors=array_competitors, possible_scores=possible_scores)




# form and validation for adding an already existing player to an already existing season or tournament
@app.route("/enrollcompetitor", methods=["GET", "POST"])
@login_required
def enrollcompetitor():

    # determine if a season or tournament is selected
    if session["selected_season"]:
        season = session["selected_season"]
        cur.execute("""SELECT * FROM seasons WHERE season_id = %(season)s""", {'season':season})
        rows = cur.fetchall()
        returnlink = None
        if len(rows) == 1:
            isseason = True
            returnlink = "seasonview"
    elif session["selected_tournament"]:
        tournament = session["selected_tournament"]
        cur.execute("""SELECT * FROM tournaments WHERE tournament_id = %(tournament)s""", {'tournament':tournament})
        cols = cur.fetchall()
        returnlink = "tournamentview"
        isseason = False
    else:
        return errorpage(sendto="/", message="Select a valid season or tournament before enrolling a competitor.")

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

            # retrieve this seasons matchup data, add new thrower and matchups to it, put it back in database
            cur.execute("""SELECT * FROM matchups WHERE season_id = %(sid)s""", {'sid':sid})
            exists = cur.fetchall()
            match len(exists):
                case 0:
                    throwers = [compid]
                    array = []
                case _:
                    array = exists[0]["todo"]
                    throwers = exists[0]["throwers"]
                    for each in throwers:
                        array.append([each, compid])
                    throwers.append(compid)
            cur.execute("""INSERT INTO matchups (season_id, throwers, todo) VALUES (%(sid)s, %(throwers)s, %(array)s) ON CONFLICT (season_id) DO UPDATE SET (throwers, todo) = (excluded.throwers, excluded.todo)""", {'sid':sid, 'throwers':throwers, 'array':array})
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
    session["selected_season"] = None
    session["selected_tournament"] = None

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

def render_player_stats():
    cur.execute("""SELECT * FROM competitors""")
    player_list = cur.fetchall()
    for each in player_list:
        player_id = each[0]
        cur.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores WHERE competitor_id = %(player_id)s""", {'player_id':player_id})
        output = cur.fetchall()
        average = output[0][0]
        games_played = output[0][1]
        cur.execute("""SELECT COUNT(*) FROM scores WHERE competitor_id = %(player_id)s AND won = true""", {'player_id':player_id})
        output = cur.fetchall()
        games_won = output[0][0]
        if (games_played == 0):
            win_rate = 0
        else:
            win_rate = round((games_won / games_played), 2)
        each.append(average)
        each.append(win_rate)
        each.append(games_played)
    return(player_list)


@app.route("/player_view")
def player_view():
    player_id = request.args.get("player_id")

    cur.execute("""SELECT * FROM competitors WHERE competitor_id = %(player_id)s""", {'player_id':player_id})
    player_stats = cur.fetchall()[0]
    player_id = player_stats[0]

    cur.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores WHERE competitor_id = %(player_id)s""", {'player_id':player_id})
    output = cur.fetchall()
    average = output[0][0]
    games_played = output[0][1]
    cur.execute("""SELECT COUNT(*) FROM scores WHERE competitor_id = %(player_id)s AND won = true""", {'player_id':player_id})
    output = cur.fetchall()
    games_won = output[0][0]
    win_rate = round((games_won / games_played), 2)
    player_stats.append(average)
    player_stats.append(win_rate)
    player_stats.append(games_played)

    cur.execute("""SELECT player_1_id, player_2_id, winner_id, player1total, player2total FROM matches WHERE (player_1_id = %(player_id)s OR player_2_id = %(player_id)s) AND winner_id IS NOT NULL""", {'player_id': player_id})
    match_list = cur.fetchall()

    cur.execute("""SELECT * FROM competitors""")
    player_list = cur.fetchall()

    for each in match_list:
        player1_id = each[0]
        player2_id = each[1]
        winner_id = each[2]
        for x in player_list:
            if x[0] == player1_id:
                each.append(x[1])
                each.append(x[2])
        for x in player_list:
            if x[0] == player2_id:
                each.append(x[1])
                each.append(x[2])
        for x in player_list:
            if x[0] == winner_id:
                each.append(x[1])
                each.append(x[2])

    return render_template("player_view.html", player_stats=player_stats, match_list=match_list)


@app.route("/tournament_stats_view")
def tournament_stats_view():
    # get the selected tournament to be displayed
    if request.args.get("tournament"):
        tournament_id = request.args.get("tournament")
    else:
        return errorpage(sendto="/", message="You must select a tournament.")

    cur.execute("""SELECT enrollment.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name FROM enrollment JOIN competitors ON competitors.competitor_id = enrollment.competitor_id WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournament_id} )
    player_list = cur.fetchall()

    cur.execute("""SELECT match_id, player_1_id, player_2_id, winner_id, player1total, player2total FROM matches WHERE tournament_id = %(tournament_id)s""", {'tournament_id':tournament_id})
    match_list = cur.fetchall()

    cur.execute("""SELECT * FROM rounds WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournament_id})
    round_list = cur.fetchall()

    first_round_found = False
    first_round = []
    results = []

    for each in round_list:
        if each["which_round"] == "F":
            if first_round_found == False:
                first_round = each
                first_round_found = True
            round_f_results = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_f_results[results_count] = []
                            else:
                                round_f_results[results_count] = [p1total, p2total]                    
                    matches_count += 1
                    results_count += 1
            results.append(round_f_results)

    for each in round_list:
        if each["which_round"] == "E":
            if first_round_found == False:
                first_round_found = True
                first_round = each
            round_e_results = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_e_results[results_count] = []
                            else:
                                round_e_results[results_count] = [p1total, p2total]                    
                    matches_count += 1
                    results_count += 1
            results.append(round_e_results)

    for each in round_list:
        if each["which_round"] == "D":
            if first_round_found == False:
                first_round = each
                first_round_found = True
            round_d_results = [[],[],[],[],[],[],[],[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_d_results[results_count] = []
                            else:
                                round_d_results[results_count] = [p1total, p2total]
                    matches_count += 1
                    results_count += 1
            results.append(round_d_results)
        
    for each in round_list:
        if each["which_round"] == "C":
            if first_round_found == False:
                first_round = each
                first_round_found = True
            round_c_results = [[],[],[],[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_c_results[results_count] = []
                            else:
                                round_c_results[results_count] = [p1total, p2total]
                    matches_count += 1
                    results_count += 1
            results.append(round_c_results)

    for each in round_list:
        if each["which_round"] == "B":
            if first_round_found == False:
                first_round = each
                first_round_found = True
            round_b_results = [[],[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_b_results[results_count] = []
                            else:
                                round_b_results[results_count] = [p1total, p2total]                    
                    matches_count += 1
                    results_count += 1
            results.append(round_b_results)
        
    for each in round_list:
        if each["which_round"] == "A":
            if first_round_found == False:
                first_round = each
                first_round_found = True
            round_a_results = [[]]
            results_count = 0
            matches_count = 0
            for x in each["bye_competitors"]:
                if x != 0:
                    results_count += 1
                else:
                    for y in match_list:
                        if y["match_id"] == each["matches"][matches_count]:
                            p1total = y["player1total"]
                            p2total = y["player2total"]
                            if (p1total == None or p2total == None):
                                round_a_results[results_count] = []
                            else:
                                round_a_results[results_count] = [p1total, p2total]                    
                    matches_count += 1
                    results_count += 1
            results.append(round_a_results)

    bye_list = first_round["bye_competitors"]
    teams_array = []
    match_count = 0
    for each in bye_list:
        if each != 0:
            for x in player_list:
                if x["competitor_id"] == each:
                    name = x["competitor_first_name"] +  " " + x["competitor_last_name"]
                    name_pair = [name, None]
                    teams_array.append(name_pair)
        else:
            match = first_round["matches"][match_count]
            for x in match_list:
                if x["match_id"] == match:
                    p1 = x["player_1_id"]
                    for y in player_list:
                        if y["competitor_id"] == p1:
                            p1name = y["competitor_first_name"] + " " + y["competitor_last_name"]
                    p2 = x["player_2_id"]
                    for y in player_list:
                        if y["competitor_id"] == p2:
                            p2name = y["competitor_first_name"] + " " + y["competitor_last_name"]
                    name_pair = [p1name, p2name]
                    teams_array.append(name_pair)
            match_count += 1
    teams_array = json.dumps(teams_array)

    return render_template("tournament_stats_view.html", teams_array=teams_array, results=results)


@app.route("/season_stats_view")
def season_stats_view():
    # get the selected season to be displayed
    if request.args.get("season"):
        season_id = request.args.get("season")
    else:
        return errorpage(sendto="/", message="You must select a season.")

    cur.execute("""SELECT enrollment.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name FROM enrollment JOIN competitors ON competitors.competitor_id = enrollment.competitor_id WHERE season_id = %(season_id)s""", {'season_id': season_id} )
    player_list = cur.fetchall()

    cur.execute("""SELECT player_1_id, player_2_id, winner_id, player1total, player2total FROM matches WHERE season_id = %(season_id)s AND winner_id IS NOT NULL""", {'season_id':season_id})
    match_list = cur.fetchall()

    for each in player_list:
        player_id = each[0]
        cur.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id WHERE scores.competitor_id = %(player_id)s AND matches.season_id = %(season_id)s""", {'player_id':player_id, 'season_id': season_id})
        output = cur.fetchall()
        average = output[0][0]
        games_played = output[0][1]
        cur.execute("""SELECT COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id WHERE competitor_id = %(player_id)s AND won = true AND matches.season_id = %(season_id)s""", {'player_id':player_id, 'season_id': season_id})
        output = cur.fetchall()
        games_won = output[0][0]
        win_rate = 0
        if (games_played > 0):
            win_rate = round((games_won / games_played), 2)
        each.append(average)
        each.append(win_rate)
        each.append(games_played)

    for each in match_list:
        player1_id = each[0]
        player2_id = each[1]
        winner_id = each[2]
        for x in player_list:
            if x[0] == player1_id:
                each.append(x[1])
                each.append(x[2])
        for x in player_list:
            if x[0] == player2_id:
                each.append(x[1])
                each.append(x[2])
        for x in player_list:
            if x[0] == winner_id:
                each.append(x[1])
                each.append(x[2])

    return render_template("season_stats_view.html", player_list=player_list, match_list=match_list)