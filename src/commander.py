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
  tiltErrList = []
  tiltOutputList = []
  panErrList = []
  panOutputList = []
  timeList = []
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
  startEvent.wait()
  cps.start()
  while True:
    if firstTimeFlag:
      firstTimeFlag = False
      startTime = epochTime()
    else:
      try:
        serialInput = serialHandler.read_until('#'.encode('utf-8')).decode('utf-8')
        logger.info('SERIAL INPUT %s', serialInput)
        tiltOutput, panOutput, _ = serialInput.split(' ')
        tiltOutputList.append(int(tiltOutput))
        panOutputList.append(int(panOutput))
        diff = epochTime() - lastTime
        if diff < 0.1:
          sleep(0.1 - diff)
      except Exception as err:
        logger.error('Serial input decode failed.')
        raise err

    lastTime = epochTime()
    data = inQ.get()
    tiltErr, panErr, finished = [data[key] for key in ('tiltErr', 'panErr', 'finished')]
    if finished:
      break

    serialOutput = f'{tiltErr * -1:.2f} {panErr * -1:.2f}$'
    serialHandler.write(serialOutput.encode('utf-8'))
    logger.info('SERIAL OUTPUT %s', serialOutput)
    cps.update()
    cps.stop()
    panErrList.append(panErr)
    tiltErrList.append(tiltErr)
    timeList.append(epochTime() - startTime)

  serialHandler.close()
  logger.info('CPS: %s', cps.fps() if len(timeList) != 0 else 0)
  pltQ.put({'timeList': timeList, 'panErrList': panErrList, 'tiltErrList': tiltErrList,
            'tiltOutputList': tiltOutputList, 'panOutputList': panOutputList})
  logger.info('COMMANDER_THREAD finished')
