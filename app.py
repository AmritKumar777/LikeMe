import os
import sqlite3
import random 
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory

# 1. INITIALIZE THE APP
app = Flask(__name__)
app.secret_key = 'likeme_fairy_secret_key'
DATABASE = 'likeme.db'


# 2. THE DATABASE SETUP (Runs once when the app starts)
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create the 'users' table
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
    
    # Create the 'likes' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liker TEXT NOT NULL,
            liked TEXT NOT NULL,
            UNIQUE(liker, liked)
        )
    ''')
    
    # Inject placeholder users cleanly if they aren't already generated
    cursor.execute("INSERT OR IGNORE INTO users (username, password, name, age, gender, bio, image_url) VALUES ('pika', '123', 'Pixie Pika ⚡', 18, 'Female', 'Glitter, high-top platforms, and electric vibes.', 'https://pokemondb.net')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, name, age, gender, bio, image_url) VALUES ('psy', '123', 'Psy Fairy 🌀', 19, 'Male', 'Overthinking my canvas bag collection & stars.', 'https://pokemondb.net')")
    
    conn.commit()
    conn.close()

init_db()


# 3. THE APP ROUTES (What happens when users visit URLs)

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js', mimetype='application/javascript')

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['username'] = user[1]
        session['gender'] = user[5]
        return redirect(url_for('dashboard'))
    
    return "<h3>Oops! Magic keys didn't match. Go back and try again! ✨</h3>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        bio = request.form.get('bio')
        
        fairy_avatars = [
            "🐱", "🦊", "🦁", "🐯", "🐼", "🐻", "🐨", "🐰", "🐭", "🐹", 
            "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🦆", "🦅", "🦉", "🦇", 
            "🐺", "🐗", "🐴", "🦄", "🐝", "✨", "🧚‍♀️", "🧚‍♂️", "🎨", "🎭",
            "💖", "👻", "⚡", "🔮", "🌈", "🌸", "🍬", "🎀", "🛸", "🌙"
        ]
        
        image_url = random.choice(fairy_avatars)
        
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, name, age, gender, bio, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (username, password, name, age, gender, bio, image_url))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            return "<h3>Fairy username already taken! 🧚‍♀️</h3>"
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    opp_gender = 'Female' if session['gender'] == 'Male' else 'Male'
    
    cursor.execute('''
        SELECT name, age, bio, image_url, username FROM users 
        WHERE gender = ? AND username NOT IN (SELECT liked FROM likes WHERE liker = ?)
    ''', (opp_gender, session['username']))
    
    profiles = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', profiles=profiles, current_user=session['username'])

@app.route('/like', methods=['POST'])
def like_user():
    if 'username' not in session:
        return jsonify({'status': 'error'}), 403
        
    liker = session['username']
    liked = request.form.get('liked_username')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO likes (liker, liked) VALUES (?, ?)", (liker, liked))
    conn.commit()
    
    cursor.execute("SELECT * FROM likes WHERE liker = ? AND liked = ?", (liked, liker))
    match = cursor.fetchone()
    conn.close()
    
    if match:
        return jsonify({'status': 'match', 'message': f"✨ A magical match happened with {liked}! 🎉"})
    
    return jsonify({'status': 'liked'})

# Added: NEW PERMANENT MATCHES TAB COMPONENT
@app.route('/matches')
def matches_tab():
    if 'username' not in session:
        return redirect(url_for('home'))
        
    current_user = session['username']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Filters rows to only load users that match bidirectional likeness rules
    cursor.execute('''
        SELECT users.name, users.age, users.bio, users.image_url 
        FROM users 
        JOIN likes AS my_likes ON my_likes.liked = users.username
        JOIN likes AS their_likes ON their_likes.liker = users.username
        WHERE my_likes.liker = ? AND their_likes.liked = ?
    ''', (current_user, current_user))
    
    successful_matches = cursor.fetchall()
    conn.close()
    
    return render_template('matches.html', matches=successful_matches, current_user=current_user)

# Fixed: Patched up your cut-off logout block cleanly!
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
