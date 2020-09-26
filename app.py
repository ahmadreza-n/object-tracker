'''
USAGE
python app.py
python app.py --help
'''
#region import
import os
import argparse
import logging
from threading import Event
from queue import Queue
from time import sleep
from dotenv import load_dotenv
load_dotenv()
# pylint: disable=wrong-import-position
from modules.object_tracker import TRACKER_CHOISES, ObjectTracker
from modules.plotter import plotter
from modules.serial_comm import SerialComm
from modules.center_tracker import CenterTracker
#endregion

#region config
logging.basicConfig(format='[%(levelname)s] (%(threadName)s): %(message)s', level=logging.INFO)
logger = logging.getLogger()


ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=TRACKER_CHOISES,
                help='OpenCV object tracker type')
ap.add_argument('-m', '--model', type=str,
                default=os.path.join(os.getcwd(),
                                     'www',
                                     'res10_300x300_ssd_iter_140000.caffemodel'),
                help='path to Caffe pre-trained model')
ap.add_argument('-p', '--prototxt', type=str,
                default=os.path.join(os.getcwd(), 'www', 'deploy.prototxt'),
                help='path to Caffe \'deploy\' prototxt file')
ap.add_argument('--skip-serial', type=bool, default=False, nargs='?',
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
errQ = Queue()
readyEvent = Event()
centerTracker = CenterTracker(ARGS['prototxt'],
                              ARGS['model'],
                              ARGS['confidence'],
                              maxDisappeared=50)

serialThread = SerialComm(inQ=errQ,
                          outQ=pltQ,
                          readyEvent=readyEvent,
                          name='SerialCommThread') if not SKIP_SERIAL else None

trackerThread = ObjectTracker(ARGS['tracker'],
                              serialThread,
                              errQ,
                              readyEvent,
                              centerTracker,
                              name='TrackerThread',
                              daemon=True)
trackerThread.start()

if not SKIP_SERIAL and not SKIP_PLOT:
  plotter(pltQ)

trackerThread.join()
sleep(1)
