# Variational Automation Benchmark (VAB)

Self-contained-YAML manipulation benchmark. One file per task: arena, robot,
objects, initial states, success predicate, language. No BDDL, no sidecar
init file, no privileged information surfaced to the agent.

## Quick start

```bash
git clone https://github.com/ehehee/Variational-Automation-Benchmark.git
cd Variational-Automation-Benchmark
pip install -r requirements.txt
pip install -e .
```

```python
import numpy as np
from libero.vab import load_task

task = load_task("seed_tasks/living_room_cream_cheese_in_basket.yaml")
env  = task.make_env()

for i in range(task.n_inits):
    obs = env.reset(init_index=i)
    # obs.keys() == {"images", "proprio"} -- nothing else.
    for _ in range(50):
        obs, reward, done, info = env.step(np.zeros(env.action_dim))
    print(f"init {i}: success={info['success']}")
env.close()
```

## Observation contract (strict)

```python
obs = {
    "images":  {camera_name: uint8[H,W,3], ...},   # one per camera in YAML
    "proprio": {
        "joint_pos":    float32[7],
        "joint_vel":    float32[7],
        "eef_pos":      float32[3],
        "eef_quat":     float32[4],   # xyzw
        "gripper_qpos": float32[2],
    },
}
```

No object names, no ground-truth poses, no segmentation masks. Success is
returned only as `info["success"]: bool` from `env.step`.

## Task YAML

```yaml
id: living_room.cream_cheese_in_basket   # required, unique
language: "Put the cream cheese in the basket."

arena:
  name: living_room        # living_room | kitchen | study | coffee_table | floor | table
  # scene_xml: optional override (path under libero/libero/assets/)
  # scene_properties: { floor_style: ..., wall_style: ... }   # optional

robot:
  name: panda
  controller: OSC_POSE

cameras: [agentview, robot0_eye_in_hand]
camera_height: 128
camera_width: 128
camera_depth: false

objects:
  - { id: cream_cheese, asset: cream_cheese }   # asset = registered OBJECTS_DICT key
  - { id: basket,       asset: basket }

inits:                                          # one or more init variants
  - cream_cheese: [x, y, z, qx, qy, qz, qw]     # xyzw quaternion
    basket:       [x, y, z, qx, qy, qz, qw]
  - cream_cheese: [...]
    basket:       [...]
default_init_index: 0                           # used when env.reset() has no init_index

success:
  predicate: contained_in
  args: { obj: cream_cheese, container: basket, xy_tol: 0.08, z_low: -0.02, z_high: 0.20 }

horizon: 400
metadata: { suite: object_target_pos_var, difficulty: easy }
```

## Success predicates (v1)

Registered in `libero/libero/vab/predicates.py`. Add new ones by appending to
the `PREDICATES` registry; each takes `(sim, body_ids, **args) -> bool`.

| predicate | required args | optional args |
| --- | --- | --- |
| `contained_in`  | `obj`, `container`            | `xy_tol`, `z_low`, `z_high` |
| `on_top_of`     | `obj`, `surface`              | `xy_tol`, `z_min`, `z_max` |
| `near`          | `obj_a`, `obj_b`              | `threshold` |
| `oriented_like` | `obj`, `quat` (xyzw)          | `tol_deg` |
| `lifted_above`  | `obj`, `z_min`                | -- |

## Layout

```
libero/libero/
├── assets/            # scene XMLs, textures, scanned/CAD meshes (runtime-essential)
├── envs/              # robosuite primitives: arenas/, robots/, objects/, textures.py
└── vab/               # YAML loader + strict-obs env
    ├── schema.py
    ├── loader.py
    ├── env.py
    ├── predicates.py
    └── _arena_table.py
seed_tasks/            # canonical example tasks
tests/test_smoke.py    # end-to-end loader + env validation
```

## Smoke test

```bash
pytest tests/test_smoke.py -v
# also dumps one agentview RGB per task to /tmp/vab_smoke/
```

## Roadmap

- Re-author the legacy 10×10 eval matrix (object_swap / pos_var / perm /
  basket_swap) programmatically from a Python template.
- Bimanual / crate-washing support (v1 is single-arm only).
- Action space beyond `OSC_POSE`.

## License

MIT.
