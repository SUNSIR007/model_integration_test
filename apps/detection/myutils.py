import math

from apps.config import settings

palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)


def calculate_intersection_ratio(bbox, region):
    """计算边界框和选定区域的交集"""
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
    """检测对象与选择区域交叉比阈值"""
    if selected_region is None:
        return True
    for region in selected_region:
        intersection_ratio = calculate_intersection_ratio(bbox, region)

        if intersection_ratio is not None and intersection_ratio > intersection_ratio_threshold:
            # 如果交集比例大于阈值，则判定为部分在区域内
            return True


def estimated_speed(location_1, location_2, interval=30):
    # 计算欧氏距离
    d_pixel = math.sqrt(math.pow(location_2[0] - location_1[0], 2) + math.pow(location_2[1] - location_1[1], 2))

    # 计算ppm
    ppm = calculate_ppm(location_2)

    # 设置像素到米的转换比例
    d_meters = d_pixel / ppm

    # 计算速度
    speed = d_meters * 3.6 / interval

    return int(speed)


def get_class_color(cls):
    """
    Simple function that adds fixed color depending on the class
    """
    if cls == 'car':
        color = (204, 51, 0)
    elif cls == 'truck':
        color = (22, 82, 17)
    elif cls == 'motorbike':
        color = (255, 0, 85)
    else:
        color = [int((p * (2 ** 2 - 14 + 1)) % 255) for p in palette]
    return tuple(color)


def calculate_ppm(location_2):
    """根据 y 轴位置计算 ppm"""
    base_ppm = settings.base_ppm
    alpha = settings.alpha
    ppm = base_ppm * math.exp(alpha * location_2[1] / 100)

    return ppm
