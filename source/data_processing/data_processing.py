import os
import cv2
import sys
import xml.etree.ElementTree as elemTree
import numpy as np

from tqdm import tqdm
from . import data_loader as dl
from . import data_download as dd

##BGR
label_rgb =dict()
#label_rgb["background"] = np.array([0, 0, 0])
label_rgb["sidewalk_blocks"] = np.array([255, 0, 0])
label_rgb["sidewalk_cement"] = np.array([217, 217, 217])
label_rgb["sidewalk_urethane"] = np.array([17, 89, 198])
label_rgb["sidewalk_asphalt"] = np.array([128, 128, 128])
label_rgb["sidewalk_soil_stone"] = np.array([153, 230, 255])
label_rgb["sidewalk_damaged"] = np.array([35, 86, 55])
label_rgb["sidewalk_other"] = np.array([70, 168, 110])
label_rgb["braille_guide_blocks_normal"] = np.array([0, 255, 255])
label_rgb["braille_guide_blocks_damaged"] = np.array([96, 96, 128])
label_rgb["roadway_normal"] = np.array([255, 128, 255])
label_rgb["roadway_crosswalk"] =np.array([255, 0, 255])
label_rgb["alley_normal"] = np.array([255, 170, 230])
label_rgb["alley_crosswalk"] = np.array([255, 88, 208])
label_rgb["alley_speed_bump"] = np.array([200, 60, 138])
label_rgb["alley_damaged"] = np.array([128, 38, 88])
label_rgb["bike_lane_normal"] = np.array([155, 155, 255])
label_rgb[ "caution_zone_stairs"] = np.array([0, 192, 255])
label_rgb[ "caution_zone_manhole"] = np.array([0, 0, 255])
label_rgb[ "caution_zone_tree_zone"] = np.array([0, 255, 0])
label_rgb[ "caution_zone_grating"] = np.array([0, 128, 255])
label_rgb[ "caution_zone_repair_zone"] = np.array([255, 105, 105])

def data_processing(channel=1):
    mask_img_paths = dl.load_path(os.path.join(os.getcwd(), 'data'), ext=['.PNG', '.png'])

    config = dd.config_read()
    possible_labels = [i.strip() for i in config['class']['possible'].split(',')]
    impossible_lables = [i.strip() for i in config['class']['impossible'].split(',')]
    
    if(len(label_rgb.keys())!=(len(possible_labels)+len(impossible_lables))):
        print(len(possible_labels)+len(impossible_lables))
        print('labelling failed....len')
        sys.exit(0)
    else:
        for i in label_rgb.keys():
            if (i not in possible_labels) and (i not in impossible_lables):
                print('labelling failed....spelling =>{}'.format(i))
                sys.exit(0)

    for mask_img_path in tqdm(mask_img_paths):
        mask = cv2.imread(mask_img_path, cv2.IMREAD_COLOR)
        for impossible_label in impossible_lables:
            mask_temp = cv2.inRange(mask, label_rgb[impossible_label], label_rgb[impossible_label])
            mask[mask_temp>0] = (0, 0, 0)
        if channel==1:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            mask[mask>0] = 255
        cv2.imwrite(mask_img_path, mask)