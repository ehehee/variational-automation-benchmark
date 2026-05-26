"""Success predicates for VAB tasks.

Each predicate is a free function ``(sim, body_ids, **args) -> bool`` where
``sim`` is the MuJoCo sim handle and ``body_ids`` maps object id (as declared
in the task YAML) to its MuJoCo body id. Predicates are registered in
``PREDICATES`` and looked up by name from the YAML.

Adding a new predicate: implement a function, decorate with ``@register``.

Stateful predicates (e.g. ``pack_all_into``) may declare an extra
``joint_names`` kwarg to receive the per-object free-joint name table,
needed for state mutations like teleporting delivered objects. ``evaluate``
introspects the predicate signature and forwards ``joint_names`` only when
declared, so stateless predicates stay unchanged.
"""
from __future__ import annotations

import inspect
from typing import Callable, Dict

import numpy as np

PREDICATES: Dict[str, Callable[..., bool]] = {}


def register(name: str):
    def deco(fn):
        PREDICATES[name] = fn
        return fn

    return deco


def _xyz(sim, body_id) -> np.ndarray:
    return np.asarray(sim.data.body_xpos[body_id])


def _quat_wxyz(sim, body_id) -> np.ndarray:
    # MuJoCo stores quats as wxyz
    return np.asarray(sim.data.body_xquat[body_id])


@register("contained_in")
def contained_in(
    sim,
    body_ids,
    *,
    obj: str,
    container: str,
    xy_tol: float = 0.10,
    z_low: float = -0.05,
    z_high: float = 0.20,
) -> bool:
    """obj XY within xy_tol of container XY, and obj Z within [z_low, z_high] of container Z."""
    p_obj = _xyz(sim, body_ids[obj])
    p_con = _xyz(sim, body_ids[container])
    dxy = np.linalg.norm(p_obj[:2] - p_con[:2])
    dz = p_obj[2] - p_con[2]
    return bool(dxy < xy_tol and z_low < dz < z_high)


@register("on_top_of")
def on_top_of(
    sim,
    body_ids,
    *,
    obj: str,
    surface: str,
    xy_tol: float = 0.15,
    z_min: float = 0.01,
    z_max: float = 0.20,
) -> bool:
    """obj XY within xy_tol of surface XY, and obj Z is z_min..z_max above surface Z."""
    p_obj = _xyz(sim, body_ids[obj])
    p_sur = _xyz(sim, body_ids[surface])
    dxy = np.linalg.norm(p_obj[:2] - p_sur[:2])
    dz = p_obj[2] - p_sur[2]
    return bool(dxy < xy_tol and z_min < dz < z_max)


@register("near")
def near(
    sim,
    body_ids,
    *,
    obj_a: str,
    obj_b: str,
    threshold: float = 0.10,
) -> bool:
    p_a = _xyz(sim, body_ids[obj_a])
    p_b = _xyz(sim, body_ids[obj_b])
    return bool(np.linalg.norm(p_a - p_b) < threshold)


@register("oriented_like")
def oriented_like(
    sim,
    body_ids,
    *,
    obj: str,
    quat: list,
    tol_deg: float = 15.0,
) -> bool:
    """quat is target in xyzw order (YAML-friendly). Converted to wxyz to match MuJoCo."""
    q_target = np.array([quat[3], quat[0], quat[1], quat[2]], dtype=np.float64)
    q_target /= np.linalg.norm(q_target) + 1e-12
    q_obj = _quat_wxyz(sim, body_ids[obj])
    q_obj = q_obj / (np.linalg.norm(q_obj) + 1e-12)
    cos_half = float(abs(np.dot(q_obj, q_target)))
    cos_half = min(1.0, max(-1.0, cos_half))
    angle_deg = float(np.degrees(2.0 * np.arccos(cos_half)))
    return angle_deg < tol_deg


@register("lifted_above")
def lifted_above(
    sim,
    body_ids,
    *,
    obj: str,
    z_min: float,
) -> bool:
    return bool(_xyz(sim, body_ids[obj])[2] > z_min)


# Far-away pose used by pack_all_into to retire delivered objects so
# they cannot be knocked out of the container by a later placement.
# Matches the LIBERO-PosVar Libero_Grocery_Packing graveyard convention.
_PACKING_GRAVEYARD = (50.0, 50.0, 5.0)


@register("pack_all_into")
def pack_all_into(
    sim,
    body_ids,
    *,
    objs: list,
    container: str,
    joint_names: dict,
    xy_tol: float = 0.10,
    z_low: float = -0.05,
    z_high: float = 0.25,
) -> bool:
    """Multi-object monotonic packing: every obj must land in container.

    Each object that satisfies ``contained_in`` is marked delivered AND
    teleported to a far graveyard pose so it cannot regress.

    State lives on the sim as ``sim._packing_state`` (a dict with
    ``objs`` tuple and ``delivered`` set). VABEnv.reset clears it; the
    predicate also reinitializes if it sees an unfamiliar ``objs`` tuple.
    """
    state = getattr(sim, "_packing_state", None)
    if state is None or state.get("objs") != tuple(objs):
        state = {"objs": tuple(objs), "delivered": set()}
        sim._packing_state = state

    p_con = _xyz(sim, body_ids[container])
    newly = False
    gx, gy, gz = _PACKING_GRAVEYARD
    for obj in objs:
        if obj in state["delivered"]:
            continue
        p_obj = _xyz(sim, body_ids[obj])
        dxy = float(np.linalg.norm(p_obj[:2] - p_con[:2]))
        dz = float(p_obj[2] - p_con[2])
        if dxy < xy_tol and z_low < dz < z_high:
            state["delivered"].add(obj)
            sim.data.set_joint_qpos(
                joint_names[obj],
                np.array([gx, gy, gz, 1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
            newly = True
    if newly:
        sim.forward()
    return len(state["delivered"]) == len(objs)


def evaluate(
    sim,
    body_ids,
    predicate: str,
    args: dict,
    *,
    joint_names: dict | None = None,
) -> bool:
    if predicate not in PREDICATES:
        raise KeyError(
            f"Unknown predicate {predicate!r}. Available: {sorted(PREDICATES)}"
        )
    fn = PREDICATES[predicate]
    if "joint_names" in inspect.signature(fn).parameters:
        return fn(sim, body_ids, joint_names=joint_names, **args)
    return fn(sim, body_ids, **args)
