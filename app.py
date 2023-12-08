import os

# flask framework for lots of things that make apps easy
from flask import Flask, render_template, request, session, redirect
# to store session variables
from flask_session import Session

import json

from db import *
from helpers import *

#initiate app
app = Flask(__name__)

# app settings
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)

# connect to database
try:
    db_connect()
except:
    print("Unable to connect to database")

# when compared against a sorted list of players, it sets the matches so that players are seeded correctly
bracket_A_seed_order = [0,1]
bracket_B_seed_order = [0,3,1,2]
bracket_C_seed_order = [0,7,3,4,2,5,1,6]
bracket_D_seed_order = [0,15,7,8,3,12,4,11,1,14,6,9,2,13,5,10]
bracket_E_seed_order = [0,31,15,16,8,23,7,24,3,28,12,19,11,20,4,27,1,30,14,17,9,22,6,25,2,29,13,18,10,21,5,26]
bracket_F_seed_order = [0,63,31,32,16,47,15,48,8,55,23,40,24,39,7,56,3,60,28,35,19,44,12,51,11,52,20,43,27,36,4,59,1,62,30,33,17,46,14,49,9,54,22,41,25,38,6,57,2,61,29,34,18,45,13,50,10,53,21,42,26,37,5,58]
        
# index page if not logged in, judgehome if they are
@app.route("/")
def index():
    # clears from any season or tournament being selected
    session["selected_season"] = None
    session["selected_tournament"] = None

    # not logged in:
    if session.get("user_id") is None:
        player_list = render_player_stats()

        rows, cols = select_season_tournament()

        return render_template("index.html", player_list=player_list, rows=rows, cols=cols)

    # logged in:
    # loads seasons and tournaments for dropdowns in judge home page
    # Filter out seasons and tournaments that are finished
    rows, cols = inactive_season_tournament()

    # sends available season and tournament info to page to be displayed
    return render_template("judgehome.html", rows=rows, cols=cols)


# a login form, validated, variables put in session and / reloaded
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # after form submission
    if request.method == "POST":
        user_name = request.form.get("name")
        judge_pw = request.form.get("password")

        try:
            judge_id, judge_name = verify_judge_account(user_name, judge_pw)
        except ValueError:
            return errorpage(message="The username or password was not found.", send_to="login")

        # save judge info in session
        session["user_id"] = judge_id
        session["name"] = judge_name
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
            return errorpage(send_to="newjudge", message="Please fill out all fields.")
        name = request.form.get("name")
        pw = request.form.get("password")
        confirm = request.form.get("confirmation")

        # check for that judge already existing
        no_duplicate_judge(name)

        # check they entered the password twice the same
        if pw != confirm:
            return errorpage(send_to="newjudge", message="Passwords did not match.")

        # generate and store password hash
        try:
            save_pw(name, pw)
            return redirect("/")
        except:
            return errorpage(send_to="newjudge", message="Could not save password.")

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
            return errorpage(send_to="newcompetitor", message="Please fill out all fields.")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        # check if that competitor already exists
        try:
            no_duplicate_competitor(fname, lname)
        except:
            return errorpage(send_to="newcompetitor", message="A competitor with this name already exists.")

        # add competitor to database
        try:
            save_competitor(fname, lname)
            return redirect("/")
        except:
            return errorpage(send_to="newcompetitor", message="Could not save competitor.")
    
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
        if not request.form.get("season") or not request.form.get("year") or not request.form.get("discipline") or not request.form.get("start_date"):
            return errorpage(send_to="newseason", message="Please fill out all fields.")
        season = request.form.get("season")
        year_of = request.form.get("year")
        discipline = request.form.get("discipline")
        start_date = request.form.get("start_date")

        # check that the season doesnt exist already
        try:
            no_duplicate_season(season, year_of, discipline)
        except:
            return errorpage(send_to="newseason", message="A {season} {year_of} {discipline} season already exists.".format(season=season, year_of=year_of, discipline=discipline))
        
        # put the season in the database
        try:
            save_season(season, year_of, discipline, start_date)
            return redirect("/")
        except:
            return errorpage(send_to="newseason", message="Could not save the season.")

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
        return errorpage(send_to="/", message="You must select a season.")

    # get that season's info from database
    try:
        rows = select_current_season(sess)
    except:
        return errorpage(send_to="/", message="You must select a valid season.")

    # get competitor info from database
    try:
        players = select_season_competitors(sess)
    except:
        return errorpage(send_to="/", message="Could not retrieve competitors.")

    # TODO display completed matches
    try:
        logged_matches = select_completed_matches(sess)
    except:
        return errorpage(send_to="/", message="Could not retrieve season matches.")

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
        return errorpage(send_to="/", message="Create match is only for seasons.")
        
    # make an array with those competitors and their information from competitor database table
    array_competitors = []
    for each in session["array_competitor_ids"]:
        competitor = select_competitor_by_id(each)
        array_competitors.append(competitor)

    # get player ids
    playerA = session["array_competitor_ids"][0]
    playerB = session["array_competitor_ids"][1]

    # get session values to be stored
    sess = session["selected_season"]

    # insert into matches, returns primary key match id for use in scores inserts
    session["match_id"] = insert_unscored_season_match(playerA, playerB, sess)

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
            return errorpage(send_to="scorematch", message="THE APOCALYPSE, your match was submitted incompletely, and therefore wasn't saved.")
        
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
        pAqt, pBqt = count_quickthrow_points(qs)

        # iterate through all the throw scores to make sure nobody hacked the html
        all_scores = [pAtone, pAttwo, pAtthree, pAtfour, pAtfive, pAtsix, pAtseven, pAteight, pBtone, pBttwo, pBtthree, pBtfour, pBtfive, pBtsix, pBtseven, pBteight]
        verify_scores(all_scores)

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
                return errorpage(message="No Tiebreaker selected, scores NOT recoreded.", send_to="seasonview")
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
        view, discipline = determine_discipline_season_or_tournament()

        judge = session["user_id"]

        # three database inserts: one to matches, and one for each player into scores
        try:
            # insert into matches, returns primary key match id for use in scores inserts
            insert_completed_match(winner, pAtotal, pBtotal, discipline, judge, ts, match_id)

            # inserts into scores for each player
            insert_player_scores(playerA, match_id, pAqt, sequence, pAtone, pAttwo, pAtthree, pAtfour, pAtfive, pAtsix, pAtseven, pAteight, pAtotal, pAwin)
            insert_player_scores(playerB, match_id, pBqt, sequence, pBtone, pBttwo, pBtthree, pBtfour, pBtfive, pBtsix, pBtseven, pBteight, pBtotal, pBwin)
        
        # error if the inserts fail
        except:
            return errorpage(message="DATABASE INSERT FAILED, SCORES NOT RECORDED", send_to="seasonview")

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
            return errorpage(send_to="newtournament", message="Please fill in all fields.")
        name = request.form.get("name")
        discipline = request.form.get("discipline")
        date = request.form.get("date")
        double_elimination = request.form.get("double_eliminaiton")

        # check that the tournament doesnt exist already
        try:
            no_duplicate_tournament(name, discipline, date)
        except:
            return errorpage(send_to="newtournament", message="A {name} {discipline} tournament on {date} already exists.".format(name=name, discipline=discipline, date=date))
        
        # put the new tournament into the database
        try:
            save_tournament(name, discipline, date, double_elimination)
            return redirect("/")
        except:
            return errorpage(send_to="newtournament", message="Could not save tournamtent info.")

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
        return errorpage(send_to="/", message="You must select a tournament.")

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
                two_competitors = select_tournament_match(match)
                
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
        return errorpage(send_to="/", message="You must select a tournament.")
    
    # get the tournament info from database
    try:
        cols = select_current_tournament(sess)
    except:
        return errorpage(send_to="/", message="Could not load tournament.")
    
    # get competitor info from database
    try:
        players = select_tournament_competitors(sess)
    except:
        return errorpage(send_to="/", message="Could not load players.")

    # get the current round id from the tournament info
    round_id = cols[0][5]

    # get the round info
    try:
        round_info = select_round(round_id)
    except:
        return errorpage(send_to="/", message="Could not load round.")

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
        return errorpage(send_to="/", message="You must select a tournament.")

    # calls refreshtournament function
    results = refreshtournament()

    players = results[0]

    # tournament info
    cols = results[1]
    tournament_id = cols[0]["tournament_id"]

    # put just the player ids into a list
    player_ids = []
    for each in players:
        player_ids.append(each[0])

    # find the number of players
    playercount = len(player_ids)

    # using all scores from all players, sort them by highest average score
    try:
        sorted_players = sort_players(player_ids)
    except:
        return errorpage(send_to="/", message="Could not load players.")

    # handle too big or too small tournaments
    if playercount < 2:
        return errorpage(send_to="newtournament", message="Tournaments can have 2 to 64 players.")
    elif playercount > 64:
        return errorpage(send_to="newtournament", message="Tournaments can have 2 to 64 players.")

    # dont allow any more players to be added to the tournament
    try:
        set_enrollment_false(tournament_id)
    except:
        return errorpage(send_to="/", message="Could not lock enrollment.")

    # create the first round
    createround(sorted_players, tournament_id)

    return tournamentview()


# takes a list of sorted players and a tournament and places player into matches, gives them byes appropriately
@login_required
def createround(sorted_players, tournament_id):

    # clears session info
    session["selected_season"] = None

    matches_array = []
    bye_array = []
    player_one = None
    player_two = None
    sorted_players = list(sorted_players)
    player_count = len(sorted_players)
    tournament_id = tournament_id

    if player_count < 2:
        return errorpage(send_to="tournamentview", message="Tournaments must include at least two players.")

    # starts at round A
    elif player_count == 2:
        which_round = "A"

        # create matches
        for each in bracket_A_seed_order:
            if player_one is None:
                player_one = sorted_players[each]
            else:
                player_two = sorted_players[each]
                try:
                    match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                except:
                    return errorpage(send_to="tournamentview", message="Could not create match.")
                matches_array.append(match_id)

        # there will be no byes by default for this smallest round
        bye_array = [0]

    # starts at round B
    elif player_count < 5:
        which_round = "B"

        # handle not full seeding
        if player_count < 4:
            sorted_players.append(0)

        # create matches
        for each in bracket_B_seed_order:
            match_id = None
            if player_one is None:
                player_one = sorted_players[each]
            else:
                if sorted_players[each]:
                    player_two = sorted_players[each]
                    try:
                        match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                    except:
                        return errorpage(send_to="tournamentview", message="Could not create match.")
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(player_one)
                player_one = None
                player_two = None

    # starts at round C
    elif player_count < 9:
        which_round = "C"

        # handle not full seeding
        bye_array = []
        count = player_count
        while count < 8:
            sorted_players.append(0)
            count += 1
        
        # create matches
        for each in bracket_C_seed_order:
            match_id = None
            if player_one is None:
                player_one = sorted_players[each]
            else:
                if sorted_players[each]:
                    player_two = sorted_players[each]
                    try:
                        match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                    except:
                        return errorpage(send_to="tournamentview", message="Could not create match.")
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(player_one)
                player_one = None
                player_two = None

    # starts at round D
    elif player_count < 17:
        which_round = "D"

        # handle not full seeding
        bye_array = []
        count = player_count
        while count < 16:
            sorted_players.append(0)
            count += 1
        
        # create matches
        for each in bracket_D_seed_order:
            match_id = None
            if player_one is None:
                player_one = sorted_players[each]
            else:
                if sorted_players[each]:
                    player_two = sorted_players[each]
                    try:
                        match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                    except:
                        return errorpage(send_to="tournamentview", message="Could not create match.")
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(player_one)
                player_one = None
                player_two = None

    # starts at round E
    elif player_count <33:
        which_round = "E"

        # handle not full seeding
        bye_array = []
        count = player_count
        while count < 32:
            sorted_players.append(0)
            count += 1
        
        # create matches
        for each in bracket_E_seed_order:
            match_id = None
            if player_one is None:
                player_one = sorted_players[each]
            else:
                if sorted_players[each]:
                    player_two = sorted_players[each]
                    try:
                        match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                    except:
                        return errorpage(send_to="tournamentview", message="Could not create match.")
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(player_one)
                player_one = None
                player_two = None

    # starts at round F
    elif player_count <65:
        which_round = "F"

        # handle not full seeding
        bye_array = []
        count = player_count
        while count < 32:
            sorted_players.append(0)
            count += 1
        
        # create matches
        for each in bracket_F_seed_order:
            match_id = None
            if player_one is None:
                player_one = sorted_players[each]
            else:
                if sorted_players[each]:
                    player_two = sorted_players[each]
                    try:
                        match_id = insert_unscored_tournament_match(player_one, player_two, tournament_id)
                    except:
                        return errorpage(send_to="tournamentview", message="Could not create match.")
                    bye_array.append(0)
                    matches_array.append(match_id)
                else:
                    bye_array.append(player_one)
                player_one = None
                player_two = None

    # insert round entry to database
    try:
        round_id = insert_round(tournament_id, matches_array, bye_array, which_round)
    except:
        return errorpage(send_to="tournamentview", message="Could not create round.")

    # set the current round in the tounament info and session
    try:
        set_current_round(round_id, tournament_id)
    except:
        return errorpage(send_to="tournamentview", message="Could not save current round.")
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
    previous_round = get_previous_round(tournament)
    
    # get previous round info
    previous_round_info = get_round_info(previous_round)

    # prepares a sorted list for the next round by taking all players with byes and winners in the previous round 
    player_id_array = []
    count = 0
    for each in previous_round_info[1]:
        if each != 0:
            player_id_array.append(each)
        else:
            match = previous_round_info[2][count]
            try:
                winner_id = select_winner(match)
            except:
                return errorpage(send_to="tournamentview", message="Could not sort players.")
            player_id_array.append(winner_id)
            count += 1

    return createround(player_id_array, tournament)


@app.route("/editmatch")
@login_required
def editmatch():
    
    match_id = request.args.get("match")

    # make sure there is a valid tournament selected
    if not session["selected_tournament"]:
        return errorpage(send_to="/", message="Create match is only for seasons.")

    # get match info
    try:
        match_info = select_match(match_id)
    except:
        return errorpage(send_to="tournamentview", message="Could not load match.")

    player_one_info = [match_info[1]]
    player_two_info = [match_info[2]]

    session["array_competitor_ids"] = [player_one_info, player_two_info]

    # get player info
    p1info = select_competitor_by_id(player_one_info)
    player_one_info.append(p1info["competitor_first_name"])
    player_one_info.append(p1info["competitor_last_name"])
    p2info = select_competitor_by_id(player_two_info)
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
    returnlink = None

    # determine if a season or tournament is selected
    if session["selected_season"]:
        season = session["selected_season"]
        rows = select_season(season)
        if len(rows) == 1:
            isseason = True
            returnlink = "seasonview"
    elif session["selected_tournament"]:
        tournament = session["selected_tournament"]
        cols = select_tournament(tournament)
        returnlink = "tournamentview"
        isseason = False
    else:
        return errorpage(send_to="/", message="Select a valid season or tournament before enrolling a competitor.")

    # after form submission
    if request.method == "POST":

        # check for empty fields
        if not request.form.get("firstname") or not request.form.get("lastname"):
            return errorpage(send_to="enrollcompetitor", message="Please fill out all fields.")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        # check if the competitor exists
        comp = select_competitor_by_name(fname, lname)
        if len(comp) != 1:
            return errorpage(send_to="enrollcompetitor", message="That competitor does not exist.")

        # check if the competitor is already enrolled in the selected season or tournament
        compid = comp[0][0]
        if isseason:
            sid = rows[0]["season_id"]
            check = select_competitor_seasons(compid)
            for each in check:
                if sid == each[0]:
                    return errorpage(send_to="enrollcompetitor", message="That competitor is already enrolled in this season.")
            insert_enrollment_season(compid, sid)

            # retrieve this seasons matchup data, add new thrower and matchups to it, put it back in database
            exists = select_season_matchups(sid)
            match len(exists):
                case 0:
                    throwers = [compid]
                    array = []
                case _:
                    array = exists[0]["to_do"]
                    throwers = exists[0]["throwers"]
                    for each in throwers:
                        array.append([each, compid])
                    throwers.append(compid)
            insert_season_matchups(sid, throwers, array)

            return redirect("/seasonview")
        else:
            tid = cols[0]["tournament_id"]
            check = select_competitor_tournaments(compid)
            for each in check:
                if tid == each[0]:
                    return errorpage(send_to="enrollcompetitor", message="That competitor is already enrolled in this tournament.")
            insert_enrollment_tournament(compid, tid)
            return redirect("/tournamentview")

    # sending data to the form page
    if isseason:
        result = "{} {} {} season".format(rows[0]['season'], rows[0]['year_of'], rows[0]['discipline'])
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
    seasonarchive, tournamentarchive = inactive_season_tournament()

     # sends available season and tournament info to page to be displayed
    return render_template("archive.html", seasonarchive=seasonarchive, tournamentarchive=tournamentarchive)

def render_player_stats():
    player_list = select_all_competitors()
    for each in player_list:
        player_id = each[0]
        output = select_competitor_average_games(player_id)
        average = output[0][0]
        games_played = output[0][1]
        games_won = select_competitor_wins(player_id)
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
    player_stats = select_competitor_by_id(player_id)
    output = select_competitor_average_games(player_id)
    average = output[0][0]
    games_played = output[0][1]
    games_won = select_competitor_wins(player_id)
    win_rate = round((games_won / games_played), 2)
    player_stats.append(average)
    player_stats.append(win_rate)
    player_stats.append(games_played)

    match_list = select_competitor_matches(player_id)
    player_list = select_all_competitors()

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
        return errorpage(send_to="/", message="You must select a tournament.")

    player_list = select_tournament_competitors(tournament_id)

    match_list = select_tournament_matches(tournament_id)

    round_list = select_tournament_rounds(tournament_id)

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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
                            p1total = y["player_1_total"]
                            p2total = y["player_2_total"]
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
        return errorpage(send_to="/", message="You must select a season.")

    player_list = select_season_competitors(season_id)

    match_list = select_season_matches(season_id)

    for each in player_list:
        player_id = each[0]
        output = select_competitor_average_games(player_id)
        average = output[0][0]
        games_played = output[0][1]
        games_won = select_competitor_wins(player_id)
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