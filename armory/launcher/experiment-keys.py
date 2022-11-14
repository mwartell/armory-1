"""
finds all keys from all predefined experiments and shows them with their
collected types.
"""


import yaml
from collections import defaultdict
from pprint import pformat

from armory import SRC_ROOT

experiment_dir = SRC_ROOT.parent / "experiments"
experiments = list(experiment_dir.glob("**/*.yaml"))

print(f"{len(experiments)=}")

keys: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

for experiment in experiments:
    exp = yaml.safe_load(experiment.read_text())
    for top in exp:
        group = keys[top]
        if isinstance(exp[top], dict):
            for key in exp[top]:
                group[key].add(type(exp[top][key]).__name__)
        else:
            group[top].add(type(exp[top]).__name__)

for key in keys:
    print(f"{key}:")
    if isinstance(keys[key], dict):
        for k in sorted(keys[key]):
            types = [x for x in keys[key][k]]
            print(f"    {k}: {' | '.join(types)}")
