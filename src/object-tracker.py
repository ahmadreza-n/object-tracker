# USAGE
# python opencv_object_tracking.py
# python opencv_object_tracking.py --video dashcam_boston.mp4 --tracker csrt

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import argparse
import imutils
import threading
import time
import cv2
import serial

ser = serial.Serial('/dev/ttyUSB0');
ser.baudrate = 115200

CAM_W = 640
CAM_H = 480
FOV = 75 # blue dot
# FOV = 56 # red dot

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", type=str,
	help="path to input video file")
ap.add_argument("-t", "--tracker", type=str, default="kcf",
	help="OpenCV object tracker type. Options are: csrt, kcf, boosting, mil, tld, medianflow, mosse")
args = vars(ap.parse_args())

# extract the OpenCV version info
(major, minor) = cv2.__version__.split(".")[:2]

# if we are using OpenCV 3.2 OR BEFORE, we can use a special factory
# function to create our object tracker
if int(major) == 3 and int(minor) < 3:
	tracker = cv2.Tracker_create(args["tracker"].upper())

# otherwise, for OpenCV 3.3 OR NEWER, we need to explicity call the
# approrpiate object tracker constructor:
else:
	# initialize a dictionary that maps strings to their corresponding
	# OpenCV object tracker implementations
	OPENCV_OBJECT_TRACKERS = {
		"csrt": cv2.TrackerCSRT_create,
		"kcf": cv2.TrackerKCF_create,
		"boosting": cv2.TrackerBoosting_create,
		"mil": cv2.TrackerMIL_create,
		"tld": cv2.TrackerTLD_create,
		"medianflow": cv2.TrackerMedianFlow_create,
		"mosse": cv2.TrackerMOSSE_create
	}

	# grab the appropriate object tracker using our dictionary of
	# OpenCV object tracker objects
	tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

# initialize the bounding box coordinates of the object we are going
# to track
initBB = None
isInited = False
isCommanded = False

# if a video path was not supplied, grab the reference to the web cam
if not args.get("video", False):
	print("[INFO] starting video stream...")
	vs = VideoStream(src=2, resolution=(CAM_W, CAM_H), framerate=30).start()
	time.sleep(1.0)

# otherwise, grab a reference to the video file
else:
	vs = cv2.VideoCapture(args["video"])

# initialize the FPS throughput estimator
fps = None
fps2 = None

lock = threading.Lock()

frame = None

wErr = 0
hErr = 0

def worker():
	while True:
		globals()['frame'] = vs.read()
		globals()['frame'] = globals()['frame'][1] if args.get("video", False) else globals()['frame']

def commander():
	flag = True
	while True:
		if not isInited:
			continue
		a = ser.read_all()
		if a:
			print(a)
			a = a.decode('utf-8')
		if flag:
			a = 'ready'
			flag = False
		h = int(hErr)
		w = int(wErr)
		if a == 'ready':
			if w == 0 and h == 0:
				flag = True
			else:
				s = f'{h} {w * -1}'
				ser.write(s.encode('utf-8'))
				print('commanded', h, w)
				globals()["isCommanded"] = True
				fps2.update()
				fps2.stop()
			

			

threading.Thread(target=worker, name='Test', daemon=True).start()
threading.Thread(target=commander, name='Test1', daemon=True).start()

# loop over frames from the video stream
while frame is None:
	pass
while True:
	# grab the current frame, then handle if we are using a
	# VideoStream or VideoCapture object
	# frame = vs.read()
	# frame = frame[1] if args.get("video", False) else frame

	# check to see if we have reached the end of the stream
	if frame is None:
		break

	# resize the frame (so we can process it faster) and grab the
	# frame dimensions
	# frame = imutils.resize(frame, width=500)
	(H, W) = frame.shape[:2]

	# check to see if we are currently tracking an object
	if initBB is not None:
		# grab the new bounding box coordinates of the object
		(success, box) = tracker.update(frame)

		# check to see if the tracking was a success
		if success:
			(x, y, w, h) = [int(v) for v in box]
			cv2.rectangle(frame, (x, y), (x + w, y + h),
				(0, 255, 0), 2)
			globals()['wErr'] = (x + w/2 - W/2)*(FOV/2)/(W/2)
			globals()['hErr'] = (y + h/2 - H/2)*(56/2)/(H/2)
			# print(f'w err: {wErr}');
			# print(f'h err: {hErr}');
		else:
			globals()['wErr'] = 0
			globals()['hErr'] = 0

		# update the FPS counter
		fps.update()
		fps.stop()

		# initialize the set of information we'll be displaying on
		# the frame
		info = [
			("H Error", f'{int(hErr)}'),
			("W Error", f'{-int(wErr)}'),
			("Tracker", args["tracker"]),
			("Success", "Yes" if success else "No"),
			("Command FPS", "{:.2f}".format(fps2.fps() if isCommanded else 0)),
			("FPS", "{:.2f}".format(fps.fps())),
		]

		print(isCommanded)

		# loop over the info tuples and draw them on our frame
		for (i, (k, v)) in enumerate(info):
			text = "{}: {}".format(k, v)
			cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
				cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the 's' key is selected, we are going to "select" a bounding
	# box to track
	if key == ord("s"):
		# select the bounding box of the object we want to track (make
		# sure you press ENTER or SPACE after selecting the ROI)
		initBB = cv2.selectROI("Frame", frame, fromCenter=False,
			showCrosshair=True)

		# start OpenCV object tracker using the supplied bounding box
		# coordinates, then start the FPS throughput estimator as well
		tracker.init(frame, initBB)
		fps = FPS().start()
		fps2 = FPS().start()
		isInited = True

	# if the `q` key was pressed, break from the loop
	elif key == ord("q"):
		break

# if we are using a webcam, release the pointer
if not args.get("video", False):
	vs.stop()

# otherwise, release the file pointer
else:
	vs.release()

# close all windows
ser.close()
cv2.destroyAllWindows()
