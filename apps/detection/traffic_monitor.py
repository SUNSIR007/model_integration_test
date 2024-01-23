import time
from collections import defaultdict

import cv2
import cvzone
import numpy as np
from PIL import Image
from ultralytics import YOLO

from apps.config import settings
from apps.detection.myutils import is_bbox_partially_inside_region, estimated_speed, get_class_color


class TrafficCongestionDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.recording_start_time = None  # 车流量统计开始时间
        self.total_flow = 0  # 最大车流量
        self.class_count = {'car': 0, 'truck': 0, 'bus': 0}  # 分类统计
        self.track_coordinate = defaultdict(lambda: [])  # 汽车历史位置信息
        self.track_speed = defaultdict(lambda: [])  # 汽车历史速度信息
        self.average_speed = []  # 所有车辆平均车速

    def predict(self, input_path, output_path, conf, selected_region=None, intersection_ratio_threshold=0.5,
                congestion_threshold=settings.congestion_threshold, time_window=settings.time_window, interval=30):

        # 追踪模式预测结果
        results = self.model.track(source=input_path, conf=conf, device=settings.device, persist=True)
        img = Image.open(input_path)
        img = np.array(img)

        if self.recording_start_time is None:
            self.recording_start_time = time.time()

        if results[0].boxes.id is not None:
            for box in results[0].boxes:
                cls_id = box.cls.item()
                xyxy = box.xyxy.int().cpu().tolist()

                if (
                        cls_id in [2, 5, 7]
                        and box.conf.item() > conf
                        and is_bbox_partially_inside_region(xyxy[0], selected_region, intersection_ratio_threshold)
                ):
                    track_id = box.id.item()
                    xywh = box.xywh.int().cpu().tolist()
                    current_class = self.model.names[cls_id]
                    _track_coordinate = self.track_coordinate[track_id]
                    _track_coordinate.append((xywh[0][0], xywh[0][1]))

                    if len(_track_coordinate) > 2:
                        _track_coordinate.pop(0)

                    if len(_track_coordinate) > 1:
                        speed = estimated_speed(self.track_coordinate[track_id][-1],
                                                self.track_coordinate[track_id][-2], interval)
                        _track_speed = self.track_speed[track_id]
                        _track_speed.append(speed)
                        if len(_track_speed) > 3:
                            _track_speed.pop(0)

                    average_speed = int(sum(self.track_speed[track_id][-3:]) / 3)
                    self.average_speed.append(average_speed)
                    if len(self.average_speed) > 20:
                        self.average_speed.pop(0)

                    cls_color = get_class_color(current_class)
                    x_min = xyxy[0][0]
                    y_min = xyxy[0][1]
                    w = xywh[0][2]
                    h = xywh[0][3]
                    cvzone.cornerRect(img, (x_min, y_min, w, h), l=1, rt=2, colorR=cls_color)
                    cvzone.putTextRect(
                        img,
                        text=f"{current_class} {average_speed} km/h",
                        pos=(max(0, x_min), max(35, y_min)),
                        colorR=cls_color,
                        scale=1,
                        thickness=1,
                        offset=2)

                    self.class_count[current_class] += 1
                    self.total_flow += 1

            if time.time() - self.recording_start_time >= time_window:
                print(f"{time_window}s内总车流量: {self.total_flow}")
                self.recording_start_time = None  # 重置记录时间
                total_speed = sum(self.average_speed) / len(self.average_speed)
                print(f'平均车速：{total_speed}')

                if self.total_flow >= congestion_threshold and total_speed < settings.average_speed:
                    cv2.imwrite(output_path, img)
                    self.total_flow = 0
                    self.average_speed = []

                    return '交通拥堵'


if __name__ == '__main__':
    model = TrafficCongestionDetector('weights/yolov8n.pt')
    model.predict('input/parking.png', 'output/traffic_congestion.png', 0.5)
