'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --video dashcam_boston.mp4 --tracker csrt
'''
#region import
# import the necessary packages
import argparse
import threading
import logging
from time import sleep, time as epochTime
import sys
import matplotlib.pyplot as plt
import cv2
import serial
from imutils.video import VideoStream
from imutils.video import FPS
#endregion

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

#region var
CAM_W = 640
CAM_H = 480
FOV_W = 75 # blue dot, change to 56 for red dot
FOV_H = FOV_W * CAM_H /CAM_W
#endregion

#region arg
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-v', '--video', type=str, help='path to input video file')
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                help='''OpenCV object tracker type. Options are: csrt, kcf,
                boosting, mil, tld, medianflow, mosse''')
ap.add_argument('-m', '--mode', type=str, default='commander',
 help='wether to command wemos or not')
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
try:
  tracker = OPENCV_OBJECT_TRACKERS[args['tracker']]()
except KeyError as err:
  logging.error('There is no such tracker %s.', args["tracker"])
  raise err

mode = args['mode']
if mode == 'commander':
  try:
    ser = serial.Serial('/dev/ttyUSB1', timeout=2000)
  except BaseException as err:
    logging.error('Serial initialization failed. %s', err)
    sys.exit()
  ser.baudrate = 115200
elif mode == 'normal':
  logging.info('Bypassing serial initialization.')
else:
  logging.error('Invalid mode %s', mode)
  sys.exit()

# if a video path was not supplied, grab the reference to the web cam
if not args.get('video', False):
  try:
    logging.info('starting video stream...')
    vs = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
    sleep(1.0)
  except Exception as err:
    logging.error('Camera error. %s', err)
    sys.exit()

# otherwise, grab a reference to the video file
else:
  try:
    vs = cv2.VideoCapture(args['video'])
  except Exception as err:
    logging.error('Loading video file %s failed. %s', args["video"], err)
    sys.exit()
#endregion

# initialize the bounding box coordinates of the object we are going
# to track
initBB = None
isInited = False
isCommanded = False
finished = False

# initialize the FPS throughput estimator
fps = None
cps = None

lock = threading.Lock()

frame = None

panErr = None
tiltErr = None

tiltErrList = []
panErrList = []
timeList = []

def updateFrame():
  while True:
    globals()['frame'] = vs.read()
    globals()['frame'] = globals()['frame'][1] if args.get('video', False) else globals()['frame']

def commander():
  logging.info('COMMANDER_THREAD started')
  firstTimeFlag = True
  zeroCommandFlag = False
  startTime = None
  lastTime = epochTime()
  while not globals()['finished']:
    if not isInited or tiltErr is None or panErr is None:
      continue
    serialInput = None
    if not firstTimeFlag:
      with lock:
        serialInput = ser.read_all()
    if serialInput:
      serialInput = serialInput.decode('ascii')
      logging.info('SERIAL INPUT %s', serialInput)
    elif firstTimeFlag:
      serialInput = '#'
      firstTimeFlag = False
      startTime = epochTime()
    elif zeroCommandFlag:
      serialInput = '#'
      zeroCommandFlag = False

    if serialInput and serialInput.find('#') != -1:
      serialOutput = f'{int(tiltErr) * -1} {int(panErr) * -1}$'
      with lock:
        ser.write(serialOutput.encode('ascii'))
      logging.info('SERIAL OUTPUT %s', serialOutput)
      globals()['isCommanded'] = True
      cps.update()
      cps.stop()
      currentTime = epochTime() - startTime
      panErrList.append(panErr)
      tiltErrList.append(tiltErr)
      timeList.append(currentTime)

  with lock:
    ser.close()
  logging.info('COMMANDER_THREAD finished')


# threading.Thread(target=updateFrame, name='updateFrame', daemon=True).start()
if mode == 'commander':
  commandThread = threading.Thread(target=commander, name='commander', daemon=True)
  commandThread.start()

# loop over frames from the video stream
while frame is None:
  frame = vs.read()
  frame = frame[1] if args.get('video', False) else frame
while not finished:
  # check to see if we have reached the end of the stream
  frame = vs.read()
  frame = frame[1] if args.get('video', False) else frame

  if frame is None:
    finished = True
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
      globals()['panErr'] = (x + w/2 - W/2)*(FOV_W/2)/(W/2)
      globals()['tiltErr'] = (y + h/2 - H/2)*(FOV_H/2)/(H/2)
    else:
      globals()['panErr'] = 0
      globals()['tiltErr'] = 0

    # update the FPS counter
    fps.update()
    fps.stop()

    # initialize the set of information we'll be displaying on
    # the frame
    info = [
        ('H Error', f'{int(tiltErr)}', (0, 0, 255)),
        ('W Error', f'{-int(panErr)}', (0, 0, 255)),
        ('Tracker', args['tracker'], (0, 0, 0)),
        ('Success', 'Yes' if success else 'No', (0, 255, 0) if success else (0, 0, 255)),
        ('Command Per Second', '{:.2f}'.format(cps.fps() if isCommanded else 0), (255, 125, 0)),
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
  if key == ord('s') and initBB is None:
    # select the bounding box of the object we want to track (make
    # sure you press ENTER or SPACE after selecting the ROI)
    initBB = cv2.selectROI('Frame', frame, fromCenter=False,
      showCrosshair=True)

    # start OpenCV object tracker using the supplied bounding box
    # coordinates, then start the FPS throughput estimator as well
    tracker.init(frame, initBB)
    fps = FPS().start()
    cps = FPS().start()
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

if mode == 'commander':
  commandThread.join()


if mode == 'commander':
  plt.plot(timeList, panErrList, label='Pan')
  plt.plot(timeList, tiltErrList, label='Tilte')
  plt.xlabel('time')
  plt.ylabel('error')
  plt.legend()
  plt.show()
