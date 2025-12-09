import bcrypt  # Secure password hashing library (bcrypt algorithm)
import supabase_db  # Module for Supabase database operations (get_user_by_username, etc.)
from models import User  # Pydantic/dataclass model representing a User with fields like role, password


def hash_password(password: str) -> str:
    """
    Generates a secure bcrypt hash for the given plaintext password.
    
    Args:
        password (str): Plaintext password to hash.
    
    Returns:
        str: Base64-encoded bcrypt hash of the password.
    """
    # Encode password to bytes and generate salted hash using bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    """
    Verifies if the provided plaintext password matches the stored bcrypt hash.
    
    Args:
        password (str): Plaintext password to verify.
        hashed (str): Stored bcrypt hash to compare against.
    
    Returns:
        bool: True if passwords match, False otherwise.
    """
    # Compares encoded plaintext entry against stored hash
    return bcrypt.checkpw(password.encode(), hashed.encode())


def authenticate(username: str, password: str):
    """
    Authenticates a user by username and password against the database.
    
    Retrieves user by username, checks password hash, and returns user if valid.
    
    Args:
        username (str): User's username.
        password (str): User's plaintext password.
    
    Returns:
        User or None: Authenticated User object or None if invalid credentials.
    """
    # Get the user records from Supabase by username
    # Step 1: Retrieve user from database
    user = supabase_db.get_user_by_username(username)
    # Step 2: Verify password if user exists; return user on success
    if user and check_password(password, user.password):
        return user
    # Return None for invalid username/password
    return None


def is_admin(user: User) -> bool:
    """
    Checks if the user has Admin role to know which permissions to give.
    
    Args:
        user (User): User object to check.
    
    Returns:
        bool: True if user is Admin, False otherwise.
    """
    # Direct role comparison
    return user.role == 'Admin'


def can_place_prediction(user: User) -> bool:
    """
    Determines if user can place predictions (Admins and Members allowed).
    
    Args:
        user (User): User object to authorize.
    
    Returns:
        bool: True if authorized, False otherwise.
    """
    # Role-based authorization: allow Admins or Members
    return user.role in ['Admin', 'Member'] # In the future allowing more roles are possible



def reset_password(email: str, new_password: str) -> bool:
    """
    Resets user's password by email.
    
    Finds user by email, hashes new password, and updates in database.
    
    Args:
        email (str): User's email address.
        new_password (str): New plaintext password.
    
    Returns:
        bool: True if update successful, False if user not found or update failed.
    """
    # Retrieve user by email from Supabase since email is unique and a required field being being the "to" line
    user = supabase_db.get_user_by_email(email)
    if user:
        # Hash new password and persist to database via user_id
        hashed = hash_password(new_password)
        return supabase_db.update_user_password(user.user_id, hashed)
    # Return False if no matching user found
    return False
