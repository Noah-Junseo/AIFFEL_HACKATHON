import sys
import cv2
import os
import time
import numpy as np
import tensorflow as tf

def caculate_IoU_score(target, predict):
    intersection = np.logical_and(target, predict)
    union = np.logical_or(target, predict)
    return float(np.sum(intersection)) / float(np.sum(union))

def test_img_processing(img):
    img = np.where(img<0.5, 0, 1).astype(np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

def predict(model_name=None, img_shape=(224, 224, 3), test_ds=None, test_imgs=None, test_paths=None, data_info=None):
    ################################ model load
    model_path = os.path.join(os.getcwd(), 'models', '{}.h5'.format(model_name))
    if os.path.isfile(model_path):
        model = tf.keras.models.load_model(os.path.join(os.getcwd(), 'models', '{}.h5'.format(model_name)), compile=False)
#        model.compile(optimizer=tf.keras.optimizers.Adam(1e-4), loss='binary_crossentropy')
        print(model.summary())
    else:
        print("model h5 file can't find")
        sys.exit(0)

    if test_ds is not None:
        start_time = time.time()
        y_pred = model.predict(test_ds,
                                steps=data_info['test_len']//data_info['batch_size'])
        total_time = time.time()-start_time
        fps = (len(y_pred)-1)/total_time

        IoU = 0
        idx = 0
        for imgs in test_ds.take(data_info['test_len']//data_info['batch_size']):
            for img in imgs[0].numpy():
                IoU += caculate_IoU_score(img, cv2.cvtColor(np.where(y_pred[idx]<0.5, 0, 1).astype('uint8')*255, cv2.COLOR_GRAY2BGR))
                idx += 1
        with open(os.path.join(os.getcwd(), 'result.txt'), 'a') as f:
            f.write('test dataset fps = {}\n'.format(fps))
            f.write("Mean IoU = {}\n".format(IoU/data_info['test_len']))
        print('test dataset fps = {}'.format(fps))
        print("Mean IoU = {}".format(IoU/data_info['test_len']))

    if len(test_paths) != 0:
        test_result_masks = []
        start_time = time.time()
        for i, img in enumerate(test_imgs):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (img_shape[0], img_shape[1]))/255.0
            img = np.expand_dims(img, axis=0)
            test_result_masks.append(np.squeeze(model(img, training=False), axis=0))
            if(i==0):
                drop_time = time.time()-start_time
        total_time = time.time()-start_time-drop_time
        fps = (len(test_imgs)-1)/total_time
        with open(os.path.join(os.getcwd(), 'result.txt'), 'a') as f:
            f.write("real fps={}\n".format(fps))

        print("real fps={}".format(fps))

        test_result_masks = list(map(test_img_processing, test_result_masks))
        test_result_blends = [cv2.cvtColor(cv2.addWeighted((cv2.resize(test_imgs[i], (img_shape[0], img_shape[1]))).astype('uint8'), 0.5, (test_result_masks[i]*255.0).astype('uint8'), 0.5, 0), cv2.COLOR_BGR2RGB) for i in range(len(test_imgs))]
        test_mask_paths = [path.replace('test_input', 'test_output') for path in test_paths]
        test_blend_paths = [path.replace('test_input', 'test_output') for path in test_paths]

        for idx in range(len(test_paths)):
            cv2.imwrite("{}_mask.jpg".format(test_mask_paths[idx][:-4]), test_result_masks[idx].astype('uint8')*255)
            cv2.imwrite("{}_blend.jpg".format(test_blend_paths[idx][:-4]), test_result_blends[idx].astype('uint8')*255)