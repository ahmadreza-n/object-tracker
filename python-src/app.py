'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --tracker csrt
'''
#region import
import argparse
import logging
from queue import Queue, LifoQueue
from time import sleep
from object_tracker import TRACKER_CHOISES, ObjectTracker
from plotter import plotter
from serial_comm import SerialComm
from center_tracker import CenterTracker
#endregion

#region config
logging.basicConfig(format='[%(levelname)s] (%(threadName)s): %(message)s', level=logging.INFO)
logger = logging.getLogger()

ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=TRACKER_CHOISES,
                help='OpenCV object tracker type')
ap.add_argument('-m', '--model', type=str,
                default='./python-src/res10_300x300_ssd_iter_140000.caffemodel',
                help='path to Caffe pre-trained model')
ap.add_argument('-p', '--prototxt', type=str, default='./python-src/deploy.prototxt',
                help='path to Caffe \'deploy\' prototxt file')
ap.add_argument('--skip-serial', type=bool, default=False,
                help='Pass true to skip serial communication')
ap.add_argument('--skip-plot', type=bool, default=True, nargs='?',
                help='Pass False to skip plotting.')
ap.add_argument('-c', '--confidence', type=float, default=0.8,
                help='minimum probability to filter weak detections')
ARGS = vars(ap.parse_args())
SKIP_SERIAL = ARGS['skip_serial'] is None
SKIP_PLOT = ARGS['skip_plot'] is None
#endregion

pltQ = Queue()
errQ = LifoQueue()
centerTracker = CenterTracker(ARGS['prototxt'],
                              ARGS['model'],
                              ARGS['confidence'],
                              maxDisappeared=30)

serialThread = SerialComm(inQ=errQ,
                          outQ=pltQ,
                          name='SerialCommThread') if not SKIP_SERIAL else None

trackerThread = ObjectTracker(ARGS['tracker'],
                              serialThread,
                              errQ,
                              centerTracker,
                              name='TrackerThread',
                              daemon=True)
trackerThread.start()

if not SKIP_SERIAL and not SKIP_PLOT:
  plotter(pltQ)

trackerThread.join()
sleep(1)
