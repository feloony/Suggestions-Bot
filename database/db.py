import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_file='suggestions.db'):
        self.db_file = db_file
        self.conn = None
        self.init_db()

    def get_connection(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_file)
        return self.conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # Create suggestions table
        c.execute('''CREATE TABLE IF NOT EXISTS suggestions
                    (message_id INTEGER PRIMARY KEY,
                     user_id INTEGER,
                     suggestion TEXT,
                     status TEXT,
                     category TEXT DEFAULT 'General',
                     is_anonymous BOOLEAN DEFAULT 0,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        # Create votes table
        c.execute('''CREATE TABLE IF NOT EXISTS votes
                    (message_id INTEGER,
                     user_id INTEGER,
                     vote_type TEXT,
                     PRIMARY KEY (message_id, user_id))''')

        # Create channel config table
        c.execute('''CREATE TABLE IF NOT EXISTS channel_config
                    (guild_id INTEGER PRIMARY KEY,
                     channel_id INTEGER)''')

        # Create categories table
        c.execute('''CREATE TABLE IF NOT EXISTS categories
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT UNIQUE)''')

        conn.commit()

    def add_suggestion(self, message_id, user_id, suggestion, category="General", anonymous=False):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO suggestions 
                     (message_id, user_id, suggestion, status, category, is_anonymous, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (message_id, user_id, suggestion, 'Pending', category, anonymous, datetime.now()))
        conn.commit()

    def get_suggestion_channel(self, guild_id: int) -> Optional[int]:
        try:
            c = self.get_connection().cursor()
            result = c.execute("SELECT channel_id FROM channel_config WHERE guild_id = ?", (guild_id,)).fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return None

    def set_suggestion_channel(self, guild_id: int, channel_id: int) -> bool:
        try:
            c = self.get_connection().cursor()
            c.execute("INSERT OR REPLACE INTO channel_config (guild_id, channel_id) VALUES (?, ?)",
                     (guild_id, channel_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return False

    def get_suggestion(self, message_id: int) -> Optional[Dict]:
        try:
            c = self.get_connection().cursor()
            result = c.execute("""
                SELECT s.*, 
                       (SELECT COUNT(*) FROM votes WHERE message_id = s.message_id AND vote_type = '👍') as upvotes,
                       (SELECT COUNT(*) FROM votes WHERE message_id = s.message_id AND vote_type = '👎') as downvotes
                FROM suggestions s 
                WHERE s.message_id = ?""", (message_id,)).fetchone()
            if result:
                return {
                    'message_id': result[0],
                    'user_id': result[1],
                    'suggestion': result[2],
                    'status': result[3],
                    'category': result[4],
                    'is_anonymous': bool(result[5]),
                    'timestamp': result[6],
                    'upvotes': result[7],
                    'downvotes': result[8]
                }
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return None

    def update_suggestion_status(self, message_id: int, status: str, reason: str = None) -> bool:
        try:
            c = self.get_connection().cursor()
            c.execute("""
                UPDATE suggestions 
                SET status = ?, status_reason = ?, status_updated_at = CURRENT_TIMESTAMP 
                WHERE message_id = ?
            """, (status, reason, message_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return False

    def count_suggestions_for_mass_update(self, category: str = None, days: int = None) -> int:
        try:
            c = self.get_connection().cursor()
            query = "SELECT COUNT(*) FROM suggestions WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            if days:
                query += " AND timestamp >= datetime('now', ?)"
                params.append(f'-{days} days')
                
            result = c.execute(query, params).fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return 0

    def mass_update_status(self, status: str, category: str = None, days: int = None) -> int:
        try:
            c = self.get_connection().cursor()
            query = "UPDATE suggestions SET status = ? WHERE 1=1"
            params = [status]
            
            if category:
                query += " AND category = ?"
                params.append(category)
            if days:
                query += " AND timestamp >= datetime('now', ?)"
                params.append(f'-{days} days')
                
            c.execute(query, params)
            self.conn.commit()
            return c.rowcount
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return 0

    def export_suggestions(self, days: int = None) -> List[Tuple]:
        try:
            c = self.get_connection().cursor()
            query = """
                SELECT message_id, user_id, suggestion, status, category, timestamp,
                       (SELECT COUNT(*) FROM votes WHERE message_id = s.message_id AND vote_type = '👍') as upvotes,
                       (SELECT COUNT(*) FROM votes WHERE message_id = s.message_id AND vote_type = '👎') as downvotes
                FROM suggestions s
                WHERE 1=1
            """
            params = []
            
            if days:
                query += " AND timestamp >= datetime('now', ?)"
                params.append(f'-{days} days')
                
            return c.execute(query, params).fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []

    def get_suggestion_stats(self) -> Dict[str, int]:
        try:
            c = self.get_connection().cursor()
            stats = {
                'total': 0,
                'pending': 0,
                'accepted': 0,
                'rejected': 0,
                'under_review': 0
            }
            for status in ['Pending', 'Accepted', 'Rejected', 'Under Review']:
                count = c.execute("SELECT COUNT(*) FROM suggestions WHERE status = ?", (status,)).fetchone()[0]
                stats[status.lower().replace(' ', '_')] = count
            stats['total'] = sum(stats.values())
            return stats
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return {'total': 0, 'pending': 0, 'accepted': 0, 'rejected': 0, 'under_review': 0}

    # Add other database methods here...

    def add_vote(self, message_id: int, user_id: int, emoji: str) -> bool:
        """Add a vote to a suggestion"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Remove any existing votes from this user on this suggestion
            c.execute("""
                DELETE FROM votes 
                WHERE message_id = ? AND user_id = ?
            """, (message_id, user_id))
            
            # Add the new vote
            c.execute("""
                INSERT INTO votes (message_id, user_id, vote_type)
                VALUES (?, ?, ?)
            """, (message_id, user_id, emoji))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error in add_vote: {e}")
            return False

    def remove_vote(self, message_id: int, user_id: int) -> bool:
        """Remove a vote from a suggestion"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""
                DELETE FROM votes 
                WHERE message_id = ? AND user_id = ?
            """, (message_id, user_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error in remove_vote: {e}")
            return False
