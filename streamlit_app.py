import streamlit as st  # Web framework for interactive data apps
import re               # Regular expressions for username validation
from models import User # Data models (User, Bet, Prediction)
from auth import hash_password, authenticate, is_admin  # Authentication utilities
from supabase import create_client, Client  # Supabase client creation
import supabase_db      # Supabase database operations layer
from betting import create_bet, close_bet, resolve_bet, place_prediction, get_bet_overview  # Betting operations
from datetime import datetime, timedelta  # Date/time calculations
import timestamper      # Human-readable timestamp formatting (ET timezone)
import os               # Environment variable access
from dotenv import load_dotenv  # Load .env configuration
import random           # Random number generation for reset codes
import string           # String constants for code generation
from email_sender import send_password_reset_email  # SMTP email utilities

# Load secure configuration from environment variables
load_dotenv()
ADMIN_CODE = os.getenv("ADMIN_CODE")  # Secret code for admin privileges

# Configure Streamlit page (wide layout for better UX)
st.set_page_config(page_title="Reedz Betting", layout="wide")

# Initialize session state to track user login and current page
if "user" not in st.session_state:
    st.session_state.user = None  # Current logged-in user (None = not authenticated)
if "page" not in st.session_state:
    st.session_state.page = "home"  # Navigation state

# UTILITY HELPER FUNCTIONS

def generate_reset_code(length=6):
    """Generates random 6-digit numeric code for password resets."""
    return ''.join(random.choices(string.digits, k=length))

def set_reset_code_for_email(email):
    """
    Generates, stores, and emails temporary password reset code (5min expiry).
    
    Args:
        email (str): User's registered email address
    
    Returns:
        tuple: (bool success, str error_message_or_None)
    """
    code = generate_reset_code()  # Create unique reset code
    expiry = datetime.now() + timedelta(minutes=5)  # 5-minute expiration
    
    # Store code + expiry in database
    supabase_db.set_user_reset_code(email, code, expiry)
    
    # Send via SMTP email
    success, error_msg = send_password_reset_email(email, code)
    return success, error_msg

# AUTHENTICATION PANEL

def auth_panel():
    """Renders login/register/reset password tabs (shown when not logged in)."""
    st.title("Reedz Betting Platform")
    st.divider()
    
    # Three-tab authentication interface
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Reset Password"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                user = authenticate(username, password)  # Verify credentials
                if user:
                    st.session_state.user = user  # Store authenticated user
                    st.success(f"Logged in as {user.username} ({user.role})")
                    st.session_state.page = "main"
                    st.rerun()  # Refresh to main panel
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        st.subheader("Register New Account")
        with st.form("register_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("New Username")
                password = st.text_input("New Password", type="password")
            with col2:
                email = st.text_input("Email")
                role = st.selectbox("Role", ["Member", "Admin"])
            
            # Conditional admin verification
            admin_code = ""
            if role == "Admin":
                admin_code = st.text_input("Admin Verification Code", type="password")
            
            reg_button = st.form_submit_button("Register", use_container_width=True)
            if reg_button:
                # Input validation
                if not all([username.strip(), password, email.strip()]):
                    st.error("All fields required")
                elif not re.match(r'^[A-Za-z0-9]+$', username):
                    st.error("Username: letters/numbers only, no spaces")
                elif role == "Admin" and admin_code != ADMIN_CODE:
                    st.error("Incorrect admin code")
                elif role not in ["Admin", "Member"]:
                    st.error("Invalid role")
                else:
                    # Create user with hashed password
                    hashed = hash_password(password)
                    u = User(
                        user_id=None,
                        username=username.strip(),
                        password=hashed,
                        email=email.strip(),
                        reedz_balance=0,
                        role=role,
                        created_at=datetime.now()
                    )
                    try:
                        supabase_db.create_user(u)
                        st.success("Registered! Please log in.")
                    except Exception as e:
                        msg = str(e).lower()
                        if any(x in msg for x in ["unique", "already exists"]):
                            st.error("Username/email already exists")
                        elif any(x in msg for x in ["null", "not-null", "empty"]):
                            st.error("All fields must be valid")
                        else:
                            st.error(f"Registration failed: {e}")
    
    with tab3:
        st.subheader("Password Reset")
        # Initialize reset session state
        for key in ["sent_reset_email", "reset_email_val", "reset_code_sent_to"]:
            if key not in st.session_state:
                st.session_state[key] = ""
        
        with st.form("reset_form", clear_on_submit=False):
            email = st.text_input("Email Address", value=st.session_state["reset_email_val"])
            send_code = st.form_submit_button("Send Reset Code")
            
            if send_code:
                if not supabase_db.get_user_by_email(email):
                    st.error("No account found for this email")
                else:
                    success, error_msg = set_reset_code_for_email(email)
                    if success:
                        st.session_state.update({
                            "sent_reset_email": True,
                            "reset_email_val": email,
                            "reset_code_sent_to": email
                        })
                        st.success("Reset code sent to your email (5min expiry)")
                    else:
                        st.session_state["sent_reset_email"] = False
                        st.error(f"Email failed: {error_msg}")
        
        # Reset code verification + new password
        if st.session_state["sent_reset_email"]:
            with st.form("change_pw_form"):
                col1, col2 = st.columns(2)
                code = col1.text_input("Reset Code from Email", max_chars=6)
                new_password = col1.text_input("New Password", type="password")
                confirm_password = col2.text_input("Confirm Password", type="password")
                
                change_btn = st.form_submit_button("Change Password", use_container_width=True)
                cancel_btn = st.form_submit_button("Cancel", use_container_width=True)
                
                if change_btn:
                    if not all([code, new_password, confirm_password]):
                        st.error("Complete all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords don't match")
                    elif not supabase_db.check_reset_code(st.session_state["reset_email_val"], code):
                        st.error("Invalid/expired code")
                    else:
                        hashed = hash_password(new_password)
                        if supabase_db.update_user_password_by_email(st.session_state["reset_email_val"], hashed):
                            supabase_db.clear_reset_code(st.session_state["reset_email_val"])
                            st.success("Password updated! Please log in.")
                            # Reset session state
                            for key in ["sent_reset_email", "reset_email_val", "reset_code_sent_to"]:
                                st.session_state[key] = ""
                        else:
                            st.error("Update failed")
                
                if cancel_btn:
                    for key in ["sent_reset_email", "reset_email_val", "reset_code_sent_to"]:
                        st.session_state[key] = ""

# USER INTERFACE PANELS

def leaderboard_panel():
    """Displays top users by Reedz balance."""
    st.subheader("Leaderboard")
    leaderboard = supabase_db.get_leaderboard()
    if leaderboard:
        st.dataframe([
            {"Rank": idx + 1, "Username": entry["username"], "Reedz": entry["reedz_balance"]}
            for idx, entry in enumerate(leaderboard)
        ], use_container_width=True)
    else:
        st.info("No users yet")

def bets_panel():
    """Shows all bets categorized by status (open/closed/resolved)."""
    st.subheader("All Bets")
    open_bets = get_bet_overview("open")
    closed_bets = get_bet_overview("closed")
    resolved_bets = get_bet_overview("resolved")
    
    with st.expander("**Open Bets (Accepting Predictions)**", expanded=True):
        if open_bets:
            for bet in open_bets:
                st.markdown(f"**ID {bet['bet_id']} | {bet['title']}**  "
                            f"*closes {timestamper.format_et(bet['close_at'])}*")
        else:
            st.info("No open bets")

    with st.expander("**Closed Bets**"):
        if closed_bets:
            for bet in closed_bets:
                st.markdown(f"**ID {bet['bet_id']} | {bet['title']}**  "
                            f"*closed {timestamper.format_et(bet['close_at'])}*")
        else:
            st.info("No closed bets")

    with st.expander("**Resolved Bets**"):
        if resolved_bets:
            for bet in resolved_bets:
                ans_str = f" | **Answer: {bet.get('correct_answer', 'N/A')}**"
                st.markdown(f"**ID {bet['bet_id']} | {bet['title']}**{ans_str}")
        else:
            st.info("No resolved bets")

def predictions_panel():
    """View all predictions for a selected bet."""
    st.subheader("View Predictions for a Bet")  # Biggest header
    
    all_bets = (get_bet_overview("open") + 
                get_bet_overview("closed") + 
                get_bet_overview("resolved"))
    
    if not all_bets:
        st.info("No bets available")
        return
    
    # Group bets by status 
    open_bets = [b for b in all_bets if not b.get('is_closed') and not b.get('is_resolved')]
    closed_bets = [b for b in all_bets if b.get('is_closed') and not b.get('is_resolved')]
    resolved_bets = [b for b in all_bets if b.get('is_resolved')]
    
    bet_titles = {}
    options = []
    
    # OPEN BETS 
    if open_bets:
        options.append("🟢 OPEN BETS")
        for b in open_bets:
            bet_titles[f"  🟢 ID {b['bet_id']} - {b['title']}"] = b['bet_id']
    
    # CLOSED BETS 
    if closed_bets:
        options.append("🔴 CLOSED BETS")
        for b in closed_bets:
            bet_titles[f"  🔴 ID {b['bet_id']} - {b['title']}"] = b['bet_id']
    
    # RESOLVED BETS 
    if resolved_bets:
        options.append("⚫ RESOLVED BETS")
        for b in resolved_bets:
            bet_titles[f"  ⚫ ID {b['bet_id']} - {b['title']}"] = b['bet_id']
    
    selected = st.selectbox("Select Bet", options if options else ["No bets available"])
    
    if selected and selected not in ["🟢 OPEN BETS", "🔴 CLOSED BETS", "⚫ RESOLVED BETS"]:
        bet_id = bet_titles[selected]
        predictions = supabase_db.get_predictions_for_bet(bet_id)
        
        if predictions:
            # Cache users to avoid N+1 queries
            user_cache = {}
            pred_data = []
            for p in predictions:
                user_id = p['user_id']  
                if user_id not in user_cache:
                    user = supabase_db.get_user_by_id(user_id)
                    user_cache[user_id] = user.username if user else f"ID {user_id}"
                
                pred_data.append({  # FIXED: append() + proper indentation
                    "User": user_cache[user_id],
                    "Prediction": p['prediction'],  
                    "Created": timestamper.format_et(p['created_at'])
                })
            
            st.dataframe(pred_data, use_container_width=True)
        else:
            st.info("No predictions for this bet")



# ADMIN PANELS (Role-protected)

def create_bet_panel(user):
    """Admin: Create new betting market."""
    st.subheader("Create Bet")
    with st.expander("New Bet Form", expanded=True):
        title = st.text_input("Bet Title")
        description = st.text_area("Description", height=80)
        answer_type = st.selectbox("Answer Type", ["number", "text"])
        close_days = st.number_input("Days until closes", min_value=1, max_value=30, value=1)
        
        if st.button("Create Bet", use_container_width=True):
            close_at = datetime.now() + timedelta(days=close_days)
            try:
                create_bet(user, title, description, answer_type, close_at)
                st.success("Bet created successfully")
            except Exception as e:
                st.error(f"{e}")

def place_prediction_panel(user):
    """Place prediction on open bet."""
    st.subheader("Place Prediction")
    open_bets = get_bet_overview("open")
    if not open_bets:
        st.info("No open bets available")
        return
    
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    selected = st.selectbox("Select Bet", list(bet_titles.keys()))
    
    if selected:
        bet_id = bet_titles[selected]
        prediction = st.text_input("Your Prediction")
        if st.button("Submit Prediction", use_container_width=True):
            try:
                place_prediction(user, bet_id, prediction)
                st.success("Prediction placed!")
            except Exception as e:
                st.error(f"{e}")

def close_bet_panel(user):
    """Admin: Close open bet (stop predictions)."""
    st.subheader("Close Bet")
    open_bets = get_bet_overview("open")
    if not open_bets:
        st.info("No open bets")
        return
    
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    selected = st.selectbox("Select Bet to Close", list(bet_titles.keys()))
    
    if selected:
        bet_id = bet_titles[selected]
        if st.button("Close Bet", use_container_width=True):
            try:
                close_bet(user, bet_id)
                st.success("Bet closed")
            except Exception as e:
                st.error(f"{e}")

def resolve_bet_panel(user):
    """Admin: Set correct answer and distribute rewards."""
    st.subheader("Resolve Bet")
    closed_bets = get_bet_overview("closed")
    if not closed_bets:
        st.info("No closed bets to resolve")
        return
    
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in closed_bets}
    selected = st.selectbox("Select Bet to Resolve", list(bet_titles.keys()))
    
    if selected:
        bet_id = bet_titles[selected]
        answer = st.text_input("Correct Answer")
        if st.button("Resolve & Distribute Rewards", use_container_width=True):
            try:
                resolve_bet(user, bet_id, answer)
                st.success("Bet resolved + Reedz distributed!")
            except Exception as e:
                st.error(f"{e}")

def user_management_panel():
    """Admin: Full user CRUD (Create, Read, Update, Delete) operations."""
    st.subheader("User Management")
    action = st.radio("Action", ["List users", "Promote/Demote", "Change Reedz", "Delete user", "Season Reset"])
    
    users = supabase_db.list_all_users()
    
    if action == "List users":
        st.dataframe([{
            "UserID": u["user_id"], "Username": u["username"], 
            "Email": u.get("email", "N/A"), "Role": u["role"], "Reedz": u["reedz_balance"]
        } for u in users], use_container_width=True)
    
    elif action == "Promote/Demote":
        user_map = {f"{u['username']} (ID {u['user_id']}) [{u['role']}]": u['user_id'] for u in users}
        selected = st.selectbox("User", list(user_map.keys()))
        uid = user_map[selected]
        new_role = st.selectbox("New Role", ["Admin", "Member"])
        
        if new_role == "Admin":
            admin_code = st.text_input("Admin Code", type="password")
            if st.button("Update Role") and admin_code == ADMIN_CODE:
                try:
                    supabase_db.change_role(uid, new_role)
                    st.success("Role updated")
                    st.rerun()
                except Exception as e:
                    st.error(f"{e}")
            elif admin_code != ADMIN_CODE and st.button("Update Role"):
                st.error("Wrong admin code")
        else:
            if st.button("Update Role"):
                try:
                    supabase_db.change_role(uid, new_role)
                    st.success("Role updated")
                    st.rerun()
                except Exception as e:
                    st.error(f"{e}")
    
    elif action == "Change Reedz":
        user_map = {f"{u['username']} (ID {u['user_id']}) [{u['reedz_balance']} Reedz]": u for u in users}
        selected = st.selectbox("User", list(user_map.keys()))
        user_data = user_map[selected]
        new_balance = st.number_input("New Balance", min_value=0, value=user_data['reedz_balance'])
        
        if st.button("Update Balance"):
            delta = new_balance - user_data['reedz_balance']
            try:
                supabase_db.add_reedz(user_data['user_id'], delta)
                st.success("Balance updated")
                st.rerun()
            except Exception as e:
                st.error(f"{e}")
    
    elif action == "Delete user":
        user_map = {f"{u['username']} (ID {u['user_id']})": u['user_id'] for u in users}
        selected = st.selectbox("User to Delete", list(user_map.keys()))
        uid = user_map[selected]
        
        if st.button("CONFIRM DELETE", type="primary"):
            try:
                supabase_db.delete_user(uid)
                st.success("User deleted")
                st.rerun()
            except Exception as e:
                st.error(f"{e}")
    
    elif action == "Season Reset":
        st.warning("**SEASON RESET**: Deletes ALL bets + predictions. Users preserved. This operation is irreversible.")       
        if st.button("CONFIRM SEASON RESET", type="primary"):
            with st.spinner("Resetting season..."):
                try:
                    supabase_db.reset_season()
                    st.success("Season reset complete!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Reset failed: {e}")

def profile_panel(user):
    """Display current user's profile information."""
    st.header("My Profile")
    
    user_db = supabase_db.get_user_by_id(user.user_id)
    
    if user_db:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Username:** {user_db.username}")
            st.markdown(f"**Email:** {user_db.email}")
        with col2:
            st.markdown(f"**Reedz Balance:** {user_db.reedz_balance:,}")
            st.markdown(f"**Role:** {user_db.role}")
        
        st.caption(f"Member since {timestamper.format_et(user_db.created_at)}")
        
        # Prediction History
        st.subheader("Prediction History")
        predictions = supabase_db.get_user_predictions(user.user_id)
        
        if predictions:
            pred_data = []
            for p in predictions:
                bet = supabase_db.get_bet(p['bet_id'])
                bet_title = bet.title if bet else f"Bet #{p['bet_id']}"
                correct_answer = (bet.correct_answer if bet and bet.is_resolved and bet.correct_answer 
                                else "Bet has not been resolved yet")
                
                pred_data.append({
                    "Bet": bet_title,
                    "Prediction": p['prediction'],
                    "Correct Answer": correct_answer,
                    "Date": timestamper.format_et(p['created_at'])
                })
            
            st.dataframe(pred_data, use_container_width=True)
        else:
            st.info("No predictions yet")
    else:
        st.error("Profile not found")

# MAIN APPLICATION LAYOUT

def main_panel():
    """Renders authenticated user dashboard with role-based sidebar."""
    user = st.session_state.user
    
    # Sidebar: User info + navigation
    st.sidebar.title("Welcome to Reedz!")
    st.sidebar.subheader(f"Username: {user.username}")
    st.sidebar.subheader(f"Role: {user.role}")
    st.sidebar.divider()
    
    # Role-based page menu
    base_pages = ["My Profile", "Leaderboard", "All Bets", "Place Prediction", "View Predictions for a Bet"]
    if is_admin(user):
        admin_pages = ["Create Bet", "Close Bet", "Resolve Bet", "User Management"]
        pages = admin_pages + base_pages
    else:
        pages = base_pages
        
    st.sidebar.subheader("Navigation")  # Subheader size text
    page = st.sidebar.radio("Select page", pages, label_visibility="collapsed")


    # Route to selected page
    page_map = {
        "My Profile": lambda: profile_panel(user),
        "Leaderboard": leaderboard_panel,
        "All Bets": bets_panel,
        "Place Prediction": lambda: place_prediction_panel(user),
        "View Predictions for a Bet": predictions_panel,
        "Create Bet": lambda: create_bet_panel(user),
        "Close Bet": lambda: close_bet_panel(user),
        "Resolve Bet": lambda: resolve_bet_panel(user),
        "User Management": user_management_panel
    }

    if page in page_map:
        page_map[page]()
    else:
       st.error(f"Unknown page: {page}")
    
    # Logout button
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "home"
        st.rerun()

# APPLICATION ENTRY POINT

def run_app():
    """Main app router: auth → dashboard."""
    if st.session_state.user is None:
        auth_panel()  # Show login/register
    else:
        main_panel()  # Show authenticated dashboard

# Streamlit entry point
if __name__ == "__main__" or st._is_running_with_streamlit:
    run_app()