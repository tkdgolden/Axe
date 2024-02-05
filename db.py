# to connect to postgresql
import os
import psycopg2
# to be able to run sql code in the app
import psycopg2.extras
# to hash and unhash judge passwords
from werkzeug.security import generate_password_hash
import helpers


def db_connect():

    which_db = "heroku"

    if which_db == "local":
        SECRET = os.environ["DATABASE_PATH"]
        print("local db access")
    elif which_db == "heroku":
        SECRET = os.environ["DATABASE_URL"]
        print("Heroku db access")

    try:
        global conn
        conn = psycopg2.connect(SECRET)
    except:
        print("ERROR connecting to db")
    global CUR
    CUR = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


def select_season_tournament():
    """ database call for ALL seasons and tournaments """

    CUR.execute("""SELECT * FROM seasons""")
    rows = CUR.fetchall()
    CUR.execute("""SELECT * FROM tournaments""")
    cols = CUR.fetchall()

    return rows, cols


def select_judge(user_name):
    """ return judge row from username """

    # pull judge accounts from database
    CUR.execute("""SELECT * FROM judges WHERE judge_name = %(user_name)s""", {'user_name': user_name})

    return CUR.fetchall()


def select_match_by_id(match_id):
    """ return match by id """

    CUR.execute(""" SELECT * FROM matches WHERE match_id = %(match_id)s """, {'match_id' : match_id})

    return CUR.fetchone()


def select_matches_by_season(season_id):
    """ selects matches from current season """

    CUR.execute("""SELECT * FROM matches JOIN laps ON laps.lap_id = matches.lap_id JOIN quarters ON quarters.quarter_id = laps.quarter_id JOIN seasons ON seasons.season_id = quarters.season_id WHERE seasons.season_id = %(season_id)s""", {'season_id':season_id})

    return CUR.fetchall()


def select_matches_by_lap_quarter_season(lap_count, quarter_month, season_id):
    """ selects matches info from current lap, need quarter and season id to get lap """

    CUR.execute(""" SELECT * FROM matches WHERE lap_id = (SELECT lap_id FROM laps WHERE counter = %(lap_count)s AND quarter_id = (SELECT quarter_id FROM quarters WHERE season_id = %(season_id)s AND month = %(quarter_month)s)) """, {'lap_count': lap_count, 'season_id': season_id, 'quarter_month': quarter_month})

    return CUR.fetchall()


def select_lap_id_by_lap_quarter_season(lap_count, quarter_month, season_id):
    """ selects lap id from current lap, need quarter and season id """

    CUR.execute("""SELECT lap_id FROM laps WHERE counter = %(lap_count)s AND quarter_id = (SELECT quarter_id FROM quarters WHERE season_id = %(season_id)s AND month = %(quarter_month)s) """, {'lap_count': lap_count, 'season_id': season_id, 'quarter_month': quarter_month})

    return CUR.fetchone()


def save_pw(name, pw):
    """ create password hash and save it to the database """

    pwhash = generate_password_hash(pw)
    CUR.execute("""INSERT INTO judges(judge_name, pass_hash) VALUES (%(name)s, %(pwhash)s)""", {'name': name, 'pwhash': pwhash})

    conn.commit()


def no_duplicate_competitor(fname, lname):
    """ check database for a competitor of the same name """

    CUR.execute("""SELECT * FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname': fname, 'lname': lname})
    rows = CUR.fetchall()
    if len(rows) > 0:
        return helpers.errorpage(send_to="newcompetitor", message="A competitor with this name already exists.")
    

def save_competitor(fname, lname):
    """ save new competitor's first and last name to database """

    CUR.execute("""INSERT INTO competitors (competitor_first_name, competitor_last_name) VALUES (%(fname)s, %(lname)s)""", {'fname': fname, 'lname': lname})
    conn.commit()


def no_duplicate_season(season, year_of):
    """ check database for a season of the same season and year"""

    CUR.execute("""SELECT season_id FROM seasons WHERE season = %(season)s AND yearof = %(year_of)s""", {'season': season, 'year_of': year_of})
    list = CUR.fetchall()
    if len(list) > 0:
        return helpers.errorpage(send_to="newseason", message="A {season} {year_of} season already exists.".format(season=season, year_of=year_of))
    

def save_season(season, year_of, start_date):
    """ save new season info to database """

    CUR.execute("""INSERT INTO seasons (season, yearof, startdate) VALUES (%(season)s, %(year_of)s, %(start_date)s)""", {'season': season, 'year_of': year_of, 'start_date': start_date})
    conn.commit()
    

def select_current_season(sess):
    """ selects full db row for current season """

    CUR.execute("""SELECT * FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})
    
    return CUR.fetchall()
    

def select_season_competitors(sess):
    """ selects all competitors enrolled in current season """

    CUR.execute("""SELECT * FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE season_id = %(sess)s""", {'sess':sess})

    return CUR.fetchall()


def select_lap_competitors(lap):
    """ selects all competitors who participated in current lap """

    CUR.execute("""SELECT * FROM competitors LEFT JOIN matches ON competitors.competitor_id = matches.player_1_id LEFT JOIN matches ON competitors.competitor_id = matches.player_2_id WHERE matches.lap_id = %(lap)s""", {'lap': lap})

    return CUR.fetchall()


def select_competitor_by_id(id):
    """ selects row of competitor by id """

    CUR.execute("""SELECT * FROM competitors WHERE competitor_id = %(id)s""", {'id':id})

    return CUR.fetchall()[0]


def insert_unscored_season_match(playerA, playerB, lap_id):
    """ insert player ids and season into an otherwise empty new match, returns match_id """

    CUR.execute("""INSERT INTO matches (player_1_id, player_2_id, lap_id) VALUES (%(playerA)s, %(playerB)s, %(lap_id)s) RETURNING match_id""", {'playerA': playerA, 'playerB': playerB, 'lap_id': lap_id})
    match = CUR.fetchall()
    conn.commit()

    return match[0][0]


def select_season_discipline(sess):
    """ returns discipline from season id """

    CUR.execute("""SELECT discipline FROM seasons WHERE season_id = %(sess)s""", {'sess':sess})

    return CUR.fetchall()


def select_tournament_discipline(sess):
    """ returns discipline from tournament id """

    CUR.execute("""SELECT discipline FROM tournaments WHERE tournament_id = %(sess)s""", {'sess':sess})

    return CUR.fetchall()


def insert_completed_match(winner, pAtotal, pBtotal, discipline, judge, ts, match_id):
    """ insert completed match info to database """

    CUR.execute("""UPDATE matches SET winner_id = %(winner)s, player1total = %(pAtotal)s, player2total = %(pBtotal)s, discipline = %(discipline)s, judge_id = %(judge)s, dt = %(ts)s WHERE match_id = %(match_id)s""", {'winner': winner, 'pAtotal': pAtotal, 'pBtotal': pBtotal, 'discipline': discipline, 'judge': judge, 'ts': ts, 'match_id': match_id})
    conn.commit()


def insert_player_scores(player, match_id, qt, sequence, tone, ttwo, tthree, tfour, tfive, tsix, tseven, teight, total, win):
    """ insert player scores into database """

    CUR.execute("""INSERT INTO scores (competitor_id, match_id, quick_points, seq, throw1, throw2, throw3, throw4, throw5, throw6, throw7, throw8, total, won) VALUES (%(player)s, %(match_id)s, %(qt)s, %(sequence)s, %(tone)s, %(ttwo)s, %(tthree)s, %(tfour)s, %(tfive)s, %(tsix)s, %(tseven)s, %(teight)s, %(total)s, %(win)s)""", {'player': player, 'match_id': match_id, 'qt': qt, 'sequence': sequence, 'tone': tone, 'ttwo': ttwo, 'tthree': tthree, 'tfour': tfour, 'tfive': tfive, 'tsix': tsix, 'tseven': tseven, 'teight': teight, 'total': total, 'win': win})
    conn.commit()


def no_duplicate_tournament(name, discipline, date):
    """ check database for a tournament of the same name, discipline, and date """

    CUR.execute("""SELECT tournament_id FROM tournaments WHERE tournament_name = %(name)s AND discipline = %(discipline)s AND tournament_date = %(date)s""", {'name': name, 'discipline': discipline, 'date': date})

    return CUR.fetchall()
    

def save_tournament(name, discipline, date, double_elimination=False):
    """ save tournament info to database """

    CUR.execute("""INSERT INTO tournaments(tournament_name, discipline, tournament_date, double_elimination) VALUES(%(name)s, %(discipline)s, %(date)s, %(double_elimination)s)""", {'name': name, 'discipline': discipline, 'date': date, 'double_elimination': double_elimination})
    conn.commit()


def select_current_tournament(tournament_id):
    """ select row from tournaments from tournament_id """

    CUR.execute("""SELECT * FROM tournaments WHERE tournament_id = %(tournament_id)s""", {'tournament_id':tournament_id})
    cols = CUR.fetchall()
    if len(cols) != 1:
        return helpers.errorpage(send_to="/", message="You must select a valid tournament.")
    
    return cols


def select_tournament_competitors(tournament_id):
    """ select competitor id, first and last name where enrolled in tournament by tournament id """

    CUR.execute("""SELECT competitors.competitor_id, competitor_first_name, competitor_last_name FROM competitors JOIN enrollment ON competitors.competitor_id = enrollment.competitor_id WHERE tournament_id = %(tournament_id)s""", {'tournament_id':tournament_id})

    return CUR.fetchall()


def select_round(round_id):
    """ select row by round id """

    CUR.execute("""SELECT * FROM rounds WHERE round_id = %(round_id)s""", {'round_id': round_id})

    return CUR.fetchall()


def sort_players(player_ids):
    """ returns list of player ids sorted high to low by average score """

    CUR.execute("""SELECT competitor_id FROM scores WHERE competitor_id = ANY(%(playerids)s) GROUP BY competitor_id ORDER BY AVG(COALESCE(total, 0)) DESC""", {'playerids':player_ids})
    rows = CUR.fetchall()
    sorted_players = []
    for each in rows:
        sorted_players.append(each[0])
    for each in player_ids:
        if each not in sorted_players:
            sorted_players.append(each)

    return sorted_players


def set_enrollment_false(tournament_id):
    """ sets tournament enrollment to false in database """

    CUR.execute("""UPDATE tournaments SET enrollment_open = FALSE WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournament_id})


def insert_unscored_tournament_match(player_one, player_two, tournament_id):
    """ insert player ids and season into an otherwise empty new match, returns match_id """

    CUR.execute("""INSERT INTO matches (player_1_id, player_2_id, tournament_id) VALUES (%(player_one)s, %(player_two)s, %(tournament_id)s) RETURNING match_id""", {'player_one': player_one, 'player_two': player_two, 'tournament_id': tournament_id})
    conn.commit()

    return CUR.fetchall()[0][0]


def insert_round(tournament_id, matches_array, bye_array, which_round):
    """ inserts new round in tournament """

    CUR.execute("""INSERT INTO rounds (tournament_id, matches, round_id, bye_competitors, which_round) VALUES (%(tournament_id)s, %(matches_array)s, nextval('round_increment'), %(bye_array)s, %(which_round)s) RETURNING round_id""", {'tournament_id': tournament_id, 'matches_array': matches_array, 'bye_array': bye_array, 'which_round': which_round})
    conn.commit()

    return CUR.fetchall()[0][0]


def set_current_round(round_id, tournament_id):
    """ updates tournament table's current round value """

    CUR.execute("""UPDATE tournaments SET current_round = %(round_id)s WHERE tournament_id = %(tournament_id)s""", {'round_id': round_id, 'tournament_id': tournament_id})
    conn.commit()


def get_previous_round(tournament_id):
    """ retrieves tournament's current round """

    CUR.execute("""SELECT current_round FROM tournaments WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournament_id})

    return CUR.fetchone()[0]


def get_round_info(round_id):
    """ returns row for round by round id """

    CUR.execute("""SELECT * FROM rounds WHERE round_id = %(round_id)s""", {'round_id': round_id})

    return CUR.fetchone()


def select_season(season_id):
    """ returns season row by season id """

    CUR.execute("""SELECT * FROM seasons WHERE season_id = %(season_id)s""", {'season_id':season_id})

    return CUR.fetchone()


def select_tournament(tournament_id):
    """ returns tournament row by tournament id """
    
    CUR.execute("""SELECT * FROM tournaments WHERE tournament_id = %(tournament_id)s""", {'tournament_id':tournament_id})

    return CUR.fetchall()


def select_competitor_by_name(fname, lname):
    """ returns competitor_id by competitor first and last name """

    CUR.execute("""SELECT competitor_id FROM competitors WHERE competitor_first_name = %(fname)s AND competitor_last_name = %(lname)s""", {'fname':fname, 'lname':lname})

    return CUR.fetchall()


def select_competitor_seasons(competitor_id):
    """ returns season ids where competitor is enrolled by competitor id """

    CUR.execute("""SELECT season_id FROM enrollment WHERE competitor_id = %(competitor_id)s""", {'competitor_id':competitor_id})

    return CUR.fetchall()


def insert_enrollment_season(competitor_id, season_id):
    """ enrolls a competitor in a season by competitor id and season id """

    CUR.execute("""INSERT INTO enrollment (competitor_id, season_id) VALUES (%(competitor_id)s, %(season_id)s)""", {'competitor_id':competitor_id, 'season_id':season_id})
    conn.commit()


def select_competitor_tournaments(competitor_id):
    """ returns tournament ids where competitor is enrolled by competitor_id """

    CUR.execute("""SELECT tournament_id FROM enrollment WHERE competitor_id = %(competitor_id)s""", {'competitor_id':competitor_id})

    return CUR.fetchall()


def insert_enrollment_tournament(competitor_id, tournament_id):
    """ enrolls a competitor in a tournament by competitor id and tournament id """

    CUR.execute("""INSERT INTO enrollment (competitor_id, tournament_id) VALUES (%(competitor_id)s, %(tournament_id)s)""", {'competitor_id':competitor_id, 'tournament_id':tournament_id})
    conn.commit()


def select_all_competitors():
    """ select all from competitors table """

    CUR.execute("""SELECT * FROM competitors""")

    return CUR.fetchall()


def select_competitor_average_games(player_id):
    """ returns player average score by player id """

    CUR.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores WHERE competitor_id = %(player_id)s""", {'player_id':player_id})

    return CUR.fetchall()


def select_competitor_average_games_by_discipline(player_id, discipline):
    """ returns player average score for a given discipline by player id """

    CUR.execute("""SELECT ROUND(AVG(scores.total), 2), COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id WHERE scores.competitor_id = %(player_id)s AND matches.discipline ILIKE %(discipline)s""", {'player_id':player_id, 'discipline':discipline})

    return CUR.fetchall()


def select_competitor_stats_by_discipline(discipline):
    """ returns player name, average, number of games and number of wins by discipline """

    CUR.execute("""SELECT competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name, ROUND(AVG(scores.total), 2), COUNT(*), COUNT(*) FILTER (WHERE scores.won = true) FROM scores LEFT JOIN matches ON scores.match_id = matches.match_id LEFT JOIN competitors ON scores.competitor_id = competitors.competitor_id WHERE matches.discipline ILIKE %(discipline)s GROUP BY competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name""", {'discipline':discipline})

    return CUR.fetchall()


def select_cumulative_competitor_stats():
    """ returns player name, average, cumulative number of games and number of wins """

    CUR.execute("""SELECT competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name, ROUND(AVG(scores.total), 2), COUNT(*), COUNT(*) FILTER (WHERE scores.won = true) FROM scores LEFT JOIN matches ON scores.match_id = matches.match_id LEFT JOIN competitors ON scores.competitor_id = competitors.competitor_id GROUP BY competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name""")

    return CUR.fetchall()


def select_competitor_stats_by_lap(lap_id):
    """ returns player name, average, number of games and number of wins by lap """

    CUR.execute("""SELECT competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name, ROUND(AVG(scores.total), 2), COUNT(*), COUNT(*) FILTER (WHERE scores.won = true) FROM scores LEFT JOIN matches ON scores.match_id = matches.match_id LEFT JOIN competitors ON scores.competitor_id = competitors.competitor_id WHERE matches.lap_id = %(lap_id)s GROUP BY competitors.competitor_id, competitors.competitor_first_name, competitors.competitor_last_name""", {'lap_id':lap_id})

    return CUR.fetchall()


def select_competitor_season_average(player_id, season_id):
    """ returns player average season score by player id """

    CUR.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id INNER JOIN laps ON laps.lap_id = matches.lap_id INNER JOIN quarters ON quarters.quarter_id = laps.quarter_id INNER JOIN seasons ON seasons.season_id = quarters.season_id WHERE scores.competitor_id = %(player_id)s AND seasons.season_id = %(season_id)s""", {'player_id': player_id, 'season_id': season_id})

    return CUR.fetchall()


def select_competitor_lap_average(player_id, lap_id):
    """ returns player average lap score by player_id """

    CUR.execute("""SELECT ROUND(AVG(total), 2), COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id WHERE scores.competitor_id = %(player_id)s AND matches.lap_id = %(lap_id)s""", {'player_id': player_id, 'lap_id': lap_id})

    return CUR.fetchall()


def select_competitor_wins(player_id):
    """ returns number of games a player has won """

    CUR.execute("""SELECT COUNT(*) FROM scores WHERE competitor_id = %(player_id)s AND won = true""", {'player_id':player_id})

    return CUR.fetchall()[0][0]


def select_competitor_wins_by_discipline(player_id, discipline):
    """ returns number of games a player has won within a given discipline """

    CUR.execute("""SELECT COUNT(*) FROM scores JOIN matches ON scores.match_id = matches.match_id WHERE competitor_id = %(player_id)s AND scores.won = true AND matches.discipline ILIKE %(discipline)s""", {'player_id':player_id, 'discipline':discipline})

    return CUR.fetchall()[0][0]


def select_competitor_season_wins(player_id, season_id):
    """ returns number of games a player has won in a given season """

    CUR.execute("""SELECT COUNT(*) FROM matches INNER JOIN laps ON laps.lap_id = matches.lap_id INNER JOIN quarters ON quarters.quarter_id = laps.quarter_id INNER JOIN seasons ON seasons.season_id = quarters.season_id WHERE matches.winner_id = %(player_id)s AND seasons.season_id = %(season_id)s""", {'player_id': player_id, 'season_id': season_id})

    return CUR.fetchall()[0][0]

def select_competitor_lap_wins(player_id, lap_id):
    """ returns number of games a player has won in a given lap """

    CUR.execute("""SELECT COUNT(*) FROM matches WHERE winner_id = %(player_id)s AND lap_id = %(lap_id)s""", {'player_id': player_id, 'lap_id': lap_id})

    return CUR.fetchall()[0][0]


def select_season_quarters(season_id):
    """ returns quarter info for a given season id """

    CUR.execute(""" SELECT * FROM quarters WHERE season_id = %(season_id)s """, {'season_id': season_id})

    return CUR.fetchall()


def select_season_laps(season_id):
    """ returns lap info for a given season id """

    CUR.execute(""" SELECT * FROM laps INNER JOIN quarters ON quarters.quarter_id = laps.quarter_id WHERE quarters.season_id = %(season_id)s ORDER BY laps.start_date DESC""", {'season_id': season_id})

    return CUR.fetchall()


def select_competitor_matches(player_id):
    """ returns match info (players, winner, scores) for each match the player has been in by player id """

    CUR.execute("""SELECT * FROM matches WHERE (player_1_id = %(player_id)s OR player_2_id = %(player_id)s) AND winner_id IS NOT NULL ORDER BY dt DESC""", {'player_id': player_id})
    matches = CUR.fetchall()
    list_matches = []
    for each in matches:
        each_dict = dict(each)
        p1 = each['player_1_id']
        CUR.execute(""" SELECT * FROM competitors WHERE (competitor_id = %(p1)s ) """, {'p1': p1})
        p1_name = CUR.fetchone()
        each_dict['player_1_name'] = f"{p1_name['competitor_first_name']} {p1_name['competitor_last_name']}"
        p2 = each['player_2_id']
        CUR.execute(""" SELECT * FROM competitors WHERE (competitor_id = %(p2)s ) """, {'p2': p2})
        p2_name = CUR.fetchone()
        each_dict['player_2_name'] = f"{p2_name['competitor_first_name']} {p2_name['competitor_last_name']}"
        list_matches.append(each_dict)


    return list_matches


def select_tournament_matches(tournament_id):
    """ returns match info (match id, players, winner, scores) for each match in the tournament by tournament id """

    CUR.execute("""SELECT match_id, player_1_id, player_2_id, winner_id, player1total, player2total FROM matches WHERE tournament_id = %(tournament_id)s""", {'tournament_id':tournament_id})

    return CUR.fetchall()


def select_tournament_rounds(tournament_id):
    """ returns rounds by tournament id """

    CUR.execute("""SELECT * FROM rounds WHERE tournament_id = %(tournament_id)s""", {'tournament_id': tournament_id})

    return CUR.fetchall()


def select_season_matches(season_id):
    """ returns match info (players, winner, scores) from all matches in season by season id """

    CUR.execute("""SELECT matches.match_id, matches.player_1_id, matches.player_2_id, matches.winner_id, matches.discipline, matches.dt, matches.player1total, matches.player2total FROM matches LEFT JOIN laps ON matches.lap_id = laps.lap_id INNER JOIN quarters ON laps.quarter_id = quarters.quarter_id INNER JOIN seasons ON quarters.season_id = seasons.season_id WHERE seasons.season_id = %(season_id)s AND matches.winner_id IS NOT NULL ORDER BY matches.dt ASC""", {'season_id':season_id})

    return CUR.fetchall()


def select_lap_matches(lap_id):
    """ returns match info (players, winner, scores) from all matches in a lap by lap_id """

    CUR.execute("""SELECT match_id, player_1_id, player_2_id, winner_id, discipline, dt, player1total, player2total FROM matches WHERE lap_id = %(lap_id)s AND winner_id IS NOT NULL ORDER BY dt DESC""", {'lap_id':lap_id})

    return CUR.fetchall()


def select_scores_by_player_id_match_id(player_id, match_id):
    """ returns score info from scores by player and match ids """

    CUR.execute(""" SELECT * FROM scores WHERE competitor_id = %(player_id)s AND match_id = %(match_id)s """, {'player_id': player_id, 'match_id': match_id})

    return CUR.fetchall()


def select_quarter_id_by_month_and_season_id(quarter_month, season_id):
    """ returns quarter_id if one exists for the quarter_month and season_id """

    CUR.execute(""" SELECT quarter_id FROM quarters WHERE month = %(quarter_month)s AND season_id = %(season_id)s """, {'quarter_month': quarter_month, 'season_id': season_id})

    return CUR.fetchone()


def insert_current_quarter(quarter_month, season_id, date):
    """creates new quarter for the selected season """

    CUR.execute(""" INSERT INTO quarters (month, season_id, start_date) VALUES (%(quarter_month)s, %(season_id)s, %(date)s)""", {'quarter_month': quarter_month, 'season_id':season_id, 'date': date})

    conn.commit()


def select_lap_id_by_lap_quarter(lap_count, quarter_id):
    """ selects lap id from current lap count and quarter id"""

    CUR.execute("""SELECT lap_id FROM laps WHERE counter = %(lap_count)s AND quarter_id = %(quarter_id)s """, {'lap_count': lap_count, 'quarter_id': quarter_id})

    return CUR.fetchone()


def insert_current_lap(lap_count, start_date, quarter_id, discipline):
    """ creates a new lap for the selected quarter and season """

    CUR.execute(""" INSERT INTO laps(counter, start_date, quarter_id, discipline) VALUES(%(lap_count)s, %(start_date)s, %(quarter_id)s, %(discipline)s) """, {'lap_count': lap_count, 'start_date': start_date, 'quarter_id': quarter_id, 'discipline': discipline})

    conn.commit()


def select_match_discipline(match_id):
    """returns the discipline of a match"""

    CUR.execute("""SELECT laps.discipline FROM laps JOIN matches ON matches.lap_id = laps.lap_id WHERE matches.match_id = %(match_id)s """, {'match_id': match_id})

    return CUR.fetchone()