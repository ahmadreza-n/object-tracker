import threading
import os
import logging
from queue import LifoQueue
from time import sleep
from imutils.video import FPS, VideoStream
import cv2
from modules.center_tracker import CenterTracker

CAM_W = 640
CAM_H = 480
CAM_FOV_W = 75 # blue dot, change to 56 for red dot
CAM_FOV_H = 56.25 # blue dot, change to 42 for red dot
CAM_FRAMERATE = 30

OPENCV_OBJECT_TRACKERS = {
    'csrt': cv2.TrackerCSRT_create,
    'kcf': cv2.TrackerKCF_create,
    'boosting': cv2.TrackerBoosting_create,
    'mil': cv2.TrackerMIL_create,
    'tld': cv2.TrackerTLD_create,
    'medianflow': cv2.TrackerMedianFlow_create,
    'mosse': cv2.TrackerMOSSE_create,
    'goturn': cv2.TrackerGOTURN_create,
}

TRACKER_CHOISES = OPENCV_OBJECT_TRACKERS.keys()

logger = logging.getLogger()

class ObjectTracker(threading.Thread):
  def __init__(self,
               trackerType: str,
               serialThread: threading.Thread,
               outQ: LifoQueue,
               centerTracker: CenterTracker,
               *args, **kwargs):
    threading.Thread.__init__(self, **kwargs)
    try:
      logger.info('starting video stream...')
      self.camW = os.getenv('CAM_W')
      self.camH = os.getenv('CAM_H')
      self.camFrameRate = os.getenv('CAM_FRAMERATE')
      self.videoStream = VideoStream(src=2,
                                     resolution=(self.camW, self.camH),
                                     framerate=self.camFrameRate).start()
      sleep(0.1)
      self.serialThread = serialThread
    except Exception as err:
      logger.error('Camera error.')
      raise err
    self.trackerType = trackerType
    self.outQ = outQ
    self.centerTracker = centerTracker
    self.objectTracker = OPENCV_OBJECT_TRACKERS[trackerType]()
    self.fps = FPS()
    self.fps2 = FPS()
    # pylint: disable=protected-access
    self.fps.getFPS = lambda: (0 if self.fps._numFrames == 0 else self.fps.fps())
    self.fps2.getFPS = lambda: (0 if self.fps2._numFrames == 0 else self.fps2.fps())

  def initTracker(self, frame, rect=None):
    if rect is None:
      initBB = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
      if initBB == (0, 0, 0, 0):
        return None
    else:
      initBB = rect
    self.objectTracker.init(frame, initBB)
    if self.serialThread:
      try:
        self.serialThread.start()
      except Exception as err:
        logger.error('ObjectTracker thread err.')
        raise err
    self.fps.start()
    return initBB

  def track(self, frame):
    (success, box) = self.objectTracker.update(frame)
    self.fps.update()
    self.fps.stop()
    if success:
      (boxX, boxY, boxW, boxH) = [int(v) for v in box]
      cv2.rectangle(frame, (boxX, boxY), (boxX + boxW, boxY + boxH), (0, 255, 0), 2)
      panErr = (boxX + boxW/2 - CAM_W/2)*(CAM_FOV_W/2)/(CAM_W/2)
      panErr = round(panErr)
      tiltErr = (boxY + boxH/2 - CAM_H/2)*(CAM_FOV_H/2)/(CAM_H/2)
      tiltErr = round(tiltErr)
      if self.serialThread:
        self.outQ.put({'panErr': panErr, 'tiltErr': tiltErr})

    info = [
      ('Success' if success else 'Failure', (0, 255, 0) if success else (0, 0, 255)),
      (f'ObjectTracker {self.trackerType}', (0, 0, 0)),
      (f'FPS {self.fps.getFPS():.2f}', (0, 0, 255)),
    ]

    if success:
      info.append((f'Tilt Error {tiltErr}', (0, 0, 255)))
      info.append((f'Pan Error {panErr}', (0, 0, 255)))

    for (i, (text, color)) in enumerate(info):
      cv2.putText(frame, text, (10, 20 + (i * 20)),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

  def detect(self, frame):
    objects = self.centerTracker.update(frame)
    self.fps2.update()
    self.fps2.stop()

    for objectID, item in objects.items():
      if item['disappeared'] == 0:
        (startX, startY, endX, endY) = item['rect']
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

      center = item['center']

      text = 'ID {}'.format(objectID)
      color = (0, 0, 255) if item['disappeared'] != 0 else (0, 255, 0)
      cv2.putText(frame, text, (center[0] - 10, center[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
      cv2.circle(frame, (center[0], center[1]), 4, color, -1)
    fpsText = f'FPS {self.fps2.getFPS():.2f}'
    fpsColor = (255, 0, 0)
    cv2.putText(frame, fpsText, (10, 20 + (0 * 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, fpsColor, 2)

  def select(self, inputKey):
    objectIds = [str(key) for key in self.centerTracker.objects.keys()]
    if chr(inputKey) in objectIds:
      obj = self.centerTracker.objects[int(chr(inputKey))]
      if obj['disappeared'] == 0:
        (startX, startY, endX, endY) = obj['rect']
        return (startX, startY, endX - startX, endY - startY)
    return None

  def run(self):
    logger.info('thread started')
    initBB = None
    self.fps2.start()

    while True:
      frame = self.videoStream.read()
      if frame is None:
        break
      if initBB is not None:
        self.track(frame)
      else:
        self.detect(frame)

      cv2.imshow('Frame', frame)
      key = cv2.waitKey(1) & 0xFF

      if key == ord('s') and initBB is None:
        initBB = self.initTracker(frame)
      elif key == ord('q'):
        break
      else:
        rect = self.select(key)
        if rect is not None:
          initBB = self.initTracker(frame, rect)

    if self.serialThread and initBB is None:
      self.serialThread.terminate()
    if initBB is not None and self.serialThread:
      self.outQ.put(None)
      self.serialThread.join()
    self.videoStream.stop()
    cv2.destroyAllWindows()
    logger.info('thread finished')
