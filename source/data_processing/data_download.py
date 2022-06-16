import os
import sys
import zipfile
import pyperclip
import time
import shutil
import configparser
from requests import options

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
from . import data_loader as dl

def set_chrome_driver():
#    options = Options()
#    options.add_argument('window-size=150,100')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def config_read():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.getcwd(), 'config.ini'), encoding='utf-8')
    return config

def ai_hub_download():
    config = config_read()
    implicitly_delay = int(config['time']['implicitly_delay'])

    driver = set_chrome_driver()
    driver.get('https://aihub.or.kr/aidata/136/download')
    driver.implicitly_wait(implicitly_delay)
    driver.find_element_by_xpath('//*[@id="container"]/article/div[3]/div[1]/div[2]/div/div/div/div/a[1]').click()
    driver.implicitly_wait(implicitly_delay)

    pyperclip.copy(config['AIHUB']['id'])
    driver.find_element_by_xpath('//*[@id="edit-name"]').send_keys(Keys.CONTROL + 'a')
    driver.find_element_by_xpath('//*[@id="edit-name"]').send_keys(Keys.CONTROL + 'v')
    pyperclip.copy(config['AIHUB']['pw'])
    driver.find_element_by_xpath('//*[@id="edit-pass"]').send_keys(Keys.CONTROL + 'a')
    driver.find_element_by_xpath('//*[@id="edit-pass"]').send_keys(Keys.CONTROL + 'v')
    driver.find_element_by_xpath('//*[@id="edit-submit"]').click()
    driver.implicitly_wait(implicitly_delay)
    if(driver.current_url != 'https://aihub.or.kr/aidata/136/download'):
        print("ID or PW ERROR")
        sys.exit(0)


    driver.find_element_by_xpath('//*[@id="container"]/article/div[3]/div[1]/div[2]/a[1]').click()
    driver.implicitly_wait(implicitly_delay)
    time.sleep(5)

    driver.switch_to.window(driver.window_handles[1])        
    driver.find_element_by_xpath('//*[@id="fileBox"]/div[3]/ul/li/div/div[2]/div').click()
    driver.implicitly_wait(implicitly_delay)
    driver.find_element_by_xpath('//*[@id="fileBox"]/div[3]/ul/li/ul/li[3]/div/div[1]').click()
    driver.implicitly_wait(implicitly_delay)
    driver.find_element_by_xpath('/html/body/div[2]/div[3]/input[1]').click()
    driver.implicitly_wait(implicitly_delay)

    element = driver.find_element_by_xpath('/html/body/div[4]/div/div[2]/div[6]/div/span')
    driver.execute_script("arguments[0].innerText = '{}'".format(os.path.join(os.getcwd(), 'data')).replace("\\", "/"), element)
    driver.implicitly_wait(implicitly_delay)
    driver.find_element_by_xpath('/html/body/div[4]/div/div[2]/div[5]/div[2]/button[3]').click()

    cnt = 0
    while(cnt != 100):
        cnt = int(driver.find_element_by_xpath('/html/body/div[4]/div/div[2]/div[4]/span[1]').text.split('%')[0])
        if cnt % 10 == 0:
            print("Downloading Please Wait : {}%".format(cnt))
            time.sleep(20)
    driver.quit()

    file_list = os.listdir(os.path.join(os.getcwd(), 'data', '인도보행 영상', '서피스마스킹'))
    if len([file for file in file_list if file[-4:] == '.irx']) != 0:
        print("Download ERROR")
        sys.exit(0)

    for i, file in enumerate(file_list):
        print("{} / {}".format(i+1, len(file_list)))
        with zipfile.ZipFile(os.path.join(os.getcwd(), 'data', '인도보행 영상', '서피스마스킹', file)) as zp:
            for member in tqdm(zp.infolist(), desc='Extracting '):
                zp.extract(member, os.path.join(os.getcwd(), 'data'))
        os.remove(os.path.join(os.getcwd(), 'data', '인도보행 영상', '서피스마스킹', file))
    shutil.rmtree(os.path.join(os.getcwd(), 'data', '인도보행 영상'))

def data_check(input_img_paths=None, mask_img_paths=None):
    if input_img_paths == None:
        input_img_paths = dl.load_path(os.path.join(os.getcwd(), 'data'), ext=['.JPG', '.jpg'])
    if mask_img_paths == None:
        mask_img_paths = dl.load_path(os.path.join(os.getcwd(), 'data'), ext=['.PNG', '.png'])

    if len(input_img_paths) == len(mask_img_paths):
        print("data PASS")
        return True
    #   데이터 확인용, 삭제
    a_paths, b_paths = (input_img_paths, mask_img_paths) if len(input_img_paths) > len(mask_img_paths) else (mask_img_paths, input_img_paths)
    b_paths_name = [b_paths[i][-10:-4] for i in range(len(b_paths))]
    for i in range(len(a_paths)):
        if(a_paths[i][-10:-4] not in b_paths_name):
            os.remove(a_paths[i])
    return False
        ######Surface_765 mask데이터 없어서 삭제
#    if os.path.isdir(os.path.join(os.getcwd(), 'data', 'Surface_765')):
#        shutil.rmtree(os.path.join(os.getcwd(), 'data', 'Surface_765'))
#    assert len(input_img_paths) == len(mask_img_paths)