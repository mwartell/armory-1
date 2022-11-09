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

## variant experiments and overrides

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

command with the merged output on stdout. As with `armory run` the `merge` command
accepts `+key=value` overrides which are applied after the merge.

## overrides using interpolation syntax

OmegaConf supports [interpolation syntax][interp] which allows you to reference
one parameter from another. For example, you could have an experiment like:

```yaml
  # obviously degenerate experiment for illustration
  attack:
    kwargs:
        targeted: ${targeted}
    targeted: ${targeted}
  dataset:
    targeted: ${targeted}
```
which would allow you to specify the `targeted` parameter on the command line:

    armory run experiments/asr_librespeech.yaml +targeted=true

Because the interpolation has to reference an existing parameter, the `+targeted=true`
becomes a datum `targeted: true` peer to attack, dataset, etc. I don't see an easy way
to avoid creating spurious parameters. We could create a `options` block or similar
which could contain those values but then we are looking at interpolations of
`${options.targeted}`. The behavior of a parameterized experiment is a syntax error if
you don't specify `+targeted=<bool>`, and there is little about the structure of the
experiment that suggests you need to define something. Comments will certainly help.

Furthermore, the interpolation mechanism assumes that we'll want to parameterize two or
more variables that all receive the same value. If a modification requires different
values than the [variant override][def] quickly looks superior.

[interp]: https://omegaconf.readthedocs.io/en/2.2_branch/usage.html#variable-interpolation
[def]: #variant-experiments-and-overrides

## reducing the experiment bestiary with composition

A second benefit of using the composition by merging approach is that it may allow
clearer relations between experiments. For example, the experiment
`ucf101_pretrained_masked_pgd_defended.yaml` differs from `ucf101_pretrained_masked_pgd.yaml`
only with the addition of the `defense:` block. Is it better to have the two to be
run like:

    armory run experiments/ucf101_pretrained_masked_pgd.yaml
    armory run experiments/ucf101_pretrained_masked_pgd.yaml --merge ucf101_defense.yaml

which illuminates the commonality between the two experiments, or to have them as
separate experiments:

    armory run experiments/ucf101_pretrained_masked_pgd_undefended.yaml
    armory run experiments/ucf101_pretrained_masked_pgd_defended.yaml

It is not obvious that the former is preferable, but I'd like to have folks think
about compositional approaches to the experiments.

I've written a short script to look for more commonalities in the experiments.
These are the matched configurations with a similarity measure of 0.85 or greater.

| file1 | file2 | similarity |
| --- | --- | ---: |
| cifar10_sleeper_agent_p30_undefended.yaml | cifar10_sleeper_agent_p20_undefended.yaml | 0.99 |
| cifar10_dlbd_watermark_activation_defense.yaml | cifar10_poison_dlbd.yaml | 0.99 |
| cifar10_witches_brew_activation_defense.yaml | cifar10_witches_brew.yaml | 0.99 |
| so2sat_sar_masked_pgd_defended.yaml | so2sat_eo_masked_pgd_defended.yaml | 0.98 |
| gtsrb_dlbd_baseline_keras.yaml | gtsrb_dlbd_baseline_pytorch.yaml | 0.98 |
| audio_p05_undefended.yaml | audio_p01_undefended.yaml | 0.98 |
| gtsrb_witches_brew_activation_defense.yaml | gtsrb_witches_brew.yaml | 0.98 |
| cifar10_sleeper_agent_p00_undefended.yaml | cifar10_sleeper_agent_p30_undefended.yaml | 0.98 |
| so2sat_sar_masked_pgd_undefended.yaml | so2sat_eo_masked_pgd.yaml | 0.98 |
| cifar10_dlbd_copyright_activation_defense.yaml | cifar10_dlbd_watermark_activation_defense.yaml | 0.97 |
| cifar10_dlbd_copyright_random_filter.yaml | cifar10_dlbd_watermark_random_filter.yaml | 0.97 |
| cifar10_dlbd_copyright_perfect_filter.yaml | cifar10_dlbd_watermark_perfect_filter.yaml | 0.97 |
| cifar10_sleeper_agent_p10_random_filter.yaml | cifar10_sleeper_agent_p10_spectral_signatures_defense.yaml | 0.97 |
| gtsrb_clbd_peace_sign_activation_defense.yaml | gtsrb_clbd_bullet_holes_activation_defense.yaml | 0.97 |
| cifar10_dlbd_copyright_undefended.yaml | cifar10_dlbd_watermark_undefended.yaml | 0.97 |
| gtsrb_clbd_peace_sign_random_filter.yaml | gtsrb_clbd_bullet_holes_random_filter.yaml | 0.97 |
| gtsrb_clbd_peace_sign_perfect_filter.yaml | gtsrb_clbd_bullet_holes_perfect_filter.yaml | 0.97 |
| targeted_snr_pgd.yaml | librispeech_asr_snr_targeted.yaml | 0.97 |
| gtsrb_clbd_peace_sign_undefended.yaml | gtsrb_clbd_bullet_holes_undefended.yaml | 0.97 |
| librispeech_asr_pgd_undefended.yaml | librispeech_asr_pgd_multipath_channel_undefended.yaml | 0.97 |
| cifar10_sleeper_agent_p10_spectral_signatures_defense.yaml | cifar10_sleeper_agent_p10_perfect_filter.yaml | 0.97 |
| gtsrb_dlbd_peace_sign_random_filter.yaml | gtsrb_dlbd_bullet_holes_random_filter.yaml | 0.97 |
| gtsrb_dlbd_peace_sign_perfect_filter.yaml | gtsrb_dlbd_bullet_holes_perfect_filter.yaml | 0.97 |
| gtsrb_clbd_peace_sign_spectral_signature_defense.yaml | gtsrb_clbd_bullet_holes_spectral_signature_defense.yaml | 0.96 |
| cifar10_dlbd_copyright_activation_defense.yaml | cifar10_poison_dlbd.yaml | 0.96 |
| gtsrb_dlbd_peace_sign_undefended.yaml | gtsrb_dlbd_bullet_holes_undefended.yaml | 0.96 |
| cifar10_witches_brew_spectral_signature_defense.yaml | cifar10_witches_brew_random_filter.yaml | 0.96 |
| cifar10_sleeper_agent_p10_random_filter.yaml | cifar10_sleeper_agent_p10_perfect_filter.yaml | 0.96 |
| audio_p00_undefended.yaml | audio_p05_undefended.yaml | 0.96 |
| librispeech_asr_snr_targeted.yaml | librispeech_asr_snr_undefended.yaml | 0.96 |
| gtsrb_dlbd_peace_sign_spectral_signature_defense.yaml | gtsrb_dlbd_bullet_holes_spectral_signature_defense.yaml | 0.96 |
| cifar10_witches_brew_random_filter.yaml | cifar10_witches_brew_perfect_filter.yaml | 0.96 |
| [… _100 more comparisons with similarity > 0.85 removed_ …] |
| carla_obj_det_multimodal_adversarialpatch_undefended.yaml | carla_obj_det_multimodal_dpatch_undefended.yaml | 0.87 |
| librispeech_asr_pgd_undefended.yaml | asr_librispeech_targeted.yaml | 0.86 |
| librispeech_asr_snr_targeted.yaml | asr_librispeech_entailment.yaml | 0.86 |
| carla_obj_det_adversarialpatch_undefended.yaml | carla_obj_det_dpatch_undefended.yaml | 0.86 |
| gtsrb_clbd_bullet_holes_undefended.yaml | gtsrb_scenario_clbd_bullethole.yaml | 0.86 |
| defended_entailment.yaml | defended_untargeted_snr_pgd.yaml | 0.86 |
| carla_obj_det_multimodal_adversarialpatch_undefended.yaml | carla_obj_det_adversarialpatch_undefended.yaml | 0.86 |
| librispeech_asr_snr_undefended.yaml | asr_librispeech_entailment.yaml | 0.85 |
| resisc45_baseline_densenet121_finetune.yaml | resisc45_baseline_densenet121_targeted.yaml | 0.85 |
| defended_targeted_snr_pgd.yaml | librispeech_asr_snr_undefended.yaml | 0.85 |
| gtsrb_dlbd_peace_sign_activation_defense.yaml | gtsrb_dlbd_bullet_holes_undefended.yaml | 0.85 |
| carla_obj_det_dpatch_undefended.yaml | carla_obj_det_multimodal_dpatch_undefended.yaml | 0.85 |

Looking at the differences in an arbitrary 0.96 similarity pair shows
```diff
--- cifar10_witches_brew_random_filter.yaml     2022-11-08 17:03:57.674036989 -0500
+++ cifar10_witches_brew_perfect_filter.yaml    2022-11-08 17:03:57.674036989 -0500
@@ -1,9 +1,8 @@
-_description: CIFAR10 poison image classification, witches' brew attack, random filter
+_description: CIFAR10 poison image classification, witches' brew attack, perfect filter
 adhoc:
   compute_fairness_metrics: true
   experiment_id: 0
   explanatory_model: cifar10_silhouette_model
-  fit_defense_classifier_outside_defense: false
   fraction_poisoned: 0.1
   poison_dataset: true
   source_class:
@@ -61,9 +60,9 @@
   name: cifar10
 defense:
   kwargs:
-    expected_pp_poison: 0.3
-  module: armory.art_experimental.poison_detection.random_filter
-  name: RandomFilterBaselineDefense
+    perfect_filter: true
+  module: 'null'
+  name: 'null'
   type: PoisonFilteringDefence
 metric: null
 model:
 ```

Does this look like a base and variant?  Looking at at an example of a 0.85 similarity
score, we can see that the differences are slight but significant. Is it worth
refactoring those to base and variant?

```diff
--- carla_obj_det_adversarialpatch_undefended.yaml      2022-11-08 17:03:57.674036989 -0500
+++ carla_obj_det_multimodal_adversarialpatch_undefended.yaml   2022-11-08 17:03:57.674036989 -0500
@@ -1,10 +1,12 @@
-_description: CARLA single modality object detection, contributed by MITRE Corporation
+_description: CARLA multimodality object detection, contributed by MITRE Corporation
 adhoc: null
 attack:
   knowledge: white
   kwargs:
     batch_size: 1
+    depth_delta_meters: 3
     learning_rate: 0.003
+    learning_rate_depth: 0.0001
     max_iter: 1000
     optimizer: pgd
     targeted: false
@@ -16,7 +18,7 @@
   batch_size: 1
   eval_split: dev
   framework: numpy
-  modality: rgb
+  modality: both
   module: armory.data.adversarial_datasets
   name: carla_obj_det_dev
 defense: null
@@ -33,11 +35,10 @@
 model:
   fit: false
   fit_kwargs: {}
-  model_kwargs:
-    num_classes: 4
-  module: armory.baseline_models.pytorch.carla_single_modality_object_detection_frcnn
-  name: get_art_model
-  weights_file: carla_rgb_weights_eval5.pt
+  model_kwargs: {}
+  module: armory.baseline_models.pytorch.carla_multimodality_object_detection_frcnn
+  name: get_art_model_mm
+  weights_file: carla_multimodal_naive_weights_eval5.pt
   wrapper_kwargs: {}
 scenario:
   kwargs: {}
msw@omen 艹armory ~/t/a/e/e/carla_object_detection (mwartell/issue1618 *) [1]> diff -u carla_obj_det_multimodal_adversarialpatch_undefended.yaml carla_obj_det_adversarialpatch_undefended.yaml
--- carla_obj_det_multimodal_adversarialpatch_undefended.yaml   2022-11-08 17:03:57.674036989 -0500
+++ carla_obj_det_adversarialpatch_undefended.yaml      2022-11-08 17:03:57.674036989 -0500
@@ -1,12 +1,10 @@
-_description: CARLA multimodality object detection, contributed by MITRE Corporation
+_description: CARLA single modality object detection, contributed by MITRE Corporation
 adhoc: null
 attack:
   knowledge: white
   kwargs:
     batch_size: 1
-    depth_delta_meters: 3
     learning_rate: 0.003
-    learning_rate_depth: 0.0001
     max_iter: 1000
     optimizer: pgd
     targeted: false
@@ -18,7 +16,7 @@
   batch_size: 1
   eval_split: dev
   framework: numpy
-  modality: both
+  modality: rgb
   module: armory.data.adversarial_datasets
   name: carla_obj_det_dev
 defense: null
@@ -35,10 +33,11 @@
 model:
   fit: false
   fit_kwargs: {}
-  model_kwargs: {}
-  module: armory.baseline_models.pytorch.carla_multimodality_object_detection_frcnn
-  name: get_art_model_mm
-  weights_file: carla_multimodal_naive_weights_eval5.pt
+  model_kwargs:
+    num_classes: 4
+  module: armory.baseline_models.pytorch.carla_single_modality_object_detection_frcnn
+  name: get_art_model
+  weights_file: carla_rgb_weights_eval5.pt
   wrapper_kwargs: {}
 scenario:
   kwargs: {}
```
