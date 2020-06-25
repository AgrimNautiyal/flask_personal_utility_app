from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from datetime import datetime
import requests
import sqlite3
import re

load_dotenv('.env')
app = Flask(__name__)
app.config.from_pyfile('settings.py')

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
@app.route('/sendMailFromContactPage', methods=['POST'])
def sendMail():
    try:
        #main logic for sending mails through API
        Name = request.form['Name']
        Email = request.form['Email']
        Subject = request.form['Subject']
        Source = request.form['Source']
        Message = request.form['Message']

        message = Mail(
        from_email=str(app.config.get("FROM_EMAIL")),
        to_emails=str(app.config.get("TO_EMAILS")),
        subject= Subject + '- sent by user - ' + Name,
        html_content='<strong>Hello developer, you have the following message : </strong><br>'+ Message + "<br><strong> Details of the contact are as follows: </strong><br> Email: " + Email +" Source: " + Source)
        sg = SendGridAPIClient(str(app.config.get("SENDGRID_API_KEY")))
        response = sg.send(message)

        flash('Your message was sent to the developer successfully!', 'success')
        return redirect(url_for('contact'))
    except:
        flash('Our service seems to be down for now. Please retry in a short while!', 'danger')
        return redirect(url_for('contact'))


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
    #to check if email exists in our database or not
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('''SELECT*FROM EnrolledUsers where userEmail=?''', (Email, ))
        rows=cur.fetchall()
        if rows!=[]:
            flash('User already exists. Please login to continue or register with a different ID.', 'danger')
            return redirect(url_for('signup'))
    if Pass != ConfPass:
        #non matching passwords
        error = "Your passwords Do Not match. Please try again."
        return render_template('signup.html', Prompt_For_Signup=error)

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex,Email):
        error = "You have entered an invalid Email Address. Please try again."
        return render_template('signup.html', Prompt_For_Signup=error)

    hashedPassword = generate_password_hash(Pass, method='sha256')
    Desc = request.form['Desc']

    #now to add values into the database
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO EnrolledUsers(userName, userEmail, userPassword, userDescription) VALUES(?,?,?,?)''', (Name, Email, hashedPassword, Desc))
        con.commit()

    #send a mail as a signup-reciept : will use this part to develop email based signup confirmation later to avoid spam
    message = Mail(
    from_email=str(app.config.get("FROM_EMAIL")),
    to_emails=Email,
    subject='Welcome to PromptMe!',
    html_content='Dear '+Name+". It's wonderful to have you on our platform. Here's to hoping for your pleasant stay, and in case of any issues/queries you can always contact the developer through the Contact Page on our website! Cheers :D")
    sg = SendGridAPIClient(str(app.config.get("SENDGRID_API_KEY")))
    response = sg.send(message)
    #mail has been sent to user after signup.

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
    if not Email or not Password:
        #redirect back to login and do not leave empty fields
        error = "You cannot leave any field empty. Please try again."
        return render_template('login.html', Prompt_For_Login=error)

    #to check if email is valid or not : (using regex validation)
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex,Email):
        error = "You have entered an invalid Email Address. Please try again."
        return render_template('login.html', Prompt_For_Login=error)
    #to check if email exists in our records
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('SELECT userEmail FROM EnrolledUsers where userEmail=?', (Email,))
        rows=cur.fetchall()
        if rows==[]: #failed case
            error = "The Email ID you provided doesn't exist in our database. Please try again."
            return render_template('login.html', Prompt_For_Login=error)
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
                flash('You have successfully logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Wrong password!', 'danger')
                return redirect(url_for('login'))

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
    #let's set our basic validations
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex,Email):
        error = "You have entered an invalid Email Address. Please try again."
        return render_template('askcontactdetails.html', Prompt_For_AddingContact=error)
    regex2 = "^(0/91)?[7-9][0-9]{9}$"
    if not re.search(regex2, Phone):
        flash("You have entered an invalid Phone Number. Please try again.", 'danger')
        return redirect(url_for('askContactDetails'))

    #if email or phone already exist, then invalid entry
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('''SELECT*FROM UserContacts where conEmail=? ''', (Email, ))
        rows1=cur.fetchall()
        cur.execute('''SELECT*FROM UserContacts where conPhone=? ''', (Phone, ))
        rows2=cur.fetchall()

        if rows1!=[] or rows2!=[]:
            #this means email or phone already exists
            flash("Contact already exists! Please add a different contact.", 'danger')
            return redirect(url_for('askContactDetails'))
    try:
        s=int(Interval)
        if s < 1 or s > 365:
            flash('Please keep your interval between 1 day and 365 days and try again!', 'danger')
            return redirect(url_for('askContactDetails'))
    except:
        flash('You seem to have entered an invalid interval of days. Please try again!', 'danger')
        return redirect(url_for('askContactDetails'))


    #now to add the above fields in the UserContacts db
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO UserContacts(userID, conEmail, conName, conOccasion, conInterval,conPhone, conDescription, conAlertText) VALUES(?,?,?,?,?,?,?,?)''', (userID, Email, Name,Occasion,Interval,Phone, ContactDesc, AlertText))
        con.commit()
    flash('We have added your contact!', 'success')
    return redirect(url_for('askContactDetails'))

@app.route('/addNote',methods=['POST'])
@login_required
def addNote():
    try:
        note_text = request.form['Note']
        userID = current_user.id
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            cur.execute('''INSERT INTO EnrolledUsersNotes(id, notes) VALUES (?,?)''',(userID, note_text))
            con.commit()
        flash('Your Note was successfully added!', 'success')
    except:
        flash('Your Note was not added :( ', 'danger')
    return redirect(url_for('dashboard'))
@app.route('/myinfo')
@login_required
def myinfo():
    #this function deals with displaying the profile Information of our current user
    return render_template('myinfo.html', name=current_user.name.split()[0])

#LOGOUT ROUTES
@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
