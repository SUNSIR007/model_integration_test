#!/usr/bin/env python3
#-*- coding:utf-8 -*-
# Copyright (C) Alibaba Group Holding Limited. All rights reserved.

TinyNAS = {
    "name": "TinyNAS_res",
    "structure_file": "tinynas_L25_k1kx.txt",
    "out_indices": (2, 4, 5),
    "with_spp": True,
    "use_focus": True,
    "act": "relu",
    "reparam": True
}

GiraffeNeckV2 = {
    "name": "GiraffeNeckV2",
    "depth": 1.0,
    "hidden_ratio": 0.75,
    "in_channels": [128, 256, 512],
    "out_channels": [128, 256, 512],
    "act": "relu",
    "spp": False,
    "block_name": 'BasicBlock_3x3_Reverse',
}

ZeroHead = {
    "name": "ZeroHead",
    "num_classes": 2,
    "in_channels": [128, 256, 512],
    "stacked_convs": 0,
    "feat_channels": [128, 256, 512],
    "reg_max": 16,
    "act": "silu",
    "nms_conf_thre": 0.6,
    "nms_iou_thre": 0.7,
}

model = {
    "backbone": TinyNAS,
    "neck": GiraffeNeckV2,
    "head": ZeroHead,
    "name": "damoyolo_tinynasL25_S_safetyhelmet.pt",
    "class_map": "label_map.pkl",
}

dataset = {
    "size_divisibility": 32,
    "input_pixel_mean": [0.0, 0.0, 0.0],
    "input_pixel_std": [1.0, 1.0, 1.0],
    "input_to_bgr255": False,
}
