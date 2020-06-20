import sqlite3
import datetime
conn = sqlite3.connect('users.db')

conn.execute('''CREATE TABLE EnrolledUsers(id integer primary key AUTOINCREMENT,
userName text, userEmail text, userPassword text, userDescription text)''')

conn.execute('''CREATE TABLE UserContacts(contactID integer primary key AUTOINCREMENT, userID integer,  conEmail text,
conName text, conOccasion text, conInterval integer, conPhone integer, conDescription text, conAlertText text)''')


conn.execute('''CREATE TABLE EnrolledUsersNotes(id integer, notes text)''')
