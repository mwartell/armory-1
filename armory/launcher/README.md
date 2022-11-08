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

With the advent of hydra-zen, experiments are now yaml files and live in
`armory/experiments/`; the structure of that mirrors `scenario_configs`. The hydra-zen
package is strongly committed to the `.yaml` extension (rather than `.yml`) so we'll
follow that.

An experiment looks like this (truncated for brevity):

```yaml
_description: truncated cifar10 image classification
# stripped down, incomplete experiment for learning hydra
attack:
  knowledge: white
  kwargs:
    batch_size: 1
    eps: 0.031
  module: art.attacks.evasion
  name: ProjectedGradientDescent
  use_label: true
dataset:
  batch_size: 64
  framework: numpy
  module: armory.data.datasets
  name: cifar10
scenario:
  kwargs: {}
  module: armory.scenarios.image_classification
  name: ImageClassificationTask
```

There is a `tools/scenario-json-to-yaml.py` script that was used to convert the
scenario_configs. The yaml experiments are handled just like the json configs
previously:

    armory run experiments/cifar10_baseline.yaml

The hydra-zen argument parser handles the command line overrides which begin with
a `+`. For example, to override the `batch_size` parameter of the experiment, you would
specify:

    armory run experiments/cifar10_baseline.yaml +dataset.batch_size=128

And multiple `+` arguments can be specified:

    armory run experiments/cifar10_baseline.yaml +dataset.batch_size=128 +attack.kwargs.eps=0.1

By using the [OmegaConf structured configs][struct], key validity and value type checking is
performed automatically. For example, if you try to override a parameter that doesn't
exist, you'll get an error:

    armory run experiments/cifar10_baseline.yaml +attack.foo=bar

Unfortunately, the `args` and `kwargs` parameters present in most of the experiment
blocks cannot be checked for validity because they are of type `list[Any]` and
`dict[Any, Any]` per their definition. TODO: Can we nail down the types? I think not
because the consumers of the args/kwargs are varadic.

[struct]: https://omegaconf.readthedocs.io/en/2.2_branch/structured_config.html

## variant experiements and overrides

While the hydra-zen command line overrides are a nice feature, they are mostly useful
for altering a parameter or two. For more complex modifications, it is easier to
provide an override file. The override file is a yaml file that contains the
alterations and additions to an experiment. For example

```yaml
  # override experiment parameters for a targeted snr_pgd attack
  attack:
    kwargs:
      targeted: true
  module: armory.art_experimental.attacks.snr_pgd
  name: SNR_PGD_Numpy
  targeted: true
  targeted_labels:
    module: armory.utils.labels
    name: ManualTargeter
```

You can apply the overrides on the armory command line:

    armory run experiments/asr_librespeech.yaml --overrides=overrides/snr_pgd_targeted.yaml

This starts with the `asr_librespeech.yaml` experiment and applies the overrides
in the `snr_pgd_targeted.yaml` file. It might be useful to pre-merge experiements and
overrides into a single file for easier sharing. This can be done with the

    armory experiment merge base.yaml overrides.yaml more_overrides.yaml

command with the merged output on stdout.
