#!/bin/bash

# 获取本机IP地址
ip_address=$(ifconfig | grep -A1 'eth0\|enp\|ens\|eno\|wlan0' | tail -n1 | awk '{print $2}')

# 检查是否成功获取到IP地址
if [ -z "$ip_address" ]; then
    echo "无法获取IP地址。"
    exit 1
fi

# 指定保存IP地址的文件路径
file_path="/data/dist/"

# 替换文件中的变量
sed -i "s/OLD_IP/$ip_address/g" "$file_path"

echo "IP地址已更新到文件: $file_path"
