import cv2
from ultralytics import YOLO
from easyocr import Reader

# load weights
coco_model = YOLO('weights/yolov8n.pt')
license_plate_detector = YOLO('weights/license_plate.pt')

# image path
image_path = 'input/license_plate2.png'

vehicles = [2, 3, 5, 7]

image = cv2.imread(image_path)

# 使用车辆检测模型检测图像中的车辆,并获取检测框
detections = coco_model(image)[0].boxes

results = {'vehicle_records': []}

# 遍历每个检测到的车辆框，提取车辆框的坐标和类别信息
for detection in detections.data:
    x1, y1, x2, y2, _, class_id = detection.tolist()

    if int(class_id) in vehicles:
        # 初始化车辆记录,包括车辆框和车牌信息
        vehicle_record = {'vehicle_bbox': [x1, y1, x2, y2], 'license_plate': None}

        # 使用车牌检测模型检测车辆框中的车牌
        license_plates = license_plate_detector(image[int(y1):int(y2), int(x1):int(x2)])[0].boxes
        for license_plate in license_plates.data:
            xlp1, ylp1, xlp2, ylp2, _, _ = license_plate.tolist()

            # 截取车牌区域，进行灰度处理和二值化
            license_plate_crop = image[int(y1) + int(ylp1):int(y1) + int(ylp2), int(x1) + int(xlp1):int(x1) + int(xlp2)]
            cv2.imwrite('license_plate_crop.jpg', license_plate_crop)
            license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
            _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

            # 使用 EasyOCR 读取车牌号
            reader = Reader(['ch_sim'], gpu=False)
            results_ocr = reader.readtext(license_plate_crop_thresh)

            # 处理 OCR 结果
            for result_ocr in results_ocr:
                detected_text = result_ocr[1]
                cleaned_text = ''.join(char for char in detected_text if char.isalnum())
                license_plate_text = cleaned_text

                vehicle_record['license_plate'] = {'bbox': [xlp1, ylp1, xlp2, ylp2],
                                                   'text': license_plate_text,
                                                   'bbox_score': _,
                                                   'text_score': result_ocr[2]}

        results['vehicle_records'].append(vehicle_record)

# Print the final results
for result in results['vehicle_records']:
    print('Detected License Plate:', result['license_plate']['text'])
