# flask framework for lots of things that make apps easy
from flask import Flask, render_template, request, session, redirect
# to store session variables
from flask_session import Session

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

        
# index page if not logged in, judgehome if they are
@app.route("/")
def index():
    # clears from any season or tournament being selected
    session["selected_season"] = None
    session["selected_tournament"] = None

    # not logged in:
    if session.get("user_id") is None:
        each_discipline_player_list = render_player_stats()

        seasons, tournaments = select_season_tournament()

        return render_template("index.html", each_discipline_player_list=each_discipline_player_list, seasons=seasons, tournaments=tournaments)

    # logged in:
    # loads seasons and tournaments for dropdowns in judge home page
    # Filter out seasons and tournaments that are finished
    seasons, tournaments = active_season_tournament()

    # sends available season and tournament info to page to be displayed
    return render_template("judgehome.html", seasons=seasons, tournaments=tournaments)


# a login form, validated, variables put in session and / reloaded
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # after form submission
    if request.method == "POST":
        user_name = request.form.get("name")
        judge_pw = request.form.get("password")

        # check for blank fields
        if not user_name or not judge_pw:
            return helpers.errorpage(message="Please enter a username and password.", send_to="login")

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


# displays info page
@app.route("/rules")
def rules():
    return render_template("rules.html")

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
        if not request.form.get("season") or not request.form.get("year") or not request.form.get("startdate"):
            return errorpage(send_to="newseason", message="Please fill out all fields.")
        season = request.form.get("season")
        year_of = request.form.get("year")
        start_date = request.form.get("startdate")

        # check that the season doesnt exist already
        no_duplicate_season(season, year_of)
        
        # put the season in the database
        # try:
        save_season(season, year_of, start_date)
        return redirect("/")
        # except:
        #     return errorpage(send_to="newseason", message="Could not save the season.")

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
    
    # get the selected quarter to be displayed
    if request.args.get("quarter"):
        quarter_month = request.args.get("quarter")
    else:
        quarter_month = 1
    session["selected_quarter"] = quarter_month

    # get the selected lap to be displayed
    if request.args.get("lap"):
        lap_count = request.args.get("lap")
    else:
        lap_count = 1
    session["selected_lap"] = lap_count

    # get that season's info from database
    try:
        rows = select_current_season(sess)
        if not rows:
            return helpers.errorpage(send_to="/", message="You must select a valid season.")
    except:
        return errorpage(send_to="/", message="You must select a valid season.")

    # get competitor info from database
    try:
        players = select_season_competitors(sess)
    except:
        return errorpage(send_to="/", message="Could not retrieve competitors.")

    # display completed matches
    try:
        logged_matches = select_matches_by_lap_quarter_season(lap_count, quarter_month, sess)
    except:
        return errorpage(send_to="/", message="Could not retrieve season matches.")
    
    season_quarters = select_season_quarters(sess)
    season_laps = select_season_laps(sess)

    players_wait_times = wait_times(logged_matches)
    print(players_wait_times)

    # send that info on to the page to be displayed
    return render_template("seasonview.html", rows=rows, players=players, logged_matches=logged_matches, season_quarters=season_quarters, season_laps=season_laps, players_wait_times=players_wait_times)


# create quarter
@app.route("/createquarter", methods=["POST"])
@login_required
def createquarter():
    sess = request.form.get("season")
    quarter_month = request.form.get("new_quarter")
    start_date = request.form.get("quarter_date")
    session["selected_quarter"] = quarter_month

    if select_quarter_id_by_month_and_season_id(quarter_month, sess) == None:
        insert_current_quarter(quarter_month, sess, start_date)
    else:
        return errorpage(message="That quarter already exists", send_to="seasonview")
    return redirect(f"/seasonview?season={sess}")


# create lap
@app.route("/createlap", methods=["POST"])
@login_required
def createlap():

    lap_count = request.form.get("new_lap")
    start_date = request.form.get("lap_date")
    quarter_id = request.form.get("quarter_id")
    discipline = request.form.get("discipline")
    session["selected_lap"] = lap_count
    sess = session["selected_season"]
    if select_lap_id_by_lap_quarter(lap_count, quarter_id) == None:
        insert_current_lap(lap_count, start_date, quarter_id, discipline)
    else:
        return errorpage(message="That lap already exists", send_to="seasonview")
    return redirect(f"/seasonview?season={sess}")


# create match used only from seasons, in tournaments matches are created when the round is created
@app.route("/creatematch")
@login_required
def creatematch():

    # make sure there is a valid season selected
    if session["selected_season"]:
        session["array_competitor_ids"] = request.args.getlist("competitor_selection")[0].strip("[]").split(",")
    else:
        return errorpage(send_to="/", message="Create match is only for seasons.")
    # make an array with those competitors and their information from competitor database table
    array_competitors = []
    for each in session["array_competitor_ids"]:
        competitor = select_competitor_by_id(each)
        array_competitors.append(competitor["competitor_id"])
        array_competitors.append(competitor["competitor_first_name"])
        array_competitors.append(competitor["competitor_last_name"])


    # get player ids
    playerA = session["array_competitor_ids"][0]
    playerB = session["array_competitor_ids"][1]

    # get session values to be stored
    sess = session["selected_season"]
    if session["selected_quarter"]:
        quarter = session["selected_quarter"]
    else:
        quarter = 1
    if session["selected_lap"]:
        lap = session["selected_lap"]
    else:
        lap = 1

    # get lap_id
    try:
        lap_id = select_lap_id_by_lap_quarter_season(lap, quarter, sess)
    except TypeError:
        return errorpage(message="Be sure to create the appropriate Quarter and Series", send_to="seasonview")

    # insert into matches, returns primary key match id for use in scores inserts
    session["match_id"] = insert_unscored_season_match(playerA, playerB, lap_id[0])

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
        view, discipline = determine_discipline_season_or_tournament(match_id)
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
        if not request.form.get("name") or not request.form.get("discipline") or not request.form.get("date"):
            return errorpage(send_to="newtournament", message="Please fill in all fields.")
        name = request.form.get("name")
        discipline = request.form.get("discipline")
        date = request.form.get("date")
        double_elimination = request.form.get("double_eliminaiton")
        if double_elimination == None:
            double_elimination = False

        # check that the tournament doesnt exist already
        list = no_duplicate_tournament(name, discipline, date)
        if len(list) > 0:
            return helpers.errorpage(send_to="newtournament", message="A {name} {discipline} tournament on {date} already exists.".format(name=name, discipline=discipline, date=date))
        
        # put the new tournament into the database
        try:
            save_tournament(name, discipline, date, double_elimination)
            return redirect("/")
        except:
            return errorpage(send_to="newtournament", message="Could not save tournament info.")

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
    players, tournament, round = refreshtournament()


    # cols is tournament info
    tournament_info = tournament
    match_info = []
    player_info = []

    # if there is a round started
    if (round):
        round_info = round[0]

        # counting the number of matches
        count = 0

        # for each competitor in the bye competitors list
        for round in round_info[1]:

            # if it is a real competitor and not a placeholder for a bye
            if round != 0:

                # add the word bye to be read by the javascript
                match_info.append("bye")

                # add the player info
                for player in players:
                    if player[0] == round:
                        player_id = player[0]
                        player_first_name = player[1]
                        player_last_name = player[2]
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
                        for player in players:
                            if player[0] == competitor:
                                player_id = player[0]
                                player_first_name = player[1]
                                player_last_name = player[2]
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
                        for player in players:
                            if player[0] == competitor:
                                player_id = player[0]
                                player_first_name = player[1]
                                player_last_name = player[2]
                                player_info = [player_id, player_first_name, player_last_name]
                        match_info.append(player_info)
                        iteration += 1
                count += 1

    # send info to page to be displayed
    return render_template("tournamentview.html", tournament_info=tournament_info, players=players, match_info=match_info)



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
    players, tournament_info, round_info = refreshtournament()
    tournament_id = tournament_info["tournament_id"]

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

    # get match info
    try:
        match_info = select_match_by_id(match_id)
    except:
        return errorpage(send_to="tournamentview", message="Could not load match.")
    player_1 = match_info['player_1_id']
    player_2 = match_info['player_2_id']

    session["array_competitor_ids"] = [player_1, player_2]

    # get player info
    player_1_info = select_competitor_by_id(player_1)
    player_1_first = (player_1_info["competitor_first_name"])
    player_1_last = (player_1_info["competitor_last_name"])
    player_2_info = select_competitor_by_id(player_2)
    player_2_first = (player_2_info["competitor_first_name"])
    player_2_last = (player_2_info["competitor_last_name"])


    # store match id in session
    session["match_id"] = match_id

    # store players in array
    array_competitors = [player_1, player_1_first, player_1_last, player_2, player_2_first, player_2_last]

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
        season_info = select_season(season)
        if season_info:
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
            sid = season_info["season_id"]
            check = select_competitor_seasons(compid)
            for each in check:
                if sid == each[0]:
                    return errorpage(send_to="enrollcompetitor", message="That competitor is already enrolled in this season.")
            insert_enrollment_season(compid, sid)

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
        result = "{} {} season".format(season_info['season'], season_info['yearof'])
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

    return render_template("player_view.html", player_stats=player_stats, match_list=match_list)

@app.route("/match_view")
def match_view():
    match_id = request.args.get("match_id")
    match_stats = select_match_by_id(match_id)
    player_1_scores = select_scores_by_player_id_match_id(match_stats['player_1_id'], match_id)[0]
    player_2_scores = select_scores_by_player_id_match_id(match_stats['player_2_id'], match_id)[0]
    if (player_1_scores['seq'] == player_2_scores['seq']):
        sequence = player_1_scores['seq'].split(',')
    else:
        return errorpage("Error retieving match info.", "/")
    player_1_name = player_name_from_id(match_stats["player_1_id"])
    player_2_name = player_name_from_id(match_stats["player_2_id"])

    return render_template("match_view.html", match_stats=match_stats, player_1_scores=player_1_scores, player_2_scores=player_2_scores, player_1_name=player_1_name, player_2_name=player_2_name, sequence=sequence)


@app.route("/tournament_stats_view")
def tournament_stats_view():
    # get the selected tournament to be displayed
    if request.args.get("tournament"):
        tournament_id = request.args.get("tournament")
    else:
        return errorpage(send_to="/", message="You must select a tournament.")
    tournament_info = select_tournament(tournament_id)[0]
    player_list = select_tournament_competitors(tournament_id)

    match_list = select_tournament_matches(tournament_id)

    round_list = select_tournament_rounds(tournament_id)

    first_round_found = False
    first_round = []
    results = []

    teams_array, results = build_bracket(player_list, match_list, round_list, first_round_found, first_round, results)



    return render_template("tournament_stats_view.html", teams_array=teams_array, results=results, tournament_info=tournament_info)


@app.route("/season_stats_view")
def season_stats_view():
    # get the selected season to be displayed
    if request.args.get("season"):
        season_id = request.args.get("season")
    else:
        return errorpage(send_to="/", message="You must select a season.")

    season_info = select_season(season_id)
    quarters_info = select_season_quarters(season_id)
    laps_info = select_season_laps(season_id)
    player_list = select_season_competitors(season_id)

    match_list = select_season_matches(season_id)

    for each in player_list:
        player_id = each[0]
        output = select_competitor_season_average(player_id, season_id)
        average = output[0][0]
        games_played = output[0][1]
        games_won = select_competitor_season_wins(player_id, season_id)
        win_rate = 0
        if (games_played > 0):
            win_rate = round((games_won / games_played), 2)
        each.append(average)
        each.append(win_rate)
        each.append(games_played)

    for each in match_list:
        winner_name = player_name_from_id(each['winner_id'])
        player_1_name = player_name_from_id(each['player_1_id'])
        player_2_name = player_name_from_id(each["player_2_id"])
        each.append(winner_name)
        each.append(player_1_name)
        each.append(player_2_name)

    return render_template("season_stats_view.html", player_list=player_list, match_list=match_list, season_info=season_info, quarters_info=quarters_info, laps_info=laps_info)