#!python2
# -*- coding: UTF-8 -*-

# REQUIREMENTS:
#
# pip install picamera[array]
# pip install imutils
#
#

# import the necessary packages
from __future__ import print_function
# from imutils.video.pivideostream import PiVideoStream
from piVideoStream.pivideostream import PiVideoStream
# from imutils.video import FPS
# from picamera.array import PiRGBArray
# from picamera import PiCamera
import argparse
import imutils
import time
import cv2
import Queue

from shapeDetector.shapedetector import ShapeDetector
from CLInterface.CLInterface import CLInterface
from SerialCom.serialcom import serialcom

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--display", type=int, default=-1,
                help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

# created a *threaded *video stream, allow the camera sensor to warmup,
# and start the FPS counter
print('Starting threaded stream.')
queue = Queue.Queue()
vs = PiVideoStream().start()
sd = ShapeDetector()
cli = CLInterface()
cli.start()
serialPort = serialcom(queue)
serialPort.start()
v = []
time.sleep(2.0)
# fps = FPS().start()

working = True
i = 0
settings = {'dispThresh': False, 'dispContours': True,
            'dispVertices': True, 'dispNames': True,
            'erodeValue': 0, 'lowerThresh': 40}
# print(setting['dispThresh'])

# loop over some frames...this time using the threaded stream
while working:
    prev = settings['dispThresh']
    settings = cli.read()
    # grab the frame from the threaded video stream and resize it
    frame = vs.read()
    # frame = imutils.resize(frame, width=600)
    frame = cv2.flip(frame, 0)
    # frame = cv2.copyMakeBorder(frame, 3, 3, 3, 3,
    #                              cv2.BORDER_CONSTANT, value=(255, 255, 255))
    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frameBlurred = cv2.GaussianBlur(frameGray, (5, 5), 0)
    frameThresh = cv2.threshold(frameBlurred, settings['lowerThresh'], 255,
                                cv2.THRESH_BINARY_INV)[1]
    frameThresh = cv2.erode(frameThresh, None,
                            iterations=settings['erodeValue'])
    frameThresh = cv2.dilate(frameThresh, None,
                             iterations=settings['erodeValue'])
    frameThresh = cv2.copyMakeBorder(frameThresh, 3, 3, 3, 3,
                                     cv2.BORDER_CONSTANT, value=(0, 0, 0))
    frameFinal = frameThresh

    # FIND CONTOURS
    cnts = cv2.findContours(frameFinal.copy(),
                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cntsCount = len(cnts)

    i = i + 1

    for c in cnts:
        M = cv2.moments(c)
        try:
            cX = int((M['m10'] / M['m00']))
            cY = int((M['m01'] / M['m00']))
            shape, v = sd.detect(c)
        except:
            continue

        c = c.astype('float')
        c = c.astype('int')

        if settings['dispContours']:
            cv2.drawContours(frame, [c], -1, (0, 255, 0), 1)
        if settings['dispNames']:
            cv2.putText(frame, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1)

        if settings['dispVertices']:
            for i in range(0, len(v)):
                cv2.circle(frame, tuple(v[i]), 4, (255, 100, 100), 1)

    # check to see if the frame should be displayed to our screen
    if args['display'] > 0:
        cv2.imshow('Frame', frame)

        if settings['dispThresh']:
            cv2.imshow('Thresholded', frameFinal)
        if prev is True and settings['dispThresh'] is False:
            cv2.destroyWindow('Thresholded')

        key = cv2.waitKey(1) & 0xFF


        # input handling - ONLY IF HIGH GUI WINDOWS EXIST
        if key == 27:
            working = False


    # update the FPS counter
    # fps.update()

    # print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    # print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# stop the timer and display FPS information
# fps.stop()

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
cli.stop()
