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
