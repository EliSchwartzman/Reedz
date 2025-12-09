import supabase_db  # Database access for bets, predictions, and user balances
from collections import defaultdict  # Groups predictions by prediction error distance


def distribute_reedz_on_resolution(bet_id):
    """
    Automatically distributes Reedz rewards to predictors after bet resolution.
    
    Implements rank-based scoring:
    * NUMBER: Closest predictions get highest points (ties share rank)
    * TEXT: Exact matches get full points, others get zero
    
    Args:
        bet_id: Resolved bet identifier
    """
    # Fetch resolved bet and all predictions
    bet = supabase_db.get_bet(bet_id)
    predictions = supabase_db.get_predictions_for_bet(bet_id)
    num_predictions = len(predictions)
    
    # No predictions = no rewards
    if num_predictions == 0:
        return
    
    # NUMBER BET SCORING: Rank by absolute error distance from correct answer
    if bet.answer_type == 'number':
        correct = float(bet.correct_answer)  # Convert official answer to float
        
        # Calculate error distance for each prediction, sort by accuracy
        sorted_preds = sorted(
            [(abs(float(pred.prediction) - correct), pred) for pred in predictions],
            key=lambda x: x[0]  # Sort by smallest error first (most accurate)
        )
        
        # Group predictions by exact error distance (handles ties perfectly)
        error_groups = defaultdict(list)
        for dist, pred in sorted_preds:
            error_groups[dist].append(pred)
        
        # Calculate rank points for each error group
        scores = {}
        given = 0  # Track how many predictors ranked so far
        positions = sorted(error_groups.keys())  # Error distances in ascending order
        
        for error in positions:
            users_in_group = error_groups[error]  # All predictors with this exact error
            rank_points = num_predictions - given  # Remaining points for this rank
            
            for pred in users_in_group:
                # Base rank points + 5 bonus for PERFECT prediction
                scores[pred.user_id] = rank_points
                if float(pred.prediction) == correct:
                    scores[pred.user_id] += 5  # Perfect score bonus
            
            given += len(users_in_group)  # Advance rank counter
        
        # Distribute calculated Reedz rewards to each user
        for pred in predictions:
            supabase_db.add_reedz(pred.user_id, scores[pred.user_id])
    
    # TEXT BET SCORING: Exact match wins, others lose
    elif bet.answer_type == 'text':
        correct_answer = bet.correct_answer.strip().lower()  # Normalize for comparison
        
        matches = []     # Exact matches (winners)
        nonmatches = []  # Incorrect predictions (losers)
        
        # Categorize predictions
        for pred in predictions:
            pred_norm = pred.prediction.strip().lower()
            if pred_norm == correct_answer:
                matches.append(pred)
            else:
                nonmatches.append(pred)
        
        # Winners get full pool + bonus, losers get nothing
        num = len(matches) + len(nonmatches)  # Total participants
        for pred in matches:
            supabase_db.add_reedz(pred.user_id, num + 5)  # Pool share + perfect bonus
        for pred in nonmatches:
            supabase_db.add_reedz(pred.user_id, 0)         # No reward
