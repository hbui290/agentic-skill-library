import re


TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(value: object) -> set[str]:
    return set(TOKEN.findall(str(value).lower()))


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0
