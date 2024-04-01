from collections import defaultdict

import cv2
import numpy as np

from ultralytics import YOLO

model = YOLO('../weights/sibao_v8n.pt')
path='../input/sibao/sibao.jpg'
results=model.predict(path)
print(results[0])
