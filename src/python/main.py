'''
USAGE
python opencv_object_tracking.py
python opencv_object_tracking.py --tracker csrt
'''
#region import
import argparse
import logging
from queue import Queue
from tracker import TRACKER_CHOISES, Tracker
from plotter import plotter
#endregion

#region config
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger()

ap = argparse.ArgumentParser()
ap.add_argument('-t', '--tracker', type=str, default='csrt',
                choices=TRACKER_CHOISES,
                help='OpenCV object tracker type')
ap.add_argument('--skip-command', type=bool, default=False,
                help='Pass true to skip commanding the motors')
ARGS = vars(ap.parse_args())
SKIP_COMMAND = ARGS['skip_command']
TRACKER_TYPE = ARGS['tracker']

#endregion

pltQ = Queue()

trackerThread = Tracker(pltQ, TRACKER_TYPE, not SKIP_COMMAND, name='tracker', daemon=True)
trackerThread.start()

if not SKIP_COMMAND:
  plotter(pltQ)

trackerThread.join()
