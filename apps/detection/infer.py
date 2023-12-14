import cv2
import torch
from PIL import Image, ImageDraw
from ultralytics import YOLO
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

from apps.config import settings


class YOLODetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, img_path, conf):
        results = self.model.predict(source=img_path, conf=conf, device=settings.device)
        return results[0]


class ResultProcessor:
    def __init__(self, result):
        self.result = result

    def save_image(self, output_path):
        if len(self.result.boxes) == 0:
            return None
        # 保存检测结果图像
        im_array = self.result.plot()
        Image.fromarray(im_array[..., ::-1]).save(output_path)
        return output_path

    def save_json(self):
        # 将检测结果转换为 JSON 格式
        len_results = len(self.result.boxes)
        result_list_json = [
            {
                'class_id': int(self.result.boxes.cls[idx]),
                'class': self.result.names[int(self.result.boxes.cls[idx])],
                'confidence': float(self.result.boxes.conf[idx]),
                'bbox': {
                    'x_min': int(self.result.boxes.data[idx][0]),
                    'y_min': int(self.result.boxes.data[idx][1]),
                    'x_max': int(self.result.boxes.data[idx][2]),
                    'y_max': int(self.result.boxes.data[idx][3]),
                },
            } for idx in range(len_results)
        ]
        if self.result.masks is not None:
            for idx in range(len_results):
                result_list_json[idx]['mask'] = cv2.resize(
                    self.result.masks.data[idx].cpu().numpy(),
                    (self.result.orig_shape[1], self.result.orig_shape[0])
                ).tolist()
                result_list_json[idx]['segments'] = self.result.masks.xyn[idx].tolist()
        if self.result.keypoints is not None:
            for idx in range(len_results):
                result_list_json[idx]['keypoints'] = self.result.keypoints.xyn[idx].tolist()
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

    def process(self, input_path, output_path, conf=0.5):
        return self.processor.process(input_path, output_path, conf)

    class YOLOProcessor:
        def __init__(self, model_path):
            self.detector = YOLODetector(model_path)

        def process(self, input_path, output_path, conf):
            result = self.detector.detect(input_path, conf)
            processor = ResultProcessor(result)
            processor.save_image(output_path)
            json_result = processor.save_json()
            return [res['class'] for res in json_result]

    class GarbageProcessor:
        def __init__(self, model_path):
            self.device = torch.device(settings.device)
            self.model = torch.hub.load('yolov5', 'custom', path=model_path, source='local')
            self.class_names = self.model.names

        def process(self, input_path, output_path, conf):
            result = self.model(input_path)

            # 获取置信度
            confidences = result.xyxy[0][:, -1]

            # 过滤置信度低于阈值的检测结果
            mask = confidences >= conf
            filtered_result = result.xyxy[0][mask]

            if len(filtered_result) == 0:
                return None

            classnames = [self.class_names[i.item()] for i in filtered_result[:, -1].int()]
            filtered_image_array = result.render()[0]
            filtered_image = Image.fromarray(filtered_image_array)
            filtered_image.save(output_path)
            return classnames

    class ModelscopeDetector:
        def __init__(self, model_path):
            self.model_id = model_path
            self.detector = pipeline(Tasks.domain_specific_object_detection,
                                     model=model_path.replace("apps/detection/", "", 1), device=settings.device)

        def process(self, input_path, output_path, conf):
            result = self.detector(input_path)

            # 获取置信度
            confidences = result['scores']

            # 过滤置信度低于阈值的检测结果
            mask = confidences >= conf
            filtered_boxes = [box for i, box in enumerate(result['boxes']) if mask[i]]
            filtered_labels = [label for i, label in enumerate(result['labels']) if mask[i]]

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
    model_wrapper = Detector('weights/damo/safety-helmet', 'modelscope')
    model_wrapper.process('input/fire3.jpg', 'output/fire.jpg', 0.4)
