import torch
from ultralytics import YOLO


model = YOLO('weights/sibao_v8n.pt')
print(model.names)


# model = torch.hub.load('yolov5', 'custom', path='weights/garbage.pt', source='local')
# print(model.names)
