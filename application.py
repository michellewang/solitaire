from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

app.config["DEBUG"] = False

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///solitaire.db")

@app.route("/")
@login_required
def index():
    """Show instructions of game."""
    
    # check if user has old game
    game = db.execute("SELECT COUNT(*) FROM cardlist WHERE user_id=:user_id",
        user_id=session["user_id"])
    
    # if user has an existing game
    if not game[0]["COUNT(*)"] == 0:
        old_game = True
    else:
        old_game = False
    
    # get number of wins
    wins = db.execute("SELECT wins FROM users WHERE id=:id", id=session["user_id"])
    wins = wins[0]["wins"]
    
    return render_template("index.html", old_game=old_game, wins=wins)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("missing username")
        
        # ensure password was submitted
        elif not request.form.get("password1"):
            return apology("missing password")
        
        # ensure passwords match
        elif not request.form.get("password1") == request.form.get("password2"):
            return apology("passwords don't match")
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
            username=(request.form.get("username")).lower())
        
        # ensure username is not already taken
        if len(rows) == 1:
            return apology("username taken")
        
        # store username and hashed password into database
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
            username=(request.form.get("username")).lower(), hash=pwd_context.hash(request.form.get("password1")))
        
        # query database for username (again)
        rows = db.execute("SELECT * FROM users WHERE username = :username",
            username=(request.form.get("username")).lower())
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]
        
        # remember settings for this user
        db.execute("INSERT INTO settings (user_id) VALUES (:user_id)", user_id=session["user_id"])
        
        # success
        flash("Registered!")
        return redirect(url_for("index"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Change user settings."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # change cards per draw
        if not request.form.get("cards_per_draw") == "":
            db.execute("UPDATE settings SET cards_per_draw=:cards_per_draw WHERE user_id=:user_id",
                cards_per_draw=request.form.get("cards_per_draw"), user_id=session["user_id"])
            
            # success
            flash("Settings changed!")
            return redirect(url_for("index"))
        
        # if user did not submit anything
        return render_template("settings.html")
    
    # if user reached route via GET (as by clicking a link or via redirect)
    else:
        
        # get user's current setting (to preselect radio button)
        settings = db.execute("SELECT cards_per_draw FROM settings WHERE user_id=:user_id",
            user_id=session["user_id"])
        
        n = settings[0]["cards_per_draw"]
        
        return render_template("settings.html", n=n)

@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    """Play a Solitaire game"""
    
    # if user accessed page by submitting a form
    if request.method == "POST":
        
        # get move info
        icg = request.form.get("initial_cardgroup_id")
        ip = request.form.get("initial_position")
        ir = request.form.get("initial_row")
        
        fcg = request.form.get("final_cardgroup_id")
        fp = request.form.get("final_position")
        fr = request.form.get("final_row")
        
        # move card if allowed
        if not move_card(icg, ip, ir, fcg, fp, fr, session["user_id"]):
            flash("Illegal move")
        
        return "OK"
    
    else:
        
        # start new game if necessary
        if request.args.get("action") == "new":
            
            new_game(session["user_id"])
        
        # draw cards if necessary
        elif request.args.get("action") == "draw":
            
            # draw 3 cards
            draw_cards(session["user_id"])
        
        # get game info
        stack, acepiles, columns = get_game(session["user_id"])
        
        # check for win
        if game_won(session["user_id"]):
            flash("You won!")

        # render game
        return render_template("play.html",
            stack=stack, acepiles=acepiles, columns=columns)