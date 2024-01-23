---
tasks:
- domain-specific-object-detection
model-type:
- tinynas-damoyolo
domain:
- cv
frameworks:
- pytorch
backbone:
- tinynas
metrics:
- mAP
customized-quickstart: False
finetune-support: True
license: Apache License 2.0
integrating: True
tags:
- DAMO-YOLO
- real-time smokefire detection
- 实时烟火检测
- 热门应用系列检测模型




---

<!--- 以下model card模型说明部分，请使用中文提供（除了代码，bibtex等部分） --->

# 实时烟火检测-通用 模型介绍
<!-- <div align="center"><img src="assets/results.png" width="2000"></div> -->

本模型为**高性能热门应用系列检测模型**中的 <u>实时烟火检测模型</u>，基于面向工业落地的高性能检测框架[DAMOYOLO](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo/summary)，其精度和速度超越当前经典的YOLO系列方法。用户使用的时候，仅需要输入一张图像，便可以获得图像中所有烟火的坐标信息。


## 相关模型

以下是ModelScope上所有的热门应用检测模型（垂类目标检测模型）：

| 序号 | 模型名称 | 序号 | 模型名称 |
| ------------ | ------------ | ------------ | ------------ |
| 1 | [实时人体检测模型](https://modelscope.cn/models/damo/cv_tinynas_human-detection_damoyolo/summary) | 6 | [实时香烟检测模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo_cigarette/summary) |
| 2 | [实时人头检测模型](https://modelscope.cn/models/damo/cv_tinynas_head-detection_damoyolo/summary) | 7 | [实时手机检测模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo_phone/summary) |
| 3 | [实时手部检测模型](https://modelscope.cn/models/damo/cv_yolox-pai_hand-detection/summary) | 8 | [实时交通标识检测模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo_traffic_sign/summary) |
| 4 | [实时口罩检测模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo_facemask/summary) | 9 | Coming soon |
| 5 | [实时安全帽检测模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo_safety-helmet/summary) |



## 模型描述
本模型为实时烟火检测模型，基于检测框架[DAMOYOLO-S模型](https://modelscope.cn/models/damo/cv_tinynas_object-detection_damoyolo/summary)，DAMO-YOLO是一个面向工业落地的目标检测框架，兼顾模型速度与精度，其训练的模型效果超越了目前的一众YOLO系列方法，并且仍然保持极高的推理速度。DAMOYOLO与YOLO系列其它经典工作的性能对比如下图所示：

<div align="center"><img src="assets/DAMOYOLO_performance.jpg" width="500"></div>

DAMOYOLO整体网络结构如下，整体由backbone (MAE-NAS), neck (GFPN), head (ZeroHead)三部分组成，基于"large neck, small head"的设计思想，对低层空间信息和高层语义信息进行更加充分的融合，从而提升模型最终的检测效果。

<div align="center"><img src="assets/DAMOYOLO_architecture.jpg" width="2000"></div>


## 期望模型使用方式以及适用范围
该模型适用于烟火检测，输入任意的图像，输出图像中烟火的外接矩形框坐标信息（支持图片中有多个烟火），以及是否佩戴口罩。

| 类别ID | 类别名称 |
| ------------ | ------------ |
| 1 | smoke |
| 2 | fire |

### 如何使用
在ModelScope框架上，提供输入图片，即可以通过简单的Pipeline调用使用当前模型，得到图像中所有人脸的外接矩形框坐标信息，以及是否佩戴口罩。

#### 推理代码范例
基础示例代码。下面的示例代码展示的是如何通过一张图片作为输入，得到图片对应的人脸佩戴口罩检测结果。
```python
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

model_id = 'damo/smokefire'
input_location = 'https://modelscope.oss-cn-beijing.aliyuncs.com/test/images/image_detection.jpg'

smokefire_detection = pipeline(Tasks.domain_specific_object_detection, model=model_id)
result = smokefire_detection(input_location)
print("result is : ", result)
```



### 相关论文以及引用信息
本模型主要参考论文如下（论文链接：[link](https://arxiv.org/abs/2211.15444)）：

```BibTeX
 @article{damoyolo,
  title={DAMO-YOLO: A Report on Real-Time Object Detection Design},
  author={Xianzhe Xu, Yiqi Jiang, Weihua Chen, Yilun Huang, Yuan Zhang and Xiuyu Sun},
  journal={arXiv preprint arXiv:2211.15444v2},
  year={2022}
}
```

