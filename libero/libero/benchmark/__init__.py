import abc
import os
import glob
import random
import torch

from typing import List, NamedTuple, Type
from libero import get_libero_path
from libero.benchmark.libero_suite_task_map import libero_task_map


BENCHMARK_MAPPING = {}


def register_benchmark(target_class):
    """We design the mapping to be case-INsensitive."""
    BENCHMARK_MAPPING[target_class.__name__.lower()] = target_class


def get_benchmark_dict(help=False):
    if help:
        print("Available benchmarks:")
        for benchmark_name in BENCHMARK_MAPPING.keys():
            print(f"\t{benchmark_name}")
    return BENCHMARK_MAPPING


def get_benchmark(benchmark_name):
    return BENCHMARK_MAPPING[benchmark_name.lower()]


def print_benchmark():
    print(BENCHMARK_MAPPING)


class Task(NamedTuple):
    name: str
    language: str
    problem: str
    problem_folder: str
    bddl_file: str
    init_states_file: str


def grab_language_from_filename(x):
    if x[0].isupper():  # LIBERO-100
        if "SCENE10" in x:
            language = " ".join(x[x.find("SCENE") + 8 :].split("_"))
        else:
            language = " ".join(x[x.find("SCENE") + 7 :].split("_"))
    else:
        language = " ".join(x.split("_"))
    en = language.find(".bddl")
    return language[:en]


libero_suites = [
    "libero_object_all_variance",
    "libero_object_target_basket_swap_variance",
    "libero_object_target_permutation_variance",
    "libero_object_target_pos_var20x20",
    "libero_popcorn_production",
    "libero_crate_washing",
]
task_maps = {}
max_len = 0
for libero_suite in libero_suites:
    task_maps[libero_suite] = {}
    for task in libero_task_map[libero_suite]:
        language = grab_language_from_filename(task + ".bddl")
        task_maps[libero_suite][task] = Task(
            name=task,
            language=language,
            problem="Libero",
            problem_folder=libero_suite,
            bddl_file=f"{task}.bddl",
            init_states_file=f"{task}.pruned_init",
        )


task_orders = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [4, 6, 8, 7, 3, 1, 2, 0, 9, 5],
    [6, 3, 5, 0, 4, 2, 9, 1, 8, 7],
    [7, 4, 3, 0, 8, 1, 2, 5, 9, 6],
    [4, 5, 6, 3, 8, 0, 2, 7, 1, 9],
    [1, 2, 3, 0, 6, 9, 5, 7, 4, 8],
    [3, 7, 8, 1, 6, 2, 9, 4, 0, 5],
    [4, 2, 9, 7, 6, 8, 5, 1, 3, 0],
    [1, 8, 5, 4, 0, 9, 6, 7, 2, 3],
    [8, 3, 6, 4, 9, 5, 1, 2, 0, 7],
    [6, 9, 0, 5, 7, 1, 2, 8, 3, 4],
    [6, 8, 3, 1, 0, 2, 5, 9, 7, 4],
    [8, 0, 6, 9, 4, 1, 7, 3, 2, 5],
    [3, 8, 6, 4, 2, 5, 0, 7, 1, 9],
    [7, 1, 5, 6, 3, 2, 8, 9, 4, 0],
    [2, 0, 9, 5, 3, 6, 8, 7, 1, 4],
    [3, 5, 9, 6, 2, 4, 8, 7, 1, 0],
    [7, 6, 5, 9, 0, 3, 4, 2, 8, 1],
    [2, 5, 0, 9, 3, 1, 6, 4, 8, 7],
    [3, 5, 1, 2, 7, 8, 6, 0, 4, 9],
    [3, 4, 1, 9, 7, 6, 8, 2, 0, 5],
]


class Benchmark(abc.ABC):
    """A Benchmark."""

    def __init__(self, task_order_index=0):
        self.task_embs = None
        self.task_order_index = task_order_index

    def _make_benchmark(self):
        """Creates the list of tasks for the benchmark, potentially applying a specific order."""
        tasks = list(task_maps.get(self.name, {}).values())

        if not tasks:
            print(f"[warning] No tasks found for benchmark: {self.name}")
            self.tasks = []
            self.n_tasks = 0
            return

        n_tasks_actual = len(tasks)
        standard_10_task_suites = ["libero_spatial", "libero_object", "libero_goal", "libero_10"]

        if self.name in standard_10_task_suites and n_tasks_actual == 10:
            if 0 <= self.task_order_index < len(task_orders):
                order = task_orders[self.task_order_index]
                print(f"[info] Applying task order index {self.task_order_index} (permutation: {order}) for benchmark '{self.name}' ({n_tasks_actual} tasks).")
                try:
                    self.tasks = [tasks[i] for i in order]
                except IndexError:
                    print(f"[error] Task order permutation {order} is invalid for the {n_tasks_actual} tasks found in benchmark '{self.name}'. Using default order.")
                    self.tasks = tasks
            else:
                print(f"[warning] task_order_index {self.task_order_index} is out of range for available orders [0, {len(task_orders)-1}]. Using default task order for benchmark '{self.name}'.")
                self.tasks = tasks
        else:
            print(f"[info] Using default task order for benchmark '{self.name}' ({n_tasks_actual} tasks).")
            self.tasks = tasks

        self.n_tasks = len(self.tasks)

    def get_num_tasks(self):
        return self.n_tasks

    def get_task_names(self):
        return [task.name for task in self.tasks]

    def get_task_problems(self):
        return [task.problem for task in self.tasks]

    def get_task_bddl_files(self):
        return [task.bddl_file for task in self.tasks]

    def get_task_bddl_file_path(self, i):
        bddl_file_path = os.path.join(
            get_libero_path("bddl_files"),
            self.tasks[i].problem_folder,
            self.tasks[i].bddl_file,
        )
        return bddl_file_path

    def get_task_demonstration(self, i):
        assert (
            0 <= i and i < self.n_tasks
        ), f"[error] task number {i} is outer of range {self.n_tasks}"
        demo_path = f"{self.tasks[i].problem_folder}/{self.tasks[i].name}_demo.hdf5"
        return demo_path

    def get_task(self, i):
        return self.tasks[i]

    def get_task_emb(self, i):
        return self.task_embs[i]

    def get_task_init_states(self, i):
        init_states_path = os.path.join(
            get_libero_path("init_states"),
            self.tasks[i].problem_folder,
            self.tasks[i].init_states_file,
        )
        init_states = torch.load(init_states_path)
        return init_states

    def set_task_embs(self, task_embs):
        self.task_embs = task_embs


@register_benchmark
class LIBERO_OBJECT_TARGET_PERMUTATION_VARIANCE(Benchmark):
    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_object_target_permutation_variance"
        self._make_benchmark()


@register_benchmark
class LIBERO_OBJECT_TARGET_BASKET_SWAP_VARIANCE(Benchmark):
    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_object_target_basket_swap_variance"
        self._make_benchmark()


@register_benchmark
class LIBERO_OBJECT_TARGET_POS_VAR20X20(Benchmark):
    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_object_target_pos_var20x20"
        self._make_benchmark()


@register_benchmark
class LIBERO_OBJECT_ALL_VARIANCE(Benchmark):
    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_object_all_variance"
        self._make_benchmark()


@register_benchmark
class LIBERO_POPCORN_PRODUCTION(Benchmark):
    """Single-task suite: place frypan on stove → on → off → off-stove.

    Per-stage success is enforced by the custom problem class
    ``Libero_Kitchen_Popcorn_Production`` (see
    ``libero/envs/problems/libero_kitchen_popcorn_production.py``).
    """

    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_popcorn_production"
        self._make_benchmark()


@register_benchmark
class LIBERO_CRATE_WASHING(Benchmark):
    """Bimanual single-task suite: lift the top crate onto the washing machine.

    Two Franka Pandas standing on a shared platform must grasp the top crate
    of an 11-crate stack and place it on the adjacent washing-machine table.
    Per-stage progress (``lifted`` → ``placed``) is exposed by the custom
    problem class ``Libero_Crate_Washing`` (see
    ``libero/envs/problems/libero_crate_washing.py``).
    """

    def __init__(self, task_order_index=0):
        super().__init__(task_order_index=task_order_index)
        self.name = "libero_crate_washing"
        self._make_benchmark()
