from flask import Flask, render_template, Response, request, jsonify,  redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
import cv2
from datetime import datetime
import face_recognition
import numpy as np
import simplejpeg
import math
import serial
import adafruit_fingerprint
import time


font = cv2.FONT_HERSHEY_SIMPLEX
# uart = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=1)
# finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'qwertyuiopasdfghjklzxcvbnm'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://rozi:admin@localhost/final_project"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db)


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    day_jonined = db.Column(db.Date, default=datetime.utcnow(), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=False)
    # landmark = db.Column(db.LargeBinary)
    landmark = db.Column(db.ARRAY(db.Float), nullable=False)
    fingerprint_taken = db.Column(db.Boolean, default=False)
    checkIn_time = db.relationship('CheckIn', backref='users')


class CheckIn(db.Model):
    __tablename__ = "checkIn_time"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    time_checkIn = db.Column(db.DateTime, nullable=False)
    checkIn_img = db.Column(db.LargeBinary, nullable=False)


# ===================================================================


def face_distance_to_conf(face_distance, face_match_threshold=0.5):
    if face_distance > face_match_threshold:
        range = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range * 2.0)
        return linear_val
    else:
        range = face_match_threshold
        linear_val = 1.0 - (face_distance / (range * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))


def openCamera():
    global img
    video = cv2.VideoCapture(0)
    while (video.isOpened()):
        ret, img0 = video.read()
        img0 = cv2.cvtColor(img0, cv2.COLOR_BGR2RGB)
        if not ret:
            break
        img = cv2.flip(img0, 1)
        frame = simplejpeg.encode_jpeg(img)
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    with open('static/img/alt.jpg', 'rb') as f:
        frame = f.read()
    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# ===================================================================


@app.route('/')
def home_page():
    return render_template('home.html')


@app.route('/signUp')
def signUp_page():
    return render_template('signUp.html')


@app.route('/checkIn')
def checkIn_page():
    return render_template('checkIn.html')


@app.route('/checkIn_with_face')
def checkIn_with_face():
    return render_template('checkIn_with_face.html')


@app.route('/users')
def user_listing():
    users = Users.query.order_by(desc(Users.id))
    return render_template('users-list.html', users=enumerate(users))


@app.route('/checkIn_list')
def checkIn_listing():
    # checkIn_list = CheckIn.query.all()
    checkIn_list = CheckIn.query.order_by(desc(CheckIn.time_checkIn))
    return render_template('checkIn-list.html', checkIn_times=enumerate(checkIn_list))


@app.route('/fingerprint/<id>')
def fingerprint_page(id):
    return render_template('fingerprint.html')


@app.route('/checkIn_with_fingerprint')
def checkIn_with_fingerprint():
    return render_template('checkIn_with_fingerprint.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


@app.route('/signUp_processing', methods=['POST'])
def signUp_processing():
    global img
    id = 1
    locations = face_recognition.face_locations(img)
    number_of_faces = len(locations)
    id_array = db.session.query(Users.id).order_by(Users.id)
    for id_temp in id_array:
        # print(id_temp[0])
        if id_temp[0] == id:
            id += 1
        else:
            break
    try:
        name = request.form['name']
        email = request.form['email']
        if len(name) < 3:
            raise Exception("Name is too short")

        if len(email) < 3:
            raise Exception("Email is too short")

        if number_of_faces > 1:
            raise Exception('More than one person is not expected')
        if number_of_faces == 0:
            raise Exception('Nobody here')

        avatar = simplejpeg.encode_jpeg(img)

        try:
            landmark = face_recognition.face_encodings(img, locations)[0]
        except:
            raise Exception('This face cannot be detected')

        # try:
        user = Users(id=id, name=name, email=email,
                     avatar=avatar, landmark=landmark)
        with app.app_context():
            db.session.add(user)
            db.session.commit()
        # except:
        #     raise Exception('This email had been used')

        return jsonify({'success': 'Sign up successfully'})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})


@app.route('/checkIn_processing', methods=['POST'])
def checkIn_processing():
    global img, face_checkIn
    locations = face_recognition.face_locations(img)
    number_of_faces = len(locations)
    min = 1
    min_user = None
    users = Users.query.all()
    try:
        if number_of_faces > 1:
            raise Exception('More than one person is not expected')
        if number_of_faces == 0:
            raise Exception('Nobody here')

        try:
            landmark = face_recognition.face_encodings(img, locations)[0]
        except:
            raise Exception('This face cannot be detected')

        checkIn_image = simplejpeg.encode_jpeg(img)

        for user in users:
            score = face_recognition.face_distance(
                np.array([user.landmark]), landmark)[0]
            if score < min:
                min = score
                min_user = user.name
                min_id = user.id
        if min < 0.48:
            checkIn_user = min_user
            face_checkIn = CheckIn(time_checkIn=datetime.now(
            ), user_id=min_id, checkIn_img=checkIn_image)
            return jsonify({'welcome': f'Welcome {checkIn_user}', 'accuracy': round(face_distance_to_conf(min)*100, 2)})
        else:
            checkIn_user = 'unknown'
            return jsonify({'unknown': f'This user is {checkIn_user}'})
    except Exception as e:
        return jsonify({'unknown': str(e)})


@app.route('/face_confirm', methods=['POST'])
def face_confirm():
    global face_checkIn
    with app.app_context():
        db.session.add(face_checkIn)
        db.session.commit()
    return jsonify({'nofication': 'successfully'})


@app.route('/camera')
def camera():
    return Response(openCamera(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/display/<id>', methods=['GET', 'POST'])
def display_image(id):
    user = Users.query.filter_by(id=id).first()
    return Response(user.avatar, mimetype='image/jpeg')


@app.route('/display_checkIn_img/<id>', methods=['GET', 'POST'])
def display_checkIn_image(id):
    checkIn = CheckIn.query.filter_by(id=id).first()
    return Response(checkIn.checkIn_img, mimetype='image/jpeg')


@app.route('/fingerprint_processing', methods=['POST'])
def fingerprint_processing():
    try:
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
            else:
                print("Other error")

        print("Templating...", end="")
        i = finger.image_2_tz(1)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")

        print("Remove finger")
        time.sleep(1)
        while i != adafruit_fingerprint.NOFINGER:
            i = finger.get_image()
        return jsonify({'fingerprint': "First Scanned Completed, Place Same Finger Again"})
    except:
        return jsonify({'fingerprint': "Fingerprint sensor is not available"})


@app.route('/fingerprint_processing2', methods=['POST'])
def fingerprint_processing2():
    id = request.form['id_from_url']
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")
            break
        if i == adafruit_fingerprint.NOFINGER:
            print(".", end="", flush=True)
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")

    print("Templating...", end="")
    i = finger.image_2_tz(2)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
            return jsonify({'fingerprint2error': "Prints did not match"})
        else:
            print("Other error")

    i = finger.store_model(int(id))
    if i == adafruit_fingerprint.OK:
        print("Stored")
        user = Users.query.filter_by(id=int(id)).first()
        user.fingerprint_taken = True
        db.session.commit()
        return jsonify({'fingerprint2success': "Enroll Successfully"})
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return jsonify({'fingerprint2error': "error"})


@app.route('/checkIn_with_fingerprint_processing', methods=['POST'])
def checkIn_with_fingerprint_processing():
    global fingerprint_checkIn
    if get_fingerprint():
        print("Detected #", finger.finger_id,
              "with confidence", finger.confidence)
        try:
            user = Users.query.filter_by(id=finger.finger_id).first()
            with open('static/img/fingerprint.jpg', 'rb') as f:
                checkIn_image = f.read()
            fingerprint_checkIn = CheckIn(time_checkIn=datetime.now(
            ), user_id=finger.finger_id, checkIn_img=checkIn_image)

            return jsonify({'welcome': f'Welcome {user.name}'})
        except:
            return jsonify({'unknown': 'This user is unknown'})

    else:
        print("Finger not found")
        return jsonify({'unknown': 'This user is unknown'})


@app.route('/fingerprint_confirm', methods=['POST'])
def fingerprint_confirm():
    global fingerprint_checkIn
    with app.app_context():
        db.session.add(fingerprint_checkIn)
        db.session.commit()
    return jsonify({'nofication': 'successfully'})


if __name__ == '__main__':
    # use on the first run to initialize database
    # with app.app_context():
    #     db.create_all()
    #     print("database created successfully")
    app.run(host='localhost', port=5000, debug=True)
