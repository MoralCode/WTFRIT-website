from flask import Flask
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for
from flask import flash
import os
import json
from six.moves.urllib.parse import urlencode 
from datetime import datetime


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('homepage.html', shelters=[])


@app.route('/volunteer')
def volunteer():
    return render_template('volunteer.html') 

@app.route('/homelessrights')
def homelessRights():
    return render_template('homelessRights.html')  

@app.route('/about')
def about():
    return render_template('about.html') 