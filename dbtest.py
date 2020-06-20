import sqlite3
#conn = sqlite3.connect('users.db')
#print("Connection established!")

#cur = conn.cursor()

#cur.execute('''INSERT INTO EnrolledUsers values('Agrim', 'ag@in.com', 'password123', 'Cool')''')
#conn.commit()
#print("Done")





with sqlite3.connect('users.db') as con:
    cur=con.cursor()
    cur.execute('SELECT * FROM UserContacts')
    rows=cur.fetchall()
    print(rows)


