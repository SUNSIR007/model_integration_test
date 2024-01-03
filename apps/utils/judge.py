def has_fire(classnames):
    return "fire" in classnames


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


def judge_by_classnames(model_name, classnames):
    if model_name == 'fire.pt':
        has_fire(classnames)
    elif model_name == 'smoking.pt':
        has_smoke(classnames)
    elif model_name == 'mask.pt':
        has_mask(classnames)
    elif model_name == 'fall.pt':
        has_fall(classnames)
    elif model_name == 'helmet.pt':
        has_safety_hat(classnames)
    elif model_name == 'vest.pt':
        has_vest(classnames)
    elif classnames is not None:
        return True
