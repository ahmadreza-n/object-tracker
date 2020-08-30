import logging
from queue import Queue
import threading
from time import time as epochTime
import serial

logger = logging.getLogger()

SERIAL_TIMEOUT = 0.05
SERIAL_ADDRESS = '/dev/ttyUSB1'
SERIAL_BAUDRATE = 115200

def commander(inQ: Queue, outQ: Queue, startEvent: threading.Event):
  firstTimeFlag = True
  startTime = None
  try:
    serialHandler = serial.Serial(SERIAL_ADDRESS, timeout=SERIAL_TIMEOUT)
  except Exception as err:
    logger.error('Serial initialization failed.')
    raise err
  serialHandler.baudrate = SERIAL_BAUDRATE
  logger.info('COMMANDER_THREAD started')
  startEvent.wait()
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
        outQ.put(pltData)
      except Exception as err:
        logger.error('Serial input decode failed.')
        raise err

    data = inQ.get()
    if data is None:
      outQ.put(None)
      break
    tiltErr, panErr = [data[key] for key in ('tiltErr', 'panErr')]

    serialOutput = f'{tiltErr * -1:.2f} {panErr * -1:.2f}$'
    serialHandler.write(serialOutput.encode('utf-8'))
    logger.info('SERIAL OUTPUT %s', serialOutput)
    pltData['time'] = float(epochTime() - startTime)
    pltData['panErr'] = float(panErr)
    pltData['tiltErr'] = float(tiltErr)

  serialHandler.close()
  logger.info('COMMANDER_THREAD finished')
