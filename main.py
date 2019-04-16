import cv2
import sys
import requests
from mail import sendEmail
from flask import Flask, render_template, Response
from camera import VideoCamera
from flask_basicauth import BasicAuth
import time
import threading
import BlynkLib
import RPi.GPIO as GPIO

file = {'imageFile':open('/home/pi/Smart-Security-Camera/a.jpg','rb')}
url = 'https://notify-api.line.me/api/notify'
token = 'HeoPBL7qDjtiKRaVjJlnrWHZypQ5Uj3gN1buyig4qFN'
msg = 'Found someone in your house!!'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token}
# Initialize Blynk
blynk = BlynkLib.Blynk('9489ad924a044777831dcacb582396e6')
pinVal = 0
aa = 0

GPIO.setwarnings(False)    # Ignore warning for now
GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
GPIO.setup(40, GPIO.OUT, initial=GPIO.LOW)   # Set pin 8 to be an output pin and set initial

# Register Virtual Pins
@blynk.VIRTUAL_WRITE(22)
def my_write_handler(value):
    print('Current V1 value: {}'.format(value))
    pinVal = int(value[0])
    if pinVal == 1:
        GPIO.output(40, GPIO.HIGH)
    else:
        GPIO.output(40, GPIO.LOW)
    #print(pinVal)
    #return pinVal
@blynk.VIRTUAL_READ(2)
def my_read_handler():
    # this widget will show some time in seconds..
    blynk.virtual_write(2, int(time.time()))
    
def lineNotify(message):
    payload = {'message':message}
    return _lineNotify(payload)

def notifyFile(filename):
    file = {'imageFile':open(filename,'rb')}
    payload = {'message': msg}
    return _lineNotify(payload,file)

def notifyPicture(url):
    payload = {'message':" ",'imageThumbnail':url,'imageFullsize':url}
    return _lineNotify(payload)

def notifySticker(stickerID,stickerPackageID):
    payload = {'message':" ",'stickerPackageId':stickerPackageID,'stickerId':stickerID}
    return _lineNotify(payload)

def _lineNotify(payload,file=None):
    import requests
    url = 'https://notify-api.line.me/api/notify'
    token = 'HeoPBL7qDjtiKRaVjJlnrWHZypQ5Uj3gN1buyig4qFN'   #EDIT
    headers = {'Authorization':'Bearer '+token}
    return requests.post(url, headers=headers , data = payload, files=file)
pinVal = 0;
email_update_interval = 10 # sends an email only once in this time interval
video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically
object_classifier = cv2.CascadeClassifier("models/facial_recognition_model.xml") # an opencv classifier

# App Globals (do not edit)
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'admin'
app.config['BASIC_AUTH_FORCE'] = False

basic_auth = BasicAuth(app)
last_epoch = 0

def check_for_objects():
    global last_epoch
    while True:
        blynk.run()
        if GPIO.input(40)==1:
            print('.')
            try:
                frame, found_obj = video_camera.get_object(object_classifier)
                if found_obj and (time.time() - last_epoch) > email_update_interval:
                    last_epoch = time.time()
                    notifyFile('/home/pi/Smart-Security-Camera-master/b.jpg')
                    print "notify"
            except:
                print "Error : ", sys.exc_info()[0]
                
@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        #cv2.imwrite('b.jpg',frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug=False)
