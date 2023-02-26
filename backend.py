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
    return render_template('homepage.html', shelters=sortByBedsFree(getShelters()))


@app.route('/volunteer')
def volunteer():
    return render_template('volunteer.html') 

@app.route('/homelessrights')
def homelessRights():
    return render_template('homelessRights.html')  

@app.route('/about')
def about():
    return render_template('about.html')  

@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        if isLoggedIn():
            return render_template(
                'account.html',
                shelters=getShelters({'owner': str(getCurrentUserId())})
                )
            # userinfo=session[PROFILE_KEY], #these are ost likely unnecessary
            # userinfo_pretty=json.dumps(session[JWT_PAYLOAD], indent=4)
        else:
            return auth0.authorize_redirect(
                redirect_uri=url_for('callbackHandling', _external=True),
                audience=AUTH0_AUDIENCE
                )
    elif request.method == 'POST':
        form = request.form
        
        formData = {
            'name': form.getlist('name')[0],
            'owner': str(getCurrentUserId()),#potential security issue?
            'capacity': int(form.getlist('capacity')[0]),
            'bedsFree': int(form.getlist('bedsFree')[0]),
            'streetAddress': form.getlist('streetaddress')[0],
            'city': 'Portland',
            'state': 'Oregon',
            'zipcode': form.getlist('zipcode')[0],
            'phoneNumber': form.getlist('phoneNumber')[0],
            'emailAddress': form.getlist('emailAddress')[0],
            'webURL': form.getlist('webURL')[0]
        }

        for field in form:
            if field == 'delete':
                print("deleting")
                deleteShelter(ObjectId(str(form.getlist('shelter-id')[0])))
                break

            elif field == 'update':
                if isFormDataValid(formData):
                    print("updating")
                    formData['_id'] = ObjectId(str(form.getlist('shelter-id')[0]))
                    updateShelter(formData)
                break
                
            elif field == 'submit':
                if isFormDataValid(formData):
                    print("creating")
                    addShelter(formData)
                break
                
        return redirect('/account')

@app.route('/logout')
def logout():
    session.clear()
    params = {
        'returnTo': url_for('home', _external=True),
        'client_id': os.environ['AUTH0_CLIENT_ID']
        }
    flash('You were successfully logged out', 'alert-success')
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


def getShelters(query=None):
    allShelters = []
    if query is None:
        shelters = db.shelters.find()
    else:
        shelters = db.shelters.find(query)

    for shelter in shelters:
        if gmaps is not None:
            shelter["mapURL"] = getMapURLForShelter(constructAddress(shelter), shelter['name'])
        allShelters.append(shelter)

    return allShelters

def sortByBedsFree(shelters):
    return sorted(shelters, key=lambda shelter: shelter['bedsFree'], reverse=True)

def addShelter(shelter):
    db.shelters.insert(shelter)
    flash('Shelter Added!', 'alert-success')

def deleteShelter(id):
    db.shelters.delete_one({ "_id": id })
    flash('Shelter Deleted!', 'alert-success')

def updateShelter(shelterData):
    shelterQuery={ '_id': shelterData['_id']}
    shelter=getShelters({ '_id': shelterData['_id']})[0]
    updateQuery={}

    for key, value in shelterData.items():
        if 'phoneNumber' not in shelter.keys():
            shelter['phoneNumber'] = ''
        if 'emailAddress' not in shelter.keys():
            shelter['emailAddress'] = ''
        if 'webURL' not in shelter.keys():
            shelter['webURL'] = ''


        if shelter[key] != value: 
            updateQuery[key] = value


    if updateQuery == {}:
        flash("Could not update this shelter. No information has changed", 'alert-danger')
        return

    updateQuery = { "$set": updateQuery }
  
    db.shelters.update_one(shelterQuery, updateQuery)
    flash('Shelter Updated!', 'alert-success')

def isFormDataValid(formData):
    passed=True
    if formData['bedsFree'] > formData['capacity']:
        flash('Error: The number of beds available cannot be higher than the shelter capacity.', 'alert-danger')
        passed=False
    #if formData['phoneNumber'] == '':
        #flash('Error: You must now enter a phone number.', 'alert-danger')
        #passed=False
    #removed address validation on form submit because it was incorrectly fetching 
    # if getNearestPlaceWithName(constructAddress(formData), formData['name']) == None:
    #     flash('Error: The address you provided could not be found in the Google Maps database.', 'alert-danger')
    #     passed=False
    
    return passed