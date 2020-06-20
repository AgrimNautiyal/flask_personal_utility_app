from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from wtforms import Form, TextAreaField, validators
from dotenv import load_dotenv
from datetime import datetime
from flask import g
import requests
import sqlite3
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


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
        cur.execute('''INSERT INTO EnrolledUsers(userName, userEmail, userPassword, userDescription) VALUES(?,?,?,?)''', (Name, Email, hashedPassword, Desc))
        con.commit()

    return render_template('login.html', Prompt_For_Login = "Sign up successful! Please login to continue.")


#LOGIN ROUTES and LOGIC
class User(UserMixin):

    def __init__(self,id,name,email,password, desc, active = True):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.desc= desc
        self.active = active

    def is_authenticated(self):
        return True
        #return true if user is authenticated, provided credentials

    def is_active(self):
        return True
    #return true if user is activte and authenticated

def is_annonymous(self):
    return False
    #return true if annon, actual user return false



@login_manager.user_loader
def load_user(id):
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('SELECT userName FROM EnrolledUsers where id=?', (id,))
        name = cur.fetchall()[0][0]
        cur.execute('SELECT userEmail FROM EnrolledUsers where id=?', (id,))
        email = cur.fetchall()[0][0]
        cur.execute('SELECT userPassword FROM EnrolledUsers where id=?', (id,))
        pswd = cur.fetchall()[0][0]
        cur.execute('SELECT userDescription FROM EnrolledUsers where id=?', (id,))
        desc = cur.fetchall()[0][0]
        user =User(id, name, email, pswd, desc)
        return user

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_verify', methods=['POST'])
def login_verify():
    print("Entering login_verify route")
    Email = request.form['Email']
    Password = request.form['Password']
    #to check if email exists in our records
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('SELECT userEmail FROM EnrolledUsers where userEmail=?', (Email,))
        rows=cur.fetchall()
        if rows==[]: #failed case
            print("Try  logging in once again!")
            return redirect(url_for('login'))
        else:
            cur.execute('SELECT userPassword FROM EnrolledUsers where userEmail=?', (Email,))
            hashPass = cur.fetchall()[0][0]
            if check_password_hash(hashPass, Password):
                #time to instantiate the User object
                cur.execute('SELECT id FROM EnrolledUsers where userEmail=?', (Email,))
                id = cur.fetchall()[0][0]
                cur.execute('SELECT userName FROM EnrolledUsers where userEmail=?', (Email,))
                Name = cur.fetchall()[0][0]
                cur.execute('SELECT userDescription FROM EnrolledUsers where userEmail=?', (Email,))
                Desc = cur.fetchall()[0][0]
                print("All details fetched!")
                user = User(id, Name, Email, hashPass,Desc)
                login_user(user)
                print("User is being logged in!")
                print("I am going to dashboard")
                print(vars(current_user))
                return redirect(url_for('dashboard'))

    f="Login Failed. Please try again!"

    return render_template('login.html', Prompt_For_Login = f)





#DASHBOARD ROUTES
@app.route('/dashboard')
@login_required
def dashboard():
    print("I am in dashboard")
    print(current_user)
    return render_template('dashboard.html', name =current_user.name)


@app.route('/askContactDetails')
@login_required
def askContactDetails():
    #this function deals with displaying the form to ask for contact details
    return render_template('askcontactdetails.html', name = current_user.name.split()[0])
@app.route('/addContact', methods=['POST'])
@login_required
def addContact():
    Name = request.form['Name']
    Email = request.form['Email']
    Phone = request.form['Phone']
    Occasion = request.form['Occasion']
    Interval = request.form['Interval']
    AlertText = request.form['AlertText']
    ContactDesc = request.form['ContactDesc']
    userID = current_user.id
    #now to add the above fields in the UserContacts db
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO UserContacts(userID, conEmail, conName, conOccasion, conInterval,conPhone, conDescription, conAlertText) VALUES(?,?,?,?,?,?,?,?)''', (userID, Email, Name,Occasion,Interval,Phone, ContactDesc, AlertText))
        con.commit()
    return redirect(url_for('askContactDetails'))


@app.route('/myinfo')
@login_required
def myinfo():
    #this function deals with displaying the profile Information of our current user
    pass

#LOGOUT ROUTES
@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
