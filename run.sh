#!/bin/bash


read -p "请输入IP地址 (回车跳过使用本机IP地址): " userInputIpAddress
inputIpAddress=${userInputIpAddress:-$(hostname -I | awk '{print $1}')}

defaultPort=3000

read -p "请输入端口号 (回车跳过使用默认端口号 $defaultPort): " userInputPort
newPort=${userInputPort:-$defaultPort}

configFile="../dist/webconfig.js"
runScript="./backup.sh"

sed -i "s/\"webApiBaseUrl\": \".*\"/\"webApiBaseUrl\": \"http:\/\/$inputIpAddress:$newPort\"/" $configFile

sed -i "s/--host [0-9.]\+ --port [0-9]*/--host $inputIpAddress --port $newPort/" $runScript

if pgrep -x "nginx" > /dev/null
then
    sudo /etc/nginx/sbin/nginx -s reload
else
    sudo /etc/nginx/sbin/nginx
fi

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

timestamp=$(date +"%Y%m%d%H%M%S")

logFilePath="$scriptDir/log/script_output_$timestamp.log"

mkdir -p "$scriptDir/log"

sudo pkill -f "uvicorn"

celeryPids=$(pgrep -f "celery")

for pid in $celeryPids; do
    sudo kill -9 "$pid"
done

bash $runScript > "$logFilePath" 2>&1 &

echo "页面访问地址: http://$inputIpAddress"
