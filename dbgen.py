import sqlite3
import datetime
conn = sqlite3.connect('users.db')

conn.execute('''CREATE TABLE EnrolledUsers(id integer primary key AUTOINCREMENT,
userName text, userEmail text, userPassword text, userDescription text)''')
