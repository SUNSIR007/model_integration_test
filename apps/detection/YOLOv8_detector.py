import cv2
from PIL import Image
from ultralytics import YOLO

from apps.detection.myutils import is_bbox_partially_inside_region
from apps.config import settings


class YOLOv8Detector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def predict(self, input_path, output_path, conf, selected_region=None, intersection_ratio_threshold=0.5):
        result = self.model.predict(source=input_path, conf=conf, device=settings.device)
        processor = ResultProcessor(result)
        processor.save_image(output_path, selected_region, intersection_ratio_threshold)
        json_result = processor.save_json(selected_region, intersection_ratio_threshold)
        return [res['class'] for res in json_result]


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
