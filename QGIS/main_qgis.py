import os
import pyproj
import json
import urllib
import requests
import mysql.connector
import pandas as pd

from urllib.request import urlopen
from mysql.connector.constants import ClientFlag
from qgis.core import QgsProject
from PyQt5 import QtTest

t_map = {
    'appKey' : '*'
}

local_path = "D:\self_d\QGIS"
p1_type = "epsg:4326"
p2_type = "epsg:5181"

config = {
    'user': 'root',
    'password': '*',
    'host': '*',
    'client_flags': [ClientFlag.SSL],
    'ssl_ca': os.path.join(local_path, 'SSL', 'server-ca.pem'),
    'ssl_cert': os.path.join(local_path, 'SSL', 'client-cert.pem'),
    'ssl_key': os.path.join(local_path, 'SSL', 'client-key.pem')
}
config['database'] = 'gps-database'  # add new database to config dict

def get_coordinate(loc):
    """
    넣는 주소가 정확해야 한다.
    ex)
    울산대학교 (X)
    울산광역시 남구 대학로 93 (O)
    """
    loc = loc.split(' ')
    while(len(loc)<5):
        loc.append('')

    url = "https://apis.openapi.sk.com/tmap/geo/geocoding?version={}&city_do={}&gu_gun={}&dong={}&bunji={}&detailAddress={}&addressFlag={}&coordType={}&appKey={}".format(
        1,
        urllib.parse.quote(loc[0]),
        urllib.parse.quote(loc[1]),
        urllib.parse.quote(loc[2]),
        urllib.parse.quote(loc[3]),
        urllib.parse.quote(loc[4]),
        'F00',
        'WGS84GEO',
        t_map['appKey'])

    request = urllib.request.Request(url)
    response = urlopen(request)
    res = response.getcode()

    if (res == 200):
        print('loc Send Success')
        response_body = response.read().decode('utf-8')
        response_body = json.loads(response_body)
        if (response_body['coordinateInfo']['newLat'])=='':
            lat = float(response_body['coordinateInfo']['lat'])
            lon = float(response_body['coordinateInfo']['lon'])        
        else:
            lat = float(response_body['coordinateInfo']['newLat'])
            lon = float(response_body['coordinateInfo']['newLon'])
        return [lon, lat]
    print('loc2coordinate Fail')
    return (-1, -1)

def get_navi(start=(0, 0), end=(0,0)):
    """
    start=(lon, lat)
    end=(lon, lat)
    """
    url = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"

    payload = {
        "startX": float(start[0]),
        "startY": float(start[1]),
        "endX": float(end[0]),
        "endY": float(end[1]),
        "startName": urllib.parse.quote("출발지"),
        "endName": urllib.parse.quote("목적지"),
        "reqCoordType": "WGS84GEO",
        "searchOption": "30",
        "resCoordType": "WGS84GEO",
        "sort": "index"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "appKey": t_map['appKey'],
        
    }
    response = requests.post(url, json=payload, headers=headers)

    if (response.status_code == 200) :
        res_json = response.json()

        coordinates = []
        for feature in res_json['features']:
            if isinstance(feature['geometry']['coordinates'][0], float):
                coordinates.append(feature['geometry']['coordinates'])
            else:
                coordinates.extend(feature['geometry']['coordinates'])

        for idx in range(len(coordinates)-1):
            if coordinates[idx][0]==coordinates[idx+1][0] and coordinates[idx][1]==coordinates[idx+1][1]:
                coordinates[idx][0] = -1
                coordinates[idx][1] = -1
        return [coordinate for coordinate in coordinates if coordinate[0] != -1]
    return -1

def coordinate_TF(coord, p1_type, p2_type):
    """
    좌표계 변환 함수
    - coord: long, lat(129, 35) 좌표 정보가 담긴 NumPy Array
    - p1_type: 입력 좌표계 정보 ex) epsg:5179
    - p2_type: 출력 좌표계 정보 ex) epsg:4326
    """
    p1 = pyproj.Proj(init=p1_type)
    p2 = pyproj.Proj(init=p2_type)
    fx, fy = pyproj.transform(p1, p2, *coord)
    return [fx, fy]

def removeLayers(layerName):
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name()==layerName:
            QgsProject.instance().removeMapLayers([layer.id()])

def get_SQL(config, trans=True):
    cnxn = mysql.connector.connect(**config)
    cursor = cnxn.cursor()
    
    cursor.execute("SHOW FULL COLUMNS FROM gps_data;")
    column_result = cursor.fetchall()
    cursor.execute("SELECT * FROM gps_data")
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=list(map(lambda x: x[0], column_result)))
    
    temp_list = []
    for lat, long in list(zip(df['gps_lat'].to_list(), df['gps_long'].to_list())):
        lat = round(int(lat/100) + (lat-int(lat/100)*100)/60, 5)
        long = round(int(long/100) + (long-int(long/100)*100)/60, 5)
        temp_list.append(coordinate_TF((long, lat), p1_type, p2_type))
    return temp_list

def path2rectangle(paths):
    boundary = 20
    lat_1m = 0.00000899320363721
    lon_1m = 0.0000111905024062
    return [[*coordinate_TF([i[0] - (boundary//2)*lon_1m, i[1] - (boundary//2)*lat_1m], p1_type, p2_type), *coordinate_TF([i[0] + (boundary//2)*lon_1m, i[1] + (boundary//2)*lat_1m], p1_type, p2_type)] for i in paths]
    """
    1(m) = (위도 1도) / 111195.080234 = 0.00000899320363721
    1(m) = (경도 1도) / 89361.4927818 = 0.0000111905024062
    """

######################################경로 생성
coordinates = get_SQL(config)
#coordinates = [[405718, 230263]]

dest = "울산광역시 남구 남산로68번길 13"
dest_coordinate = get_coordinate(dest)

if(dest_coordinate[0] == -1):
    os._exit(0)

start_idx = len(coordinates)-1
path_coordinates = get_navi(start=coordinate_TF(coordinates[-1], p2_type, p1_type), end=dest_coordinate)
path_coordinates = path2rectangle(path_coordinates)

cnxn = mysql.connector.connect(**config)
cursor = cnxn.cursor()
for path_coordinate in path_coordinates:
    query = ("INSERT INTO gps_waypoint_data (gps_0, gps_1, gps_2, gps_3) "
            "VALUES (%s, %s, %s, %s)")
    cursor.executemany(query, [path_coordinate])
    cnxn.commit()  # and commit changes

#################################layer clear and setting
removeLayers('Polygons')
removeLayers('_Polygons')
removeLayers('Linea')

layer = QgsVectorLayer("Polygon?crs=epsg:5181", "Polygons", "memory")

props = layer.renderer().symbol()[0]
props.setColor(QColor("transparent"))
props.setStrokeColor(QColor("blue"))
props.setStrokeWidth(1)

_layer = QgsVectorLayer("Polygon?crs=epsg:5181", "_Polygons", "memory")

props = _layer.renderer().symbol()[0]
props.setColor(QColor("transparent"))
props.setStrokeColor(QColor("red"))
props.setStrokeWidth(1)
###########################################
for path_coordinate in path_coordinates:
    QgsProject.instance().addMapLayer(layer)

    rect = QgsRectangle(*path_coordinate)
    polygon = QgsGeometry.fromRect(rect)

    feature = QgsFeature()
    feature.setGeometry(polygon)

    layer.dataProvider().addFeatures([feature])

#####################################
canvas = qgis.utils.iface.mapCanvas()
now_idx = -1
while(now_idx!=(len(path_coordinates)-1)):
    temp_list = get_SQL(config)
    pointList = list(map(lambda x: QgsPoint(float(x[0]), float(x[1])), temp_list[start_idx:]))

    for i, coordinat in enumerate(path_coordinates):
        if(temp_list[-1][0]>coordinat[0] and temp_list[-1][0]<coordinat[2] and temp_list[-1][1]>coordinat[1] and temp_list[-1][1]<coordinat[3]):
            now_idx = i

    if now_idx != -1:
        for path_coordinate in path_coordinates[:now_idx+1]:
            QgsProject.instance().addMapLayer(_layer)

            rect = QgsRectangle(*path_coordinate)
            polygon = QgsGeometry.fromRect(rect)

            feature = QgsFeature()
            feature.setGeometry(polygon)

            _layer.dataProvider().addFeatures([feature])

    removeLayers('Linea')
    linea = iface.addVectorLayer("LineString?crs=epsg:5181&field=id:integer&index=yes","Linea","memory")
    props = linea.renderer().symbol().symbolLayer(0).properties()
    props['line_width'] = '1.5'
    linea.renderer().setSymbol(QgsLineSymbol.createSimple(props))
    linea.startEditing()
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPolyline(pointList))
    feature.setAttributes([1])
    linea.addFeature(feature)
    linea.commitChanges()
    iface.zoomToActiveLayer()    
    canvas.zoomScale(1500)
    
    print(now_idx)
    QtTest.QTest.qWait(1000)