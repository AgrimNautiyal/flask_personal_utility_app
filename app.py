from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, jsonify, flash
from wtforms import Form, TextAreaField, validators
from dotenv import load_dotenv
from datetime import datetime
import requests
import sqlite3
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
conn = sqlite3.connect('users.db')


#HOME PAGE
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

#SIGNUP ROUTES
@app.route('/signup')
def signup():
    return render_template('signup.html')
@app.route('/signup_verify', methods=['POST'])
def signup_verify():
    Name = request.form['Name']
    Email = request.form['Email']
    Pass = request.form['Password']
    ConfPass = request.form['ConfPassword']
    if Pass != ConfPass:
        #non matching passwords ---> need to add in a prompt on webpage
        return redirect(url_for('signup'))
    hashedPassword = generate_password_hash(Pass, method='sha256')
    Desc = request.form['Desc']
    #now to add values into the database
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO EnrolledUsers VALUES(?,?,?,?)''', (Name, Email, hashedPassword, Desc))
        con.commit()

    return render_template('login.html', Prompt_For_Login = "Sign up successful! Please login to continue.")
    #return render_template('login.html')

#LOGIN ROUTES
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/login_verify', methods=['POST'])
def login_verify():
    return 1


#DASHBOARD ROUTES
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

#LOGOUT ROUTES
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
