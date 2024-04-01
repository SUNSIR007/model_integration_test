from collections import defaultdict

import cv2
import numpy as np

from ultralytics import YOLO


model = YOLO('/Users/ryuichi/Documents/Graduation_Project/model_integration_test/yolov8n.pt')

video_path='../input/people.mp4'

cap = cv2.VideoCapture(video_path)

track_history = defaultdict(lambda: [])

while cap.isOpened():
    success , frame = cap.read()
    if success:
        results = model.track(frame,persist=True)
        track_ids=results[0].boxes.id.int().cpu().tolist()
        boxes = results[0].boxes.xywh.cpu()
        an_frame = results[0].plot()
        for track_id,box in zip(track_ids,boxes):
            track = track_history[track_id]
            x,y,w,h=box
            track.append((float(x),float(y)))
            if len(track)>30:
                track.pop(0)

        cv2.imshow("people",an_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    else:
        break
cap.release()
cv2.destroyAllWindows()





