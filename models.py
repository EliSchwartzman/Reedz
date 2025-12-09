# Define the structure of Users, Bets, and Predictions.

class User:
    """
    User entity representing platform accounts with authentication and balance.
    
    Fields:
        user_id: Unique database identifier (None for new users)
        username: Unique login identifier
        password: bcrypt-hashed password (never store plaintext)
        email: Contact email for password resets
        reedz_balance: Virtual currency for betting rewards
        role: Access level ('Admin' or 'Member')
        created_at: Account creation timestamp
    """
    def __init__(
        self, 
        user_id, 
        username, 
        password, 
        email, 
        reedz_balance, 
        role, 
        created_at
        ): # __init__ method sets up the User object with its attributes
        
        self.user_id = user_id              # Primary key (int/None)
        self.username = username            # Unique string identifier
        self.password = password            # bcrypt hash (never plaintext)
        self.email = email                  # Valid email address
        self.reedz_balance = reedz_balance  # Integer currency balance (starts at 0)
        self.role = role                    # 'Admin' or 'Member'
        self.created_at = created_at        # datetime object


class Prediction:
    """
    Individual user prediction on a specific bet.
    
    Links users to bets with their predicted answer.
    
    Fields:
        prediction_id: Unique database identifier
        user_id: Foreign key to User
        bet_id: Foreign key to Bet
        prediction: String prediction value (flexible for different answer_types)
        created_at: Prediction timestamp
    """
    def __init__(
        self,
        prediction_id, 
        user_id, 
        bet_id, 
        prediction, 
        created_at
        ): 
        # __init__ method sets up the Prediction object with its attributes

        self.prediction_id = prediction_id  # Primary key (auto-generated)
        self.user_id = user_id              # References User.user_id
        self.bet_id = bet_id                # References Bet.bet_id
        self.prediction = prediction        # str: user's answer/guess
        self.created_at = created_at        # datetime when predicted


class Bet:
    """
    Betting market/prediction event managed by admins.
    
    Complete lifecycle: open → closed → resolved → archived.
    
    Fields:
        bet_id: Unique database identifier
        created_by_user_id: Admin who created the bet
        title: Short human-readable name
        description: Detailed event information
        answer_type: 'number', 'text', 'yes/no', etc.
        is_open: True if accepting predictions
        is_resolved: True if correct_answer set
        created_at: Bet creation timestamp
        close_at: Betting deadline timestamp
        resolved_at: When admin set final answer
        correct_answer: Official resolution (set by admin)
        is_closed: True if past close_at or manually closed
    """
    def __init__(
        self,
        bet_id,
        created_by_user_id,
        title,
        description,
        answer_type,
        is_open,
        is_resolved,
        created_at,
        close_at,
        resolved_at=None,      
        correct_answer=None,   
        is_closed=False,       
    ): # __init__ method sets up the Bet object with its attributes 
        
        self.bet_id = bet_id               # Primary key (auto-generated)
        self.created_by_user_id = created_by_user_id  # Admin User.user_id
        self.title = title                 # Short name (e.g., "Will it snow?")
        self.description = description     # Full details
        self.answer_type = answer_type     # Validation type for predictions
        self.is_open = is_open             # Accepting predictions?
        self.is_resolved = is_resolved     # Has official answer?
        self.created_at = created_at       # When bet created
        self.close_at = close_at           # Betting deadline
        self.resolved_at = resolved_at     # When resolved (nullable)
        self.correct_answer = correct_answer  # Official answer (nullable)
        self.is_closed = is_closed         # Manually closed or expired
