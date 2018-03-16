# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, redirect, Response
import face_recognition
import uuid
import cv2
from flask.ext.sqlalchemy import SQLAlchemy
import pymysql
from models import *
import json
import numpy

pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://irlans:1995813zxc@localhost/test'  # 配置数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


def open_door():
    # GPIO.setwarnings(False)
    # GPIO.setmode(GPIO.BCM)
    # pin = 17 # GPIO PIN 17
    # GPIO.setup(pin, GPIO.OUT)
    # GPIO.output(pin,GPIO.HIGH)
    # time.sleep(5)
    # GPIO.output(pin, GPIO.LOW)
    # GPIO.cleanup()
    print('开门')


# @app.route('/test/function/api',methods = ['POST','GET'])
# def get_parms():
#     #api地址为127.0.0.1：5000/test/function/api，请求为post时调用function方法
#
#     if request.method == 'GET':
#         return '方法调用有误'
#     if request.method == 'POST':
#         print(request.values['a'])
#         open_door()
#         json_mess = {
#             'status':"200"
#         }
#         return jsonify(json_mess)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Camera():
    def __init__(self, locations):
        self.cap = cv2.VideoCapture(0)
        self.locations = locations

    def __del__(self):
        self.cap.release()

    def recognition(self):
        know_face_encodings = []
        unknow_uname = []
        know_uname = []

        ret, unknow_frame = self.cap.read()
        unknow_small_frame = cv2.resize(unknow_frame, (0, 0), fx=0.25, fy=0.25)
        unknow_face_locations = face_recognition.face_locations(unknow_small_frame, number_of_times_to_upsample=1)
        unknow_face_encodings = face_recognition.face_encodings(unknow_small_frame, unknow_face_locations,
                                                                num_jitters=5)

        for i in self.locations:
            know_face_encodings.append(numpy.array(json.loads(i.location)))
            unknow_uname.append(i.uname)

        for unknow_face_encoding in unknow_face_encodings:
            matchs = face_recognition.compare_faces(know_face_encodings, unknow_face_encoding, tolerance=0.4)
            print(matchs)

            if True in matchs:
                match_index = matchs.index(True)
                know_uname.append(unknow_uname[match_index])
                print(know_uname)

        for (top, right, bottom, left), uname in zip(unknow_face_locations, know_uname):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(unknow_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(unknow_frame, uname, (left, top), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 1)

        imgencode = cv2.imencode('.jpg', unknow_frame)[1]
        return imgencode.tobytes()


def gen(camera):
    while True:
        frame = camera.recognition()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files['file']

        if 'file' not in request.files:
            return redirect(request.url)

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # 图片文件有效，检测人脸并将特征码传入数据库
            photo_file = request.files['file']
            uname = request.values['uname']
            photo_name = str(uuid.uuid4())
            photo_file.save('upload/' + photo_name + '.jpg')

            know_face = face_recognition.load_image_file(photo_file)
            know_face_location = face_recognition.face_locations(know_face, number_of_times_to_upsample=1)
            know_face_encoding = face_recognition.face_encodings(know_face, know_face_location, num_jitters=5)[0]

            Locations = Location()
            Locations.pid = photo_name
            Locations.location = json.dumps(know_face_encoding.tolist())
            Locations.uname = uname
            db.session.add(Locations)

            try:
                db.session.commit()


            except Exception as e:
                db.session.rollback()
                return (e)

            return '上传成功！'
    return '''
        <!doctype html>
        <title>是目标的图片吗?</title>
        <h1>上传目标对象图片!</h1>
        <form method="POST" enctype="multipart/form-data">
          <input type="file" name="file">
          <input type="text" name="uname" placeholder="请输入姓名">
          <input type="submit" value="Upload">
        </form>
        '''


@app.route('/getlocations')
def get_locations():
    locations = Location.query.all()
    for i in locations:
        location = numpy.array(json.loads(i.location))
        print(location)
    return 'test'


@app.route('/video')
def video_page():
    # know_face_encodings = []
    locations = db.session.query(Location).all()

    # for i in locations:
    #     location = numpy.array(json.loads(i.location))
    #     know_face_encodings.append(location)
    return Response(gen(Camera(locations)), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
