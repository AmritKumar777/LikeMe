import os
import ast
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import models as dbHandler

# Initialize Flask first to avoid NameError
app = Flask(__name__)

# Configure the upload directory correctly
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','JPG'])

# Fixed the list lower() typo by accessing the file extension index [1]
def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/showMatch', methods=['POST', 'GET'])
def showMatches():
    if request.method == 'POST':
        username = request.form['liker'] 
        matches = dbHandler.retrieveMatches(username)
        return render_template("matches.html", match=matches)

@app.route('/OneSided', methods=['POST', 'GET'])
def makematch():
    if request.method == 'POST':
        liker = request.form['current-username']
        liked = request.form['liked-person']
        pagedata = request.form['pagedata']
        data = list(ast.literal_eval(pagedata))
        count1 = dbHandler.checkMatch(liked, liker)
        if count1[0][0] >= 1:
            dbHandler.insertMatch(liker, liked)
            return render_template("dashboard.html", users=data, currentlogin=liker) 
        count2 = dbHandler.checkMatch(liker, liked)
        count3 = dbHandler.checkOneSided(liker, liked)
        if count2[0][0] >= 1 or count3[0][0] >= 1:
            return render_template("dashboard.html", users=data, currentlogin=liker)
        else:
            dbHandler.insertOnesidedLikes(liker, liked)
            return render_template("dashboard.html", users=data, currentlogin=liker)
    else:
        return render_template("dashboard.html", users=[], currentlogin="")

@app.route('/dashboard', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        count = dbHandler.checkUser(username, password)
        if count[0][0] >= 1:            
            users = dbHandler.findGender(username)
            gender = users[0][0]
            data = dbHandler.retrieveUserDetails(gender)
            if username == "admin":
                return render_template('admin.html', users=data)
            return render_template('dashboard.html', users=data, currentlogin=username)
        else:
            return render_template('welcome.html')
    else:
        return render_template('index.html')

@app.route('/reg')
def reg():
    return render_template('welcome.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        description = request.form['descriptn']
        
        if 'image' not in request.files:
            return render_template('welcome.html')
        file = request.files['image']
        if file.filename == '':
            return render_template('welcome.html') 
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image = "/static/" + filename
        else:
            image = "/static/default.png"
            
        dbHandler.insertUserDetails(username, password, age, image, gender, email, description)
        return render_template('index.html')
    else:
        return render_template('welcome.html')

if __name__ == '__main__':
    app.run(debug=True)
