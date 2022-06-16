import cv2
import sys
import time
import os
import keyboard
import numpy as np

from math import pi, sin, cos
from mysql.connector.constants import ClientFlag
from serial import Serial
from LIDAR.Lidar import LidarX2, sector_mask, process
from UART.uart import GPS_data_check, motor, IMU_data_check
from SQL.sql import server_connect, server_process_kill, server_get_df
from algorithm.astar import aStar
from evaluate.evaluate import model_evaluate
from multiprocessing import Pool

config = {
    'user': 'root',
    'password': '',
    'host': '',
    'client_flags': [ClientFlag.SSL],
    'ssl_ca': os.path.join(os.getcwd(), 'SSL', 'server-ca.pem'),
    'ssl_cert': os.path.join(os.getcwd(), 'SSL', 'client-cert.pem'),
    'ssl_key': os.path.join(os.getcwd(), 'SSL', 'client-key.pem')
}

def main():
    ##########################################
    heading = 0.0
    heading_compass = 0.0
    IMU_data_first = True
    GPS_waypoint = False
    GPS_waypoint_df = None
    Serial_PORT = "COM3"
    Lidar_PORT = "COM4"

    dis_1m = 200
    range_points = [[dis_1m*2*sin(((-10/180.0)*pi)), dis_1m*2*cos(((-10/180.0)*pi))], [dis_1m*sin(((30/180.0)*pi)), dis_1m*cos(((30/180.0)*pi))], [dis_1m*sin(((70/180.0)*pi)), dis_1m*cos(((70/180.0)*pi))], [dis_1m*sin(((110/180.0)*pi)), dis_1m*cos(((110/180.0)*pi))], [dis_1m*sin(((150/180.0)*pi)), dis_1m*cos(((150/180.0)*pi))], [dis_1m*2*sin(((190/180.0)*pi)), dis_1m*2*cos(((190/180.0)*pi))]]
    range_angles = [(170, 210), (210, 250), (250, 290), (290, 330), (330, 10)]
    count_points = [[] for _ in range(len(range_angles))]
    delete_points = [217, 221, 217, 224, 217]
#    threshold_point = 80
    threshold_point = 30
    #dis_1m = 200
    #max dis 5m
    #angle 0~120, 240~360

    ser = Serial(Serial_PORT, 1000000)
    lidar = LidarX2(Lidar_PORT)
    get_mask = model_evaluate(path=os.getcwd(), cam_num=0, model_name='unet')

    if not lidar.open():
        print("Cannot open lidar")
        sys.exit(0)
    if not get_mask.open():
        print("Cannot open camera")
        sys.exit(0)

    #############################################################SQL 최초 시작 데이터 베이스 초기화
    config['database'] = 'gps-database'  # add new database to config dict
    cursor, cnxn = server_connect(config)
    print("database 접속")

    server_process_kill(cursor=cursor)
    print("프로세스 정리")

    try:
        cursor.execute("DROP TABLE gps_data")
        cnxn.commit()  # this commits changes to the database
        print("SQL 서버 gps_data 테이블 삭제")

        cursor.execute("DROP TABLE gps_waypoint_data")
        cnxn.commit()  # this commits changes to the database
        print("SQL 서버 gps_waypoint_data 테이블 삭제")
    except Exception as e:
        print(e)

    cursor.execute("CREATE TABLE gps_data ("
                "gps_lat FLOAT(10,5),"
                "gps_long FLOAT(10,5),"
                "gps_speed FLOAT(10,5),"
                "gps_degree FLOAT(10,5) )")
    cnxn.commit()  # this commits changes to the database
    print("SQL 서버 gps_data 테이블 새 설정")

    cursor.execute("CREATE TABLE gps_waypoint_data ("
                "gps_0 FLOAT(12,6),"
                "gps_1 FLOAT(12,6),"
                "gps_2 FLOAT(12,6),"
                "gps_3 FLOAT(12,6) )")
    cnxn.commit()  # this commits changes to the database
    print("SQL 서버 gps_waypoint_data 테이블 새 설정")
    #############################################################

    #############################################################IMU, Compass correction
    while True:
        if keyboard.is_pressed("s"):
            print("로봇의 전방이 가르키는 degree입력: ")
            heading_compass = int(input())
            break

        if ser.readable():
            try:
                res = ser.readline()
                res = res.decode()
                if(IMU_data_check(res)==1):
                    print("heading: {}".format((float(res[1:-5])/10.0)))
                else:
                    print(res, end='')
            except:
                pass
    #############################################################
    commit=0
    error=0
    motor_send_count = 0
    while True:
        start_time = time.time()
        measures = lidar.getMeasures()
        if len(measures) != 0:
            img = np.zeros((512, 512, 3), np.uint8)
            cv2.circle(img, (256, 450), dis_1m, (0,0,255), 2)
            for range_point in range_points:
                cv2.line(img, (256+int(range_point[1]), 450-int(range_point[0])), (256, 450), (0,0,255), 2)

            corr = np.array(list(map(process, measures)))
            for idx in range(len(measures)):
                if corr[idx] is not None:
                    cv2.circle(img, (256+int(corr[idx][0]/5.0), 450-int(corr[idx][1]/5.0)), 2, (255, 0, 0), -1)

            for i, range_angle in enumerate(range_angles):
                mask = sector_mask((512, 512), (450, 256), dis_1m, range_angle)
                temp_img = np.zeros((512, 512, 3), np.uint8)
                temp_img[mask] = (255, 0, 0)
                temp = cv2.bitwise_and(img,temp_img)
#                count_points[i] = np.sum(temp == 255) - delete_points[i]
                count_points[i] = np.sum(temp == 255)

            for i in range(5):
                if count_points[i] > threshold_point:
                    mask = sector_mask((512, 512), (450, 256), dis_1m, range_angles[i])
                    temp_img = np.zeros((512, 512, 3), np.uint8)
                    temp_img[mask] = (255, 255, 255)
                    img = cv2.bitwise_or(img,temp_img)

            astar_img = np.zeros((32, 32, 3), np.uint8)
            resized_img = cv2.resize(img[:,:,1], (32,32), cv2.INTER_NEAREST)
            cv2.circle(resized_img, (256//16, 450//16), 5, (0, 0, 0), -1)
            path = aStar(resized_img, (450//16, 256//16), (0, 256//16))
            for i, j in path:
                astar_img[i][j] = (0, 255, 0)
            astar_temp_img = np.zeros((32, 32, 3), np.uint8)
            cv2.circle(astar_temp_img, (256//16, 450//16), dis_1m//16-2, (0, 255, 0), 2)
            astar_temp_img = cv2.bitwise_and(astar_img[:,:,1], astar_temp_img[:,:,1])

            x, y = np.where(astar_temp_img == 255)
            motor_send_count += 1
            ser.flush()
#            if ((24 in x) and (6 in y)) or ((20 in x) and (12 in y)) and GPS_wass120sypoint:
            if (((24 in x) and (6 in y)) or ((20 in x) and (12 in y))) and (motor_send_count>0):
                motor(ser=ser, L_motor_speed=-50, R_motor_speed=50)
                motor_send_count = 0
                print('전방이 열려있을 때까지 왼쪽으로 회전')
#            elif (17 in x) and (18 in x) and (16 in y) and GPS_waypoint:
            elif ((17 in x) and (18 in x) and (16 in y)) and (motor_send_count>0):
                motor(ser=ser, L_motor_speed=80, R_motor_speed=80)
                motor_send_count = 0
                print('전진')
#            elif ((18 in x) and (20 in y)) or ((23 in x) and (24 in y)) and GPS_waypoint:
            elif (((18 in x) and (20 in y)) or ((23 in x) and (24 in y))) and (motor_send_count>0):
                motor(ser=ser, L_motor_speed=50, R_motor_speed=-50)
                motor_send_count = 0
                print('전방이 열려있을 때까지 오른쪽으로 회전')
            elif (motor_send_count>0):
                motor(ser=ser, L_motor_speed=0, R_motor_speed=0)
                motor_send_count = 0
                print('정지')
            cv2.imshow("lidar", img)
            cv2.imshow('lidar2', cv2.resize(astar_img, (512, 512), cv2.INTER_NEAREST))

        if get_mask.get_mask_img() is not None:
            cv2.imshow('mask', get_mask.get_mask_img())
        if len(server_get_df(cursor=cursor, table='gps_waypoint_data')):
            GPS_waypoint = True
            GPS_waypoint_df = server_get_df(cursor=cursor, table='gps_waypoint_data')

        ser.flush()
        if ser.readable():
            try:
                res = ser.readline()
                res = res.decode()
            except:
                pass
            print(res)
            if(GPS_data_check(res)==1):
                res = res[1:-5].replace('\x00', '')
                try:
                    gps_data = [float(res[:9]), float(res[10:20]), float(res[21:25]), float(res[26:29])]
    #############################################################SQL 서버에 데이터 올리기
                    query = ("INSERT INTO gps_data (gps_lat, gps_long, gps_degree, gps_speed) "
                            "VALUES (%s, %s, %s, %s)")
                    cursor.executemany(query, [gps_data])
                    cnxn.commit()  # and commit changes
                    commit = commit + 1
                    print("data commit = {}".format(gps_data))
    #############################################################
                except:
                    error = error + 1
                    print("GPS parsing ERROR")
                    pass
                print("{}/{}".format(error, error+commit))
            if(IMU_data_check(res)==1):
                if IMU_data_first:
                    heading_compass = (float(res[1:-5])/10.0)-heading_compass
                    IMU_data_first=False
                else:
                    heading = (float(res[1:-5])/10.0)-heading_compass
                    print("heading: {}".format(heading))

        print("{}Hz".format(1/(time.time()-start_time)))
        cv2.waitKey(1)
        if keyboard.is_pressed("q"):
            motor(ser=ser, L_motor_speed=0, R_motor_speed=0)
            cv2.destroyAllWindows()
            sys.exit()


if __name__ == '__main__':
    main()