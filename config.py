import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    MAX_SUGGESTION_LENGTH = int(os.getenv('MAX_SUGGESTION_LENGTH', 1000))
    
    # Rate limiting configuration
    RATE_LIMIT_DURATION = int(os.getenv('RATE_LIMIT_DURATION', 300))  # 5 minutes
    MAX_SUGGESTIONS_PER_USER = int(os.getenv('MAX_SUGGESTIONS_PER_USER', 3))
    
    VALID_STATUSES = ['Pending', 'Accepted', 'Rejected', 'Under Review']
