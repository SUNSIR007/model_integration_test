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
runScript="backup.sh"

# 更新前端服务的ip地址
sed -i "s/\"webApiBaseUrl\": \".*\"/\"webApiBaseUrl\": \"http:\/\/$inputIpAddress:$newPort\"/" $configFile

# 更新后端服务ip地址
sed -i "s/--host 0.0.0.0 --port [0-9]*/--host $inputIpAddress --port $newPort/" $runScript

# 检查Nginx是否已经启动
if pgrep -x "nginx" > /dev/null
then
    /etc/nginx/sbin/nginx -s reload
else
    /etc/nginx/sbin/nginx
fi

# 执行后端服务启动脚本
bash $runScript

echo "访问地址: http://$inputIpAddress"
