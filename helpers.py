import csv
import urllib.request

from objects import Card, Pile, Column, Stack

from cs50 import SQL
from flask import redirect, render_template, request, session, url_for
from functools import wraps

db = SQL("sqlite:///solitaire.db")

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def generate_cards(user_id):
    """Creates a deck of 53 cards."""
    
    suits = ["c", "d", "h", "s"]
    ranks = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"]
    
    for suit in suits:
        
        if suit == "c" or suit == "s":
            color = "black"
        else:
            color = "red"
        
        for rank in ranks:
            
            db.execute("""INSERT INTO cards (value, suit, rank, color, user_id)
                VALUES (:value, :suit, :rank, :color, :user_id)""",
                value=(suit+rank), suit=suit, rank=rank, color=color, user_id=user_id)

def distribute_cards(deck, user_id):
    """Distributes a deck of 52 cards for a game of Solitaire."""
    
    # make 7 columns containing the appropriate amount of cards
    for i in range(7):
        
        for j in range(i + 1):
            
            # remove last card of deck
            card = deck.pop()
            
            # add card to column
            db.execute("""UPDATE cardlist SET card_id=:card_id
                WHERE cardgroup_id=2 AND position=:position AND row=:row AND user_id=:user_id""",
                card_id=card["id"], position=i, row=j, user_id=user_id)
            
            # flip last card of column
            if j == i:
                db.execute("""UPDATE cards SET name=:name WHERE id=:id""",
                    name=card["value"], id=card["id"])
                card["name"] = card["value"]
    
    
    # add remaining cards to stack
    for i in range(len(deck)):
        
        # remove last card from deck
        card = deck.pop()
        
        # put card on top of stack
        db.execute("""UPDATE cardlist SET card_id=:card_id
            WHERE cardgroup_id=0 AND position=0 AND row=:row AND user_id=:user_id""",
            card_id=card["id"], row=i, user_id=user_id)
    
    return

def initialize_cardlist(user_id):
    """Creates empty positions/indexes for one user in cardlist."""
    
    # left and right stacks
    for i in range(2):
        for j in range(24):
            
            db.execute("""INSERT INTO cardlist (cardgroup_id, position, row, user_id)
                VALUES (:cardgroup_id, :position, :row, :user_id)""",
                cardgroup_id=0, position=i, row=j, user_id=user_id)
    
    # acepiles
    for i in range(4):
        for j in range(13):
            
            db.execute("""INSERT INTO cardlist (cardgroup_id, position, row, user_id)
                VALUES (:cardgroup_id, :position, :row, :user_id)""",
                cardgroup_id=1, position=i, row=j, user_id=user_id)
    
    # columns:
    for i in range(7):
        for j in range(i + 13):
            db.execute("""INSERT INTO cardlist (cardgroup_id, position, row, user_id)
                VALUES (:cardgroup_id, :position, :row, :user_id)""",
                cardgroup_id=2, position=i, row=j, user_id=user_id)

def draw_cards(user_id):
    """Moves three cards from initial stack to final stack."""
    
    stacksize = db.execute("""SELECT COUNT(*) FROM cardlist
            WHERE cardgroup_id=0 AND position=0 AND card_id IS NOT NULL AND user_id=:user_id""",
            user_id=user_id)
    
    # move cards from right stack to left stack if left stack is empty
    if stacksize[0]["COUNT(*)"] == 0:
        
        stackcards = db.execute("""SELECT card_id FROM cardlist
            WHERE cardgroup_id=0 AND position=1 AND card_id IS NOT NULL AND user_id=:user_id
            ORDER BY row DESC""",
            user_id=user_id)
        
        for i, stackcard in enumerate(stackcards):
            
            # remove card from right
            db.execute("""UPDATE cardlist SET card_id=NULL WHERE card_id=:id""",
                id=stackcard["card_id"])
            
            # add card to new position
            db.execute("""UPDATE cardlist SET card_id=:id
                WHERE cardgroup_id=0 AND position=0 AND row=:i AND user_id=:user_id""",
                id=stackcard["card_id"], i=i, user_id=user_id)
            
            # flip back card
            db.execute("UPDATE cards SET name=:name WHERE id=:id",
                name="back", id=stackcard["card_id"])
    
    # get top card from right stack
    rightstacktop = db.execute("""SELECT card_id FROM cardlist
        WHERE cardgroup_id=0 AND card_id IS NOT NULL AND position=1 AND user_id=:user_id
        ORDER BY row DESC
        LIMIT 1""",
        user_id=user_id)
    
    # flip back top card
    if len(rightstacktop) == 1:
        db.execute("UPDATE cards SET name='back' WHERE id=:id", id=rightstacktop[0]["card_id"])
    
    # get number of cards per draw
    n = db.execute("SELECT cards_per_draw FROM settings WHERE user_id=:user_id", user_id=user_id)
    n = n[0]["cards_per_draw"]
    
    # draw n cards
    for i in range(n):
        
        # get last card of left stack
        card = db.execute("""SELECT card_id FROM cardlist
            WHERE cardgroup_id=0 AND position=0 AND card_id IS NOT NULL AND user_id=:user_id
            ORDER BY row DESC
            LIMIT 1""",
            user_id=user_id)
        
        # get size of right stack
        size = db.execute("""SELECT COUNT(*) FROM cardlist
            WHERE cardgroup_id=0 AND position=1 AND card_id IS NOT NULL AND user_id=:user_id""",
            user_id=user_id)
        
        if len(card) == 1:
            
            # flip last card
            if i == n - 1:
                db.execute("UPDATE cards SET name=value WHERE id=:id", id=card[0]["card_id"])
            
            # remove card from initial stack
            db.execute("""UPDATE cardlist SET card_id=NULL
                WHERE card_id=:card_id""",
                card_id=card[0]["card_id"])
            
            # add card to final stack
            db.execute("""UPDATE cardlist SET card_id=:card_id 
                WHERE cardgroup_id=0 AND position=1 AND row=:row AND user_id=:user_id""",
                card_id=card[0]["card_id"], row=size[0]["COUNT(*)"], user_id=user_id)
    
    return

def get_game(user_id):
    """Gets acepile cards and column cards from database."""
    
    stack = {}
    
    # get top card of right stack
    card = db.execute("""SELECT card_id FROM cardlist
        WHERE cardgroup_id=0 AND position=1 AND card_id IS NOT NULL AND user_id=:user_id
        ORDER BY row DESC
        LIMIT 1""",
        user_id=user_id)
    
    # if stack is empty
    if len(card) == 0:
        stack["right"] = list()
        stack["right"].append({"name": "blank"})
    
    # else get card name
    else:
        rightstacktop = db.execute("""SELECT cards.name, cards.value FROM cards WHERE id=:id""",
            id=card[0]["card_id"])
        
        # flip card if necessary
        if rightstacktop[0]["name"] == "back":
            stack["right"] = list()
            stack["right"].append({"name": rightstacktop[0]["value"]})
            db.execute("UPDATE cards SET name=value WHERE id=:id", id=card[0]["card_id"])
        else:
            stack["right"] = rightstacktop
    
    # determine if top card of left stack is "back" or "blank"
    card = db.execute("""SELECT card_id, row FROM cardlist
        WHERE cardgroup_id=0 AND position=0 AND card_id IS NOT NULL AND user_id=:user_id
        ORDER BY row DESC
        LIMIT 1""",
        user_id=user_id)
    
    if len(card) == 1:
        stack["left"] = "back"
    
    else:
        stack["left"] = "blank"
    
    # get top card of 4 acepiles
    acepiles = list()
    
    for i in range(4):
        acepile = db.execute("""SELECT cards.name FROM cardlist
            JOIN cards ON cards.id = cardlist.card_id
            WHERE cardlist.cardgroup_id = 1 AND cardlist.position = :position AND cardlist.user_id=:user_id
            ORDER BY row DESC
            LIMIT 1""",
            position=i, user_id=user_id)
        
        # add blank card if acepile is empty
        if len(acepile) == 0:
            acepile.append({"name": "blank"})
        
        acepiles.append(acepile[0])
    
    # get cards of 7 columns
    columns = list()
    
    for i in range(7):
        column = list()
        
        column = db.execute("""SELECT cards.name, cards.value, cards.id FROM cardlist
            JOIN cards ON cards.id=cardlist.card_id
            JOIN cardgroups ON cardgroups.id=cardlist.cardgroup_id
            WHERE cardgroup_id=2 AND position=:position AND cardlist.user_id=:user_id
            ORDER BY row""",
            position=i, user_id=user_id)
        
        if len(column) != 0:
            # flip last card of column
            db.execute("UPDATE cards SET name=value WHERE id=:id", id=column[len(column) - 1]["id"])
            column[len(column) - 1]["name"] = column[len(column) - 1]["value"]
        
        # empty column
        else:
            d = {"name": "blank"}
            column.append(d)
        
        columns.append(column)
    
    return stack, acepiles, columns

def move_card(icg, ip, ir, fcg, fp, fr, user_id):
    """Move card from one location to another."""
    
    # initial card if from stack
    if icg == "0":
        
        # right stack
        ip = 1
        
        # get size of stack
        stacksize = db.execute("""SELECT COUNT(*) FROM cardlist
            WHERE cardgroup_id=0 AND position=1 AND card_id IS NOT NULL AND user_id=:user_id""",
            user_id=user_id)
        
        # set initial row
        ir = stacksize[0]["COUNT(*)"] - 1
    
    # get card(s) to be moved
    cards = db.execute("""SELECT card_id FROM cardlist
        WHERE cardgroup_id=:icg AND position=:ip AND row>=:ir AND card_id IS NOT NULL AND user_id=:user_id
        ORDER BY row ASC""",
        icg=icg, ip=ip, ir=ir, user_id=user_id)
    
    # get top card (to verify if move is legal)
    top = cards[0]
    
    # get final card's row
    finalsize = db.execute("""SELECT COUNT(*) FROM cardlist
        WHERE cardgroup_id=:fcg AND position=:fp AND card_id IS NOT NULL AND user_id=:user_id""",
        fcg=fcg, fp=fp, user_id=user_id)
    
    # set final row
    fr = finalsize[0]["COUNT(*)"] - 1
    
    # adjust if necessary
    if fr < 0:
        fr = 0
    
    # get destination card
    dest = db.execute("""SELECT card_id FROM cardlist
    WHERE cardgroup_id=:fcg AND position =:fp AND row>=:fr AND card_id IS NOT NULL AND user_id=:user_id
    ORDER BY row ASC
    LIMIT 1""",
    fcg=fcg, fp=fp, fr=fr, user_id=user_id)
    
    # readjust fr
    if len(dest) == 0:
        dest_id = 0
        fr = -1;
    else:
        dest_id = dest[0]["card_id"]
    
    # remember wheter destination is acepile or column
    if fcg == "1":
        destination = "acepile"
    else:
        destination = "column"
    
    # check if move is legal
    if not legal_move(top["card_id"], dest_id, destination):
        return False
    
    for i, card in enumerate(cards, start=1):
        
        # remove card from initial location
        db.execute("""UPDATE cardlist SET card_id=NULL WHERE card_id=:id""",
            id=card["card_id"])
        
        # add card to new position
        db.execute("""UPDATE cardlist SET card_id=:id
            WHERE cardgroup_id=:fcg AND position=:fp AND row=(:fr + :i) AND user_id=:user_id""",
            id=card["card_id"], fcg=fcg, fp=fp, fr=fr, i=i, user_id=user_id)
    
    return True

def new_game(user_id):
    """Start a new game."""
    
    # check if existing game exists
    old_game = db.execute("SELECT COUNT(*) FROM cardlist WHERE user_id=:user_id",
        user_id=user_id)
    
    # user does not have existing cards and cardlist rows
    if old_game[0]["COUNT(*)"] == 0:
        initialize_cardlist(user_id)
        generate_cards(user_id)
    
    # user has played before
    else:
        db.execute("UPDATE cardlist SET card_id=NULL WHERE user_id=:user_id", user_id=user_id)
        db.execute("UPDATE cards SET name='back' WHERE id > 0 AND user_id=:user_id", user_id=user_id)
    
    # shuffle cards
    deck = db.execute("""SELECT * FROM cards WHERE id > 0 AND user_id=:user_id ORDER BY RANDOM()""",
        user_id=user_id)
    
    # distribute cards into stack, acepiles and columns
    distribute_cards(deck, user_id)
    
    # get number of cards per draw
    n = db.execute("SELECT cards_per_draw FROM settings WHERE user_id=:user_id", user_id=user_id)
    
    # clear win info for current game
    db.execute("UPDATE users SET current_game_won='False' WHERE id=:id", id=user_id)
    
    # draw n cards
    draw_cards(user_id)

def legal_move(top_id, dest_id, destination):
    """Check if user is performing a legal move."""
    
    # get top card info
    top = db.execute("SELECT * FROM cards WHERE id=:id", id=top_id)
    top = top[0]
    
    # get dest card info
    if not dest_id == 0:
        dest = db.execute("SELECT * FROM cards WHERE id=:id", id=dest_id)
        dest = dest[0]
    
    # if user is trying to move a card to an acepile
    if destination == "acepile":
        
        # get location of top card
        location = db.execute("""SELECT cardgroup_id, position, row, user_id FROM cardlist
            WHERE card_id=:card_id""",
            card_id=top["id"])
        location = location[0]
        
        # get number of cards to be moved if top card is from column
        if location["cardgroup_id"] == 2:
            
            size = db.execute("""SELECT COUNT(*) FROM cardlist
                WHERE cardgroup_id=2 AND position=:position AND row>:row AND card_id IS NOT NULL AND user_id=:user_id""",
                position=location["position"], row=location["row"], user_id=location["user_id"])
            
            # make sure user cannot move more than one card to acepile
            if not size[0]["COUNT(*)"] == 0:
                return False
        
        # if acepile is empty
        if dest_id == 0:
            if not top["rank"] == "01":
                return False
        
        # if acepile is not empty
        else:
            if not top["suit"] == dest["suit"]:
                return False
            elif not int(top["rank"]) == int(dest["rank"]) + 1:
                return False
    
    # if user is trying to move a card to a column
    else:
        
        # if column is empty
        if dest_id == 0:
            if not top["rank"] == "13":
                return False
        
        # if acepile is not empty
        else:
            if top["color"] == dest["color"]:
                return False
            elif not int(top["rank"]) == int(dest["rank"]) - 1:
                return False
    
    return True

def game_won(user_id):
    """Returns True if game is won else False."""
    
    # get all cards
    cards = db.execute("""SELECT COUNT(*) FROM cardlist
        JOIN cards ON cardlist.card_id=cards.id
        WHERE cards.name!="back" AND card_id IS NOT NULL AND cardlist.user_id=:user_id""",
        user_id=user_id)
    
    # user has not won game
    if cards[0]["COUNT(*)"] != 52:
        return False
    
    # user won game
    won_data = db.execute("SELECT current_game_won, wins FROM users WHERE id=:id",
        id=user_id)
    
    # user won game for the first time
    if won_data[0]["current_game_won"] == "False":
        db.execute("UPDATE users SET current_game_won='True', wins=:wins WHERE id=:id",
            wins=(won_data[0]["wins"]+1), id=user_id)
    
    return True
