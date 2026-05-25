# Variational Automation Benchmark

Derivative of [LIBERO-PosVar](https://github.com/ehehee/LIBERO-PosVar) containing only the six new benchmark suites
developed on the `vos-variance-suites` and `bosch/crate-washing` branches. All original LIBERO and LIBERO-Pro task
definitions have been removed; the simulator, environment wrappers, asset library, and lifelong-learning infrastructure
are inherited intact.

## Suites

| Suite | Tasks | Description |
| --- | --- | --- |
| `libero_object_target_pos_var20x20` | 10 | LIBERO-Object pick-and-place with a 20×20 grid of target-basket positions to measure spatial generalisation. |
| `libero_object_target_permutation_variance` | 10 | Target basket and distractor objects permuted across the workspace. |
| `libero_object_target_basket_swap_variance` | 10 | Target basket swapped with distractor basket on each trial. |
| `libero_object_all_variance` | 10 | Combined variance suite: position, permutation, and basket-swap perturbations applied jointly. |
| `libero_popcorn_production` | 1 | Single-task multi-stage suite — place frypan on stove → turn on → turn off → remove. Per-stage success is enforced by `Libero_Kitchen_Popcorn_Production`. |
| `libero_crate_washing` | 1 | Bimanual single-task suite — two Franka Pandas lift the top crate of an 11-crate stack onto an adjacent washing-machine table. Per-stage progress (`lifted` → `placed`) is exposed by `Libero_Crate_Washing`. |

All BDDL files live under `libero/libero/bddl_files/<suite>/` and initial states under `libero/libero/init_files/<suite>/`.
Registrations are in `libero/libero/benchmark/__init__.py`.

## Installation

```bash
git clone https://github.com/ehehee/Variational-Automation-Benchmark.git
cd Variational-Automation-Benchmark
pip install -r requirements.txt
pip install -e .
```

Requires MuJoCo / robosuite (see `requirements.txt`).

## Usage

```python
from libero.libero import benchmark

bench = benchmark.get_benchmark("libero_crate_washing")()
print(bench.get_num_tasks(), bench.get_task_names())

bddl_path = bench.get_task_bddl_file_path(0)
init_states = bench.get_task_init_states(0)
```

Sanity-check that all bddl and init files are in place:

```bash
python benchmark_scripts/check_task_suites.py
```

## Tooling

Scripts specific to the new suites live in `scripts/`:

- `teleop_crate_washing.py` — bimanual teleop for the crate-washing scene.
- `view_crate_washing.py` — interactive viewer for the scene.
- `bake_crate_washing_init.py`, `bake_libero_crate_waypoints.py`, `bake_first_frame_init.py` — generate / re-bake initial states.
- `verify_baked_init.py` — sanity-check baked init files.
- `eval_crate_washing_smoke.py` — minimal smoke test for the crate-washing env.
- `permute_distractor_init.py`, `render_permuted_trials.py` — utilities for the variance suites.

## Layout

```
libero/libero/
├── assets/        # shared scene XMLs, textures, scanned objects (+ new crate_washing scene)
├── bddl_files/    # 6 suites
├── init_files/    # 6 suites
├── benchmark/     # registration: __init__.py, libero_suite_task_map.py
├── envs/          # simulator wrappers + new crate-washing arena and bimanual base domain
└── utils/         # shared helpers
libero/lifelong/   # lifelong-learning algorithms / training loop (inherited from upstream)
benchmark_scripts/ # check_task_suites.py, render_single_task.py
scripts/           # see Tooling above
templates/         # scene / problem-class templates for adding new suites
```

## Provenance

Built from upstream LIBERO-PosVar at branches `vos-variance-suites` and `bosch/crate-washing`. The original LIBERO-100,
LIBERO-Spatial/Object/Goal task families and their `_with_*` variants, the LIBERO-OOD configs, and the upstream demo
notebooks have been removed.

## License

MIT (inherited from upstream LIBERO / LIBERO-PosVar — see `LICENSE`).
