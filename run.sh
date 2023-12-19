#!/bin/bash


# 询问用户输入新的IP地址，如果为空则使用本机IP地址
read -p "请输入IP地址 (回车跳过使用本机IP地址): " userInputIpAddress
inputIpAddress=${userInputIpAddress:-$(hostname -I | awk '{print $1}')}

# 默认端口号为3000
defaultPort=3000

# 询问用户输入新的端口号，如果为空则使用默认端口号
read -p "请输入端口号 (回车跳过使用默认端口号 $defaultPort): " userInputPort
newPort=${userInputPort:-$defaultPort}

# 文件路径
configFile="../dist/webconfig.js"
runScript="./backup.sh"

# 更新前端服务的ip地址
sed -i "s/\"webApiBaseUrl\": \".*\"/\"webApiBaseUrl\": \"http:\/\/$inputIpAddress:$newPort\"/" $configFile

# 更新后端服务ip地址
sed -i "s/--host [0-9.]\+ --port [0-9]*/--host $inputIpAddress --port $newPort/" $runScript

# 检查Nginx是否已经启动
if pgrep -x "nginx" > /dev/null
then
    sudo /etc/nginx/sbin/nginx -s reload
else
    sudo /etc/nginx/sbin/nginx
fi

# 获取脚本所在目录
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 生成时间戳
timestamp=$(date +"%Y%m%d%H%M%S")

# 日志文件路径，包含时间戳字段
logFilePath="$scriptDir/log/script_output_$timestamp.log"

# 创建日志文件所在的目录（如果不存在）
mkdir -p "$scriptDir/log"

# 杀死已存在的 Python 进程
sudo pkill -f "python"

# 获取已存在的 Celery 进程号列表
celeryPids=$(pgrep -f "celery")

# 循环杀死每个 Celery 进程
for pid in $celeryPids; do
    sudo kill -9 "$pid"
done

# 等待一段时间，确保进程被终止
sleep 2

# 执行后端服务启动脚本
bash $runScript > "$logFilePath" 2>&1 &

echo "访问地址: http://$inputIpAddress"
