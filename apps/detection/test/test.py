# from PIL import Image
# from ultralytics import YOLO
#
#
# model = YOLO('../weights/last.pt')
#
# result = model.predict('../input/1.png')
#
# for r in result:
#     print(r.boxes)
#     im_array = r.plot()
#     im = Image.fromarray(im_array[..., ::-1])
#     im.show()
#     im.save('../output/1.png')


import cv2
import yolov5


model = yolov5.load('../weights/best.pt', 'cpu')
results = model('../input/2.png')
image = cv2.imread('../input/2.png')

for result in results.xyxy[0]:
    conf = result[4].item()
    if conf > 0.5:
        x_min, y_min, x_max, y_max = map(int, result[:4])
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

cv2.imwrite('../output/1.png', image)
