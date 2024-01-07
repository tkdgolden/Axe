from datetime import date
import datetime
import json
from flask import render_template, request, session
from functools import wraps
import db
# to hash and unhash judge passwords
from werkzeug.security import check_password_hash

possible_scores = [0,1,2,3,4,6,12]

# when compared against a sorted list of players, it sets the matches so that players are seeded correctly
bracket_A_seed_order = [0,1]
bracket_B_seed_order = [0,3,1,2]
bracket_C_seed_order = [0,7,3,4,2,5,1,6]
bracket_D_seed_order = [0,15,7,8,3,12,4,11,1,14,6,9,2,13,5,10]
bracket_E_seed_order = [0,31,15,16,8,23,7,24,3,28,12,19,11,20,4,27,1,30,14,17,9,22,6,25,2,29,13,18,10,21,5,26]
bracket_F_seed_order = [0,63,31,32,16,47,15,48,8,55,23,40,24,39,7,56,3,60,28,35,19,44,12,51,11,52,20,43,27,36,4,59,1,62,30,33,17,46,14,49,9,54,22,41,25,38,6,57,2,61,29,34,18,45,13,50,10,53,21,42,26,37,5,58]

disciplines = ['hatchet', 'knives', 'bigaxe', 'duals']

# function to output error message and send the user back to what they were attempting so they can try again
def errorpage(message, send_to):
    """ returns errorpage displaying message and "back to" button with custom route """
    return render_template("errorpage.html", message=message, sendto=send_to)


def login_required(f):
    """ checks that a user is logged in """
    @wraps(f)
    def check_login(*args, **kwargs):
        if session.get("user_id") is None:
            return errorpage(send_to="login", message="Please log in to access.")
        return (f(*args, **kwargs))
    return check_login

def count_quickthrow_points(qs):
    """ increment each players quickthrow score for each quickthrow score that went to them """

    pAqt = 0;
    pBqt = 0;
    for each in qs:
        if each == "p1":
            pAqt += 1
        elif each == "p2":
            pBqt += 1

    return pAqt, pBqt

def verify_scores(all_scores):
    """ verify the scores are in the possible scores array """

    for each in all_scores:
        if each not in possible_scores:
            return errorpage(message="someone tried to hack your form.", send_to="seasonview")
        

def determine_discipline_season_or_tournament(match_id):
    """ determine season or tournament, get discipline value from database """

    if session["selected_season"]:
        sess = session["selected_season"]
        discipline = db.select_match_discipline(int(match_id))[0]
        view = 'season'
    else:
        sess = session["selected_tournament"]
        cols = db.select_tournament_discipline(sess)
        view = 'tournament'
        discipline = cols[0][0]
    return view, discipline

def player_name_from_id(player_id):
    """ return string of first and last name from db competitor row """

    row = db.select_competitor_by_id(player_id)

    full_name = row[1] + " " + row[2]

    return full_name

def build_bracket(player_list, match_list, round_list, first_round_found, first_round, results):
    """ appropriately fills in bracket with winners moving on and byes """

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
                            print(y)
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

    return teams_array, results

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
                    match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
                        match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
                        match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
                        match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
                        match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
                        match_id = db.insert_unscored_tournament_match(player_one, player_two, tournament_id)
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
        round_id = db.insert_round(tournament_id, matches_array, bye_array, which_round)
    except:
        return errorpage(send_to="tournamentview", message="Could not create round.")

    # set the current round in the tounament info and session
    try:
        db.set_current_round(round_id, tournament_id)
    except:
        return errorpage(send_to="tournamentview", message="Could not save current round.")
    session["current_round"] = round_id

    

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
        tournament_info = db.select_current_tournament(sess)[0]
    except:
        return errorpage(send_to="/", message="Could not load tournament.")
    
    # get competitor info from database
    try:
        players = db.select_tournament_competitors(sess)
    except:
        return errorpage(send_to="/", message="Could not load players.")

    # get the current round id from the tournament info
    round_id = tournament_info[5]

    # get the round info
    try:
        round_info = db.select_round(round_id)
    except:
        return errorpage(send_to="/", message="Could not load round.")

    # returns players and tournament info to the route that called refresh
    return players, tournament_info, round_info


def verify_judge_account(user_name, judge_pw):
    """ verify judge username and password from database info """

    rows = db.select_judge(user_name)

    # check if the judge doesnt exist, or the given password doesnt hash
    if (len(rows) != 1) or not check_password_hash(rows[0]["pass_hash"], judge_pw):
        return errorpage(message="The username or password was not found.", send_to="login")
    
    return rows[0]['judge_id'], rows[0]["judge_name"]

def inactive_season_tournament():
    """ from all seasons and tournaments, returns only the ones that are no longer active """
    rows, cols = db.select_season_tournament()
    today = date.today()

    seasonarchive = []
    for each in rows:
        enddate = each[3] + datetime.timedelta(days=70)
        if (enddate < today):
            seasonarchive.append(each)

    tournamentarchive = []
    for each in cols:
        enddate = each["tournament_date"]  + datetime.timedelta(days=1)
        if (enddate < today):
            tournamentarchive.append(each)

    return seasonarchive, tournamentarchive

def active_season_tournament():
    """ from all seasons and tournaments, returns only the ones that are active """
    rows, cols = db.select_season_tournament()
    seasonarchive, tournamentarchive = inactive_season_tournament()

    for each in seasonarchive:
        rows.remove(each)
    for each in tournamentarchive:
        cols.remove(each)
    print(rows, cols)
    return rows, cols

def no_duplicate_judge(name):
    """ check database for a judge of the same name """

    rows = db.select_judge(name)
    if len(rows) > 0:
        return errorpage(send_to="newjudge", message="A judge account with this name already exists.")
    
    
def select_winner(match_id):
    """ returns winner id from match id """

    match = db.select_match_by_id(match_id)
    relevant = filter(lambda x: x in ['winner_id'], match)

    return relevant


def select_tournament_match(match_id):
    """ select player & winner info from database with match_id """

    match = db.select_match_by_id(match_id)
    relevant = [match['player_1_id'], match['player_2_id'], match['winner_id']]

    return relevant


def render_player_stats():
    each_discipline_player_list = []
    for discipline in disciplines:
        player_list = db.select_all_competitors()
        for each in player_list:
            player_id = each[0]
            output = db.select_competitor_average_games_by_discipline(player_id, discipline)
            average = output[0][0]
            games_played = output[0][1]
            games_won = db.select_competitor_wins_by_discipline(player_id, discipline)
            if (games_played == 0):
                win_rate = 0
            else:
                win_rate = round((games_won / games_played), 2)
            each.append(average)
            each.append(win_rate)
            each.append(games_played)
            each.append(discipline)
        each_discipline_player_list.append(player_list)
    all_discipline_player_list = db.select_all_competitors()
    for each in all_discipline_player_list:
        player_id = each[0]
        output = db.select_competitor_average_games(player_id)
        average = output[0][0]
        games_played = output[0][1]
        games_won = db.select_competitor_wins(player_id)
        if (games_played == 0):
            win_rate = 0
        else:
            win_rate = round((games_won / games_played), 2)
        each.append(average)
        each.append(win_rate)
        each.append(games_played)
        each.append("cumulative")
    each_discipline_player_list.append(all_discipline_player_list)

    return(each_discipline_player_list)