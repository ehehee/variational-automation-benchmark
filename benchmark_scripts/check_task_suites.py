"""Verify that all bddl and init-state files for the registered suites exist on disk."""
import os
from termcolor import colored

from libero.libero import benchmark, get_libero_path


def main():

    init_states_default_path = get_libero_path("init_states")
    bddl_files_default_path = get_libero_path("bddl_files")

    for benchmark_name in [
        "libero_object_all_variance",
        "libero_object_target_basket_swap_variance",
        "libero_object_target_permutation_variance",
        "libero_object_target_pos_var20x20",
        "libero_popcorn_production",
        "libero_crate_washing",
    ]:
        benchmark_instance = benchmark.get_benchmark_dict()[benchmark_name]()
        num_tasks = benchmark_instance.get_num_tasks()
        print(f"{num_tasks} tasks in the benchmark {benchmark_instance.name}: ")

        task_names = benchmark_instance.get_task_names()
        for task_id in range(num_tasks):
            task = benchmark_instance.get_task(task_id)
            bddl_file = os.path.join(
                bddl_files_default_path, task.problem_folder, task.bddl_file
            )
            assert os.path.exists(bddl_file), f"{bddl_file} does not exist!"
            init_states_path = os.path.join(
                init_states_default_path, task.problem_folder, task.init_states_file
            )
            assert os.path.exists(
                init_states_path
            ), f"{init_states_path} does not exist!"
            print(f"  [{task_id}] {task_names[task_id]}")

    print(colored("All bddl and init-state files exist!", "green"))


if __name__ == "__main__":
    main()
