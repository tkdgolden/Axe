import json
from flask import render_template, session
from functools import wraps
import db

possible_scores = [0,1,2,3,4,6,12]

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
        

def determine_discipline_season_or_tournament():
    """ determine season or tournament, get discipline value from database """

    if session["selected_season"]:
        sess = session["selected_season"]
        cols = db.select_season_discipline(sess)
        view = 'season'
    else:
        sess = session["selected_tournament"]
        cols = db.select_tournament_discipline(sess)
        view = 'tournament'
    discipline = cols[0]

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