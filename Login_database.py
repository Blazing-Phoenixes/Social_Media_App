import sqlite3
import re
import os
from passlib.hash import pbkdf2_sha256
from datetime import datetime

DB_NAME = "users.db"

# -------------------- DATABASE INITIALIZATION --------------------
def connect_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # User table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT UNIQUE,
                profile_image TEXT
            )
        ''')
        # Friend requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Chat messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        ''')
        # Media uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                file_path TEXT,
                file_type TEXT,
                visibility TEXT CHECK (visibility IN ('public', 'private')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# -------------------- VALIDATION HELPERS --------------------
def validate_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[a-z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

def validate_username(username):
    return re.fullmatch(r'[A-Za-z0-9_]+', username)

def validate_phone(phone):
    return phone.isdigit() and len(phone) == 10

def validate_email(email):
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)

# -------------------- USER REGISTRATION --------------------
def add_user(username, phone, password, email=None):
    if not validate_username(username):
        return "Username must contain only letters, numbers, and underscores."
    if not validate_phone(phone):
        return "Phone number must contain exactly 10 digits."
    if not validate_password(password):
        return "Password must include uppercase, lowercase, digit, and special character."
    if email and not validate_email(email):
        return "Invalid email format."

    hashed_password = pbkdf2_sha256.hash(password)
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, phone, password, email, profile_image)
                VALUES (?, ?, ?, ?, ?)
            """, (username.lower(), phone, hashed_password, email, None))
            return "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return "Username already exists!"
        elif "phone" in str(e):
            return "Phone number already exists!"
        elif "email" in str(e):
            return "Email already in use!"
        return "Account creation failed!"

# -------------------- USER LOGIN --------------------
def login_user(user_input, password):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=? OR phone=?", 
                       (user_input.lower(), user_input))
        result = cursor.fetchone()
    return result and pbkdf2_sha256.verify(password, result[0])

# -------------------- PROFILE FUNCTIONS --------------------
def get_user_details(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, phone, email, profile_image 
            FROM users 
            WHERE LOWER(username)=? OR phone=?
        """, (identifier, identifier))
        return cursor.fetchone()

def get_profile_image_path(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT profile_image FROM users WHERE LOWER(username)=? OR phone=?", 
                       (identifier, identifier))
        result = cursor.fetchone()
        return result[0] if result else None

def update_profile_image(identifier, image_path):
    identifier = str(identifier).lower()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET profile_image=? 
                WHERE LOWER(username)=? OR phone=?
            """, (image_path, identifier, identifier))
        return "Profile Picture Saved!"
    except sqlite3.IntegrityError:
        return "Can't save profile picture."

def update_email(identifier, new_email):
    if not validate_email(new_email):
        return "Invalid email format."
    identifier = str(identifier).lower()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET email=? 
                WHERE LOWER(username)=? OR phone=?
            """, (new_email, identifier, identifier))
            return "Email updated successfully!"
    except sqlite3.IntegrityError:
        return "Email already in use!"

# -------------------- PASSWORD MANAGEMENT --------------------
def verify_password(identifier, input_password):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=? OR phone=?", 
                       (identifier.lower(), identifier))
        result = cursor.fetchone()
    return result and pbkdf2_sha256.verify(input_password, result[0])

def update_password(identifier, new_password):
    if not validate_password(new_password):
        return "Password must include uppercase, lowercase, digit, and special character."
    hashed = pbkdf2_sha256.hash(new_password)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=? OR phone=?", 
                       (hashed, identifier.lower(), identifier))
    return "Password updated successfully!"

# -------------------- DELETE ACCOUNT --------------------
def delete_user(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_requests WHERE sender=? OR receiver=?", (identifier, identifier))
        cursor.execute("DELETE FROM chat_messages WHERE sender=? OR receiver=?", (identifier, identifier))
        cursor.execute("DELETE FROM media WHERE user_id=?", (identifier,))
        cursor.execute("DELETE FROM users WHERE username=? OR phone=?", (identifier, identifier))
    return "User deleted successfully!"

# -------------------- FRIEND SYSTEM --------------------
def search_users(query):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, phone FROM users WHERE username LIKE ? OR phone LIKE ?",
                       (f"%{query}%", f"%{query}%"))
        return cursor.fetchall()

def send_friend_request(sender, receiver):
    if sender == receiver:
        return "You cannot send a request to yourself."
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=? OR phone=?", (receiver.lower(), receiver))
        if not cursor.fetchone():
            return "Receiver does not exist."

        cursor.execute("""
            SELECT 1 FROM friend_requests 
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) 
        """, (sender, receiver, receiver, sender))
        if cursor.fetchone():
            return "Friend request already exists."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO friend_requests (sender, receiver, timestamp) VALUES (?, ?, ?)",
                       (sender, receiver, timestamp))
    return "Request sent successfully!"

def get_friend_requests(receiver):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, timestamp 
            FROM friend_requests 
            WHERE receiver=? AND status='pending'
            ORDER BY timestamp DESC
        """, (receiver,))
        return cursor.fetchall()

def update_request_status(sender, receiver, action):
    if action not in ("accepted", "rejected"):
        return "Invalid action."
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE friend_requests SET status=? WHERE sender=? AND receiver=?", 
                       (action, sender, receiver))
    return f"Request {action}!"

def get_friends_list(user):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CASE 
                     WHEN sender=? THEN receiver 
                     ELSE sender 
                   END AS friend
            FROM friend_requests 
            WHERE (sender=? OR receiver=?) AND status='accepted'
        """, (user, user, user))
        return [row[0] for row in cursor.fetchall()]

def unfriend_user(user1, user2):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM friend_requests
            WHERE ((sender=? AND receiver=?) OR (sender=? AND receiver=?))
            AND status='accepted'
        """, (user1, user2, user2, user1))
        return cursor.rowcount > 0

# -------------------- CHAT FUNCTIONS --------------------
def send_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (sender, receiver, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sender, receiver, message, timestamp))

def get_conversation(user1, user2, limit=100):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, message, timestamp FROM chat_messages
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
            ORDER BY timestamp DESC LIMIT ?
        """, (user1, user2, user2, user1, limit))
        return cursor.fetchall()[::-1]

def mark_messages_as_read(sender, receiver):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_messages SET is_read=1
            WHERE sender=? AND receiver=? AND is_read=0
        """, (sender, receiver))

def get_unread_count(user):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, COUNT(*) FROM chat_messages
            WHERE receiver=? AND is_read=0 GROUP BY sender
        """, (user,))
        return dict(cursor.fetchall())

# -------------------- MEDIA FUNCTIONS --------------------
def post_media(user_id, username, file_path, file_type, visibility):
    if os.path.getsize(file_path) > 500 * 1024 * 1024:
        return "File size exceeds 500MB"
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO media (user_id, username, file_path, file_type, visibility)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, file_path, file_type, visibility))
        return "Posted"

def get_public_media():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media WHERE visibility='public' ORDER BY timestamp DESC")
        return cursor.fetchall()

def get_private_media_for_user(user_id, friends_ids):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if not friends_ids:
            return []
        format_ids = ','.join(['?'] * len(friends_ids))
        query = f"SELECT * FROM media WHERE visibility='private' AND user_id IN ({format_ids}) ORDER BY timestamp DESC"
        cursor.execute(query, friends_ids)
        return cursor.fetchall()

def delete_media(media_id, user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media WHERE id=? AND user_id=?", (media_id, user_id))

def update_media(media_id, new_file_path, new_visibility, user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE media SET file_path=?, visibility=?
            WHERE id=? AND user_id=?
        """, (new_file_path, new_visibility, media_id, user_id))