import torch


def en_to_ch(chinese_names, weights):
    """将英文标签训练好的权重文件，转换为中文标签"""
    weights_dict = torch.load(weights)

    print(weights_dict["model"].names)

    # 将原来的英文标签，替换为中文标签
    weights_dict["model"].names = chinese_names

    # 最后保存到原文件中
    torch.save(weights_dict, weights)


en_to_ch({0: 'safety-helmet', 1: 'without safety-helmet'}, "weights/helmet.pt")
