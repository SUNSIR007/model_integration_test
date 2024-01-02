import os
import shutil
from datetime import datetime

import psutil


def get_memory_total() -> int:
    # 获取内存总量（单位：字节）
    memory = psutil.virtual_memory()
    return memory.total


def get_memory_usage() -> int:
    # 获取内存使用量（单位：字节）
    memory = psutil.virtual_memory()
    return memory.used


def get_disk_total() -> int:
    # 获取磁盘总量（单位：字节）
    disk = psutil.disk_usage('/')
    return disk.total


def get_disk_usage() -> int:
    # 获取磁盘使用量（单位：字节）
    disk = psutil.disk_usage('/')
    return disk.used


def get_temperature() -> float:
    # 获取温度（例如 CPU 温度）
    temperature = psutil.sensors_temperatures()
    if 'cpu-thermal' in temperature:
        return temperature['cpu-thermal'][0].current
    return 0.0


def get_cpu_usage() -> float:
    # 获取 CPU 使用率
    cpu_usage = psutil.cpu_percent()
    return cpu_usage


def delete_folders_before_date(base_folder, target_date):
    try:
        target_date = datetime.strptime(str(target_date), "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use 'YYYY-MM-DD'.")
        return

    for folder_name in os.listdir(base_folder):
        folder_path = os.path.join(base_folder, folder_name)
        try:
            # 解析文件夹名中的日期部分
            folder_date = datetime.strptime(folder_name, "%Y-%m-%d")

            # 如果文件夹日期早于目标日期，删除文件夹及其内容
            if folder_date < target_date:
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")
        except ValueError:
            print(f"Skipping folder with invalid date format: {folder_path}")
