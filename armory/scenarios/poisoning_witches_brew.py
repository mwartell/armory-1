import os
import copy

import numpy as np

from armory.scenarios.poison import Poison
from armory.utils.poisoning import FairnessMetrics
from armory.logs import log
from armory.utils import config_loading, metrics
from armory import paths


class DatasetPoisonerWitchesBrew:
    def __init__(
        self,
        attack,
        x_test,
        y_test,
        source_class,
        target_class,
        trigger_index,
        data_filepath,
    ):
        """
        Individual source-class triggers are chosen from x_test.  At poison time, the
        train set is modified to induce misclassification of the triggers as target_class.

        """
        self.attack = attack
        self.x_test = x_test
        self.y_test = y_test
        self.source_class = source_class
        self.target_class = target_class
        self.trigger_index = trigger_index
        self.data_filepath = data_filepath

    def poison_dataset(self, x_train, y_train, return_index=True):
        """
        Return a poisoned version of dataset x, y
            if return_index, return x, y, index
        """
        if len(x_train) != len(y_train):
            raise ValueError("Sizes of x and y do not match")

        if (
            None in self.source_class
            and None in self.target_class
            and None in self.trigger_index
        ):
            # In this case we just want to use the saved dataset, use empty x_trigger and y_trigger to signal that
            x_trigger = []
            y_trigger = []

        else:
            x_trigger = self.x_test[self.trigger_index]
            if len(x_trigger.shape) == 3:
                x_trigger = np.expand_dims(x_trigger, axis=0)

            y_trigger = self.target_class

        (
            poison_x,
            poison_y,
            poison_index,
            new_trigger_index,
            new_source_class,
            new_target_class,
        ) = self.attack.poison(
            self.data_filepath,
            x_trigger,
            y_trigger,
            x_train,
            y_train,
            self.trigger_index,
        )

        # attack.poison() may have modified trigger, source, and target,
        # if they were None in the config, and loaded from a pre-saved file.
        self.trigger_index = new_trigger_index
        self.source_class = new_source_class
        self.target_class = new_target_class

        if return_index:
            return (
                poison_x,
                poison_y,
                self.trigger_index,
                self.source_class,
                self.target_class,
                poison_index,
            )
        return (
            poison_x,
            poison_y,
            self.trigger_index,
            self.source_class,
            self.target_class,
        )


class WitchesBrewScenario(Poison):
    def _validate_attack_args(self, adhoc_config, y_test):
        """ Ensures that the attack parameters from the config are valid and
            sufficient to create a poisoned dataset.

            Returns a standardized version of trigger_index, source_class, and
            target_class from the config, as well as a bool indicating whether
            the triggers were selected randomly.
        """

        ###
        # A word of explanation.
        #
        # We have three lists: target_class, trigger_index, source_class.
        # If source (or target) contains only 1 value, but either of the other lists contains more,
        # that source (or target) value is repeated to the length of the longer list.
        #
        # Source or trigger may be None.
        # If trigger_index is None, choose randomly from source class.
        # If source_class is None, infer from trigger_index.
        #
        # Target_class may only be None if the other two are also both None.
        # In this case, the scenario expects to load a presaved dataset specified elsewhere in the config.
        # It would be possible to choose target_class randomly as well,
        # but that was not something the poison group asked for and it significantly complicates things.
        ###

        trigger_index = adhoc_config["trigger_index"]
        if not isinstance(trigger_index, list):
            trigger_index = [trigger_index]

        target_class = adhoc_config["target_class"]
        if not isinstance(target_class, list):
            target_class = [target_class]

        source_class = adhoc_config["source_class"]
        if not isinstance(source_class, list):
            source_class = [source_class]

        if None in target_class and None in source_class and None in trigger_index:
            # If all three are None, we'll just use the saved dataset
            return [], [], [], False

        if None in target_class:
            raise ValueError("Please specify target_class in the config.")

        if None in source_class and None in trigger_index:
            raise ValueError(
                "Either source_class or trigger_index may be None but not both; please specify one."
            )

        # Now, target is not None, and only one of source or trigger is None.

        lengths = [len(trigger_index), len(target_class), len(source_class)]
        names = ["trigger_index", "target_class", "source_class"]
        max_name = names[np.argmax(lengths)]
        N = max(lengths)

        # Can't accept single int trigger_index if N > 1
        if N > 1 and len(trigger_index) == 1 and trigger_index[0] is not None:
            raise ValueError(
                f"trigger_index must have {N} unique elements to match {max_name}"
            )
        # now, trigger is one None, many Nones, or many ints.  Or one int if N is 1.
        if len(trigger_index) == 1:
            trigger_index = trigger_index * N
        # now, trigger is N Nones or N ints, or a wrong number
        if len(trigger_index) != N:
            if None in trigger_index:
                raise ValueError(
                    f"trigger_index should be 'null' or a list of {N} 'null's to match {max_name}"
                )
            else:
                raise
        # now, trigger is N Nones or N ints.
        if None not in trigger_index:
            if len(np.unique(trigger_index)) != len(trigger_index):
                raise ValueError("All elements of trigger_index must be unique")
        # now, trigger is N Nones or N unique ints.  As we need it.

        if len(target_class) == 1:
            target_class = target_class * N
        elif len(target_class) != N:
            raise ValueError(
                f"target_class must have one element or as many as {max_name}"
            )

        if len(source_class) == 1:
            source_class = source_class * N
        elif len(source_class) != N:
            raise ValueError(
                f"source_class must have one element or as many as {max_name}"
            )

        # Now, source, target, and trigger have length N.  Either source or trigger may be lists of None, but not both.
        # If source or trigger contain None, select randomly, but set a flag for reference in attack.

        triggers_chosen_randomly = False

        if None in trigger_index:
            log.info("Selecting random trigger images according to source_class")
            triggers_chosen_randomly = True
            used = []  # want to avoid using any trigger twice
            for i, class_i in enumerate(source_class):
                if class_i not in y_test:
                    raise ValueError(
                        f"Test set contains no examples of class {class_i}"
                    )
                options = [
                    index
                    for index in np.where(y_test == class_i)[0]
                    if index not in used
                ]
                trig_ind = np.random.choice(options)
                used.append(trig_ind)
                trigger_index[i] = trig_ind

            if len(np.unique(trigger_index)) != len(trigger_index):
                raise ValueError(
                    "Selected same trigger image multiple times.  If this happens, there is a bug in the 'for' block preceding this line of code"
                )

        if None in source_class:
            log.info(
                "Inferring source_class from the classes of the chosen trigger images"
            )
            for i, trig_ind in enumerate(trigger_index):
                source_class[i] = y_test[trig_ind]

        for i, trigger_ind in enumerate(trigger_index):
            if y_test[trigger_ind] != source_class[i]:
                raise ValueError(
                    f"Trigger image {i} does not belong to source class (class {y_test[trigger_ind]} != class {source_class[i]})"
                )

        if sum([t == s for t, s in zip(target_class, source_class)]) > 0:
            raise ValueError(
                f" No target class may equal source class; got target = {target_class} and source = {source_class}"
            )

        return trigger_index, target_class, source_class, triggers_chosen_randomly

    def load_poisoner(self):
        adhoc_config = self.config.get("adhoc") or {}
        attack_config = copy.deepcopy(self.config["attack"])
        if attack_config.get("type") == "preloaded":
            raise ValueError("preloaded attacks not currently supported for poisoning")

        self.use_poison = bool(adhoc_config["poison_dataset"])

        dataset_config = self.config["dataset"]
        test_dataset = config_loading.load_dataset(
            dataset_config, split="test", num_batches=None, **self.dataset_kwargs
        )
        x_test, y_test = (np.concatenate(z, axis=0) for z in zip(*list(test_dataset)))

        (
            self.trigger_index,
            self.target_class,
            self.source_class,
            triggers_chosen_randomly,
        ) = self._validate_attack_args(adhoc_config, y_test)

        if self.use_poison:

            attack_config["kwargs"]["percent_poison"] = adhoc_config[
                "fraction_poisoned"
            ]
            attack_config["kwargs"]["source_class"] = self.source_class
            attack_config["kwargs"]["target_class"] = self.target_class
            attack_config["kwargs"][
                "triggers_chosen_randomly"
            ] = triggers_chosen_randomly

            data_filepath = (
                attack_config["kwargs"].pop("data_filepath")
                if "data_filepath" in attack_config["kwargs"].keys()
                else None
            )

            attack_dir = os.path.join(paths.runtime_paths().saved_model_dir, "attacks")
            os.makedirs(attack_dir, exist_ok=True)

            attack = config_loading.load_attack(attack_config, self.model)

            if data_filepath is not None:
                data_filepath = os.path.join(attack_dir, data_filepath)

            self.poisoner = DatasetPoisonerWitchesBrew(
                attack,
                x_test,
                y_test,
                self.source_class,
                self.target_class,
                self.trigger_index,
                data_filepath,
            )
            self.test_poisoner = self.poisoner

    def poison_dataset(self):
        # Over-ridden because poisoner returns possibly-modified trigger_index, target_class, source_class

        if self.use_poison:
            (
                self.x_poison,
                self.y_poison,
                self.trigger_index,
                self.source_class,
                self.target_class,
                self.poison_index,
            ) = self.poisoner.poison_dataset(
                self.x_clean, self.y_clean, return_index=True
            )
        else:
            self.x_poison, self.y_poison, self.poison_index = (
                self.x_clean,
                self.y_clean,
                np.array([]),
            )

        # make sure config has updated and serializable versions of source, target, and trigger
        self.config["adhoc"]["trigger_index"] = [int(t) for t in self.trigger_index]
        self.config["adhoc"]["source_class"] = [int(c) for c in self.source_class]
        self.config["adhoc"]["target_class"] = [int(c) for c in self.target_class]

    def load_dataset(self, eval_split_default="test"):
        # Over-ridden because we need batch_size = 1 for the test set for this attack.

        dataset_config = self.config["dataset"]
        dataset_config = copy.deepcopy(dataset_config)
        dataset_config["batch_size"] = 1
        eval_split = dataset_config.get("eval_split", eval_split_default)
        log.info(f"Loading test dataset {dataset_config['name']}...")
        self.test_dataset = config_loading.load_dataset(
            dataset_config,
            split=eval_split,
            num_batches=self.num_eval_batches,
            **self.dataset_kwargs,
        )
        self.i = -1

    def load_metrics(self):
        self.non_trigger_accuracy_metric = metrics.MetricList("categorical_accuracy")
        self.trigger_accuracy_metric = metrics.MetricList("categorical_accuracy")

        self.benign_test_accuracy_per_class = (
            {}
        )  # store accuracy results for each class
        if self.config["adhoc"].get("compute_fairness_metrics", False):
            self.fairness_metrics = FairnessMetrics(
                self.config["adhoc"], self.use_filtering_defense, self
            )
        else:
            log.warning(
                "Not computing fairness metrics.  If these are desired, set 'compute_fairness_metrics':true under the 'adhoc' section of the config"
            )

    def run_benign(self):
        # Called for all non-triggers

        x, y = self.x, self.y

        x.flags.writeable = False
        y_pred = self.model.predict(x, **self.predict_kwargs)

        self.non_trigger_accuracy_metric.add_results(y, y_pred)

        for y_, y_pred_ in zip(y, y_pred):
            if y_ not in self.benign_test_accuracy_per_class.keys():
                self.benign_test_accuracy_per_class[y_] = []

            self.benign_test_accuracy_per_class[y_].append(
                y_ == np.argmax(y_pred_, axis=-1)
            )

        self.y_pred = y_pred  # for exporting when function returns

    def run_attack(self):
        # Only called for the trigger images

        x, y = self.x, self.y

        x.flags.writeable = False
        y_pred_adv = self.model.predict(x, **self.predict_kwargs)

        self.trigger_accuracy_metric.add_results(y, y_pred_adv)

        self.y_pred_adv = y_pred_adv  # for exporting when function returns

    def evaluate_current(self):

        if self.i in self.trigger_index:
            self.run_attack()
        else:
            self.run_benign()

        # This just exports clean test samples up to num_eval_batches, and all the triggers.
        if self.config["scenario"].get("export_batches"):
            if (
                self.num_export_batches > self.sample_exporter.saved_batches
            ) or self.i in self.trigger_index:
                if self.sample_exporter.saved_samples == 0:
                    self.sample_exporter._make_output_dir()
                name = "trigger" if self.i in self.trigger_index else "non-trigger"
                self.sample_exporter._export_image(self.x[0], name=name)
                self.sample_exporter.saved_samples += 1
                self.sample_exporter.saved_batches = (
                    self.sample_exporter.saved_samples
                    // self.config["dataset"]["batch_size"]
                )

    def _add_accuracy_metrics_results(self):
        """ Adds accuracy results for trigger and non-trigger images
        """
        self.results[
            "accuracy_non_trigger_images"
        ] = self.non_trigger_accuracy_metric.mean()
        log.info(
            f"Accuracy on non-trigger images: {self.non_trigger_accuracy_metric.mean():.2%}"
        )

        self.results["accuracy_trigger_images"] = self.trigger_accuracy_metric.mean()
        log.info(
            f"Accuracy on trigger images: {self.trigger_accuracy_metric.mean():.2%}"
        )