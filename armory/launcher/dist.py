"""
compute pairwise similarities of all experiments
"""

import difflib

from armory import SRC_ROOT


def compare(s1, s2) -> float:
    """return the edit distance between the contents of two list[str]"""
    matcher = difflib.SequenceMatcher(None, s1, s2)
    return matcher.ratio()


def pairwise():
    path = SRC_ROOT.parent / "experiments"
    files = list(path.glob("**/*.yaml"))
    print(f"found {len(files)} files")

    # ucf101_pretrained_frame_saliency_undefended.yaml vs ucf101_pretrained_frame_saliency_defended.yaml: 0.91

    ratios = {}
    while files:
        f1 = files.pop()
        s1 = f1.read_text().splitlines()
        matcher = difflib.SequenceMatcher(None, [], s1)
        for f2 in files:
            s2 = f2.read_text().splitlines()
            matcher.set_seq1(s2)
            ratio = matcher.ratio()
            ratios[f1, f2] = ratio

    return ratios


ratios = pairwise()

tops = {}
for (f1, f2) in ratios:
    ratio = ratios[f1, f2]
    if ratio > 0.85:
        tops[ratio] = (f1.name, f2.name)

print("top 10:", sorted(tops.items(), reverse=True)[:10])
print("| file1 | file2 | ratio |")
print("| --- | --- | ---: |")
for k in sorted(tops.keys(), reverse=True):
    print(f"| {tops[k][0]} | {tops[k][1]} | {k:.2f} |")
