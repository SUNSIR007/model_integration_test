import math


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


def calculate_ppm(location_2):
    """根据 y 轴位置计算 ppm"""
    base_ppm = 0.2
    alpha = 1
    ppm = base_ppm * math.exp(alpha * location_2[1] / 100)

    return ppm


print(calculate_ppm([100, 50]))
