from flask import Flask, render_template, request, jsonify, flash
from wtforms import Form, TextAreaField, validators
from dotenv import load_dotenv
from datetime import datetime
import sqlite3
import json
import requests


app = Flask(__name__)

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
    pass

#LOGIN ROUTES
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/login_verify', methods=['POST'])
def login_verify():
    pass


if __name__ == '__main__':
    app.run(debug=True)
