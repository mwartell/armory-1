import difflib

from armory import SRC_ROOT


def compare(s1, s2) -> float:
    """return the edit distance between the contents of two list[str]"""
    matcher = difflib.SequenceMatcher(None, s1, s2)
    return matcher.ratio()


def pairwise():
    path = SRC_ROOT.parent / "experiments/eval1-4"
    for section in path.glob("*/"):
        files = list(section.glob("*.yaml"))
        if len(files) < 2:
            continue
        while files:
            f1 = files.pop()
            for f2 in files:
                s1 = f1.read_text().splitlines()
                s2 = f2.read_text().splitlines()
                ratio = compare(s1, s2)
                print(f"{f1.name} vs {f2.name}: {ratio:.2f}")
        return


pairwise()
