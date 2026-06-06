import json
import time
from datetime import timedelta, datetime
from pathlib import Path

from minizinc import Model, Solver, Instance

from lib.utils import gen_pallet_info


# The 5 pallet presets act as the instance generator: running one box size
# against all 5 presets yields 5 different instances (different n) for that pair.
PALLET_PRESETS = {
    "europallet":   (1200, 800),
    "industrie":    (1200, 1000),
    "us_40x48":     (1219, 1016),
    "halfpallet":   (800, 600),
    "australian":   (1165, 1165),
}

# 4 box-size pairs (x, y), ordered with decreasing x, y so that n_boxes
# increases down the list. 4 pairs x 5 presets = 20 instances total.
BOX_SIZES = [
    (200, 200),
    (150, 150),
    (100, 100),
    (50, 50),
]

# S (grip_size) may be at most 3 * box_x  ->  grip_size = k * boxes_x_dim, k in [1, 3].
# Each of the 20 instances is tested under all three grip settings.
GRIP_MULTIPLIERS = [1, 2, 3]

SOLVERS = ["gecode", "chuffed",  "cp-sat", "highs"]

TIMEOUT_SECONDS = 300 # 5 minutes timeout

def available_solvers(names):
    found = []
    for name in names:
        try:
            Solver.lookup(name)
            found.append(name)
        except Exception as e:
            print(f"[skip] solver '{name}' not available: {e}")
    return found

def run_one(model, solver_name, box_x, box_y, pallet_x, pallet_y, grip_multiplier, timeout_s):
    pallet_info = gen_pallet_info(box_x, box_y, pallet_x, pallet_y)
    boxes_x_dim = box_x if not pallet_info["rotated"] else box_y
    grip_size = grip_multiplier * boxes_x_dim

    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)
    instance["n_boxes"]       = pallet_info["n_boxes"]
    instance["boxes_x_dim"]   = boxes_x_dim
    instance["boxes_along_x"] = pallet_info["boxes_along_x"]
    instance["boxes_along_y"] = pallet_info["boxes_along_y"]
    instance["grip_size"]     = grip_size

    max_pkble      = (grip_size + boxes_x_dim) // boxes_x_dim
    chunks_per_row = (pallet_info["boxes_along_x"] + max_pkble - 1) // max_pkble
    n_chunks       = pallet_info["boxes_along_y"] * chunks_per_row

    record = {
        "solver":          solver_name,
        "box_x":           box_x,
        "box_y":           box_y,
        "pallet_x":        pallet_x,
        "pallet_y":        pallet_y,
        "n_boxes":         pallet_info["n_boxes"],
        "n_chunks":        n_chunks,
        "boxes_along_x":   pallet_info["boxes_along_x"],
        "boxes_along_y":   pallet_info["boxes_along_y"],
        "grip_size":       grip_size,
        "grip_multiplier": grip_multiplier,
        "timeout_s":       timeout_s,
    }

    t0 = time.perf_counter()
    try:
        result = instance.solve(timeout=timedelta(seconds=timeout_s))
        wall = time.perf_counter() - t0
        status = str(result.status).split(".")[-1] if result.status else "UNKNOWN"
        stats = {k: (v.total_seconds() if hasattr(v, "total_seconds") else v)
                 for k, v in (result.statistics or {}).items()}
        record.update({
            "status":     status,
            "wall_time":  wall,
            "solve_time": stats.get("solveTime", None),
            "flat_time":  stats.get("flatTime", None),
            "statistics": stats,
            "error":      None,
        })
    except Exception as e:
        record.update({
            "status":     "ERROR",
            "wall_time":  time.perf_counter() - t0,
            "solve_time": None,
            "flat_time":  None,
            "statistics": {},
            "error":      str(e),
        })
    return record


def main():
    model = Model("satisfy.mzn")
    solvers = available_solvers(SOLVERS)
    print(f"Running solvers: {solvers}")

    results = []
    n_instances = len(BOX_SIZES) * len(PALLET_PRESETS)  # 4 pairs x 5 presets = 20
    total = n_instances * len(GRIP_MULTIPLIERS) * len(solvers)
    i = 0
    # Outer loop over box pairs (decreasing x, y -> increasing n);
    # next loop over the 5 presets gives the 5 instances for each pair;
    # each instance is then tested under every grip setting and solver.
    for pair_id, (box_x, box_y) in enumerate(BOX_SIZES, start=1):
        for instance_id, (pallet_name, (pallet_x, pallet_y)) in enumerate(PALLET_PRESETS.items(), start=1):
            for grip_mult in GRIP_MULTIPLIERS:
                for solver_name in solvers:
                    i += 1
                    print(f"[{i}/{total}] {solver_name} | pair {pair_id} box {box_x}x{box_y} | "
                          f"instance {instance_id} {pallet_name} {pallet_x}x{pallet_y} | grip x{grip_mult}")
                    rec = run_one(model, solver_name, box_x, box_y, pallet_x, pallet_y, grip_mult, TIMEOUT_SECONDS)
                    rec["pair_id"]       = pair_id
                    rec["instance_id"]   = instance_id
                    rec["pallet_preset"] = pallet_name
                    results.append(rec)
                    print(f"   → status={rec['status']} wall={rec['wall_time']:.3f}s "
                          f"n_boxes={rec['n_boxes']} n_chunks={rec['n_chunks']}")

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "timeout_s":    TIMEOUT_SECONDS,
        "n_instances":  n_instances,
        "solvers":      solvers,
        "pallet_presets": {k: {"x": v[0], "y": v[1]} for k, v in PALLET_PRESETS.items()},
        "box_sizes":   [{"x": x, "y": y} for (x, y) in BOX_SIZES],
        "grip_multipliers": GRIP_MULTIPLIERS,
        "results":      results,
    }

    root_dir = Path("benchmark")
    root_dir.mkdir(exist_ok=True)
    out_file = root_dir / Path("results.json")
    out_file.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {len(results)} records in {out_file.resolve()}")

if __name__ == "__main__":
    main()