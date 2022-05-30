# AIFFEL_HACKATHON
TEAM_Tayo

Yolo-용어 정리
[용어정의]

batch : 딥러닝에서 배치는 모델의 가중치를 한번 업데이트 시킬 때 사용되는 샘플들의 묶음을 의미합니다. 만약 총 1000개의 훈련 샘플이 있는데, 배치 사이즈가 20이라면, 20개의 샘플 단위마다 모델의 가중치를 한번씩 업데이트 시킵니다. 그러면, 총 50번 가중치가 업데이트 됩니다.

epoch : 딥러닝에서 에포크는 학습의 횟수를 의미합니다. 만약, 에포크가 10이고 배치 사이즈가 20이면, 가중치를 50번 업데이트 하는 것을 총 10번 반복합니다. 결과적으로 가중치가 총 500번 업데이트 됩니다.

배치와 에포크  : 배치 사이즈가 너무 크면 한번에 처리해야 할 양이 그만큼 많기 때문에 학습 속도가 느려집니다. 반대로, 너무 적은 샘플을 참조해서 가중치가 자주 업데이트 되기 때문에 비교적 불안정하게 훈련됩니다.

TP (True Positive) : 옳은 검출을 의미합니다.

FP (False Positive) : 다른 클래스의 객체로 검출한 것을 의미합니다. (틀린 검출)

FN (False Negative) : 검출되었어야 하는 물체인데 검출되지 않은 것을 의미합니다.

TN (True Negative) : 검출되지 말아야 할 것이 검출되지 않음을 의미합니다.

Precision : 정밀도라고도 하며, 모든 검출 결과 중 옳게 검출한 비율을 의미합니다.

Recall : 재현률이라고도 하며, 입력으로 positive를 주었을 때 얼마나 잘 positive로 예측하는지 나타내는데 사용됩니다. 간단히 말하면, 얼마나 잘 검출하냐를 말합니다.

Recall과 Precision 예시 : 사람을 검출하고자 할 때, 사진 속 4명의 사람 중 3명을 검출했다면, recall = 3/4 = 75% 입니다. 그런데 사람은 3명만 검출했는데 총 6개의 검출 결과가 있었다
면, precision = 3/6 = 50% 입니다.

AP (Average Preicision) : 예측된 결과가 얼마나 정확한지 나타냅니다.

mAP (mean Average Preicision) :

Ground Truth : 참값

IoU (Intersection over Union) : 실제 바운더리 박스와 예측된 바운더리 박스 사이의 교집합을 구해 정확도를 구하는 것입니다. 이값은 0.5 이상이면 제대로 검출되었다고 판단합니다.

[참고문헌]

배치와 에포크란? - bskyvision

커스텀 데이터셋으로 객체 인식을 더 효율적으로 훈련시키는 방법 - Jacob Solawets

[파라미터]

--weights : 감지에 사용할 모델

--source : 분석할 이미지 경로

--img-size : 추론할 이미지 사이즈 (기본값: 640)

--view-img : 결과를 보고 싶은 경우 입력

--classes : 원하는 클래스만 필터링할 수 있다. (e.g. --class 0 2 3)

--name : 결과를 저장할 이름

--exist-ok : 기존 파일이 존재하면 덮어씌운다

[3D 엔진으로 좋은 데이터셋 만들기]

객체의 크기 : 가까이 있는 객체는 크게 보이고 멀리있는 객체는 작게 보인다. 따라서, 가장 가까이 있는 거리부터 충분히 멀리있는 거리까지 학습을 시켜야 한다.

객체의 방향 : 객체의 yaw, raw pitch 값을 랜덤하게 지정하여 학습시켜야 다양한 각도에 대한 유연성이 생긴다. 단, 밑에서 위로 바라보는 경우는 거의 없으므로 학습하지 않는다.

객체의 재질 : 실제 객체에서 반사가 잘 되는 부위와 그렇지 않은 부위를 잘 반영해야 인지율을 높일 수 있다.

빛의 방향 : 객체를 비추는 조명이 다양한 각도에서 비추고 그에 대한 반사가 표현될 때 더 객체 인지율을 높일 수 있다.

빛의 세기 : 매우 어두운 조명부터 매우 밝은 조명까지 그 세기를 랜덤값으로 하여 학습시켜야 그 객체에 대한 밝기에 유연성이 생긴다.

배경 이미지 : 단색 배경과 실제 객체가 위치한 배경을 적절한 비율로 혼용하여 학습해야 좋은 인지율을 달성할 수 있다. 일반적으로 실제 배경 4장에 단색 배경 1장 비율로 학습시키는 것이 좋다. (20%를 단색 배경으로 사용)

학습 이미지 개수 : 3D 이미지를 무조건 많이 학습시킨다고 해서 인지율이 높아지지는 않았다. 1000개를 학습시킨 것 보다 250개를 학습시킨 것이 더 좋은 인지율을 보여주었다.
클래스 간 이미지 개수 비율 : 특정 클래스 이미지만 너무 많이 학습시키면 다른 클래스도 그 클래스로 인식하는 경향이 높아졌다. 따라서, 적절한 클래스 간 이미지 비율을 정하는 것이 좋다. 아직 황금비율을 찾지는 못했다. 클래스가 여러 개라면 train과 test에 사용되는 각 클래스의 이미지 개수 비율도 동일해야 한다. 20프로가 테스트셋으로 적합하다.

epoch 수 : epoch가 너무 낮으면 underfitting이 발생하고, 너무 높으면 overfitting이 발생한다. 따라서, 적절한 epoch를 선정해야 한다.

객체 애니메이션 : 사람 또는 동물들은 자동차와 달리 다양한 자세로 존재할 수 있기 때문에 각각의 자세에 대해 별도로 학습을 시켜주어야 한다.
