from pickletools import optimize
import cv2
import os
import time
from cv2 import cvtColor
from cv2 import CV_64F
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from tensorflow.keras.optimizers import Adam

class Training_evaluate(tf.keras.callbacks.Callback):
    def __init__(self, x_test, y_test, model_name, img_width, img_height):
        self._IMG_WIDTH = img_width
        self._IMG_HEIGHT = img_height
        self.x_test = x_test
        self.y_test = y_test
        self.model_name = model_name
        self.IoU = list()

    def on_epoch_end(self, epoch, logs={}):
        y_pred = self.model.predict(self.x_test)
        y_pred = np.reshape(y_pred[-1], (self._IMG_HEIGHT, self._IMG_WIDTH))
        y_pred = np.where(y_pred<0.5, 0, 1).astype(np.uint8)
        y_pred = cv2.cvtColor(y_pred, cv2.COLOR_GRAY2BGR)
        y_pred_blend = cv2.addWeighted(np.reshape(self.x_test[-1], (self._IMG_HEIGHT, self._IMG_WIDTH, 3)), 0.5, y_pred, 0.5, 0, dtype=cv2.CV_64F)

        cv2.imwrite(os.path.join(os.getcwd(), 'img', 'train_evaluate', self.model_name, '1_{}_blend_{}.png'.format(self.model_name, epoch)), cv2.cvtColor(y_pred_blend.astype('uint8')*255, cv2.COLOR_BGR2RGB))
        cv2.imwrite(os.path.join(os.getcwd(), 'img', 'train_evaluate', self.model_name, '2_{}_mask_{}.png'.format(self.model_name, epoch)), y_pred.astype('uint8')*255)

        self.IoU.append(caculate_IoU_score(np.reshape(self.y_test[-1], (self._IMG_HEIGHT, self._IMG_WIDTH)), cv2.cvtColor(y_pred, cv2.COLOR_RGB2GRAY)*255))
        plt.close()
        plt.plot(self.IoU)
        plt.title('img IoU')
        plt.ylabel('IoU')
        plt.xlabel('epoch')
        plt.legend(['IoU'], loc='lower right')
        plt.savefig(os.path.join(os.getcwd(), 'img', 'IoU.png'))

def caculate_IoU_score(target, predict):
    intersection = np.logical_and(target, predict)
    union = np.logical_or(target, predict)
    return float(np.sum(intersection)) / float(np.sum(union))

def train(model, train_ds, val_ds, test_ds, data_info, optimizer=Adam(1e-4), loss='binary_crossentropy', EarlyStopping_patience=5, model_name='-', model_save=True, visual=False):
    if not os.path.isdir(os.path.join(os.getcwd(), 'img', 'train_evaluate', model_name)):
        os.makedirs(os.path.join(os.getcwd(), 'img', 'train_evaluate', model_name))
    ################################ model summary print, save
#    plot_model(model, os.path.join(os.getcwd(), 'img', 'model.png'))
    print(model.summary())
    ################################

    ################################ model optimizer, loss set
    model.compile(optimizer=optimizer, loss=loss)
    ################################

    ################################ check point
    #### 1. ckeck point model save
    chackpoint_path = os.path.join(os.getcwd(), 'checkpoints', 'checkpoint.ckpt')
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
    chackpoint_path, monitor='val_loss', save_best_only=True, save_weights_only=True, verbose = 1)
    #### 2. early stop
    earlystopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=EarlyStopping_patience)
    #### 3. save test img for each epoch
    test_img_batch, test_mask_batch = list(test_ds.take(1).as_numpy_iterator())[0]
    test_img = np.reshape(test_img_batch[-1], (data_info['img_height'], data_info['img_width'], 3))
    test_mask = cv2.cvtColor(np.reshape(test_mask_batch[-1], (data_info['img_height'], data_info['img_width'])), cv2.COLOR_GRAY2BGR)
    cv2.imwrite(os.path.join(os.getcwd(), 'img', 'train_evaluate', model_name, '0_input.png'), cv2.cvtColor(test_img*255.0, cv2.COLOR_BGR2RGB))
    cv2.imwrite(os.path.join(os.getcwd(), 'img', 'train_evaluate', model_name, '3_mask.png'), test_mask*255.0)
    performance = Training_evaluate(test_img_batch, test_mask_batch, model_name, img_width=data_info['img_width'], img_height=data_info['img_height'])
    ################################

    if visual:
        temp = []
        temp.extend(train_ds.take(2))
        temp.extend(val_ds.take(2))
        temp.extend(test_ds.take(2))
        for img, mask in temp:
            cv2.imshow("img", cv2.cvtColor(img.numpy()[0], cv2.COLOR_RGB2BGR))
            cv2.imshow("mask", cv2.cvtColor(mask.numpy()[0], cv2.COLOR_RGB2BGR))
            cv2.waitKey()
            cv2.destroyAllWindows()

    ################################ model train
    history = model.fit(train_ds, epochs=data_info['epochs'],
#            steps_per_epoch=data_info['train_len']//data_info['batch_size'],
#            validation_steps=data_info['val_len']//data_info['batch_size'],
            validation_data=val_ds,
            callbacks=[checkpoint, earlystopping, performance])
    ################################

    ################################ model save
    if model_save:
        model.save(os.path.join(os.getcwd(), 'models', '{}.h5'.format(model_name)))
    ################################
    return history