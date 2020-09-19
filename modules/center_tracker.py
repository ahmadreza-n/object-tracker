from collections import OrderedDict
import cv2
from scipy.spatial import distance as dist

CAM_W = 640
CAM_H = 480

class CenterTracker():
  '''
  Assign's unique ID to each detected object
  '''
  def __init__(self, prototxt: str, model: str, confidence: float, maxDisappeared=50):
    self.nextObjectID = 0
    self.objects = OrderedDict()
    self.net = cv2.dnn.readNetFromCaffe(prototxt, model)  # pylint: disable=no-member
    self.confidence = confidence
    self.maxDisappeared = maxDisappeared

  @staticmethod
  def getCenter(rect: tuple):
    (startX, startY, endX, endY) = rect
    return (int((startX + endX) / 2.0), int((startY + endY) / 2.0))

  def register(self, rect: tuple):
    self.objects[self.nextObjectID] = {'center': CenterTracker.getCenter(rect),
                                       'rect': rect, 'disappeared': 0}
    self.nextObjectID += 1

  def deregister(self, objectID: int):
    del self.objects[objectID]

  def disappear(self, objectID: int):
    self.objects[objectID]['disappeared'] += 1
    if self.objects[objectID]['disappeared'] > self.maxDisappeared:
      self.deregister(objectID)

  def disappearAll(self):
    for objectID in list(self.objects.keys()):
      self.disappear(objectID)

  def updateInfo(self, objectID: int, rect: tuple):
    self.objects[objectID]['rect'] = rect
    self.objects[objectID]['center'] = CenterTracker.getCenter(rect)
    self.objects[objectID]['disappeared'] = 0

  def getDistances(self, rects: list):
    objectCenters = [item['center'] for item in list(self.objects.values())]

    inputCenters = []
    for rect in rects:
      inputCenters.append(CenterTracker.getCenter(rect))

    return dist.cdist(objectCenters, inputCenters)

  def getRects(self, frame):
    rects = []

    blob = cv2.dnn.blobFromImage(frame, 1.0, (CAM_W, CAM_H), (104.0, 177.0, 123.0))  # pylint: disable=no-member
    self.net.setInput(blob)

    detections = self.net.forward()[0, 0]
    detections = filter(lambda x: x[2] > self.confidence, detections)
    for obj in list(detections):
      box = obj[3:7] * [CAM_W, CAM_H, CAM_W, CAM_H]
      rects.append(tuple(box.astype('int')))

    return rects

  def update(self, frame):
    rects = self.getRects(frame)

    if len(rects) == 0:
      self.disappearAll()
      return self.objects

    if len(self.objects) == 0:
      for item in rects:
        self.register(item)
      return self.objects

    objectIDs = list(self.objects.keys())

    distances = self.getDistances(rects)

    rows = distances.min(axis=1).argsort()
    cols = set()

    for row in rows:
      if len(cols) == len(rects):
        break
      indices = distances[row].argsort()
      i = 0
      col = indices[i]
      while col in cols:
        i += 1
        col = indices[i]
      cols.add(col)

    usedRows = set()

    for (row, col) in zip(rows, cols):
      self.updateInfo(objectIDs[row], rects[col])
      usedRows.add(row)

    unusedRows = set(range(0, len(self.objects))).difference(usedRows)
    for row in unusedRows:
      self.disappear(objectIDs[row])

    unusedCols = set(range(0, len(rects))).difference(cols)
    for col in unusedCols:
      self.register(rects[col])

    return self.objects
