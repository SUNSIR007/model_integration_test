from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from PIL import Image, ImageDraw
import numpy as np

from apps.detection.myutils import is_bbox_partially_inside_region


class ModelscopeDetector:
    def __init__(self, model_path):
        self.model_id = model_path
        self.detector = pipeline(Tasks.domain_specific_object_detection, model=model_path, device='cpu')

    def predict(self, input_path, output_path, conf, selected_region=None, intersection_ratio_threshold=0.5):
        result = self.detector(input_path)
        confidences = np.array(result['scores'])
        mask = confidences >= conf
        if 'boxes' not in result:
            filter_labels = [label for i, label in enumerate(result['labels']) if mask[i]]
            return filter_labels
        else:
            filtered_labels = [label for i, label in enumerate(result['labels']) if
                               mask[i] and is_bbox_partially_inside_region(result['boxes'][i], selected_region,
                                                                           intersection_ratio_threshold)]

            filtered_boxes = [box for i, box in enumerate(result['boxes']) if
                              mask[i] and is_bbox_partially_inside_region(box, selected_region,
                                                                          intersection_ratio_threshold)]

            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            for box, label in zip(filtered_boxes, filtered_labels):
                x_min, y_min, x_max, y_max = box
                draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

            image.save(output_path)

            return filtered_labels
