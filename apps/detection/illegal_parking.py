import time
from collections import defaultdict

import cv2
import cvzone
import numpy as np
from PIL import Image
from ultralytics import YOLO

from apps.detection.utils import is_bbox_partially_inside_region


class IllegalParkingDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(lambda: [])
        self.start_time = {}

    def predict(self, input_path, output_path, conf, selected_region=None, intersection_ratio_threshold=0.5,
                min_stay_time=3):
        results = self.model.track(input_path, persist=True)
        image = Image.open(input_path)
        image = np.array(image)

        if results[0].boxes.id is not None:
            class_ids = (results[0].boxes.cls.int().cpu().tolist())
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            scores = results[0].boxes.conf.cpu().numpy()

            # 绘制selected_region的矩形区域
            if selected_region:
                for region in selected_region:
                    x_min, y_min, x_max, y_max = region
                    region = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
                    region = np.array(region, dtype=np.int32)
                    filled_rectangle = np.zeros_like(image)
                    cv2.fillPoly(filled_rectangle, [region], color=(0, 255, 0))
                    alpha = 0.1  # 调整透明度
                    image = cv2.addWeighted(image, 1 - alpha, filled_rectangle, alpha, 0)

            current_time = time.time()

            for box, track_id, class_id, score in zip(boxes, track_ids, class_ids, scores):
                if class_id == 2 or class_id == 7:
                    x, y, w, h = box
                    x_min = int(x - w / 2)
                    y_min = int(y - h / 2)
                    x_max = int(x + w / 2)
                    y_max = int(y + h / 2)
                    track = self.track_history[track_id]
                    track.append((float(x), float(y)))  # x, y中心点

                    if track_id not in self.start_time and score > conf \
                            and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                selected_region, intersection_ratio_threshold):
                        self.start_time[track_id] = current_time

                    parking_duration = int(current_time - self.start_time[track_id])
                    if track_id in self.start_time and current_time - self.start_time[track_id] > min_stay_time \
                            and score > conf \
                            and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                selected_region, intersection_ratio_threshold):

                        cvzone.cornerRect(image, (x_min, y_min, int(w), int(h)), l=1, rt=2,
                                          colorR=(204, 51, 0))

                        text = f"parking time: {parking_duration} s"
                        cv2.putText(image, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                    (0, 0, 255), 2, cv2.LINE_AA)
                        cv2.imwrite(output_path, image)

                        return "illegal parking"
                    if len(track) > 30:
                        track.pop(0)
