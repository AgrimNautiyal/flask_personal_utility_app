import sqlite3
import datetime
conn = sqlite3.connect('users.db')

conn.execute('''CREATE TABLE EnrolledUsers(
userName text, userEmail text, userPassword, userDescription)''')


conn.execute('''CREATE TABLE IndividualUser(
userEmail text, connName text, connEmail text, connOccasion text, connOccasion date, connInterval int, connDescription text, connAlertText text )''')


)

)
