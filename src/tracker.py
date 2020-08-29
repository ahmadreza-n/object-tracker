from queue import LifoQueue
import logging
from time import sleep
import threading
import cv2
from imutils.video import VideoStream, FPS

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
  def __init__(self, videoStream: VideoStream, trackerType: str,
               outQ: LifoQueue, skipCommand: bool, startEvent: threading.Event):
    threading.Thread.__init__(self, name='tracker')
    self.videoStream = videoStream
    self.objectTracker = OPENCV_OBJECT_TRACKERS[trackerType]()
    self.trackerType = trackerType
    self.outQ = outQ
    self.shoudlCommand = not skipCommand
    self.fps = FPS()
    self.startEvent = startEvent

  def track(self, frame):
    (H, W) = frame.shape[:2]

    (success, box) = self.objectTracker.update(frame)

    if success:
      (x, y, w, h) = [int(v) for v in box]
      cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
      panErr = (x + w/2 - W/2)*(FOV_W/2)/(W/2)
      tiltErr = (y + h/2 - H/2)*(FOV_H/2)/(H/2)
    else:
      panErr = 0
      tiltErr = 0

    return (success, (tiltErr, panErr))

  def run(self):
    logger.info('TRACKER THREAD started')
    initBB = None
    while True:
      frame = self.videoStream.read()

      if frame is None:
        if self.shoudlCommand:
          self.outQ.put({'tiltErr': 0, 'panErr': 0, 'finished': True})
        break

      if initBB is not None:
        success, (tiltErr, panErr) = self.track(frame)
        if self.shoudlCommand:
          self.outQ.put({'tiltErr': tiltErr, 'panErr': panErr, 'finished': False})
        self.fps.update()
        self.fps.stop()

        info = [
            ('Success' if success else 'Failure', (0, 255, 0) if success else (0, 0, 255)),
            (f'Tilt Error {tiltErr:.2f}' if success else '', (0, 0, 255)),
            (f'Pan Error {panErr:.2f}' if success else '', (0, 0, 255)),
            (f'Tracker {self.trackerType}', (0, 0, 0)),
            (f'FPS {self.fps.fps():.2f}', (0, 0, 255)),
        ]

        for (i, (text, color)) in enumerate(info):
          cv2.putText(frame, text, (10, 20 + (i * 20)),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

      cv2.imshow('Frame', frame)
      key = cv2.waitKey(1) & 0xFF

      if key == ord('s') and initBB is None:
        initBB = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
        self.objectTracker.init(frame, initBB)
        self.startEvent.set()
        self.fps.start()
      elif key == ord('q'):
        if self.shoudlCommand:
          if not self.startEvent.isSet():
            self.startEvent.set()
          self.outQ.put({'tiltErr': 0, 'panErr': 0, 'finished': True})
        break

    cv2.destroyAllWindows()
    self.videoStream.stop()
    sleep(1)
    logger.info('TRACKER THREAD finished')
