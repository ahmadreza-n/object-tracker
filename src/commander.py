import logging
from queue import LifoQueue
import threading
from time import sleep, time as epochTime
from imutils.video import FPS
import serial

logger = logging.getLogger()

SERIAL_TIMEOUT = 2000
SERIAL_ADDRESS = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 115200

def commander(inQ: LifoQueue, pltQ: LifoQueue, startEvent: threading.Event):
  firstTimeFlag = True
  startTime = None
  lastTime = None
  try:
    serialHandler = serial.Serial(SERIAL_ADDRESS, timeout=SERIAL_TIMEOUT)
  except Exception as err:
    logger.error('Serial initialization failed.')
    raise err
  serialHandler.baudrate = SERIAL_BAUDRATE
  logger.info('COMMANDER_THREAD started')
  cps = FPS()
  # pylint: disable=protected-access 
  cps.getFPS = lambda: 0 if cps._numFrames == 0 else cps.fps
  startEvent.wait()
  cps.start()
  pltData = {}
  while True:
    if firstTimeFlag:
      firstTimeFlag = False
      startTime = epochTime()
    else:
      try:
        serialInput = serialHandler.read_until('#'.encode('utf-8')).decode('utf-8')
        logger.info('SERIAL INPUT %s', serialInput)
        tiltOutput, panOutput, _ = serialInput.split(' ')
        pltData['tiltOutput'] = int(tiltOutput)
        pltData['panOutput'] = int(panOutput)
        pltQ.put(pltData)
        diff = epochTime() - lastTime
        if diff < 0.1:
          sleep(0.1 - diff)
      except Exception as err:
        logger.error('Serial input decode failed.')
        raise err

    lastTime = epochTime()
    data = inQ.get()
    if data is None:
      break
    tiltErr, panErr = [data[key] for key in ('tiltErr', 'panErr')]

    serialOutput = f'{tiltErr * -1:.2f} {panErr * -1:.2f}$'
    serialHandler.write(serialOutput.encode('utf-8'))
    logger.info('SERIAL OUTPUT %s', serialOutput)
    cps.update()
    cps.stop()
    pltData['time'] = float(epochTime() - startTime)
    pltData['panErr'] = float(panErr)
    pltData['tiltErr'] = float(tiltErr)

  serialHandler.close()
  pltQ.put(None)
  logger.info('CPS: %s', cps.getFPS())
  logger.info('COMMANDER_THREAD finished')
