'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --video dashcam_boston.mp4 --tracker csrt
'''
#region import
import argparse
import threading
import logging
from time import time as epochTime
import sys
import matplotlib.pyplot as plt
import cv2
import serial
from imutils.video import VideoStream
from imutils.video import FPS
#endregion

#region var
CAM_W = 640
CAM_H = 480
FOV_W = 75 # blue dot, change to 56 for red dot
FOV_H = FOV_W * CAM_H /CAM_W

SERIAL_TIMEOUT = 2000
SERIAL_ADDRESS = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 115200

OPENCV_OBJECT_TRACKERS = {
    'csrt': cv2.TrackerCSRT_create,
    'kcf': cv2.TrackerKCF_create,
    'boosting': cv2.TrackerBoosting_create,
    'mil': cv2.TrackerMIL_create,
    'tld': cv2.TrackerTLD_create,
    'medianflow': cv2.TrackerMedianFlow_create,
    'mosse': cv2.TrackerMOSSE_create
}

fps = FPS()
cps = FPS()

lock = threading.Lock()

tiltErrList = []
panErrList = []
timeList = []

TRACKER_TYPE = None
TRACKER = None

SKIP_COMMAND = None

vs = None
isCommanded = False
finished = False
isUpdated = False

initBB = None

frame = None

panErr = None
tiltErr = None
#endregion

#region config
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=OPENCV_OBJECT_TRACKERS.keys(),
                help='''OpenCV object tracker type. Options are: csrt, kcf,
                boosting, mil, tld, medianflow, mosse''')
ap.add_argument('--skip-command', type=bool, default=False,
                help='wether to command wemos or not')
ARGS = vars(ap.parse_args())
SKIP_COMMAND = ARGS['skip_command']
TRACKER_TYPE = ARGS['tracker']
TRACKER = OPENCV_OBJECT_TRACKERS[TRACKER_TYPE]()

try:
  logging.info('starting video stream...')
  vs = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
except Exception as err:
  logging.error('Camera error. %s', err)
  sys.exit()
#endregion

def commander():
  try:
    serialHandler = serial.Serial(SERIAL_ADDRESS, timeout=SERIAL_TIMEOUT)
  except Exception as err:
    logging.error('Serial initialization failed. %s', err)
    raise err
  serialHandler.baudrate = SERIAL_BAUDRATE
  logging.info('COMMANDER_THREAD started')
  firstTimeFlag = True
  startTime = None
  while not globals()['finished']:
    if not globals()['isUpdated']:
      continue
    serialInput = None
    serialInput = serialHandler.read_all()
    if firstTimeFlag:
      serialInput = '#'
      firstTimeFlag = False
      startTime = epochTime()
    elif serialInput:
      try:
        serialInput = serialInput.decode('utf-8')
        logging.info('SERIAL INPUT %s', serialInput)
      except Exception as err:
        logging.error('Serial input decode failed. %s', err)
        serialInput = '#'

    if serialInput and serialInput.find('#') != -1:
      serialOutput = f'{int(tiltErr) * -1} {int(panErr) * -1}$'
      serialHandler.write(serialOutput.encode('utf-8'))
      logging.info('SERIAL OUTPUT %s', serialOutput)
      globals()['isCommanded'] = True
      cps.update()
      cps.stop()
      panErrList.append(panErr)
      tiltErrList.append(tiltErr)
      timeList.append(epochTime() - startTime)
      globals()['isUpdated'] = False

  serialHandler.close()
  logging.info('COMMANDER_THREAD finished')

if not SKIP_COMMAND:
  commandThread = threading.Thread(target=commander, name='commander', daemon=True)
  commandThread.start()

while not finished:
  frame = vs.read()

  if frame is None:
    finished = True
    break
  (H, W) = frame.shape[:2]

  if initBB is not None:
    (success, box) = TRACKER.update(frame)

    if success:
      (x, y, w, h) = [int(v) for v in box]
      cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
      globals()['panErr'] = (x + w/2 - W/2)*(FOV_W/2)/(W/2)
      globals()['tiltErr'] = (y + h/2 - H/2)*(FOV_H/2)/(H/2)
    else:
      globals()['panErr'] = 0
      globals()['tiltErr'] = 0

    globals()['isUpdated'] = True

    fps.update()
    fps.stop()

    info = [
        ('H Error', f'{int(tiltErr)}' if tiltErr else '', (0, 0, 255)),
        ('W Error', f'{-int(panErr)}' if panErr else '', (0, 0, 255)),
        ('Tracker', TRACKER_TYPE, (0, 0, 0)),
        ('Success', 'Yes' if success else 'No', (0, 255, 0) if success else (0, 0, 255)),
        ('Command Per Second', '{:.2f}'.format(cps.fps() if isCommanded else 0), (255, 125, 0)),
        ('FPS', '{:.2f}'.format(fps.fps()), (0, 0, 255)),
    ]

    for (i, (k, v, color)) in enumerate(info):
      text = '{}: {}'.format(k, v)
      cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

  cv2.imshow('Frame', frame)
  key = cv2.waitKey(1) & 0xFF

  if key == ord('s') and initBB is None:
    initBB = cv2.selectROI('Frame', frame, fromCenter=False,
      showCrosshair=True)
    TRACKER.init(frame, initBB)

    fps.start()
    cps.start()

  elif key == ord('q'):
    finished = True

vs.stop()

# close all windows
cv2.destroyAllWindows()

if not SKIP_COMMAND:
  commandThread.join()
  plt.plot(timeList, panErrList, label='Pan')
  plt.plot(timeList, tiltErrList, label='Tilte')
  plt.xlabel('time')
  plt.ylabel('error')
  plt.legend()
  plt.show()
