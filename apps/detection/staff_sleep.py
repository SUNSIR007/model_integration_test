import cv2
import torch
from ultralytics import YOLO
from apps.detection.utils import is_bbox_partially_inside_region


class SleepDetector:
    def __init__(self, model_weights_path):
        self.model = YOLO(model_weights_path)

    @staticmethod
    def is_sleeping(keypoints, distance_threshold):
        left_ear = keypoints[3]
        right_ear = keypoints[4]
        left_wrist = keypoints[9]
        right_wrist = keypoints[10]

        distance_left_ear_to_left_wrist = torch.norm(left_ear[:2] - left_wrist[:2])
        distance_right_ear_to_right_wrist = torch.norm(right_ear[:2] - right_wrist[:2])

        return distance_left_ear_to_left_wrist < distance_threshold or distance_right_ear_to_right_wrist < distance_threshold

    def predict(self, input_image_path, output_image_path, confidence_threshold=0.5, selected_region=None):
        results = self.model.predict(source=input_image_path, conf=confidence_threshold)
        im = cv2.imread(input_image_path)
        image_height, image_width = im.shape[0], im.shape[1]

        detected_class_names = []
        for i in range(len(results[0].boxes.data)):
            threshold_percentage = 0.2
            threshold = threshold_percentage * image_height

            if results[0].names[i] == "person" and self.is_sleeping(results[0].keypoints.data[i], threshold):
                x1, y1, x2, y2, _, _ = results[0].boxes.data[i]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # 判断是否部分在选定区域内
                if is_bbox_partially_inside_region((x1, y1, x2, y2), selected_region):
                    # 绘制边界框和标签
                    cv2.rectangle(im, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    label = "Sleeping Person"
                    detected_class_names.append(label)
                    cv2.putText(im, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 保存输出图像
        cv2.imwrite(output_image_path, im)

        return detected_class_names
