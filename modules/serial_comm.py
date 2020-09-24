import logging
from queue import Queue
import threading
from time import time as epochTime
from imutils.video import FPS
import serial

logger = logging.getLogger()

SERIAL_TIMEOUT = 2000
SERIAL_ADDRESS = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 115200

class SerialComm(threading.Thread):
  def __init__(self, inQ: Queue, outQ: Queue, readyEvent: threading.Event, *args, **kwargs):
    threading.Thread.__init__(self, **kwargs)
    try:
      self.handler = serial.Serial(SERIAL_ADDRESS, timeout=SERIAL_TIMEOUT, baudrate=SERIAL_BAUDRATE)
      self.handler.read_all()
      self.handler.flush()
      self.handler.write('@$'.encode('utf-8'))
    except Exception as err:
      logger.error('Serial initialization failed.')
      raise err
    self.inQ = inQ
    self.outQ = outQ
    self.readyEvent = readyEvent

  def run(self):
    logger.info('thread started')
    pltData = {}
    cps = FPS()
    cps.getFPS = lambda: (0 if cps._numFrames == 0 else cps.fps())  # pylint: disable=protected-access
    startTime = epochTime()
    cps.start()
    while True:
      try:
        serialInput = self.handler.read_until('#'.encode('utf-8')).decode('utf-8')
        logger.info('INPUT: %s', serialInput)
        if serialInput != '@#':
          tiltOutput, panOutput, _ = serialInput.split(' ')
          pltData['tiltOutput'] = int(tiltOutput)
          pltData['panOutput'] = int(panOutput)
          self.outQ.put(pltData)
      except Exception as err:
        logger.error('serial input failed. %s', err)
        continue

      self.readyEvent.set()
      data = self.inQ.get()
      if data is None:
        break
      tiltErr, panErr = [data[key] for key in ('tiltErr', 'panErr')]

      serialOutput = f'{tiltErr * -1} {panErr * -1}$'
      self.handler.write(serialOutput.encode('utf-8'))
      logger.info('OUTPUT: %s', serialOutput)
      cps.update()
      cps.stop()
      pltData['time'] = float(epochTime() - startTime)
      pltData['panErr'] = panErr
      pltData['tiltErr'] = tiltErr

    self.outQ.put(None)

    self.handler.close()
    logger.info('CPS: %s', cps.getFPS())
    logger.info('thread finished')

  def terminate(self):
    self.outQ.put(None)
    self.handler.close()
    logger.info('SerialComm terminated')
