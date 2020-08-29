'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --tracker csrt
'''
#region import
import argparse
import threading
import logging
from time import sleep
from queue import LifoQueue, Queue
import matplotlib.pyplot as plt
from imutils.video import VideoStream
from tracker import TRACKER_CHOISES, Tracker
from commander import commander
#endregion

#region var
CAM_W = 640
CAM_H = 480
#endregion

#region config
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger()

ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=TRACKER_CHOISES,
                help='OpenCV object tracker type')
ap.add_argument('--skip-command', type=bool, default=False,
                help='Pass true to skip commanding the motors')
ARGS = vars(ap.parse_args())
SKIP_COMMAND = ARGS['skip_command']
TRACKER_TYPE = ARGS['tracker']

try:
  logger.info('starting video stream...')
  vs = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
  sleep(0.1)
except Exception as err:
  logger.error('Camera error.')
  raise err
#endregion

q = LifoQueue()
pltQ = Queue()
startEvent = threading.Event()


try:
  trackerThread = Tracker(videoStream=vs, trackerType=TRACKER_TYPE,
                          outQ=q, skipCommand=SKIP_COMMAND,
                          startEvent=startEvent)
  trackerThread.start()
except Exception as err:
  logger.error('Tracker thread err.')
  raise err

if not SKIP_COMMAND:
  try:
    commandThread = threading.Thread(target=commander, name='commander',
                                     kwargs={'inQ': q, 'pltQ': pltQ, 'startEvent': startEvent})
    commandThread.start()
  except Exception as err:
    logger.error('Commander thread err.')
    raise err


fig, a = plt.subplots(2)
timeList = []
panErrList = []
panOutputList = []
tiltErrList = []
tiltOutputList = []
plt.ion()

while True:
  plt.pause(0.001)
  data = pltQ.get()
  if data is None:
    break
  time, panErr, tiltErr, panOutput, tiltOutput = [
    data[key] for key in ('time', 'panErr', 'tiltErr', 'panOutput', 'tiltOutput')]
  timeList.append(time)
  panErrList.append(panErr)
  panOutputList.append(panOutput)
  tiltErrList.append(tiltErr)
  tiltOutputList.append(tiltOutput)

  a[0].plot(timeList, panErrList, label='Pan Error', color='r')
  a[0].plot(timeList, panOutputList, label='Pan Output', color='g')

  if len(timeList) == 1:
    a[0].legend()

  a[1].plot(timeList, tiltErrList, label='Tilt Error', color='r')
  a[1].plot(timeList, tiltOutputList, label='Tilt Output', color='g')
  if len(timeList) == 1:
    a[1].legend()

  plt.draw()

trackerThread.join()

if not SKIP_COMMAND:
  commandThread.join()
