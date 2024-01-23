import torch
from ultralytics import YOLO


model = YOLO('weights/weeds.pt')
print(model.names)


# model = torch.hub.load('yolov5', 'custom', path='weights/garbage.pt', source='local')
# print(model.names)
