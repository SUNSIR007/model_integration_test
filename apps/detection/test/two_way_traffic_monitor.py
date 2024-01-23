import math

import cv2
import cvzone
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO

from ..myutils import get_class_color, estimated_speed

cap = cv2.VideoCapture("../input/video.mp4")
cap.set(cv2.CAP_PROP_FPS, 30)

model = YOLO("../weights/yolov8n.pt")


mainCounter = cv2.imread("../../../static/main_counter.png", cv2.IMREAD_UNCHANGED)
mainCounter = cv2.resize(mainCounter, (700, 250))

tracker = DeepSort(max_iou_distance=0.7, max_age=2, n_init=3, nms_max_overlap=3.0, max_cosine_distance=0.2)

limitsUp = [180, 450, 560, 450]
limitsDown = [710, 450, 1150, 450]

totalCountUp = []
totalCountDown = []

coordinatesDict = dict()
speed_history = dict()

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_video.mp4', fourcc, 20.0, (1280, 720))

while True:
    success, img = cap.read()
    if success:
        img = cv2.resize(img, (1280, 720))
        img = cvzone.overlayPNG(img, mainCounter, (300, 0))

        results = model(img, stream=True)
        detections = list()
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                w, h = x2 - x1, y2 - y1
                bbox = (x1, y1, w, h)
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])

                currentClass = model.names[cls]
                if currentClass == 'car' and conf > 0.5:
                    w, h = x2 - x1, y2 - y1
                    detections.append(([x1, y1, w, h], conf, cls))

                elif currentClass == "truck":
                    w, h = x2 - x1, y2 - y1
                    detections.append(([x1, y1, w, h], conf, cls))

                elif currentClass == "motorbike":
                    w, h = x2 - x1, y2 - y1
                    detections.append(([x1, y1, w, h], conf, cls))

                elif currentClass == "bus":
                    w, h = x2 - x1, y2 - y1
                    detections.append(([x1, y1, w, h], conf, cls))

        cv2.line(img, (limitsUp[0], limitsUp[1]), (limitsUp[2], limitsUp[3]), (0, 0, 255), thickness=5)
        cv2.line(img, (limitsDown[0], limitsDown[1]), (limitsDown[2], limitsDown[3]), (0, 255, 0), thickness=5)

        tracks = tracker.update_tracks(detections, frame=img)
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id

            bbox = track.to_ltrb()
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            w, h = x2 - x1, y2 - y1

            co_ord = [x1 + w // 2, y1 + h // 2]

            if track_id not in coordinatesDict:
                coordinatesDict[track_id] = co_ord
            else:
                if len(coordinatesDict[track_id]) > 2:
                    coordinatesDict[track_id] = coordinatesDict[track_id][-2:]
                coordinatesDict[track_id].append(co_ord[0])
                coordinatesDict[track_id].append(co_ord[1])
            estimatedSpeedValue = 0

            if len(coordinatesDict[track_id]) > 2:
                location1 = [coordinatesDict[track_id][0], coordinatesDict[track_id][1]]
                location2 = [coordinatesDict[track_id][2], coordinatesDict[track_id][3]]

                if location1 == location2:
                    estimatedSpeedValue = 0
                else:
                    estimatedSpeedValue = estimated_speed(location1, location2)

            if track_id not in speed_history:
                speed_history[track_id] = [estimatedSpeedValue]
            else:
                speed_history[track_id].append(estimatedSpeedValue)
                if len(speed_history[track_id]) > 10:
                    speed_history[track_id].pop(0)

            average_speed = int(sum(speed_history[track_id][-3:]) / 3)
            cls = track.get_det_class()
            currentClass = model.names[cls]
            clsColor = get_class_color(currentClass)

            cvzone.cornerRect(img, (x1, y1, w, h), l=1, rt=2, colorR=clsColor)

            cvzone.putTextRect(
                img,
                text=f"{model.names[cls]} {average_speed} km/h",
                pos=(max(0, x1), max(35, y1)),
                colorR=clsColor,
                scale=1,
                thickness=1,
                offset=2)

            cx, cy = x1 + w // 2, y1 + h // 2

            if limitsUp[0] < cx < limitsUp[2] and limitsUp[1] - 15 < cy < limitsUp[1] + 15:
                if totalCountUp.count(track_id) == 0:
                    totalCountUp.append(track_id)
                    cv2.line(img, (limitsUp[0], limitsUp[1]), (limitsUp[2], limitsUp[3]), (255, 255, 255),
                             thickness=3)

            if limitsDown[0] < cx < limitsDown[2] and limitsDown[1] - 15 < cy < limitsDown[1] + 15:
                if totalCountDown.count(track_id) == 0:
                    totalCountDown.append(track_id)
                    cv2.line(img, (limitsDown[0], limitsDown[1]), (limitsDown[2], limitsDown[3]), (255, 255, 255),
                             thickness=3)

    else:
        break

    cv2.putText(img, str(len(totalCountUp)), (565, 112), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 2)
    cv2.putText(img, str(len(totalCountDown)), (750, 112), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 2)

    out.write(img)

    cv2.imshow('traffic monitor', img)
    cv2.waitKey(1)

out.release()
