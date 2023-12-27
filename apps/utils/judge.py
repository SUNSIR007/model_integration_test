def has_fire(classnames):
    return "fire" in classnames


def has_smoke(classnames):
    return "smoking" in classnames


def has_mask(classnames):
    return "without_mask" in classnames or "mask_weared_incorrect" in classnames


def has_fall(classnames):
    return "Fall-Detected" in classnames


def has_safety_hat(classnames):
    return "person" in classnames


def has_vest(classnames):
    return "others" in classnames
