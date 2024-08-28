from flask import Flask, render_template, redirect, url_for, request, Response, session
from flask_session import Session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://db:27017/roam_emo"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
Session(app)

def available_mode_of_transport():
    if 'transport_modes' not in mongo.db.list_collection_names():
        modes = ['On Foot', 'Bicycle', 'Car (As Passenger)', 'Car (Self Driven)','Bike (As Passenger)', 'Bike (Self Driven)', 'Bus', 'Train', 'Flight']
        mongo.db.transport_modes.insert_many([{'mode': mode} for mode in modes])


@app.route("/", methods=['GET'])
def index():
    return redirect(url_for('login'))

@app.route("/register", methods=['GET','POST'])
def register():
    if session.get('username'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        if data['password'] == data['c_password']:
            if mongo.db.users.find_one({'username': data['username']}):
                return Response('<h1>User already exists!<h1>')
            mongo.db.users.insert_one({'username': data['username'], 'name': data['name'], 'email': data['emailID'], 'password': bcrypt.generate_password_hash(data['password']).decode('utf-8')})
            return redirect(url_for('login'))
        else:
            return Response('<h1>Passwords do not match!<h1>')
    return render_template('register.html')

@app.route("/login", methods=['GET','POST'])
def login():
    if session.get('username'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        user = mongo.db.users.find_one({'username': data['username']})
        if user:
            if bcrypt.check_password_hash(user['password'], data['password']):
                session['username'] = data['username']
                return redirect(url_for('home'))
            else:
                return Response('Invalid Password!')
        else:
            return Response('Invalid Usename!')
    return render_template('login.html')

@app.route("/logout", methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/home", methods=['GET'])
def home():
    if session.get('username'):
        return render_template('home.html', content = mongo.db.users.find_one({'username':session['username']}))
    else:
        return redirect(url_for('login'))

@app.route("/ride", methods=['GET','POST'])
def ride():
    if not session.get('username'):
        return redirect(url_for('login'))
    # get all the available modes of transport
    transport_modes = mongo.db.transport_modes.find()
    if request.method == 'POST':
        data = request.form
        ride_payload = {
            '_id': str(ObjectId()),
            'from': data['from_location'],
            'to': data['to_location'],
            'description': data['description'],
            'distance': data['distance'],
            'date': data['date'],
            'mode_of_transport': data['mode_of_transport']
        }
        mongo.db.users.update_one(
            {'username': session['username']},
            {'$push':{
                'rides': ride_payload
                }
            }
        )
        return render_template('ride.html', content = {'transport_modes':transport_modes, 'alert':True})
    return render_template('ride.html', content = {'transport_modes':transport_modes, 'alert':False})

@app.route("/history", methods=['GET','POST'])
def history():
    if not session.get('username'):
        return redirect(url_for('login'))
    user = session['username']
    transport_modes = mongo.db.transport_modes.find()
    if 'rides' in mongo.db.users.find_one({'username':user}).keys():
        rides = mongo.db.users.find_one({'username':user})['rides']
    else:
        rides = None
    return render_template('history.html', context={'rides':rides, 'transport_modes':transport_modes})

@app.route("/history/edit/<ride_id>", methods=['GET', 'POST'])
def edit(ride_id):
    if not session.get('username'):
        return redirect(url_for('login'))
    user = session['username']
    reqd_ride = mongo.db.users.find_one({
        'username': user,
        'rides._id': ride_id
    })
    transport_modes = mongo.db.transport_modes.find()
    if not reqd_ride:
        alert = True
        ride = None
    else:
        alert = False
        ride = reqd_ride['rides'][0]

        if request.method == 'POST':
            data = request.form
            payload = {
                '_id': ride_id,
                'from': data['from_location'],
                'to': data['to_location'],
                'description': data['description'],
                'distance': data['distance'],
                'date': data['date'],
                'mode_of_transport': data['mode_of_transport']
            }

            mongo.db.users.update_one(
                {'username': user,'rides._id': ride_id },
                {'$set': {'rides.$': payload}}
            )

            return redirect(url_for('history'))
    return render_template('edit.html', context={'ride': ride, 'alert': alert, 'transport_modes': transport_modes, 'ride_id': ride_id})


@app.route("/history/delete/<ride_id>", methods=['GET'])
def delete(ride_id):
    if not session.get('username'):
        return redirect(url_for('login'))
    user = session['username']

    reqd_ride = mongo.db.users.find_one({
        'username': user,
        'rides._id': ride_id
    })

    if not reqd_ride:
        return Response('<h1>Ride not found!</h1>')
    else:
        mongo.db.users.update_one(
            { 'username': user },
            {'$pull': {'rides': {'_id': ride_id}}}
        )
    return redirect(url_for('history'))

if __name__ == '__main__':
    available_mode_of_transport()
    app.run(debug=False, port=5000, host='0.0.0.0')
