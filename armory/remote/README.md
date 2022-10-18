# remote resources for armory

This is an exploration and prototype of providing mount-like remote resources for
armory. I am attempting to abstract the concept into a generic interface that can demand
load resources from a variety of sources.

  - large files (weights, datasets, models) on s3
  - code repositories (github, gitlab)
  - writable output sinks for results and logging

## existing data fetchers in armory

### armory.utils.config_loading

This defines a number of fetch functions.

  - `load_and_call` - imports and calls a python module.function(*args, **kwargs)
  - `load_fn` - imports and returns a python module.function
  - `load_dataset` - returns an ArmoryDatasetGenerator
  - `load_adversarial_dataset` - returns an ArmoryDatasetGenerator
  - `load_model` - loads and preprocesses model weights
  - `load_attack` - returns art.attacks.Attack
  - `load_defense_wrapper` - returns art.defences.trainer.Trainer
  - `load_label_targeter` - loads a defense_config and decorates a classifier

The `load` and `load_and_call` methods are data driven equivalents of

    from module import name
    return module.name

and the similar

    from module import name as func
    return func(*args, **kwargs)

respectively where `module` and `name`, `args` and `kwargs` are specified
in the input dict. The input dict is typically a block from an Experiment
such as

    ---
    attack:
    module: art.attacks.evasion
    name: ProjectedGradientDescent
    kwargs:
        batch_size: 1
        eps: 0.031

Note that `load_and_call` used to be called `load` but I renamed it for clarity.

### armory.datasets.ArmoryDataGenerator
### armory.
