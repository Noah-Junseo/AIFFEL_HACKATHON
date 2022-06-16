import cv2
import os
import sys
import numpy as np
import tensorflow as tf

from threading import Thread

class model_evaluate:
    def __init__(self, path=None, cam_num=None, model_name=None):
        self.path = path
        self.cam_num = cam_num
        self.model_name = model_name
        self.connected = False
        self.mask_Thread = None
        self.video_capture = None
        self.model = None
        self.mask_img = None

    def open(self):
        if not self.connected:
            # Open model h5
            model_path = os.path.join(self.path, 'model', '{}.h5'.format(self.model_name))
            print(model_path)
            if os.path.isfile(model_path):
                self.model = tf.keras.models.load_model(model_path, compile=False)
                print(self.model.summary())
            else:
                print("model h5 file can't find")
                sys.exit(0)

            if self.cam_num is not None:
                self.video_capture = cv2.VideoCapture(self.cam_num, cv2.CAP_DSHOW)
                if self.video_capture is None or not self.video_capture.isOpened():
                    print("webcam can't open")
                    sys.exit(0)
                self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
                self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

            # Start thread
            self.mask_Thread = Thread(target=model_evaluate.__modelThread, args=(self,))
            self.mask_Thread.setDaemon(True)
            self.mask_Thread.start()
            return True

    def __modelThread(self):
        while True:
            ret, frame = self.video_capture.read()
            frame = cv2.resize(frame, (self.IMG_WIDTH, self.IMG_HEIGHT), cv2.INTER_LINEAR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame/255.0
            frame = np.expand_dims(frame, axis=0)
            self.mask_img = np.squeeze(self.model(frame, training=False), axis=0)
            self.mask_img = np.where(self.mask_img > 0.5, 0.0, 1.0).astype('float32')
            self.mask_img = cv2.cvtColor(self.mask_img, cv2.COLOR_GRAY2BGR)

            L_points = len(np.where(self.mask_img[0:self.IMG_HEIGHT//2, 0:self.IMG_WIDTH//2,0]>0.5)[0])+len(np.where(self.mask_img[0:self.IMG_HEIGHT//2, 0:self.IMG_WIDTH//2,0]>0.5)[1])
            R_points = len(np.where(self.mask_img[0:self.IMG_HEIGHT//2, self.IMG_WIDTH//2+1:self.IMG_WIDTH,0]>0.5)[0])+len(np.where(self.mask_img[0:self.IMG_HEIGHT//2, self.IMG_WIDTH//2+1:self.IMG_WIDTH,0]>0.5)[1])
            if L_points<100 and R_points<100:
                print('길 없음')
            elif abs(L_points-R_points)<50:
                cv2.arrowedLine(self.mask_img, (self.IMG_WIDTH//2, self.IMG_HEIGHT), ((self.IMG_WIDTH//2), self.IMG_HEIGHT//4), (0,0,255), 2)
            elif L_points>R_points:
                cv2.arrowedLine(self.mask_img, (self.IMG_WIDTH//2, self.IMG_HEIGHT), ((self.IMG_WIDTH//2)-10, self.IMG_HEIGHT//4), (0,0,255), 2)
            elif L_points<R_points:
                cv2.arrowedLine(self.mask_img, (self.IMG_WIDTH//2, self.IMG_HEIGHT), ((self.IMG_WIDTH//2)+10, self.IMG_HEIGHT//4), (0,0,255), 2)

    def get_mask_img(self):
        return self.mask_img