from queue import Queue
import logging
import cv2

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

def tracker(initFrame, initBB, trackerType: str, inQ: Queue, outQ: Queue):
  logger.info('TRACKER THREAD started')

  objectTracker = OPENCV_OBJECT_TRACKERS[trackerType]()

  objectTracker.init(initFrame, initBB)

  while True:
    frame = inQ.get()

    if frame is None:
      break

    (success, box) = objectTracker.update(frame)

    if success:
      outQ.put(box)
    else:
      outQ.put(None)

  logger.info('TRACKER THREAD finished')
