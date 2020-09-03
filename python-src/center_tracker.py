from collections import OrderedDict
from scipy.spatial import distance as dist

class CenterTracker():
  '''
  Assign's unique ID to each detected object
  '''
  def __init__(self, maxDisappeared=50):
    self.nextObjectID = 0
    self.objects = OrderedDict()

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

  def update(self, rects: list):
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
    cols = distances.argmin(axis=1)[rows]

    usedRows = set()
    usedCols = set()

    for (row, col) in zip(rows, cols):
      if row in usedRows or col in usedCols:
        continue

      self.updateInfo(objectIDs[row], rects[col])

      usedRows.add(row)
      usedCols.add(col)

    if distances.shape[0] >= distances.shape[1]:
      unusedRows = set(range(0, distances.shape[0])).difference(usedRows)
      for row in unusedRows:
        self.disappear(objectIDs[row])

    else:
      unusedCols = set(range(0, distances.shape[1])).difference(usedCols)
      for col in unusedCols:
        self.register(rects[col])

    return self.objects
