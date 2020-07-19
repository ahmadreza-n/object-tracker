'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --video dashcam_boston.mp4 --tracker csrt
'''
#region import
# import the necessary packages
import argparse
import threading
from time import sleep
import cv2
import serial
from imutils.video import VideoStream
from imutils.video import FPS
#endregion

#region var
ser = serial.Serial('/dev/ttyUSB0', timeout=2000)
ser.baudrate = 9600

CAM_W = 640
CAM_H = 480
FOV = 75 # blue dot
# FOV = 56 # red dot
#endregion

#region arg
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-v', '--video', type=str, help='path to input video file')
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                help='''OpenCV object tracker type. Options are: csrt, kcf,
                boosting, mil, tld, medianflow, mosse''')
args = vars(ap.parse_args())

# if we are using OpenCV 3.2 OR BEFORE, we can use a special factory

# otherwise, for OpenCV 3.3 OR NEWER, we need to explicity call the
# approrpiate object tracker constructor:
# initialize a dictionary that maps strings to their corresponding
# OpenCV object tracker implementations
OPENCV_OBJECT_TRACKERS = {
    'csrt': cv2.TrackerCSRT_create,
    'kcf': cv2.TrackerKCF_create,
    'boosting': cv2.TrackerBoosting_create,
    'mil': cv2.TrackerMIL_create,
    'tld': cv2.TrackerTLD_create,
    'medianflow': cv2.TrackerMedianFlow_create,
    'mosse': cv2.TrackerMOSSE_create
}

# grab the appropriate object tracker using our dictionary of
# OpenCV object tracker objects
tracker = OPENCV_OBJECT_TRACKERS[args['tracker']]()

# if a video path was not supplied, grab the reference to the web cam
if not args.get('video', False):
  print('[INFO] starting video stream...')
  vs = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
  sleep(1.0)

# otherwise, grab a reference to the video file
else:
  vs = cv2.VideoCapture(args['video'])
#endregion

# initialize the bounding box coordinates of the object we are going
# to track
initBB = None
isInited = False
isCommanded = False
finished = False

# initialize the FPS throughput estimator
fps = None
fps2 = None

lock = threading.Lock()

frame = None

wErr = None
hErr = None

def updateFrame():
  while True:
    globals()['frame'] = vs.read()
    globals()['frame'] = globals()['frame'][1] if args.get('video', False) else globals()['frame']

def commander():
  print('COMMANDER_THREAD started')
  firstTimeFlag = True
  zeroCommandFlag = False
  while not globals()['finished']:
    if not isInited or hErr is None or wErr is None:
      continue
    serialInput = None
    if not firstTimeFlag:
      with lock:
        serialInput = ser.read_all()
    if serialInput:
      serialInput = serialInput.decode('ascii')
      print(f'SERIAL INPUT {serialInput}')
    elif firstTimeFlag or zeroCommandFlag:
      serialInput = '#'
      firstTimeFlag = False
      zeroCommandFlag = False

    hOutput = int(hErr)
    wOutput = int(wErr)
    if serialInput and serialInput.find('#') != -1:
      serialOutput = f'{hOutput} {wOutput * -1}$'
      with lock:
        ser.write(serialOutput.encode('ascii'))
      print(f'SERIAL OUTPUT {serialOutput}')
      globals()['isCommanded'] = True
      fps2.update()
      fps2.stop()

  with lock:
    ser.close()
  print('COMMANDER_THREAD finished')


threading.Thread(target=updateFrame, name='updateFrame', daemon=True).start()
commandThread = threading.Thread(target=commander, name='commander', daemon=True)
commandThread.start()

# loop over frames from the video stream
while frame is None:
  pass
while not finished:
  # grab the current frame, then handle if we are using a
  # VideoStream or VideoCapture object
  # frame = vs.read()
  # frame = frame[1] if args.get('video', False) else frame

  # check to see if we have reached the end of the stream
  if frame is None:
    break

  # resize the frame (so we can process it faster) and grab the
  # frame dimensions
  # frame = imutils.resize(frame, width=500)
  (H, W) = frame.shape[:2]

  # check to see if we are currently tracking an object
  if initBB is not None:
    # grab the new bounding box coordinates of the object
    (success, box) = tracker.update(frame)

    # check to see if the tracking was a success
    if success:
      (x, y, w, h) = [int(v) for v in box]
      cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
      globals()['wErr'] = (x + w/2 - W/2)*(FOV/2)/(W/2)
      globals()['hErr'] = (y + h/2 - H/2)*(56/2)/(H/2)
      # print(f'w err: {wErr}');
      # print(f'h err: {hErr}');
    else:
      globals()['wErr'] = 0
      globals()['hErr'] = 0

    # update the FPS counter
    fps.update()
    fps.stop()

    # initialize the set of information we'll be displaying on
    # the frame
    info = [
        ('H Error', f'{int(hErr)}', (0, 0, 255)),
        ('W Error', f'{-int(wErr)}', (0, 0, 255)),
        ('Tracker', args['tracker'], (0, 0, 0)),
        ('Success', 'Yes' if success else 'No', (0, 255, 0) if success else (0, 0, 255)),
        ('Command Per Second', '{:.2f}'.format(fps2.fps() if isCommanded else 0), (255, 125, 0)),
        ('FPS', '{:.2f}'.format(fps.fps()), (0, 0, 255)),
    ]

    # loop over the info tuples and draw them on our frame
    for (i, (k, v, color)) in enumerate(info):
      text = '{}: {}'.format(k, v)
      cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

  # show the output frame
  cv2.imshow('Frame', frame)
  key = cv2.waitKey(1) & 0xFF

  # if the 's' key is selected, we are going to 'select' a bounding
  # box to track
  if key == ord('s'):
    # select the bounding box of the object we want to track (make
    # sure you press ENTER or SPACE after selecting the ROI)
    initBB = cv2.selectROI('Frame', frame, fromCenter=False,
      showCrosshair=True)

    # start OpenCV object tracker using the supplied bounding box
    # coordinates, then start the FPS throughput estimator as well
    tracker.init(frame, initBB)
    fps = FPS().start()
    fps2 = FPS().start()
    isInited = True

  # if the `q` key was pressed, break from the loop
  elif key == ord('q'):
    finished = True

# if we are using a webcam, release the pointer
if not args.get('video', False):
  vs.stop()

# otherwise, release the file pointer
else:
  vs.release()

# close all windows
cv2.destroyAllWindows()

commandThread.join()
