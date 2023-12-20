import cv2
import torch
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks


from apps.config import settings


def calculate_intersection_ratio(bbox, region):
    # 计算边界框和选定区域的交集
    x1 = max(bbox[0], region[0])
    y1 = max(bbox[1], region[1])
    x2 = min(bbox[2], region[2])
    y2 = min(bbox[3], region[3])

    # 计算交集区域的面积
    intersection_area = max(0, x2 - x1 + 1) * max(0, y2 - y1 + 1)

    # 计算交集比例（交集/目标边界框面积）
    bbox_area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
    intersection_ratio = intersection_area / bbox_area

    return intersection_ratio


def is_bbox_partially_inside_region(bbox, selected_region, intersection_ratio_threshold=0.5):
    if not selected_region.any():
        return True

    intersection_ratio = calculate_intersection_ratio(bbox, selected_region)

    if intersection_ratio is not None:
        # 如果交集比例大于阈值，则判定为部分在区域内
        return intersection_ratio > intersection_ratio_threshold



class YOLODetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, img_path, conf):
        results = self.model.predict(source=img_path, conf=conf, device=settings.device)
        return results[0]


class ResultProcessor:
    def __init__(self, result):
        self.result = result

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


class Detector:
    def __init__(self, model_path, model_type):
        self.model_type = model_type
        if self.model_type == 'yolov8':
            self.processor = self.YOLOProcessor(model_path)
        elif self.model_type == 'yolov5':
            self.processor = self.GarbageProcessor(model_path)
        elif self.model_type == 'modelscope':
            self.processor = self.ModelscopeDetector(model_path)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def process(self, input_path, output_path, conf=0.5, selected_region=None, intersection_ratio_threshold=0.5):
        return self.processor.process(input_path, output_path, conf, selected_region, intersection_ratio_threshold)

    class YOLOProcessor:
        def __init__(self, model_path):
            self.detector = YOLODetector(model_path)

        def process(self, input_path, output_path, conf, selected_region, intersection_ratio_threshold):
            result = self.detector.detect(input_path, conf)
            processor = ResultProcessor(result)
            processor.save_image(output_path, selected_region, intersection_ratio_threshold)
            json_result = processor.save_json(selected_region, intersection_ratio_threshold)
            return [res['class'] for res in json_result]

    class GarbageProcessor:
        def __init__(self, model_path):
            self.device = torch.device(settings.device)
            self.model = torch.hub.load('yolov5', 'custom', path=model_path, source='local')
            self.class_names = self.model.names

        def process(self, input_path, output_path, conf, selected_region, intersection_ratio_threshold):
            result = self.model(input_path)
            confidences = result.xyxy[0][:, -2]

            mask = confidences >= conf
            filtered_result = result.xyxy[0][mask]

            if len(filtered_result) == 0:
                return None

            inside_filtered_result = []
            for idx in range(len(filtered_result)):
                bbox = filtered_result[idx, :-2].cpu().numpy()
                if is_bbox_partially_inside_region(bbox, selected_region, intersection_ratio_threshold):
                    inside_filtered_result.append(filtered_result[idx])

            if len(inside_filtered_result) == 0:
                return None

            classnames = []
            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            for item in inside_filtered_result:
                bbox = item[:-2].cpu().numpy()
                class_idx = int(item[-1].item())
                class_name = self.class_names[class_idx]
                confidence = item[-2].item()
                classnames.append(class_name)

                x_min, y_min, x_max, y_max = bbox
                draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

                draw.text((x_min, y_min - 20), f"{confidence:.2f}", fill="red",
                          font=ImageFont.truetype("arial.ttf", 16))

            image = image.convert("RGB")
            image.save(output_path)
            return classnames

    class ModelscopeDetector:
        def __init__(self, model_path):
            self.model_id = model_path
            self.detector = pipeline(Tasks.domain_specific_object_detection, model=model_path, device='gpu')

        def process(self, input_path, output_path, conf, selected_region, intersection_ratio_threshold):
            result = self.detector(input_path)

            confidences = result['scores']

            mask = confidences >= conf
            filtered_boxes = [box for i, box in enumerate(result['boxes']) if
                              mask[i] and is_bbox_partially_inside_region(box, selected_region,
                                                                          intersection_ratio_threshold)]
            filtered_labels = [label for i, label in enumerate(result['labels']) if
                               mask[i] and is_bbox_partially_inside_region(result['boxes'][i], selected_region,
                                                                           intersection_ratio_threshold)]

            if not filtered_boxes:
                return None

            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            for box, label in zip(filtered_boxes, filtered_labels):
                x_min, y_min, x_max, y_max = box
                draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

            image.save(output_path)

            return filtered_labels


if __name__ == '__main__':
    model_wrapper = Detector('weights/fire.pt', 'yolov8')
    model_wrapper.process(
        'input/fire.jpg', 'output/fire.jpg', 0.2, [0, 0, 1700, 900], 0.6
    )
