import os
import pyproj
import time
import mysql.connector
import pandas as pd

from mysql.connector.constants import ClientFlag
from qgis.core import QgsProject
from PyQt5 import QtTest

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

canvas = qgis.utils.iface.mapCanvas()
canvas_m=iface.mapCanvas()
m = QgsVertexMarker(canvas)

while(True):
    cnxn = mysql.connector.connect(**config)
    cursor = cnxn.cursor()
    print("접속")

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

    ###############################plot
    removeLayers('Linea')
    pointList = list(map(lambda x: QgsPoint(float(x[0]), float(x[1])), temp_list))
    centerList = list(map(lambda x: QgsPointXY(x[0], x[1]), temp_list))

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
    
    for center in centerList:
        m.setCenter(center)
        m.setColor(QColor(255,0,0))
        m.setFillColor(QColor(255,255,0))
        m.setIconSize(10)
        m.setIconType(QgsVertexMarker.ICON_CIRCLE)
        m.setPenWidth(3)
    iface.mapCanvas().refresh()
    canvas.zoomScale(1000)
    QtTest.QTest.qWait(1000)