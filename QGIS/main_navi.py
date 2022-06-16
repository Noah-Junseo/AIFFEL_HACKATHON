
import json
import urllib
import pyproj
from urllib.request import urlopen

p1_type = "epsg:4326"
p2_type = "epsg:5181"

naver = {
    'client_id' : '*',
    'client_secret' : '*'
}
now = {
    'lat' : 35.548822899075354, #위도
    'lon' : 129.27816873423     #경도
}
goal = '울산 남구 대학로 64'

def get_coordinate(loc):
    """
    넣는 주소가 정확해야 한다.
    ex)
    울산대학교 (X)
    울산광역시 남구 대학로 93 (O)
    """
    url = f"https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=" \
    + urllib.parse.quote(loc)
    
    request = urllib.request.Request(url)
    request.add_header('X-NCP-APIGW-API-KEY-ID', naver['client_id'])
    request.add_header('X-NCP-APIGW-API-KEY', naver['client_secret'])

    response = urlopen(request)
    res = response.getcode()

    if (res == 200):
        print('loc Send Success')
        response_body = response.read().decode('utf-8')
        response_body = json.loads(response_body)
        print(response_body)

        if response_body['meta']['totalCount'] == 1 :
            print('loc2coordinate Success')
            lat = float(response_body['addresses'][0]['y'])
            lon = float(response_body['addresses'][0]['x'])
            return (lat, lon)
    print('loc2coordinate Fail')
    return (-1, -1)

def get_navi(start=(0, 0), end=(0,0), option=''):
    url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start={},{}&goal={},{}&option={}"\
    .format(start[1], start[0], end[1], end[0], option)
    request = urllib.request.Request(url)
    request.add_header('X-NCP-APIGW-API-KEY-ID', naver['client_id'])
    request.add_header('X-NCP-APIGW-API-KEY', naver['client_secret'])

    response = urllib.request.urlopen(request)
    res = response.getcode()

    if (res == 200) :
        response_body = response.read().decode('utf-8')
        temp = json.loads(response_body)
        if temp['code'] == 0:
            print('get navigation Success')
            return json.loads(response_body)
    print('get navigation Fail')
    return -1




def path2rectangle(path):
    boundary = 30
    lat_1m = 0.00000899320363721
    lon_1m = 0.0000111905024062
    return [[i[0] - (boundary//2)*lat_1m, i[1] - (boundary//2)*lon_1m, i[0] + (boundary//2)*lat_1m, i[1] + (boundary//2)*lon_1m] for i in path]
    """
    1(m) = (위도 1도) / 111195.080234 = 0.00000899320363721
    1(m) = (경도 1도) / 89361.4927818 = 0.0000111905024062
    """

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

"""
goal_lat, goal_lon = get_coordinate(goal)

navi_info = get_navi(start=(now['lat'], now['lon']), end=(goal_lat, goal_lon), option='')

if navi_info is not -1:
    distance = navi_info['route']['traoptimal'][0]['summary']['distance']
    current_time = navi_info['currentDateTime']
    departure_time = navi_info['route']['traoptimal'][0]['summary']['departureTime']
    path = navi_info['route']['traoptimal'][0]['path']

    print(navi_info)
    print(distance)
    print(departure_time)
    print(path)
"""
distance = 3078
path = [[129.2780032, 35.5488914], [129.2780752, 35.5490048], [129.2781243, 35.5490825], [129.2781802, 35.5491665], [129.278268, 35.5492968], [129.2785167, 35.5496672], [129.2786114, 35.5498092], [129.2786366, 35.5498494], [129.2786925, 35.5499351], [129.2788137, 35.5501298], [129.2788995, 35.5502674], [129.2789602, 35.5503684], [129.2790116, 35.5504497], [129.2788348, 35.5505325], [129.2787998, 35.5505484], [129.2778731, 35.5509434], [129.277224, 35.5512243], [129.2770426, 35.5513027], [129.2766886, 35.5514549], [129.2758624, 35.5518114], [129.2758122, 35.5518329], [129.2757116, 35.551875], [129.2755118, 35.5519671], [129.2754593, 35.5519896], [129.275374, 35.5520242], [129.2749302, 35.5522083], [129.2747903, 35.5522663], [129.2747498, 35.5522831], [129.2743608, 35.5524502], [129.2742962, 35.5524737], [129.2738748, 35.5525745], [129.2734746, 35.5526327], [129.272895, 35.5526674], [129.2728168, 35.5526721], [129.2728157, 35.5526721], [129.2727353, 35.5526769], [129.2726615, 35.5526825], [129.2723366, 35.5527576], [129.2717159, 35.5527758], [129.2708275, 35.5528096], [129.270767, 35.5528159], [129.270408, 35.5528437], [129.2702457, 35.5528884], [129.2700416, 35.5527868], [129.2693882, 35.5525711], [129.2693247, 35.5525458], [129.2692748, 35.5525312], [129.2690496, 35.5524742], [129.2685747, 35.5523495], [129.2683815, 35.5522955], [129.2680498, 35.5522075], [129.2676904, 35.5521173], [129.2675872, 35.5520908], [129.2674141, 35.5520474], [129.2671289, 35.5519668], [129.2662464, 35.5517192], [129.26594, 35.5516299], [129.2655996, 35.5514492], [129.2654323, 35.5513173], [129.2653256, 35.5512306], [129.2645155, 35.5506104], [129.2641614, 35.5503578], [129.2640928, 35.5504003], [129.2639912, 35.5504432], [129.2638749, 35.5504747], [129.2637857, 35.5504796], [129.2637316, 35.5504786], [129.2636497, 35.5504663], [129.2635743, 35.5504493], [129.2634686, 35.5504049], [129.2633688, 35.5503324], [129.2633177, 35.5502647], [129.2632773, 35.5501859], [129.263256, 35.5501186], [129.2632552, 35.550033], [129.2632874, 35.5499415], [129.2631674, 35.5497485], [129.2631125, 35.5494076], [129.2630905, 35.5493611], [129.2628866, 35.548916], [129.2627438, 35.548644], [129.2625646, 35.5482671], [129.2624425, 35.5480291], [129.2624263, 35.5479968], [129.2623376, 35.5478223], [129.2622419, 35.5476335], [129.262213, 35.5475753], [129.2621714, 35.5474867], [129.2620138, 35.5471942], [129.2619453, 35.5470843], [129.2618678, 35.5469719], [129.2614999, 35.5464408], [129.261462, 35.5463747], [129.2610725, 35.5457628], [129.2610119, 35.5456663], [129.2608623, 35.5453827], [129.2604997, 35.5445911], [129.2604119, 35.5444076], [129.2599732, 35.5435142], [129.2598833, 35.5433371], [129.2597976, 35.5431508], [129.2595249, 35.5425327], [129.2593746, 35.5422663], [129.2593117, 35.5421662], [129.2592687, 35.5421155], [129.2591114, 35.5419329], [129.2590118, 35.5418163], [129.2582615, 35.5409996], [129.2577993, 35.5404916], [129.2582615, 35.5409996], [129.2584052, 35.5409119], [129.2584988, 35.5408528]]
rectangle_point = path2rectangle(path)
rectangle_point = [[*coordinate_TF((i[0], i[1]), p1_type, p2_type), *coordinate_TF((i[2], i[3]), p1_type, p2_type)] for i in rectangle_point]

print(rectangle_point[:1])
print('거리: {}m'.format(distance))