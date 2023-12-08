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