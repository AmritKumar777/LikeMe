import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory

# 1. INITIALIZE THE APP
# We tell Python to create a web application using the Flask framework.
app = Flask(__name__)

# The secret key keeps user sessions secure. A session remembers who is logged in
# so they don't have to keep re-entering their password on every single click.
app.secret_key = 'likeme_fairy_secret_key'

# This is the name of our database file where all user data will be saved.
DATABASE = 'likeme.db'


# 2. THE DATABASE SETUP (Runs once when the app starts)
def init_db():
    # Connect to SQLite. If the file 'likeme.db' doesn't exist, it creates it instantly.
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create the 'users' table if it's not already there.
    # It stores usernames, passwords, display names, ages, genders, bios, and avatar images.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            bio TEXT,
            image_url TEXT
        )
    ''')
    
    # Create the 'likes' table. It keeps track of who likes whom.
    # 'liker' is the person clicking the heart button, 'liked' is the target profile.
    # UNIQUE(liker, liked) stops someone from clicking like on the same person 50 times.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liker TEXT NOT NULL,
            liked TEXT NOT NULL,
            UNIQUE(liker, liked)
        )
    ''')
    
    # INJECT PLACEHOLDER USERS: So your app isn't empty when you open it the first time!
    # "INSERT OR IGNORE" tells SQLite: "If these accounts already exist, don't overwrite them."
    cursor.execute("INSERT OR IGNORE INTO users (username, password, name, age, gender, bio, image_url) VALUES ('pika', '123', 'Pixie Pika ⚡', 18, 'Female', 'Glitter, high-top platforms, and electric vibes.', 'https://pokemondb.net')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, name, age, gender, bio, image_url) VALUES ('psy', '123', 'Psy Fairy 🌀', 19, 'Male', 'Overthinking my canvas bag collection & stars.', 'https://pokemondb.net')")
    
    # Save the changes and close the database connection.
    conn.commit()
    conn.close()

# Execute the database builder function
init_db()


# 3. THE APP ROUTES (What happens when users visit URLs)

# This route serves the PWA Service Worker script from the root directory.
# Browsers require the service worker to live at the root ('/sw.js') to work correctly.
@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js', mimetype='application/javascript')

# THE HOME PAGE URL ('/')
@app.route('/')
def home():
    # If the user is already logged in, skip the login screen and send them straight to the swiping board.
    if 'username' in session:
        return redirect(url_for('dashboard'))
    # Otherwise, render the beautiful Y2K login page.
    return render_template('login.html')

# THE LOGIN SUBMIT PROCESS
@app.route('/login', methods=['POST'])
def login():
    # Capture what the user typed into the input boxes on login.html
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Open the database and look for a user matching that exact username and password.
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # If found, save their info inside the 'session' cookie.
        # user[1] is the username, user[5] is their gender.
        session['username'] = user[1]
        session['gender'] = user[5]
        return redirect(url_for('dashboard'))
    
    # If login fails, show an error message
    return "<h3>Oops! Magic keys didn't match. Go back and try again! ✨</h3>"

# THE SIGNUP / REGISTRATION ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    # If they submitted the form (POST), read the data and write it to the database
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        bio = request.form.get('bio')
        
        # Free API trick: Generates a cute placeholder pixel-art profile pic using their username!
        image_url = f"https://dicebear.com{username}"
        
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, name, age, gender, bio, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (username, password, name, age, gender, bio, image_url))
            conn.commit()
            conn.close()
            # After signing up, send them back to the login page so they can log in.
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            # This triggers if the username is already taken because the username column is UNIQUE
            return "<h3>Fairy username already taken! 🧚‍♀️</h3>"
            
    # If they are just browsing to /register (GET), just show them the blank signup form page.
    return render_template('register.html')

# THE MAIN SWIPING DASHBOARD URL
@app.route('/dashboard')
def dashboard():
    # Security check: If someone tries to open /dashboard directly without logging in, kick them back to login page.
    if 'username' not in session:
        return redirect(url_for('home'))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Filter algorithm: Determine the opposite gender to display.
    opp_gender = 'Female' if session['gender'] == 'Male' else 'Male'
    
    # COMPLEX SQL EXPLAINED: Select profiles of the opposite gender, BUT
    # completely ignore profiles that the current logged-in user has already liked.
    # This prevents the same user card from popping up again after you already liked them!
    cursor.execute('''
        SELECT name, age, bio, image_url, username FROM users 
        WHERE gender = ? AND username NOT IN (SELECT liked FROM likes WHERE liker = ?)
    ''', (opp_gender, session['username']))
    
    profiles = cursor.fetchall()
    conn.close()
    
    # Render the swiping board, sending the filtered profiles list over to the HTML template
    return render_template('dashboard.html', profiles=profiles, current_user=session['username'])

# THE HEART / LIKE BUTTON PROCESS (Asynchronous API endpoint)
@app.route('/like', methods=['POST'])
def like_user():
    if 'username' not in session:
        return jsonify({'status': 'error'}), 403
        
    liker = session['username']
    liked = request.form.get('liked_username')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Save the like event into the likes table
    cursor.execute("INSERT OR IGNORE INTO likes (liker, liked) VALUES (?, ?)", (liker, liked))
    conn.commit()
    
    # THE MATCHMAKING LOGIC CHECK:
    # Look into the likes table to see if the person you just liked has also previously liked YOU.
    cursor.execute("SELECT * FROM likes WHERE liker = ? AND liked = ?", (liked, liker))
    match = cursor.fetchone()
    conn.close()
    
    # If yes, send back a special alert signal to the browser to display a celebration match box!
    if match:
        return jsonify({'status': 'match', 'message': f"✨ A magical match happened with {liked}! 🎉"})
    
    # If not a mutual match yet, just say they liked them successfully
    return jsonify({'status': 'liked'})

# THE LOGOUT PROCESS
@app.route('/logout')
def logout():
    # Erase the session cookie, clearing out who is logged in.
    session.clear()
    return redirect(url_for('home'))

# Start the Flask app engine locally with debugging enabled (auto-reloads if you edit code).
if __name__ == '__main__':
    app.run(debug=True)
