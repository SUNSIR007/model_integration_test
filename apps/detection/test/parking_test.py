from collections import defaultdict

import cv2
import cvzone
import numpy as np
from ultralytics import YOLO

from utils import is_bbox_partially_inside_region


class IllegalParkingDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(lambda: [])
        self.frame_count = {}
        self.parking_duration = {}

    def predict(self, source, conf, selected_region=None, intersection_ratio_threshold=0.5, min_stay_time=10):
        video_path = source
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output_video.mp4', fourcc=fourcc, fps=fps, frameSize=(1080, 720))

        while cap.isOpened():
            success, frame = cap.read()
            if success:
                frame = cv2.resize(frame, (1080, 720))
                results = self.model.track(frame, persist=True)
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
                            filled_rectangle = np.zeros_like(frame)
                            cv2.fillPoly(filled_rectangle, [region], color=(0, 255, 0))
                            alpha = 0.07  # 调整透明度
                            frame = cv2.addWeighted(frame, 1 - alpha, filled_rectangle, alpha, 0)

                    for box, track_id, class_id, score in zip(boxes, track_ids, class_ids, scores):
                        if class_id == 2 or class_id == 7:
                            x, y, w, h = box
                            x_min = int(x - w / 2)
                            y_min = int(y - h / 2)
                            x_max = int(x + w / 2)
                            y_max = int(y + h / 2)
                            track = self.track_history[track_id]
                            track.append((float(x), float(y)))  # x, y中心点

                            if track_id not in self.frame_count \
                                    and score > conf \
                                    and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                        selected_region, intersection_ratio_threshold):
                                self.frame_count[track_id] = 1
                                self.parking_duration[track_id] = 0

                            if track_id in self.frame_count \
                                    and self.parking_duration[track_id] > min_stay_time \
                                    and score > conf \
                                    and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                        selected_region, intersection_ratio_threshold):
                                cvzone.cornerRect(frame, (x_min, y_min, int(w), int(h)), l=1, rt=2,
                                                  colorR=(204, 51, 0))

                                text = f"parking time: {int(self.parking_duration[track_id])} s"
                                cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                            (0, 0, 255), 1, cv2.LINE_AA)

                                if len(track) > 30:
                                    track.pop(0)

                            if track_id in self.frame_count:
                                self.frame_count[track_id] += 1
                                if self.frame_count[track_id] % fps == 0:
                                    self.parking_duration[track_id] += 1

                out.write(frame)  # 写入帧到输出视频
                cv2.imshow("Illgal parking monitor", frame)
                cv2.waitKey(1)

            else:
                # 如果视频结束则退出循环
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()


detector = IllegalParkingDetector('../weights/yolov8l.pt')
detector.predict(source='input/illegal_parking.mp4',
                 conf=0.5,
                 selected_region=[[500, 260, 600, 300], [570, 350, 800, 650]],
                 min_stay_time=10
                 )
