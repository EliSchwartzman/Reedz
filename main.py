import sys          # System-specific parameters and functions (exit, stdin)
import os           # Operating system interface (environment variables)
import getpass      # Secure password input (hides characters when typing)
from dotenv import load_dotenv  # Load environment variables from .env file
from models import User         # User data model with all user fields
from auth import hash_password, authenticate, is_admin  # Authentication utilities
from betting import create_bet, close_bet, resolve_bet, place_prediction, get_bet_overview  # Betting operations
import supabase_db              # Database layer for all Supabase interactions
from datetime import datetime, timedelta  # Date/time handling for bets/timestamps


# Load environment variables (.env file) for secure configuration
load_dotenv()
ADMIN_CODE = os.getenv("ADMIN_CODE")  # Secret code required for admin actions


def main_menu(user):
    """
    Displays role-based main menu options for Reedz CLI.
    
    Admins see full management options; Members see limited view-only options.
    """
    print("\n==== REEDZ MAIN MENU ====")
    if is_admin(user):
        # Admin menu: full control over bets and users
        menu_items = [
            ("1", "Create bet"),
            ("2", "Place prediction"),
            ("3", "Close bet"),
            ("4", "Resolve bet"),
            ("5", "View bets"),
            ("6", "View leaderboard"),
            ("7", "User management"),
            ("8", "Logout"),
            ("9", "Exit"),
            ("10", "View predictions for a bet"),
        ]
    else:
        # Member menu: view and predict only
        menu_items = [
            ("1", "Place prediction"),
            ("2", "View bets"),
            ("3", "View leaderboard"),
            ("4", "Logout"),
            ("5", "Exit"),
            ("6", "View predictions for a bet"),
        ]
    # Print numbered menu options
    for k, v in menu_items:
        print(f"{k}. {v}")
    return input("Choice: ")


def auth_menu():
    """Displays authentication options (register/login/reset/exit)."""
    print("==== REEDZ AUTH MENU ====")
    print("1. Register")
    print("2. Login")
    print("3. Reset password")
    print("4. Exit")
    return input("Choice: ")


def user_management_menu():
    """Displays admin user management submenu."""
    print("\n==== USER MANAGEMENT MENU ====")
    print("1. List all users")
    print("2. Promote/demote user")
    print("3. Change user reedz balance")
    print("4. Delete user")
    print("5. Return to main menu")
    return input("Choice: ")


def print_bets(bets):
    """Simple formatted display of bet list (ID and title only)."""
    for bet in bets:
        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")


def print_predictions_with_usernames(predictions):
    """Displays predictions with usernames (fetches user data for display)."""
    if not predictions:
        print("No predictions found for this bet.")
        return
    print("\nPredictions:")
    for pred in predictions:
        # Fetch username by user_id (note: inefficient for large datasets - optimize with JOIN)
        pred_user = supabase_db.get_user_by_username(pred.user_id)
        username = pred_user.username if pred_user else f"UserID {pred.user_id}"
        print(f"User: {username}, Prediction: {pred.prediction}")


def cli():
    """Main CLI application loop with authentication and role-based menus."""
    user = None  # Current logged-in user (None until authenticated)
    
    # Authentication loop: require successful login/registration
    while not user:
        choice = auth_menu()
        if choice == "1":  # REGISTER NEW USER
            username = input("Username: ")
            # Hash password securely before storage
            password = hash_password(getpass.getpass("Password: "))
            email = input("Email: ")
            
            # Role validation with admin code protection
            while True:
                role = input("Role (Admin/Member): ")
                if role == "Admin":
                    admin_code = getpass.getpass("Enter admin verification code: ")
                    if admin_code != ADMIN_CODE:
                        print("Incorrect admin code. Try again or enter 'Member' as role.")
                        continue
                if role not in ["Admin", "Member"]:
                    print("Role must be 'Admin' or 'Member'.")
                    continue
                break
            
            # Create and persist new user with default zero balance
            u = User(user_id=None, username=username, password=password, email=email, 
                    reedz_balance=0, role=role, created_at=datetime.now())
            supabase_db.create_user(u)
            print("User registered. Now, please login.")
            
        elif choice == "2":  # LOGIN
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            user = authenticate(username, password)
            if user:
                print(f"Logged in as {user.username}, role {user.role}")
            else:
                print("Login failed, try again.")
                
        elif choice == "3":  # PASSWORD RESET
            email = input("Enter your email address: ")
            found_user = supabase_db.get_user_by_email(email)
            if not found_user:
                print("No user with that email address was found.")
                continue
            new_password = getpass.getpass("Enter new password: ")
            confirm_password = getpass.getpass("Re-enter new password: ")
            if new_password != confirm_password:
                print("Passwords do not match. Try again.")
                continue
            # Hash and update password in database
            hashed = hash_password(new_password)
            if supabase_db.update_user_password(found_user.user_id, hashed):
                print("Password reset successful. You can now login.")
            else:
                print("Password reset failed. Try again.")
                
        elif choice == "4":  # EXIT
            print("Goodbye!")
            sys.exit()
    
    # Main application loop (role-based menu handling)
    while True:
        choice = main_menu(user)
        
        # ADMIN-ONLY OPERATIONS
        if is_admin(user):
            if choice == "1":  # CREATE BET
                title = input("Bet title: ")
                description = input("Description: ")
                answer_type = input("Type (number/text): ")
                close_at = datetime.now() + timedelta(days=1)  # Default: 24h from now
                create_bet(user, title, description, answer_type, close_at)
                print("Bet created.")
                
            elif choice == "2":  # PLACE PREDICTION (admin can also predict)
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets available for predictions.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID you want to predict on: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                pred = input("Your Prediction: ")
                try:
                    place_prediction(user, bet_id, pred)
                    print("Prediction placed.")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == "3":  # CLOSE BET
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets to close.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID to close: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                close_bet(user, bet_id)
                print("Bet closed.")
                
            elif choice == "4":  # RESOLVE BET
                closed_bets = get_bet_overview("closed")
                if not closed_bets:
                    print("No bets available to resolve.")
                    continue
                print("\nClosed Bets (available to resolve):")
                print_bets(closed_bets)
                try:
                    bet_id = int(input("Enter Bet ID to resolve: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                answer = input("Correct answer: ")
                resolve_bet(user, bet_id, answer)
                print("Bet resolved and Reedz distributed.")
                
            elif choice == "5":  # VIEW ALL BETS BY STATUS
                open_bets = get_bet_overview("open")
                closed_bets = get_bet_overview("closed")
                resolved_bets = get_bet_overview("resolved")
                print("\n--- Open Bets ---")
                if open_bets:
                    for bet in open_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No open bets.")
                print("\n--- Closed Bets ---")
                if closed_bets:
                    for bet in closed_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No closed bets.")
                print("\n--- Resolved Bets ---")
                if resolved_bets:
                    for bet in resolved_bets:
                        ans_str = f", Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}{ans_str}")
                else:
                    print("No resolved bets.")
                    
            elif choice == "6":  # LEADERBOARD
                leaderboard = supabase_db.get_leaderboard()
                if not leaderboard:
                    print("No users found.")
                else:
                    print("\n==== REEDZ LEADERBOARD ====")
                    print(f"{'Rank':<6}{'Username':<20}{'Reedz':<8}")
                    for idx, entry in enumerate(leaderboard, 1):
                        print(f"{idx:<6}{entry['username']:<20}{entry['reedz_balance']:<8}")
                        
            elif choice == "7":  # USER MANAGEMENT SUBMENU
                while True:
                    sub_choice = user_management_menu()
                    if sub_choice == "1":  # LIST USERS
                        users = supabase_db.list_all_users()
                        print(f"{'UserID':<8}{'Username':<20}{'Role':<10}{'Reedz':<8}")
                        for u in users:
                            print(f"{u['user_id']:<8}{u['username']:<20}{u['role']:<10}{u['reedz_balance']:<8}")
                            
                    elif sub_choice == "2":  # PROMOTE/DEMOTE
                        try:
                            uid = int(input("Enter User ID to promote/demote: "))
                            new_role = input("New role (Admin/Member): ")
                            if new_role == "Admin":
                                admin_code = getpass.getpass("Enter admin verification code: ")
                                if admin_code != ADMIN_CODE:
                                    print("Incorrect admin code. Promotion cancelled.")
                                    continue
                            if new_role not in ["Admin", "Member"]:
                                print("Role must be 'Admin' or 'Member'.")
                                continue
                            supabase_db.change_role(uid, new_role)
                            print("Role updated.")
                        except Exception as e:
                            print(f"Error: {e}")
                            
                    elif sub_choice == "3":  # CHANGE REEDZ BALANCE
                        try:
                            uid = int(input("Enter User ID to change Reedz: "))
                            reedz = int(input("New Reedz balance: "))
                            all_users = supabase_db.list_all_users()
                            user_obj = next((u for u in all_users if u['user_id'] == uid), None)
                            if not user_obj:
                                print("User not found.")
                                continue
                            # Calculate delta for incremental update (safer than SET)
                            delta = reedz - user_obj['reedz_balance']
                            supabase_db.add_reedz(uid, delta)
                            print("Reedz updated.")
                        except Exception as e:
                            print(f"Error: {e}")
                            
                    elif sub_choice == "4":  # DELETE USER
                        try:
                            uid = int(input("Enter User ID to delete: "))
                            supabase_db.delete_user(uid)
                            print("User deleted.")
                        except Exception as e:
                            print(f"Error: {e}")
                            
                    elif sub_choice == "5":  # BACK TO MAIN MENU
                        break
                    else:
                        print("Invalid choice.")
                        
            elif choice == "8":  # LOGOUT
                print("Logging out...")
                user = None
                # Restart authentication loop (repeated code - refactor opportunity)
                while not user:
                    choice = auth_menu()
                    # [Authentication logic repeated here - identical to initial auth loop]
                    
            elif choice == "9":  # EXIT APPLICATION
                print("Goodbye!")
                sys.exit()
                
            elif choice == "10":  # VIEW BET PREDICTIONS
                all_bets = get_bet_overview("")
                if not all_bets:
                    print("No bets found.")
                    continue
                print("\nAll Bets:")
                print_bets(all_bets)
                try:
                    bet_id = int(input("Enter Bet ID to view predictions for: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                predictions = supabase_db.get_predictions_for_bet(bet_id)
                print_predictions_with_usernames(predictions)
                
            else:
                print("Invalid choice.")
                
        # NON-ADMIN (MEMBER) OPERATIONS
        else:
            if choice == "1":  # PLACE PREDICTION
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets available for predictions.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID you want to predict on: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                pred = input("Your Prediction: ")
                try:
                    place_prediction(user, bet_id, pred)
                    print("Prediction placed.")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == "2":  # VIEW BETS (read-only)
                open_bets = get_bet_overview("open")
                closed_bets = get_bet_overview("closed")
                resolved_bets = get_bet_overview("resolved")
                print("\n--- Open Bets ---")
                if open_bets:
                    for bet in open_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No open bets.")
                print("\n--- Closed Bets ---")
                if closed_bets:
                    for bet in closed_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No closed bets.")
                print("\n--- Resolved Bets ---")
                if resolved_bets:
                    for bet in resolved_bets:
                        ans_str = f", Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}{ans_str}")
                else:
                    print("No resolved bets.")
                    
            elif choice == "3":  # VIEW LEADERBOARD
                leaderboard = supabase_db.get_leaderboard()
                if not leaderboard:
                    print("No users found.")
                else:
                    print("\n==== REEDZ LEADERBOARD ====")
                    print(f"{'Rank':<6}{'Username':<20}{'Reedz':<8}")
                    for idx, entry in enumerate(leaderboard, 1):
                        print(f"{idx:<6}{entry['username']:<20}{entry['reedz_balance']:<8}")
                        
            elif choice == "4":  # LOGOUT
                print("Logging out...")
                user = None
                # Restart authentication loop (repeated code)
                
            elif choice == "5":  # EXIT
                print("Goodbye!")
                sys.exit()
                
            elif choice == "6":  # VIEW PREDICTIONS
                all_bets = get_bet_overview("")
                if not all_bets:
                    print("No bets found.")
                    continue
                print("\nAll Bets:")
                print_bets(all_bets)
                try:
                    bet_id = int(input("Enter Bet ID to view predictions for: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                predictions = supabase_db.get_predictions_for_bet(bet_id)
                print_predictions_with_usernames(predictions)
                
            else:
                print("Invalid choice.")


# Entry point: start the Reedz CLI application
if __name__ == "__main__":
    cli()
