# 边缘计算平台盒子终端管理api服务

在边缘对采集的数据、视频进行分析

## 功能特性

| **模块** | **功能描述**                                                 |
| -------- | ------------------------------------------------------------ |
| 登录     | 信息展示包括设备编号，硬件版本，固件版本，设备名称，系统资源利用率（cpu，内存，存储空间） |
|          | 设备重启按钮支持对设备重启。                                 |
|          | 系统重置按钮重置所有设置。                                   |
|          | 列表展示当前盒子已经加载的所有算法，展示表头包括 算法名称，算法版本，安装时间，操作（删除）。 |
|          | 点击安装算法按钮进入安装算法弹窗，弹窗内可以选择本地下载的算法包，上传成功即安装成功。 |
|          | 列表操作栏点击删除按钮，弹出删除确认框，点击确定删除该算法。 |

| **模块** | **功能描述**                                                 |
| -------- | ------------------------------------------------------------ |
| 设备列表 | 点击设备管理菜单栏进入设备管理页面，设备管理页面分上下两栏显示。 |
|          | 下边栏显示所有的设备列表，表头包括，通道号，设备名称，设备地址，设备状态，ip，已配置算法，操作（详情，配置算法）。 |
|          | 点击添加设备按钮进入添加设备弹窗。                           |
|          | 点击列表操作栏的详情按钮进入设备编辑弹窗。                   |
|          | 点击列表操作栏的配置算法按钮跳转至设备已配置算法列表页面。   |

| **模块**      | **功能描述**                                                 |
| ------------- | ------------------------------------------------------------ |
| 新增/编辑设备 | 添加设备弹窗内表单字段包括 通道号，设备名称，接入协议，ip地址，端口号，用户名，密码等属性，点击保存按钮完成设备添加。 |
|               | 设备编辑弹窗内表单展示字段与新增相同。                       |

| **模块**           | **功能描述**                                                 |
| ------------------ | ------------------------------------------------------------ |
| 设备已配置算法管理 | 1.设备已配置算法列表页面，列表表头包括算法名称，算法版本，算法状态，操作（详情，[启用\|暂停]，删除）2.点击详情按钮进入设备算法配置页面。3.点击[启用\|暂停]按钮 启用或暂停该算法。4.点击删除按钮删除该算法。5.点击配置算法按钮下拉展示设备已经安装算法，选择算法后进入设备算法配置页面。 |
|                    | 设备算法配置页面内展示内容包括摄像头截图，可编辑字段包括抽帧间隔，报警间隔，算法配置。点击确认保存当前配置。 |

| **模块** | **功能描述**                                                 |
| -------- | ------------------------------------------------------------ |
| 实时视频 | 实例视频展示盒子接入的摄像头的实时监控画面，支持一分屏，四分屏...(最高分屏数由盒子可接入监控的路数决定)，分屏中只展示选中的视频通道，未选中的视频通道不展示。 |

| **模块** | **功能描述**                                                 |
| -------- | ------------------------------------------------------------ |
| 告警管理 | 点击告警管理菜单栏进入告警列表页，告警列表内展示所有的告警记录列表，表头字段包括 设备通道，设备名称，报警算法，报图片，报警时间，操作（详情，删除）。 |
|          | 点击详情弹窗展示告警内容，弹窗内字段包括，告警事件，告警算法，原始图片，告警图片 |

## 快速开始

```
使用以下步骤来运行项目：
# config.py配置相关信息

# 安装依赖
pip install -r requirements.txt

# 运行 run.sh 脚本：
./run.sh

```


