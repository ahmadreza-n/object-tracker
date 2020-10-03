from queue import Queue
import matplotlib
matplotlib.use('tkagg')
# pylint: disable=wrong-import-position
from matplotlib import pyplot as plt
from matplotlib.ticker import FormatStrFormatter

def plotter(pltQ: Queue, mode: str):
  fig, ((panErr, tiltErr), (panOutput, tiltOutput)) = plt.subplots(nrows=2, ncols=2)

  timeList = []
  panErrList = []
  panOutputList = []
  tiltErrList = []
  tiltOutputList = []

  def getData():
    data = pltQ.get()
    if data is None:
      return False
    timeList.append(data['time'])
    panErrList.append(data['panErr'])
    panOutputList.append(data['panOutput'])
    tiltErrList.append(data['tiltErr'])
    tiltOutputList.append(data['tiltOutput'])
    return True

  def callBack():
    while True:
      if not getData():
        break

      panErr.plot(timeList, panErrList, label='Pan Error', color='r')
      panOutput.plot(timeList, panOutputList, label='Pan Controller Output', color='g')

      if len(timeList) == 1:
        panErr.legend()
        panOutput.legend()

      tiltErr.plot(timeList, tiltErrList, label='Tilt Error', color='r')
      tiltOutput.plot(timeList, tiltOutputList, label='Tilt Controller Output', color='g')
      if len(timeList) == 1:
        tiltErr.legend()
        tiltOutput.legend()

      fig.canvas.draw()
    if len (timeList) ==0:
      plt.close()
    else:
      plt.show()

  if mode == 'live':
    timer = fig.canvas.new_timer(interval=178)
    timer.add_callback(callBack)
    timer.start()

  else:
    while True:
      if not getData():
        break

    panErr.plot(timeList, panErrList, label='Pan Error', color='r')
    panErr.legend()
    panOutput.plot(timeList, panOutputList, label='Pan Controller Output', color='g')
    panOutput.legend()

    tiltErr.plot(timeList, tiltErrList, label='Tilt Error', color='r')
    tiltErr.legend()
    tiltOutput.plot(timeList, tiltOutputList, label='Tilt Controller Output', color='g')
    tiltOutput.legend()

  panErr.xaxis.set_major_formatter(FormatStrFormatter('%.2f s'))
  panErr.yaxis.set_major_formatter(FormatStrFormatter('%d°'))

  panOutput.xaxis.set_major_formatter(FormatStrFormatter('%.2f s'))
  panOutput.yaxis.set_major_formatter(FormatStrFormatter('%d°'))

  tiltErr.xaxis.set_major_formatter(FormatStrFormatter('%.2f s'))
  tiltErr.yaxis.set_major_formatter(FormatStrFormatter('%d°'))

  tiltOutput.xaxis.set_major_formatter(FormatStrFormatter('%.2f s'))
  tiltOutput.yaxis.set_major_formatter(FormatStrFormatter('%d°'))
  plt.show()
