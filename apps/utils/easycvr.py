import time

import httpx
import hashlib
from fastapi import HTTPException

from apps.config import settings


EASYCVR_SERVER_URL = settings.easycvr_url
LOGIN_URL = "/api/v1/login"
ADD_DEVICE_URL = "/api/v1/adddevice"
ADD_CHANNEL_URL = "/api/v1/addchannel"
CHANNEL_STREAM_URL = "/api/v1/devices/channelstream"

SERVER_ID = "EasyCVR_NODE_01"


def md5_hash(input_str):
    """计算输入字符串的 MD5 哈希值"""
    return hashlib.md5(input_str.encode('utf-8')).hexdigest()


def make_request(url, method, headers=None, params=None, json_data=None):
    with httpx.Client() as client:
        response = client.request(
            method, url, headers=headers, params=params, json=json_data
        )
        return response


def get_access_token():
    params = {
        "username": settings.easycvr_username,
        "password": md5_hash(settings.easycvr_password)
    }
    response = make_request(EASYCVR_SERVER_URL + LOGIN_URL, "GET", params=params)

    if response.status_code == 200:
        return response.json()["EasyDarwin"]["Body"]["Token"]
    else:
        raise HTTPException(status_code=401, detail="无效的用户名或密码")


def add_device(device_name: str, device_type: str, transport: str, access_token: str):
    """
    添加设备

    :param device_name: 设备名
    :param device_type: 设备类型 (e.g., "ipc")
    :param transport: 传输协议 (e.g., "TCP")
    :param access_token: token
    :return: 设备ID
    """
    headers = {"Content-Type": "application/json", "token": access_token}
    data = {
        "DeviceName": device_name,
        "DeviceType": device_type,
        "Enable": True,
        "Transport": transport,
        "ServerID": SERVER_ID,
    }

    response = make_request(EASYCVR_SERVER_URL + ADD_DEVICE_URL, "POST", headers=headers, json_data=data)

    if response.status_code == 200:
        return response.json()["EasyDarwin"]["Body"]["DeviceID"]
    else:
        raise HTTPException(status_code=401, detail="添加设备失败")


def add_channel(channel_name: str, protocol: str, parent_device_id: int, rtsp_url: str, access_token: str):
    """
    添加通道

    :param channel_name: 通道名
    :param rtsp_url: 接入RTSP码流地址
    :param protocol: 通道协议类型 (e.g., "RTSP").
    :param parent_device_id: 通道所属设备ID
    :param access_token: token
    :return: 通道ID
    """
    headers = {"Content-Type": "application/json", "token": access_token}
    data = {
        "Enable": 1,
        "Name": channel_name,
        "RtspUrl": rtsp_url,
        "Protocol": protocol,
        "ParentDeviceID": parent_device_id,
        "ServerID": SERVER_ID,
    }

    response = make_request(EASYCVR_SERVER_URL + ADD_CHANNEL_URL, "POST", headers=headers, json_data=data)

    if response.status_code == 200:
        return response.json()["EasyDarwin"]["Body"]["ChannelID"]
    else:
        raise HTTPException(status_code=401, detail="添加通道失败")


def get_channel_stream(device_id: int, channel_id: int, protocol: str, access_token: str):
    headers = {"Content-Type": "application/json", "token": access_token}
    params = {
        "device": device_id,
        "channel": channel_id,
        "protocol": protocol,
        "token": access_token,
    }
    max_retries = 30  # 设置最大轮询次数
    retries = 0

    while retries < max_retries:
        response = make_request(EASYCVR_SERVER_URL + CHANNEL_STREAM_URL, "GET", headers=headers, params=params)

        if response.status_code == 200:
            status = response.json()["EasyDarwin"]["Header"]["ErrorNum"]
            if status == "200":
                return EASYCVR_SERVER_URL + response.json()["EasyDarwin"]["Body"]["URL"]

        time.sleep(1)
        retries += 1

    # 如果在最大轮询次数内通道仍然离线，则抛出异常
    raise HTTPException(status_code=401, detail=f"通道[{device_id}][{channel_id}]未能在线")


def convert_rtsp_to_http(device_name: str, device_type: str, transport: str, channel_name: str, protocol: str,
                         rtsp_url: str, target_protocol: str):
    token = get_access_token()
    device_id = add_device(device_name, device_type, transport, token)
    channel_id = add_channel(channel_name, protocol, device_id, rtsp_url, token)
    stream_url = get_channel_stream(device_id, channel_id, target_protocol, token)
    return stream_url
