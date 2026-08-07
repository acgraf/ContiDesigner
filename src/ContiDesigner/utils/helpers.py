def save_divide(num, denom, eps=1e-10):
    if abs(denom) < eps:
        return 0
    return num / denom
