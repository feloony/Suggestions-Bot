import re
from datetime import datetime, timedelta
from typing import Dict, Tuple
from config import Config
from collections import defaultdict

# Store user's last suggestion timestamps
user_suggestions = defaultdict(list)

def check_rate_limit(user_id: int) -> Tuple[bool, float]:
    """Check if user has exceeded suggestion rate limit
    Returns: (is_allowed: bool, time_remaining: float)
    """
    current_time = datetime.now().timestamp()
    
    # Remove old timestamps
    user_suggestions[user_id] = [
        timestamp for timestamp in user_suggestions[user_id]
        if current_time - timestamp < Config.RATE_LIMIT_DURATION
    ]
    
    # Check if user has reached limit
    if len(user_suggestions[user_id]) >= Config.MAX_SUGGESTIONS_PER_USER:
        oldest = min(user_suggestions[user_id]) if user_suggestions[user_id] else current_time
        time_remaining = Config.RATE_LIMIT_DURATION - (current_time - oldest)
        return False, max(0, time_remaining)
        
    # Add new timestamp and return success
    user_suggestions[user_id].append(current_time)
    return True, 0.0

def get_rate_limit_remaining(user_id: int) -> int:
    """Get remaining time until user can suggest again"""
    current_time = datetime.now().timestamp()
    if not user_suggestions[user_id]:
        return 0
        
    oldest_suggestion = min(user_suggestions[user_id])
    time_remaining = max(0, Config.RATE_LIMIT_DURATION - (current_time - oldest_suggestion))
    return int(time_remaining)

def format_time_remaining(seconds: float) -> str:
    """Format seconds into a readable time string"""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    return re.sub(r'[^\w\s\-.,!?()]', '', text)
