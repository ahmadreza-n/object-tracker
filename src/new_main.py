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
from queue import Queue
import cv2
from imutils.video import VideoStream, FPS
from matplotlib import pyplot as plt
from new_tracker import TRACKER_CHOISES, tracker
from new_commander import commander
#endregion

#region var
CAM_W = 640
CAM_H = 480
FOV_W = 75 # blue dot, change to 56 for red dot
FOV_H = 56.25 # blue dot, change to 42 for red dot
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
  vs = VideoStream(src=3, resolution=(CAM_W, CAM_H), framerate=30).start()
  sleep(0.1)
except Exception as err:
  logger.error('Camera error.')
  raise err
#endregion

frameQ = Queue()
boxQ = Queue()
errQ = Queue()
pltQ = Queue()
startEvent = threading.Event()

if not SKIP_COMMAND:
  try:
    threading.Thread(target=commander, name='commander',
                     kwargs={'inQ': errQ, 'outQ': pltQ,
                             'startEvent': startEvent}).start()
  except Exception as err:
    logger.error('Commander thread err.')
    raise err


def frameUpdater():
  fps = FPS()
  initBB = None
  while True:
    frame = vs.read()

    if frame is None:
      frameQ.put(None)
      errQ.put(None)
      break

    (height, width) = frame.shape[:2]

    if initBB is not None:
      frameQ.put(frame)
      box = boxQ.get()
      fps.update()
      fps.stop()
      if box is None:
        success = False
      else:
        success = True
        (boxX, boxY, boxW, boxH) = [int(v) for v in box]
        cv2.rectangle(frame, (boxX, boxY), (boxX + boxW, boxY + boxH), (0, 255, 0), 2)
        panErr = (boxX + boxW/2 - width/2)*(FOV_W/2)/(width/2)
        tiltErr = (boxY + boxH/2 - height/2)*(FOV_H/2)/(height/2)
        errQ.put({'panErr': panErr, 'tiltErr': tiltErr})

      info = [
        ('Success' if success else 'Failure', (0, 255, 0) if success else (0, 0, 255)),
        (f'Tilt Error {tiltErr:.2f}' if success else '', (0, 0, 255)),
        (f'Pan Error {panErr:.2f}' if success else '', (0, 0, 255)),
        (f'Tracker {TRACKER_TYPE}', (0, 0, 0)),
        (f'FPS {fps.fps():.2f}', (0, 0, 255)),
      ]

      for (i, (text, color)) in enumerate(info):
        cv2.putText(frame, text, (10, 20 + (i * 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow('Frame', frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s') and initBB is None:
      initBB = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
      try:
        threading.Thread(target=tracker,
                         kwargs={'initFrame': frame, 'initBB': initBB,
                                 'trackerType': TRACKER_TYPE,
                                 'inQ': frameQ, 'outQ': boxQ}).start()
        fps.start()
        if not SKIP_COMMAND:
          startEvent.set()
      except Exception as err:
        logger.error('Tracker thread err.')
        raise err

    elif key == ord('q'):
      frameQ.put(None)
      if initBB is None:
        startEvent.set()
      errQ.put(None)
      break

  cv2.destroyAllWindows()
  vs.stop()
  sleep(1)

threading.Thread(target=frameUpdater, name='frame').start()

if not SKIP_COMMAND:
  fig, axs = plt.subplots(2)
  timeList = []
  panErrList = []
  panOutputList = []
  tiltErrList = []
  tiltOutputList = []
  def callBack():
    while True:
      data = pltQ.get()
      if data is None:
        break
      timeList.append(data['time'])
      panErrList.append(data['panErr'])
      panOutputList.append(data['panOutput'])
      tiltErrList.append(data['tiltErr'])
      tiltOutputList.append(data['tiltOutput'])

      axs[0].plot(timeList, panErrList, label='Pan Error', color='r')
      axs[0].plot(timeList, panOutputList, label='Pan Output', color='g')

      if len(timeList) == 1:
        axs[0].legend()

      axs[1].plot(timeList, tiltErrList, label='Tilt Error', color='r')
      axs[1].plot(timeList, tiltOutputList, label='Tilt Output', color='g')
      if len(timeList) == 1:
        axs[1].legend()

      fig.canvas.draw()
    plt.show()
  timer = fig.canvas.new_timer(interval=100)
  timer.add_callback(callBack)
  timer.start()

  plt.show()

for thread in threading.enumerate():
  if thread is not threading.main_thread():
    thread.join()
