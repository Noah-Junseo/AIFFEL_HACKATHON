import shutil
import cv2
import os
import sys
import zipfile
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from tensorflow.keras.utils import plot_model
from tensorflow.keras.optimizers import Adam

from data_processing.data_download import ai_hub_download, config_read, data_check
from data_processing.data_processing import data_processing as mask_data_processing
from data_processing.data_loader import load_path, data_load, data_loader_set, configure_for_performance, augment
from train.train import train
from predict.test import predict
from models.unet import unet_model
from models.pspunet import pspunet
from models.pspunet_vgg16 import pspunet_vgg16
from models.deeplab_v3 import deeplab_v3
from models.fcn import fcn

def check_dir():
    trees = [os.path.join(os.getcwd(), 'data')\
    , os.path.join(os.getcwd(), 'train'), os.path.join(os.getcwd(), 'test')\
    , os.path.join(os.getcwd(), 'models'), os.path.join(os.getcwd(), 'utils')\
    , os.path.join(os.getcwd(), 'img', 'train_evaluate'), os.path.join(os.getcwd(), 'img', 'test_input'), os.path.join(os.getcwd(), 'img', 'test_output')]

    tree_result = list([True if os.path.isdir(i) else False for i in trees])
    for i, _bool in enumerate(tree_result):
        if _bool == False:
            os.makedirs(trees[i])
        if i in[5, 7]:    ## 결과 학습 중복 방지
            shutil.rmtree(trees[i])
            os.makedirs(trees[i])
    
    if os.path.isfile(os.path.join(os.getcwd(), 'result.txt')):
        os.remove(os.path.join(os.getcwd(), 'result.txt'))
    print("directory PASS")

def check_img_size(img_width, img_height):
    for _ in range(5):
        if (img_width%2 !=0) or (img_height%2 !=0):
            print('change img size')
            sys.exit(0)
        else:
            img_width=img_width/2
            img_height=img_height/2

def main():
    #################################GPU 확인
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu,  True)
            logical_gpus = tf.config.experimental.list_logical_devices('GPU')
            print("Physical GPUs: {}, lOGICAL_GPUs: {}".format(len(gpus), len(logical_gpus)))
        except RuntimeError as e:
            print(e)

    IMG_WIDTH, IMG_HEIGHT, IMG_CHANNEL = int(config_read()['size']['IMG_WIDTH']), int(config_read()['size']['IMG_HEIGHT']), int(config_read()['size']['IMG_CHANNEL'])
    BATCH_SIZE = int(config_read()['learning']['batch_size'])
    EPOCHS =int(config_read()['learning']['EPOCHS'])

    ################################# python 인자값 받기
    Download_bool = False
    Data_processing = False
    Data_load = True
    Data_augment = True
    Data_visual = False
    train_bool = True
    test_bool = True
    ################################

    ################################ config, 데이터, 디렉토리 확인
    check_img_size(img_width=IMG_WIDTH, img_height=IMG_HEIGHT)
    data_loader_set()
    check_dir()
    ################################

    ################################ 데이터 다운로드
    if Download_bool:
        ai_hub_download()
        data_check()
        print("data download DONE")
    ################################

    ################################ 데이터 전처리 ex: MASK(label에 따라 RGB -> GRAY) 
    if Data_processing:
        mask_data_processing(channel=1)
        print("mask data processing DONE")
    ################################

    ################################ 데이터 로드 ex: (IMG->tf.dataset), shuffle, resize, split
    if Data_load:
        train_ds, val_ds, test_ds, data_info = data_load(check=Data_visual,
                                                        train_split=0.8, val_split=0.1, test_split=0.1, 
                                                        shuffle=True, shuffle_seed=1004)
        print("data split DONE")
    ################################

    ################################ 데이터 전처리2 ex: random brightness, clip by value등 custom, configure for performance
    if Data_augment:
        train_ds = train_ds.map(
            augment,
            num_parallel_calls=2
        )
        train_ds = configure_for_performance(train_ds)
        val_ds = configure_for_performance(val_ds)
        test_ds = configure_for_performance(test_ds)
    ################################

    ################################ 시각화 (img, mask가 제대로 만들어졌는지 확인)
    if Data_visual:
        print('img process')
        temp = []
        temp.extend(train_ds.take(2))
        temp.extend(val_ds.take(2))
        temp.extend(test_ds.take(2))
        for img, mask in temp:
            print("img max pixel = {}, img min pixel = {}".format(np.max(img[0].numpy()), np.min(img[0].numpy())))
            print("mask max pixel = {}, mask min pixel = {}".format(np.max(mask[0].numpy()), np.min(mask[0].numpy())))
            cv2.imshow("img", cv2.cvtColor(img[0].numpy(), cv2.COLOR_RGB2BGR))
            cv2.imshow("mask", cv2.cvtColor(mask[0].numpy(), cv2.COLOR_RGB2BGR))
            cv2.waitKey()
            cv2.destroyAllWindows()
    ################################

    ################################ 모델 불러오기
    model, model_name = pspunet_vgg16(input_shape=(IMG_HEIGHT, IMG_WIDTH, IMG_CHANNEL))
#    model, model_name = deeplab_v3(input_shape=(IMG_HEIGHT, IMG_WIDTH, IMG_CHANNEL))
#    model, model_name = fcn(input_shape=(IMG_HEIGHT, IMG_WIDTH, IMG_CHANNEL))
    print(model.summary())
    ################################


    ################################ 학습
    if train_bool:
        history = train(model=model, train_ds=train_ds, val_ds=val_ds, test_ds=test_ds, data_info=data_info,
                        optimizer=Adam(1e-4), loss='binary_crossentropy', EarlyStopping_patience=3,
                        model_name=model_name, model_save=True, visual=Data_visual)
    ################################

    ################################ loss 시각화, 저장
        plt.close()
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['loss', 'val loss'], loc='upper right')
        plt.savefig(os.path.join(os.getcwd(), 'img', 'loss.png'))
    ################################
    if test_bool:
        test_input_img_paths = load_path(os.path.join(os.getcwd(), 'img', 'test_input'), ext=['.JPG', '.jpg', '.PNG', '.png'])
        test_input_imgs = []
        for test_input_img in test_input_img_paths:
            img = cv2.imread(test_input_img, cv2.IMREAD_COLOR)
            test_input_imgs.append(img)

        if 'test_ds' in locals():
            predict(model_name = model_name, img_shape=(IMG_WIDTH, IMG_HEIGHT, IMG_CHANNEL), test_ds=test_ds, test_imgs=test_input_imgs, test_paths=test_input_img_paths, data_info=data_info)
        else:
            predict(model_name = model_name, img_shape=(IMG_WIDTH, IMG_HEIGHT, IMG_CHANNEL), test_imgs=test_input_imgs, test_paths=test_input_img_paths, data_info=data_info)
        
        _zip = zipfile.ZipFile(os.path.join(os.getcwd(), "{}_{}_{}.zip".format(model_name, IMG_WIDTH, IMG_HEIGHT)), 'w')
        _zip_paths = [os.path.join(os.getcwd(), 'models', "{}.h5".format(model_name)), os.path.join(os.getcwd(), 'config.ini'), os.path.join(os.getcwd(), 'result.txt')]
        for (path, dir, files) in os.walk(os.path.join(os.getcwd(), 'img')):
            for filename in files:
                _zip_paths.append(os.path.join(path, filename))
        for path in _zip_paths:
            _zip.write(path)
        _zip.close()
        """
        첫번째 이미지는 일반적 처리보다 45배 느리므로 첫번째 이미지는 제외한 나머지 이미지로 FPS계산
        """

if __name__ == '__main__':
    main()