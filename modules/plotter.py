from queue import Queue
from matplotlib import pyplot as plt

def plotter(pltQ: Queue):
  fig, axs = plt.subplots(2)
  timeList = []
  panErrList = []
  panOutputList = []
  tiltErrList = []
  tiltOutputList = []
  def callBack():
    while True:
      data = pltQ.get()
      if data is None:
        break
      timeList.append(data['time'])
      panErrList.append(data['panErr'])
      panOutputList.append(data['panOutput'])
      tiltErrList.append(data['tiltErr'])
      tiltOutputList.append(data['tiltOutput'])

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
  timer = fig.canvas.new_timer(interval=10)
  timer.add_callback(callBack)
  timer.start()

  plt.show()