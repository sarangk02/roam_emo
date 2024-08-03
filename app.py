from flask import Flask, render_template, redirect, url_for, request, Response, session
from flask_session import Session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/roam_emo"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
Session(app)

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

# @app.route("/history")
# def history():
#     return render_template('history.html')

@app.route("/ride", methods=['GET','POST'])
def ride():
    if request.method == 'POST':
        data = request.form
        payload = {
            'from': data['from_location'],
            'to': data['to_location'],
            'description': data['description'],
            'distance': data['distance'],
            'date': data['date'],
            'mode_of_transport': data['mode_of_transport']
        }
        print(payload)
        mongo.db.users.update_one(
            {'username': session['username']},
            {'$push':
                {'rides':payload
                    }
                }
            )
        return render_template('ride.html', content = {'alert':True})
    return render_template('ride.html', content = {'alert':False})

if __name__ == '__main__':
    app.run(debug=True)


# docker run -d -p 27017:27017 -v ~/db:/data/db --name mongodb mongo