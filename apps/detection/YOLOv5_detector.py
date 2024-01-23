import yolov5
from PIL import Image, ImageDraw, ImageFont

from apps.detection.utils import is_bbox_partially_inside_region


class YOLOv5Detector:
    def __init__(self, model_path):
        self.model = yolov5.load(model_path, 'cpu')
        self.class_names = self.model.names

    def predict(self, input_path, output_path, conf, selected_region=None, intersection_ratio_threshold=0.5):
        results = self.model(input_path)
        predictions = results.pred[0]
        confidences = predictions[:, 4]

        mask = confidences >= conf
        boxes = predictions[:, :4]

        if boxes.size(0) == 0:
            return []

        inside_filtered_result = []
        filtered_predictions = predictions[mask]

        if filtered_predictions.size(0) == 0:
            return []

        for idx in range(filtered_predictions.size(0)):
            bbox = boxes[idx].cpu().numpy()
            if is_bbox_partially_inside_region(bbox, selected_region, intersection_ratio_threshold):
                inside_filtered_result.append(filtered_predictions[idx])

        if not inside_filtered_result:
            return []

        classnames = []
        image = Image.open(input_path)
        draw = ImageDraw.Draw(image)
        font_size = 30
        font = ImageFont.truetype("arial.ttf", font_size)

        for item in inside_filtered_result:
            bbox = item[:4].cpu().numpy()
            class_idx = int(item[5].item())
            class_name = self.class_names[class_idx]
            confidence = item[4].item()
            classnames.append(class_name)

            x_min, y_min, x_max, y_max = bbox
            draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

            draw.text((x_min, y_min - 30), f"{class_name} ({confidence:.2f})", fill="red", font=font)

        image = image.convert("RGB")
        image.save(output_path)
        return classnames


if __name__ == '__main__':
    model = YOLOv5Detector('weights/garbage.pt')
    model.predict('input/111.jpg', 'output/1.png', 0.5)
