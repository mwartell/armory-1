# armory launcher prototype

Rather than twist `armory.__main__.py` to accommodate the new hydra-zen tooling, I've
created this directory to house a prototype launcher script. It is probably not the
final location for this code.

I am using a degenerate experiment to fiddle around with the design. Now that
experiments are in yaml, I can call that out in a comment.

# prospective command line interface

The first thing that hydra-zen brings to Armory is the unification of experiments
and command line overrides. A second function of hydra-zen is to provide execution
tracking which I don't cover yet.

## basic usage

The temporary name of the new launcher is `fire`. The syntax is:

    fire <experiment> <overrides>

where `<experiment>` is the path to an experiment yaml file and `<overrides>` is a
list of hydra overrides. The overrides are applied to the experiment config.
