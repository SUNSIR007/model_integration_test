def has_fire(classnames):
    return "Fire" in classnames


def has_smoke(classnames):
    return "smoking" in classnames


def has_mask(classnames):
    return "without_mask" in classnames or "mask_weared_incorrect" in classnames


def has_fall(classnames):
    return "Fall-Detected" in classnames


def has_safety_hat(classnames):
    return "without safety-helmet" in classnames


def has_vest(classnames):
    return "others" in classnames


def judge_by_classnames(name, classnames):
    if name == '火焰检测':
        return has_fire(classnames)
    elif name == '烟雾检测':
        return has_smoke(classnames)
    elif name == '佩戴口罩检测':
        return has_mask(classnames)
    elif name == '跌倒检测':
        return has_fall(classnames)
    elif name == '安全帽检测':
        return has_safety_hat(classnames)
    elif name == '反光衣检测':
        return has_vest(classnames)
    elif classnames is not None:
        return True
    else:
        return False
