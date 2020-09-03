'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --tracker csrt
'''
#region import
import argparse
import logging
from queue import Queue
from object_tracker import TRACKER_CHOISES, ObjectTracker
from plotter import plotter
#endregion

#region config
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger()

ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=TRACKER_CHOISES,
                help='OpenCV object tracker type')
ap.add_argument('--skip-serial', type=bool, default=False,
                help='Pass true to skip serial communication')
ARGS = vars(ap.parse_args())
SKIP_SERIAL = ARGS['skip_serial']
TRACKER_TYPE = ARGS['tracker']
#endregion

pltQ = Queue()

trackerThread = ObjectTracker(pltQ, TRACKER_TYPE, not SKIP_SERIAL, name='tracker', daemon=True)
trackerThread.start()

if not SKIP_SERIAL:
  plotter(pltQ)

trackerThread.join()
