import threading
import logging
from queue import Queue, LifoQueue
from time import sleep
from imutils.video import FPS, VideoStream
import cv2
from serial_comm import SerialComm

CAM_W = 640
CAM_H = 480
FOV_W = 75 # blue dot, change to 56 for red dot
FOV_H = 56.25 # blue dot, change to 42 for red dot

OPENCV_OBJECT_TRACKERS = {
    'csrt': cv2.TrackerCSRT_create,
    'kcf': cv2.TrackerKCF_create,
    'boosting': cv2.TrackerBoosting_create,
    'mil': cv2.TrackerMIL_create,
    'tld': cv2.TrackerTLD_create,
    'medianflow': cv2.TrackerMedianFlow_create,
    'mosse': cv2.TrackerMOSSE_create
}

TRACKER_CHOISES = OPENCV_OBJECT_TRACKERS.keys()

logger = logging.getLogger()

class Tracker(threading.Thread):
  def __init__(self, pltQ: Queue,
               trackerType: str, shoudCommand: bool, *args, **kwargs):
    threading.Thread.__init__(self, **kwargs)
    try:
      logger.info('starting video stream...')
      self.videoStream = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
      sleep(0.1)
      if shoudCommand:
        self.errQ = LifoQueue()
        self.serialThread = SerialComm(inQ=self.errQ, outQ=pltQ, name='Serial Comm')
    except Exception as err:
      logger.error('Camera error.')
      raise err
    self.trackerType = trackerType
    self.objectTracker = OPENCV_OBJECT_TRACKERS[trackerType]()
    self.shoudCommand = shoudCommand
    self.fps = FPS()
    # pylint: disable=protected-access
    self.fps.getFPS = lambda: (0 if self.fps._numFrames == 0 else self.fps.fps())

  def initTracker(self, frame):
    initBB = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
    if initBB == (0, 0, 0, 0):
      return None
    self.objectTracker.init(frame, initBB)
    self.fps.start()
    if self.shoudCommand:
      try:
        self.serialThread.start()
      except Exception as err:
        logger.error('Tracker thread err.')
        raise err
    return initBB

  def track(self, frame):
    (success, box) = self.objectTracker.update(frame)
    self.fps.update()
    self.fps.stop()
    if success:
      (boxX, boxY, boxW, boxH) = [int(v) for v in box]
      cv2.rectangle(frame, (boxX, boxY), (boxX + boxW, boxY + boxH), (0, 255, 0), 2)
      panErr = (boxX + boxW/2 - CAM_W/2)*(FOV_W/2)/(CAM_W/2)
      tiltErr = (boxY + boxH/2 - CAM_H/2)*(FOV_H/2)/(CAM_H/2)
      if self.shoudCommand:
        self.errQ.put({'panErr': panErr, 'tiltErr': tiltErr})

    info = [
      ('Success' if success else 'Failure', (0, 255, 0) if success else (0, 0, 255)),
      (f'Tilt Error {tiltErr:.2f}' if success else '', (0, 0, 255)),
      (f'Pan Error {panErr:.2f}' if success else '', (0, 0, 255)),
      (f'Tracker {self.trackerType}', (0, 0, 0)),
      (f'FPS {self.fps.getFPS():.2f}', (0, 0, 255)),
    ]

    for (i, (text, color)) in enumerate(info):
      cv2.putText(frame, text, (10, 20 + (i * 20)),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


  def run(self):
    initBB = None

    while True:
      frame = self.videoStream.read()
      if frame is None:
        break
      if initBB is not None:
        self.track(frame)

      cv2.imshow('Frame', frame)
      key = cv2.waitKey(1) & 0xFF

      if key == ord('s') and initBB is None:
        initBB = self.initTracker(frame)
      elif key == ord('q'):
        break

    if self.shoudCommand and initBB is None:
      self.serialThread.terminate()
    if initBB is not None and self.shoudCommand:
      self.errQ.put(None)
      self.serialThread.join()
    self.videoStream.stop()
    cv2.destroyAllWindows()
