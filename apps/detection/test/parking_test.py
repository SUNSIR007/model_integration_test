from collections import defaultdict

import cv2
import cvzone
import numpy as np
from ultralytics import YOLO

from apps.detection.myutils import is_bbox_partially_inside_region


class IllegalParkingDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(lambda: []) #使用defaultdict创建了一个字典self.track_history，用于跟踪每个检测到的对象的历史位置。如果访问的键不存在，defaultdict会自动创建一个空列表作为默认值。
        self.frame_count = {} #初始化一个空字典self.frame_count，可能用于记录每个对象出现在视频帧中的次数。
        self.parking_duration = {} #初始化另一个空字典self.parking_duration，可能用于存储每个检测到的停车对象的停车持续时间。

    def predict(self, source, conf, selected_region=None, intersection_ratio_threshold=0.5, min_stay_time=10):
        video_path = source
        cap = cv2.VideoCapture(video_path) #使用cv2.VideoCapture打开视频文件。cap对象用于逐帧读取视频。
        fps = cap.get(cv2.CAP_PROP_FPS) #获取视频的帧率（FPS），即每秒显示的帧数。这个信息对于后续视频处理和分析至关重要。

        fourcc = cv2.VideoWriter_fourcc(*'mp4v') #定义视频编码格式为mp4v。fourcc是一个4字符代码，用来指定视频文件的编码格式。
        out = cv2.VideoWriter('output_video.mp4', fourcc=fourcc, fps=fps, frameSize=(1080, 720)) #创建一个VideoWriter对象out，用于输出处理后的视频。输出视频的文件名为output_video.mp4，使用与输入相同的帧率fps，但帧大小设置为1080x720。

        while cap.isOpened(): #使用while循环来持续读取视频帧，直到视频结束或无法打开。cap.isOpened()检查视频是否成功打开。
            success, frame = cap.read() #使用cap.read()从视频中读取下一帧。success是一个布尔值，指示是否成功读取帧；frame是读取的帧本身。
            if success:
                frame = cv2.resize(frame, (1080, 720)) #将读取的视频帧大小调整为1080x720。这是为了标准化输入数据，确保后续处理的一致性。
                results = self.model.track(frame, persist=True) #调用track方法进行对象的检测和跟踪。persist=True参数可能意味着跟踪信息会被保留用于后续分析。
                if results[0].boxes.id is not None: #检查第一个结果中的boxes.id是否不为空。这意味着至少有一个对象被检测到并且有一个分配给它的ID。
                    class_ids = (results[0].boxes.cls.int().cpu().tolist()) #这行代码提取检测到的对象的类别ID，并将其转换为一个整数列表。cls.int()将类别转换为整数类型，.cpu()确保操作在CPU上执行（如果使用的是GPU进行计算的话），tolist()将结果转换为Python列表。
                    boxes = results[0].boxes.xywh.cpu() #这行代码提取检测到的每个对象的边界框，格式为(x, y, width, height)。.cpu()同样确保数据被移到CPU上。
                    track_ids = results[0].boxes.id.int().cpu().tolist() #这行代码提取每个检测到的对象的跟踪ID，并将其转换为一个整数列表。这个ID用于在视频帧之间跟踪同一对象。同样，数据被确保处理在CPU上并转换为列表。
                    scores = results[0].boxes.conf.cpu().numpy() #这行代码提取每个检测到的对象的置信度分数，并将结果转换为NumPy数组。置信度分数反映了模型对其检测结果的置信程度。

                    # 绘制selected_region的矩形区域
                    if selected_region: #这行代码判断是否提供了selected_region参数。如果该参数存在，即存在一个或多个需要标记的区域，则执行下面的代码块。
                        for region in selected_region:
                            x_min, y_min, x_max, y_max = region #每个region预期包含四个坐标值(x_min, y_min, x_max, y_max)，定义了需要高亮显示的矩形区域的左下角和右上角。
                            region = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]] #矩形区域通过将坐标转换为四个角点的列表[[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]来定义，然后将这个列表转换为NumPy数组，用于后续的图形操作。
                            region = np.array(region, dtype=np.int32)
                            filled_rectangle = np.zeros_like(frame) #创建一个与当前视频帧大小相同，但所有像素值均为0（即全黑）的图像。
                            cv2.fillPoly(filled_rectangle, [region], color=(0, 255, 0)) #使用OpenCV的fillPoly函数在filled_rectangle图像上填充一个多边形，多边形的顶点由region定义，填充颜色为绿色(0, 255, 0)。
                            alpha = 0.07  # 调整透明度
                            frame = cv2.addWeighted(frame, 1 - alpha, filled_rectangle, alpha, 0) #使用OpenCV的addWeighted函数将原始帧与绿色矩形叠加，根据alpha值调整透明度。这里，原始帧的权重为1 - alpha，而绿色矩形的权重为alpha，最后一个参数0是加权和的标量值。

                    for box, track_id, class_id, score in zip(boxes, track_ids, class_ids, scores): #这行代码使用zip函数将检测到的对象的边界框(boxes)、跟踪ID(track_ids)、类别ID(class_ids)和置信度分数(scores)组合在一起，然后遍历每个组合。这允许你同时访问每个检测到的对象的所有相关信息。
                        if class_id == 2 or class_id == 7: #这行代码检查对象的类别ID是否为2或7。如果是，那么执行下面的操作。这可能表示只对特定类型的对象（如汽车和卡车）感兴趣。
                            x, y, w, h = box #从box变量中提取中心点坐标(x, y)和宽度(w)、高度(h)。
                            x_min = int(x - w / 2) #计算边界框的左上角(x_min, y_min)和右下角(x_max, y_max)坐标，以便后续可能的操作，如绘制边界框或进一步分析。
                            y_min = int(y - h / 2)
                            x_max = int(x + w / 2)
                            y_max = int(y + h / 2)
                            track = self.track_history[track_id] #访问track_history字典，该字典跟踪每个对象的历史位置。track_id是该对象的唯一标识符。
                            track.append((float(x), float(y)))  #向该对象的跟踪历史中添加当前帧的中心点坐标。这可以用于后续的运动分析或可视化该对象在视频中的移动路径。

                            if track_id not in self.frame_count \
                                    and score > conf \
                                    and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                        selected_region, intersection_ratio_threshold):
                                #检查当前跟踪ID是否尚未记录在self.frame_count字典中，即这个对象是否是首次被检测到。
                                #确认当前对象的置信度分数是否高于预先设定的阈值conf。只有当对象的检测置信度足够高时，才会考虑进一步的处理。
                                #判断当前对象的边界框是否至少部分位于指定的区域内。这个函数可能会根据边界框与指定区域的交集比例与预设的阈值intersection_ratio_threshold来做决定。
                                self.frame_count[track_id] = 1 #如果满足以上所有条件，说明当前对象是首次被检测到且符合后续处理的要求，因此在self.frame_count字典中为这个对象创建一个条目，并设置其值为1，表示当前帧是这个对象首次出现。
                                self.parking_duration[track_id] = 0 #为这个对象在self.parking_duration字典中创建一个条目，并初始化其值为0。这个值可能会在后续帧中更新，以计算对象在感兴趣区域内停留的持续时间。

                            if track_id in self.frame_count \
                                    and self.parking_duration[track_id] > min_stay_time \
                                    and score > conf \
                                    and is_bbox_partially_inside_region([x_min, y_min, x_max, y_max],
                                                                        selected_region, intersection_ratio_threshold):
                                cvzone.cornerRect(frame, (x_min, y_min, int(w), int(h)), l=1, rt=2,
                                                  colorR=(204, 51, 0)) #如果上述条件全部满足，使用cvzone.cornerRect函数在视频帧上绘制一个矩形，这个矩形标记了被追踪对象的位置。这个矩形的颜色被设置为橙色（RGB值为(204, 51, 0)），这可以帮助视觉上区分这些特定的对象。

                                text = f"parking time: {int(self.parking_duration[track_id])} s"
                                cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                            (0, 0, 255), 1, cv2.LINE_AA) #使用cv2.putText在矩形的上方绘制文本，显示对象的停车持续时间（以秒为单位）

                                if len(track) > 30: #最后，这段代码检查对象的跟踪历史长度是否超过了30个点（if len(track) > 30:）。如果是的话，它从跟踪历史的开始处删除最旧的点（track.pop(0)）。这个操作确保了跟踪历史的长度被保持在一个合理的范围内，既可以避免内存占用过高，也保证了跟踪数据的实时性和准确性。
                                    track.pop(0)

                            if track_id in self.frame_count: #这行代码检查给定的track_id是否存在于self.frame_count字典中。该字典跟踪每个被检测对象的帧计数，即该对象出现在视频中的帧数。
                                self.frame_count[track_id] += 1 #如果该对象已经被追踪，则其帧计数加1。这表示该对象在又一个新的视频帧中被检测到。
                                if self.frame_count[track_id] % fps == 0: #这行代码检查对象的帧计数是否是视频帧率（fps）的整数倍。如果是，这意味着对象已经在视频中出现了足够的帧数，相当于又过去了一秒钟。
                                    self.parking_duration[track_id] += 1 #在上述条件满足的情况下，该对象的停车持续时间（秒）加1。这个操作基于假设视频以实时速度播放，即视频的每一帧代表了实际时间中的一个固定间隔。

                out.write(frame)  # 这行代码使用之前创建的cv2.VideoWriter对象（在这个场景中假定为out）将处理后的帧（frame）写入到输出视频文件中。这个操作确保了所有经过处理（如标记非法停车区域）的帧都被保存下来，从而生成一个包含了所有检测和注释的新视频文件。
                cv2.imshow("Illgal parking monitor", frame) #使用OpenCV的imshow函数在窗口中显示当前处理过的帧。这个窗口被命名为"Illegal parking monitor"，它会展示视频帧，包括所有的图形标记和文本注释，让用户能够实时看到非法停车监测的结果。
                cv2.waitKey(1) #这个函数是OpenCV中用于等待键盘输入的标准方法。参数1表示函数会等待1毫秒的时间。这个短暂的延迟允许OpenCV有足够的时间处理和显示当前帧，同时使得视频能够以接近实时的速度播放。如果在这1毫秒内，有任何键盘输入，函数将返回按键的ASCII码，否则返回-1。在这个特定场景中，按键输入并没有被明确用于控制流程，但这个函数调用对于图像显示窗口的正常工作是必需的。

            else:
                # 如果视频结束则退出循环
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    detector = IllegalParkingDetector('../weights/sibao_v8n.pt')
    detector.predict(source='../input/sibao.jpg',
                 conf=0.5,
                 selected_region=None,
                 min_stay_time=2
                 )
