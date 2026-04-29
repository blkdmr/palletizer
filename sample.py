from minizinc import Model, Solver, Instance

from lib.utils import gen_pallet_info
from lib.visualize import render_pallet, render_schedule

from pathlib import Path
import os

def solve_instance(pack_x, pack_y, pallet_x, pallet_y, solver_name="gecode"):
    pallet_info = gen_pallet_info(pack_x, pack_y, pallet_x, pallet_y)
    boxes_x_dim = pack_x if not pallet_info["rotated"] else pack_y
    grip_size   = 3 * boxes_x_dim

    model    = Model("model.mzn")
    solver   = Solver.lookup(solver_name)
    instance = Instance(solver, model)
    instance["n_boxes"]       = pallet_info["n_boxes"]
    instance["boxes_x_dim"]   = boxes_x_dim
    instance["boxes_along_x"] = pallet_info["boxes_along_x"]
    instance["boxes_along_y"] = pallet_info["boxes_along_y"]
    instance["grip_size"]     = grip_size

    print(f"Solving with {solver_name}: {pallet_info['n_boxes']} boxes in "
          f"{pallet_info['boxes_along_x']}x{pallet_info['boxes_along_y']} grid "
          f"(rotated={pallet_info['rotated']})")
    result = instance.solve()

    group_start = list(result["group_start"])
    group_len   = list(result["group_len"])
    drop_order  = list(result["drop_order"])
    plate       = list(result["plate"])

    groups = [list(range(s, s + l)) for s, l in zip(group_start, group_len)]
    schedule = sorted(
        [
            {
                "step":        drop_order[g],
                "group_index": g + 1,
                "boxes":       groups[g],
                "open_plate":  "left" if plate[g] == 0 else "right",
            }
            for g in range(len(group_start))
        ],
        key=lambda x: x["step"],
    )

    cell_w = pack_y if pallet_info["rotated"] else pack_x
    cell_h = pack_x if pallet_info["rotated"] else pack_y

    return {
        "groups":         groups,
        "schedule":       schedule,
        "boxes_along_x":  pallet_info["boxes_along_x"],
        "boxes_along_y":  pallet_info["boxes_along_y"],
        "cell_w":         cell_w,
        "cell_h":         cell_h,
        "rotated":        pallet_info["rotated"],
        "n_boxes":        pallet_info["n_boxes"],
    }


def main():
    pack_x, pack_y     = 70, 70
    pallet_x, pallet_y = 800, 1200

    solution = solve_instance(pack_x, pack_y, pallet_x, pallet_y, solver_name="gecode")

    root_export_dir = Path("sample")
    schedule_export_dir = root_export_dir / Path("schedule")
    root_export_dir.mkdir(exist_ok=True)
    schedule_export_dir.mkdir(exist_ok=True)
    
    render_pallet(solution,   root_export_dir / "pallet.pdf")
    render_schedule(solution, schedule_export_dir / "schedule.pdf")
    print(f"Wrote pallet.png ({len(solution['groups'])} groups) and "
          f"schedule.png ({len(solution['schedule'])} steps)")


if __name__ == "__main__":
    main()
