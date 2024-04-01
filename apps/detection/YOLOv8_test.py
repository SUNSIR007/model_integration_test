import cv2
from PIL import Image
from ultralytics import YOLO

from apps.detection.myutils import is_bbox_partially_inside_region
from apps.config import settings
import cvzone
from collections import defaultdict
import numpy as np


class YOLOv8Detector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(lambda: [])
        self.frame_count = {}
        self.parking_duration = {}

    def predict(self, input_file, output_file, conf, selected_region=None, intersection_ratio_threshold=0.5,
                min_stay_time=10):
        # video_path = input_path
        # cap = cv2.VideoCapture(video_path)
        # success, frame = cap.read()
        # fps = cap.get(cv2.CAP_PROP_FPS)
        fps = 24
        frame = input_file
        # if success:
        results = self.model.track(frame, persist=True)
        if results[0].boxes.id is not None:
            class_ids = (results[0].boxes.cls.int().cpu().tolist())
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            scores = results[0].boxes.conf.cpu().numpy()
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
                if class_id == 0:
                    x, y, w, h = box #x,y是中心点坐标,w和h 分别是宽和高
                    x_min = int(x - w / 2)
                    y_min = int(y - h / 2)
                    x_max = int(x + w / 2)
                    y_max = int(y + h / 2)
                    track = self.track_history[track_id]
                    track.append((float(x), float(y)))

                    if track_id not in self.frame_count and score > conf and is_bbox_partially_inside_region(
                            [x_min, y_min, x_max, y_max], selected_region, intersection_ratio_threshold):
                        self.frame_count[track_id] = 1
                        self.parking_duration[track_id] = 0

                    if track_id in self.frame_count and self.parking_duration[
                        track_id] >= min_stay_time and score > conf and is_bbox_partially_inside_region(
                            [x_min, y_min, x_max, y_max], selected_region, intersection_ratio_threshold):
                        cvzone.cornerRect(frame, (x_min, y_min, int(w), int(h)), l=1, rt=2, colorR=(204, 51, 0))
                        text = f"parking time: {int(self.parking_duration[track_id])} s"
                        cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
                                    cv2.LINE_AA)
                        result_list_json = []
                        result_dict = {
                            'class_id': class_id,
                            'class': results[0].names[int(box.cls)],
                            'confidence': float(box.conf),
                            'bbox': {
                                'x_min': int(box[0]),
                                'y_min': int(box[1]),
                                'x_max': int(box[2]),
                                'y_max': int(box[3]),
                            }
                        }
                        result_list_json.append(result_dict)
                        if len(track) > 30:
                            track.pop(0)
                        #存储预测后的图像
                        im_array = results[0].plot()
                        Image.fromarray(im_array[..., ::-1]).save(output_file)

                        return [res['class'] for res in result_list_json]

                    if track_id in self.frame_count:
                        self.frame_count[track_id] += 1
                        if self.frame_count[track_id] % fps == 0:
                            self.parking_duration[track_id] += 1

            #im_array = results[0].plot()
            #Image.fromarray(im_array[..., ::-1]).save(output_file)

# result = self.model(source=input_path, conf=conf, device=settings.device)
# processor = ResultProcessor(result)
# processor.save_image(output_path, selected_region, intersection_ratio_threshold)
# json_result = processor.save_json(selected_region, intersection_ratio_threshold)
# return [res['class'] for res in json_result]


class ResultProcessor:
    def __init__(self, result):
        self.result = result[0]

    def save_image(self, output_path, selected_region, intersection_ratio_threshold):
        if len(self.result.boxes) == 0:
            return None

        if selected_region is not None:
            filtered_boxes = [box for box in self.result.boxes.data.cpu().numpy() if
                              is_bbox_partially_inside_region(box, selected_region, intersection_ratio_threshold)]
            if not filtered_boxes:
                return None

        im_array = self.result.plot()
        Image.fromarray(im_array[..., ::-1]).save(output_path)
        return output_path

    def save_json(self, selected_region, intersection_ratio_threshold):
        len_results = len(self.result.boxes)
        result_list_json = []

        for idx in range(len_results):
            bbox = self.result.boxes.data[idx].cpu().numpy()
            if selected_region is not None and not is_bbox_partially_inside_region(bbox, selected_region,
                                                                                   intersection_ratio_threshold):
                continue

            result_dict = {
                'class_id': int(self.result.boxes.cls[idx]),
                'class': self.result.names[int(self.result.boxes.cls[idx])],
                'confidence': float(self.result.boxes.conf[idx]),
                'bbox': {
                    'x_min': int(bbox[0]),
                    'y_min': int(bbox[1]),
                    'x_max': int(bbox[2]),
                    'y_max': int(bbox[3]),
                },
            }

            if self.result.masks is not None:
                result_dict['mask'] = cv2.resize(
                    self.result.masks.data[idx].cpu().numpy(),
                    (self.result.orig_shape[1], self.result.orig_shape[0])
                ).tolist()
                result_dict['segments'] = self.result.masks.xyn[idx].tolist()

            if self.result.keypoints is not None:
                result_dict['keypoints'] = self.result.keypoints.xyn[idx].tolist()

            result_list_json.append(result_dict)

        return result_list_json


if __name__ == '__main__':
    detector = YOLOv8Detector('weights/sibao_v8n.pt')
    print(detector.predict(input_file='input/sibao/sibao.jpg',
                           output_file='output/sibao.jpg',
                           conf=0.5,
                           selected_region=None,
                           intersection_ratio_threshold=0.2
                           ))
