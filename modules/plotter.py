from queue import Queue
import matplotlib
matplotlib.use('tkagg')
# pylint: disable=wrong-import-position
from matplotlib import pyplot as plt

def plotter(pltQ: Queue, mode: str):
  fig, axs = plt.subplots(2)
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

      axs[0].plot(timeList, panErrList, label='Pan Error', color='r')
      axs[0].plot(timeList, panOutputList, label='Pan Controller Output', color='g')

      if len(timeList) == 1:
        axs[0].legend()

      axs[1].plot(timeList, tiltErrList, label='Tilt Error', color='r')
      axs[1].plot(timeList, tiltOutputList, label='Tilt Controller Output', color='g')
      if len(timeList) == 1:
        axs[1].legend()

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

    axs[0].plot(timeList, panErrList, label='Pan Error', color='r')
    axs[0].plot(timeList, panOutputList, label='Pan Controller Output', color='g')

    axs[0].legend()

    axs[1].plot(timeList, tiltErrList, label='Tilt Error', color='r')
    axs[1].plot(timeList, tiltOutputList, label='Tilt Controller Output', color='g')
    axs[1].legend()

  plt.show()
