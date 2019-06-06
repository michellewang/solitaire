from cs50 import SQL
db = SQL("sqlite:///solitaire.db")

class Card():
    """Represents a playing card."""
    
    def __init__(self, suit, rank):
        """Stores Card into database."""
        
        # blank card
        if suit == "" or rank == "":
            db.execute("""INSERT INTO cards (id, name, value, suit, rank, color, visible)
            VALUES (:id, :name, :value, :suit, :rank, :color, :visible)""",
            id=0, name="blank", value="", suit="", rank="", color="", visible="True")
        
        # non-blank card
        else:
            if suit == "c" or suit == "s":
                color = "black"
            elif suit == "d" or suit == "h":
                color = "red"
            
            db.execute("""INSERT INTO cards (name, value, suit, rank, color, visible)
                VALUES (:name, :value, :suit, :rank, :color, :visible)""",
                name="back", value=(suit + rank), suit=suit, rank=rank, color=color, visible="False")

class Pile():
    """Represents a pile of cards."""
    
    def __init__(self, n):
        """Initializes an empty pile."""
        
        self.name = "acepile" + str(n)
        self.top = Card("", "")
        self.size = 0
    
    def add_card(self, card):
        """Adds card to acepile if possible."""
        
        # replace existing card with new card if legal
        if ((self.top == "blank" and card.rank == "01") or 
            (int(card.rank) == int(self.top.rank) + 1 and card.suit == self.top.suit)):
            
            self.card = card
            
            self.card.location = self.top.name
            self.card.position = self.size
            self.size += 1
            
            return card
        
        # illegal move
        else:
            return ""

class Column():
    """Represents a column of flipped and/or unflipped cards."""
    
    def __init__(self, n):
        """Initializes empty column."""
        
        self.cards = list()
        self.name = "column" + str(n)
        self.size = 0
    
    def add_card(self, card):
        """Add card to end of column."""
        
        self.cards.append(card)
        self.cards[self.size].location = self.name
        self.cards[self.size].position = self.size
        self.size += 1

class Stack():
    """Represents a stack of cards."""
    
    def __init__(self):
        """Initializes empty stack."""
        
        self.name = "stack"
        self.cards = list()
        self.size = 0
    
    def add_card(self, card):
        """Adds card to top of stack."""
        
        self.cards.append(card)
        self.cards[self.size].location = self.name
        self.cards[self.size].position = self.size
        self.size += 1
    
    def remove_card(self, index):
        """Removes one card from stack."""
        
        card = self.cards.pop(index)
        self.size -= 1
        
        return card
    
    def draw(self):
        """Draws the top card of stack."""
        
        # make sure stack is not empty
        if self.size > 0:
            
            # draw top card
            card = self.cards[self.size - 1]
            
            return card
        
        else:
            return
