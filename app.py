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

@app.route('/check_flag')
@login_required
def check_flag():
    return render_template('flag.html')

@app.route('/validate_flag_info', methods=['POST'])
@login_required
def validate():
    k1 = int(request.form['K1'])
    k2 = int(request.form['K2'])

    cookie = request.form['Cookie']
    if k1 == 5 and k2 == 12 and cookie == 'IEEECTF{Could_This_Be_The_Flag_Though}':
        #condition is met
        f = str(app.config.get("FLAG"))
        print(f)
        flash(f, 'success')
        return redirect(url_for('check_flag'))
    flash('BOOO. Try again, and this time put in a little effort will you? ', 'danger')
    return redirect(url_for('check_flag'))


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


    #if email or phone already exist, then invalid entry
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        try:
            cur.execute('''SELECT userID FROM UserContacts where conEmail=?''', (Email,))
            rows1=cur.fetchall()
            rows1_id=rows1[0][0]
        except:
            rows1_id=current_user.id
            rows1=[]
        try:
            cur.execute('''SELECT userID FROM UserContacts where conPhone=?''', (Phone,))
            rows2=cur.fetchall()
            rows2_id = rows2[0][0]
        except:
            rows2_id=current_user.id
            rows2=[]

        if rows1!=[] or rows2!=[]:
            #this means email or phone already exists
            print("This condition is active")
            print
            #at this point send a mail to the current user congratulating them for discovering a design flaw
            if int(rows1_id) != int(current_user.id) or int(rows2_id)!=int(current_user.id) :
                print("Sending mail")
                print(current_user.id, "current_user_id")
                print(rows1, "rows1")
                print(rows2, "rows2")
                message = Mail(
                from_email=str(app.config.get("FROM_EMAIL")),
                to_emails=current_user.email,
                subject='You are one step closer to finding the flag',
                html_content='Hey '+current_user.name+". You've stumbled upon a major vulnerability in this system's design. Here's your cookie : IEEECTF{Could_This_Be_The_Flag_Though}. Also, take a hint : When I'm at home, it takes me forever to find the grays with the darks of life, but when I do; I get the keys to the chest with all the treasures that I seek.")
                sg = SendGridAPIClient(str(app.config.get("SENDGRID_API_KEY")))
                response = sg.send(message)
                flash("Contact already exists! Please add a different contact. Check your mail though.", 'danger')
                return redirect(url_for('askContactDetails'))
            else:
                print("Still not discovered the flaw")
                flash('Contact already exists! Please add a different contact.', 'danger')
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
    return render_template('myinfo.html', name=current_user.name.split()[0], full_name = current_user.name, Email = current_user.email, Desc = current_user.desc)
#route to display user contacts info
@app.route('/view_contact_info')
@login_required
def view_contact_info():
    users=[]
    #collect all contact IDs
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''SELECT conName, conEmail, conPhone, conAlertText, conDescription FROM UserContacts where userID=? ''', (current_user.id,))
        rows = cur.fetchall()
        tmp=[]
        for i in rows:
            tmp.append(i)
        users.append(tmp)
    #return render_template('contact_info.html', users= users)
    return render_template('contact_info.html', users = users, name = current_user.name.split()[0])


@app.route('/logged_user_settings')
@login_required
def settings():
    return render_template('user_settings.html', name = current_user.name.split()[0])

@app.route('/changePassword')
@login_required
def changePassword():
    return render_template('user_change_password_form.html', name = current_user.name.split()[0])

@app.route('/changepass', methods=['POST'])
@login_required
def changepass():
    Current_Password = request.form['C_Password']
    #compare if Current_Password hash exists for the current_user and only if True, then allow for new password change to reflect in the database
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('SELECT userPassword FROM EnrolledUsers where id=?', (current_user.id,))
        hashPass = cur.fetchall()[0][0]
        if check_password_hash(hashPass, Current_Password):
            #allow change
            New_Password = request.form['N_Password']
            if New_Password == Current_Password:
                #user seems to try to perform a redundant task, so need to invalidate the operation
                flash('New password should not match with Current password. Please Try Again.', 'danger')
                return redirect(url_for('settings'))

            newhashedPassword = generate_password_hash(New_Password, method='sha256')
            cur.execute('UPDATE EnrolledUsers SET userPassword =? where id=? ', (newhashedPassword, current_user.id,))
            con.commit();
            flash('Password changed successfully!', 'success')
            return redirect(url_for('settings'))
        else:
            #user seems to have entered a wrong password : so flash error message and reload current PAGE
            flash('Please re-enter correct current password.', 'danger')
            return redirect(url_for('changePassword'))



@app.route('/changeEmail')
@login_required
def changeEmail():
    return render_template('user_change_email_form.html')
@app.route('/changeemail', methods=['POST'])
@login_required
def changeemail():
        Current_Password = request.form['C_Password']
        #compare if Current_Password hash exists for the current_user and only if True, then allow for update
        with sqlite3.connect('users.db') as con:
            cur=con.cursor()
            cur.execute('SELECT userPassword FROM EnrolledUsers where id=?', (current_user.id,))
            hashPass = cur.fetchall()[0][0]
            if check_password_hash(hashPass, Current_Password):
                #allow change
                New_Email = request.form['N_Email']
                Prev_Email = current_user.email
                if New_Email == current_user.email:
                    #user seems to try to perform a redundant task, so need to invalidate the operation
                    flash('New email should not match with current email. Please Try Again.', 'danger')
                    return redirect(url_for('settings'))

                cur.execute('UPDATE EnrolledUsers SET userEmail =? where id=? ', (New_Email, current_user.id,))
                con.commit();
                #we can send mails to user on both previous and current user email informing change of email for securtiy reasons

                #mail alert to previous email ID
                message = Mail(
                from_email=str(app.config.get("FROM_EMAIL")),
                to_emails=Prev_Email,
                subject='Email Change Notification Alert!',
                html_content='Dear '+current_user.name.split()[0]+". We have recieved a request to change your primary Email that is required for login and communication purposes. This mail is just an alert for the same. You have chosen to set your new email address as : " +New_Email +". If you have not initiated this change, you may consider the possibility that your account has been compromised and we would advise you to change your password and secure your account!")
                sg = SendGridAPIClient(str(app.config.get("SENDGRID_API_KEY")))
                response = sg.send(message)

                #mail alert to new email ID
                message = Mail(
                from_email=str(app.config.get("FROM_EMAIL")),
                to_emails=New_Email,
                subject='Email Change Notification Alert!',
                html_content='Dear '+current_user.name.split()[0]+". We have recieved a request to change your primary Email that is required for login and communication purposes. This mail is just an alert for the same. You have chosen to set your new email address as : " +New_Email +". If you have not initiated this change, you may consider the possibility that your account has been compromised and we would advise you to change your password and secure your account!")
                sg = SendGridAPIClient(str(app.config.get("SENDGRID_API_KEY")))
                response = sg.send(message)


                flash('Email changed successfully. Please Login again to continue.', 'success')
                logout_user()
                return redirect(url_for('login'))
            else:
                #user seems to have entered a wrong password : so flash error message and reload current PAGE
                flash('Please re-enter correct current password.', 'danger')
                return redirect(url_for('changeEmail'))


@app.route('/changeDescription')
@login_required
def changeDescription():
    return render_template('user_change_description_form.html', name = current_user.name.split()[0])
@app.route('/changedescription', methods=['POST'])
@login_required
def changedescription():
    New_Desc = request.form['N_Desc']
    Prev_Desc = current_user.desc
    if New_Desc == current_user.desc:
        #user seems to try to perform a redundant task, so need to invalidate the operation
        flash('New Description should not match with current Description. Please Try Again.', 'danger')
        return redirect(url_for('settings'))
    with sqlite3.connect('users.db') as con:
        cur=con.cursor()
        cur.execute('UPDATE EnrolledUsers SET userDescription =? where id=? ', (New_Desc, current_user.id,))
        con.commit();


    flash('Your description has changed successfully.', 'success')
    return redirect(url_for('settings'))


#LOGOUT ROUTES
@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
