import logging
from queue import LifoQueue, Queue
import threading
from time import time as epochTime
from imutils.video import FPS
import serial

logger = logging.getLogger()

SERIAL_TIMEOUT = 2000
SERIAL_ADDRESS = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 115200

class SerialComm(threading.Thread):
  def __init__(self, inQ: LifoQueue, outQ: Queue, **kwargs):
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

  def run(self):
    logger.info('COMMANDER_THREAD started')
    pltData = {}
    cps = FPS()
    # pylint: disable=protected-access
    cps.getFPS = lambda: (0 if cps._numFrames == 0 else cps.fps())
    startTime = epochTime()
    cps.start()
    while True:
      try:
        serialInput = self.handler.read_until('#'.encode('utf-8')).decode('utf-8')
        logger.info('SERIAL INPUT %s', serialInput)
        if serialInput != '@#':
          tiltOutput, panOutput, _ = serialInput.split(' ')
          pltData['tiltOutput'] = int(tiltOutput)
          pltData['panOutput'] = int(panOutput)
          self.outQ.put(pltData)
      except Exception as err:
        logger.error('Serial input decode failed.')
        raise err

      data = self.inQ.get()
      if data is None:
        break
      tiltErr, panErr = [data[key] for key in ('tiltErr', 'panErr')]

      serialOutput = f'{tiltErr * -1:.2f} {panErr * -1:.2f}$'
      self.handler.write(serialOutput.encode('utf-8'))
      logger.info('SERIAL OUTPUT %s', serialOutput)
      cps.update()
      cps.stop()
      pltData['time'] = float(epochTime() - startTime)
      pltData['panErr'] = float(panErr)
      pltData['tiltErr'] = float(tiltErr)

    self.outQ.put(None)

    self.handler.close()
    logger.info('CPS: %s', cps.getFPS())
    logger.info('COMMANDER_THREAD finished')

  def terminate(self):
    self.outQ.put(None)
    self.handler.close()
    logger.info('COMMANDER_THREAD terminated')
