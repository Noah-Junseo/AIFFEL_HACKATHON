import os
from signal import valid_signals
import sys
import shutil
import cv2
import random
import configparser
import copy
import numpy as np
import tensorflow as tf

from PIL import Image
from glob import glob
from tqdm import tqdm
from . import data_download as dd

AUTOTUNE = tf.data.experimental.AUTOTUNE
global _batch_size
global _epochs
global _mask_channel
global _IMG_WIDTH
global _IMG_HEIGHT

def data_loader_set():
    global _IMG_WIDTH
    global _IMG_HEIGHT
    global _batch_size
    global _epochs
    global _mask_channel

    config = dd.config_read()
    _batch_size = int(config['learning']['batch_size'])
    _epochs = int(config['learning']['EPOCHS'])
    _IMG_WIDTH = int(config['size']['IMG_WIDTH'])
    _IMG_HEIGHT = int(config['size']['IMG_HEIGHT'])
    _mask_channel = int(config['size']['MASK_CHANNEL'])


def load_path(img_dir, ext=['.JPG', '.jpg']):
    img_paths = []

    for (path, dir, files) in os.walk(img_dir):
        for filename in files:
            files = sorted(files)
            if os.path.splitext(filename)[-1] in ext:
                img_paths.append(os.path.join(path, filename))
    print("이미지 개수는 {}입니다.".format(len(img_paths)))
    if len(img_paths) == 0:
        print("이미지가 없습니다!")
        sys.exit()
    return img_paths

def process_img_path(paths):
    img = tf.io.read_file(paths)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.cast(img, tf.float32)/255.0
    img = tf.image.resize(img, [_IMG_HEIGHT, _IMG_WIDTH])
    return img

def process_mask_path(paths):
    img = tf.io.read_file(paths)
    img = tf.image.decode_jpeg(img, channels=_mask_channel)
    img = tf.cast(img, tf.float32)/255.0
    img = tf.image.resize(img, [_IMG_HEIGHT, _IMG_WIDTH], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
    return img

def data_load(check=True, train_split=0.8, val_split=0.1, test_split=0.1, shuffle=True, shuffle_seed=1004):
    assert (train_split + test_split + val_split) == 1

    data_info = dict()
    input_img_paths = load_path(os.path.join(os.getcwd(), 'data'), ext=['.JPG', '.jpg'])
    mask_img_paths = load_path(os.path.join(os.getcwd(), 'data'), ext=['.PNG', '.png'])
    if dd.data_check(input_img_paths=input_img_paths, mask_img_paths=mask_img_paths):
        print("안 맞는 이미지 삭제")
        input_img_paths = load_path(os.path.join(os.getcwd(), 'data'), ext=['.JPG', '.jpg'])
        mask_img_paths = load_path(os.path.join(os.getcwd(), 'data'), ext=['.PNG', '.png'])
        if not dd.data_check(input_img_paths=input_img_paths, mask_img_paths=mask_img_paths):
            sys.exit(0)

    input_img_paths = sorted(input_img_paths, key=lambda x: int(os.path.basename(x)[-10:-4]))
    mask_img_paths = sorted(mask_img_paths, key=lambda x: int(os.path.basename(x)[-10:-4]))
    
    for idx in range(len(input_img_paths)):
        if int(os.path.basename(input_img_paths[idx])[-10:-4]) != int(os.path.basename(mask_img_paths[idx])[-10:-4]):
            print("순서가 안맞음")
            sys.exit(0)
    print("순서 확인 완료")

    if shuffle:
        temp = list(zip(input_img_paths, mask_img_paths))
        random.seed(shuffle_seed)
        random.shuffle(temp)
        input_img_paths, mask_img_paths = zip(*temp)

    train_size = int(train_split*len(input_img_paths))
    val_size = int(val_split*len(input_img_paths))
    test_size = int(test_split*len(input_img_paths))

    train_imgs_ds = tf.data.Dataset.list_files(input_img_paths[:train_size], shuffle=False)
    train_masks_ds = tf.data.Dataset.list_files(mask_img_paths[:train_size], shuffle=False)
    val_imgs_ds = tf.data.Dataset.list_files(input_img_paths[train_size:train_size+val_size], shuffle=False)
    val_masks_ds = tf.data.Dataset.list_files(mask_img_paths[train_size:train_size+val_size], shuffle=False)
    test_imgs_ds = tf.data.Dataset.list_files(input_img_paths[train_size+val_size:], shuffle=False)
    test_masks_ds = tf.data.Dataset.list_files(mask_img_paths[train_size+val_size:], shuffle=False)

    train_ds = tf.data.Dataset.zip((train_imgs_ds.map(process_img_path, num_parallel_calls=AUTOTUNE), train_masks_ds.map(process_mask_path, num_parallel_calls=AUTOTUNE)))
    val_ds = tf.data.Dataset.zip((val_imgs_ds.map(process_img_path, num_parallel_calls=AUTOTUNE), val_masks_ds.map(process_mask_path, num_parallel_calls=AUTOTUNE)))
    test_ds = tf.data.Dataset.zip((test_imgs_ds.map(process_img_path, num_parallel_calls=AUTOTUNE), test_masks_ds.map(process_mask_path, num_parallel_calls=AUTOTUNE)))

    if check:
        print('img load')
        temp = []
        temp.extend(train_ds.take(2))
        temp.extend(val_ds.take(2))
        temp.extend(test_ds.take(2))
        for img, mask in temp:
            cv2.imshow("img", cv2.cvtColor(img.numpy(), cv2.COLOR_RGB2BGR))
            cv2.imshow("mask", cv2.cvtColor(mask.numpy(), cv2.COLOR_RGB2BGR))
            cv2.waitKey()
            cv2.destroyAllWindows()

    data_info['train_len'] = train_size
    data_info['val_len'] = val_size
    data_info['test_len'] = test_size
    data_info['batch_size'] = _batch_size
    data_info['epochs'] = _epochs
    data_info['img_width'] = _IMG_WIDTH
    data_info['img_height'] = _IMG_HEIGHT
    data_info['mask_channel'] = _mask_channel

    return train_ds, val_ds, test_ds, data_info

def configure_for_performance(ds):
#    ds = ds.cache()
#    ds = ds.repeat()
    ds = ds.batch(_batch_size)
    ds = ds.prefetch(buffer_size=AUTOTUNE)
    return ds

def augment(img, mask):
    img = tf.image.random_brightness(img, 0.3)
    img = tf.clip_by_value(img, 0.0, 1.0)
    return img, mask
