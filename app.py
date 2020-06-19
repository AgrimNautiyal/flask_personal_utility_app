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
@app.route('/signup')
def signup():
    pass
@app.route('/login')
def login():
    pass

if __name__ == '__main__':
    app.run(debug=True)
