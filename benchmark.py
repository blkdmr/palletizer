import json
import time
from datetime import timedelta, datetime
from pathlib import Path

from minizinc import Model, Solver, Instance

from lib.utils import gen_pallet_info


PALLET_PRESETS = {
    "europallet":   (1200, 800),
    "industrie":    (1200, 1000),
    "us_40x48":     (1219, 1016),
    "halfpallet":   (800, 600),
    "australian":   (1165, 1165),
}

PACK_SIZES = [
    (50, 50),
    (70, 70),
    (100, 100),
    (120, 80),
    (150, 150),
    (200, 200),
]

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


def run_one(model, solver_name, pack_x, pack_y, pallet_x, pallet_y, timeout_s):
    pallet_info = gen_pallet_info(pack_x, pack_y, pallet_x, pallet_y)
    packs_x_dim = pack_x if not pallet_info["rotated"] else pack_y
    grip_size = 3 * packs_x_dim

    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)
    instance["n_packs"]       = pallet_info["n_packs"]
    instance["packs_x_dim"]   = packs_x_dim
    instance["packs_along_x"] = pallet_info["packs_along_x"]
    instance["packs_along_y"] = pallet_info["packs_along_y"]
    instance["grip_size"]     = grip_size

    max_pkble = (grip_size + packs_x_dim) // packs_x_dim
    groups_per_row = (pallet_info["packs_along_x"] + max_pkble - 1) // max_pkble
    n_groups = pallet_info["packs_along_y"] * groups_per_row

    record = {
        "solver":         solver_name,
        "pack_x":         pack_x,
        "pack_y":         pack_y,
        "pallet_x":       pallet_x,
        "pallet_y":       pallet_y,
        "n_packs":        pallet_info["n_packs"],
        "n_groups":       n_groups,
        "packs_along_x":  pallet_info["packs_along_x"],
        "packs_along_y":  pallet_info["packs_along_y"],
        "grip_size":      grip_size,
        "timeout_s":      timeout_s,
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
    model = Model("model.mzn")
    solvers = available_solvers(SOLVERS)
    print(f"Running solvers: {solvers}")

    results = []
    total = len(PALLET_PRESETS) * len(PACK_SIZES) * len(solvers)
    i = 0
    for pallet_name, (pallet_x, pallet_y) in PALLET_PRESETS.items():
        for (pack_x, pack_y) in PACK_SIZES:
            for solver_name in solvers:
                i += 1
                print(f"[{i}/{total}] {solver_name} | {pallet_name} {pallet_x}x{pallet_y} | pack {pack_x}x{pack_y}")
                rec = run_one(model, solver_name, pack_x, pack_y, pallet_x, pallet_y, TIMEOUT_SECONDS)
                rec["pallet_preset"] = pallet_name
                print(f"   → status={rec['status']} wall={rec['wall_time']:.3f}s n_packs={rec['n_packs']} n_groups={rec['n_groups']}")
                results.append(rec)

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "timeout_s":    TIMEOUT_SECONDS,
        "solvers":      solvers,
        "pallet_presets": {k: {"x": v[0], "y": v[1]} for k, v in PALLET_PRESETS.items()},
        "pack_sizes":   [{"x": x, "y": y} for (x, y) in PACK_SIZES],
        "results":      results,
    }

    root_dir = Path("benchmark")
    root_dir.mkdir(exist_ok=True)
    out_file = root_dir / Path("results.json")
    out_file.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {len(results)} records in {out_file.resolve()}")

if __name__ == "__main__":
    main()
