from lib.utils import gen_pallet_info
from lib.visualize import render_pallet, render_schedule

from minizinc import Model, Solver, Instance
from pathlib import Path
import matplotlib as mpl

mpl.rcParams.update({
    "font.size": 16,
    "axes.labelsize": 18,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 14,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

def solve_instance(box_x, box_y, pallet_x, pallet_y, solver_name="gecode"):
    pallet_info = gen_pallet_info(box_x, box_y, pallet_x, pallet_y)
    boxes_x_dim = box_x if not pallet_info["rotated"] else box_y
    grip_size = 3 * boxes_x_dim

    model = Model("satisfy.mzn")
    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)

    instance["n_boxes"] = pallet_info["n_boxes"]
    instance["boxes_x_dim"] = boxes_x_dim
    instance["boxes_along_x"] = pallet_info["boxes_along_x"]
    instance["boxes_along_y"] = pallet_info["boxes_along_y"]
    instance["grip_size"] = grip_size

    print(f"Solving with {solver_name}: {pallet_info['n_boxes']} boxes in "
          f"{pallet_info['boxes_along_x']}x{pallet_info['boxes_along_y']} grid "
          f"(rotated={pallet_info['rotated']})")

    result = instance.solve()

    chunk_start = list(result["chunk_start"])
    chunk_len = list(result["chunk_len"])
    plate = list(result["plate"])
    y_row_vals = list(result["y_row"])
    x_start_vals = list(result["x_start"])

    groups = [list(range(s, s + l)) for s, l in zip(chunk_start, chunk_len)]
    placements = list(zip(y_row_vals, x_start_vals))

    schedule = [
        {
            "step": g + 1,
            "group_index": g + 1,
            "boxes": groups[g],
            "y_row": y_row_vals[g],
            "x_start": x_start_vals[g],
            "x_end": x_start_vals[g] + chunk_len[g] - 1,
            "open_plate": "up" if plate[g] == 0 else "down",
        }
        for g in range(len(chunk_start))
    ]

    cell_w = box_y if pallet_info["rotated"] else box_x
    cell_h = box_x if pallet_info["rotated"] else box_y

    return {
        "groups": groups,
        "schedule": schedule,
        "placements": placements,
        "boxes_along_x": pallet_info["boxes_along_x"],
        "boxes_along_y": pallet_info["boxes_along_y"],
        "cell_w": cell_w,
        "cell_h": cell_h,
        "rotated": pallet_info["rotated"],
        "n_boxes": pallet_info["n_boxes"],
    }

def main():
    box_x, box_y = 70, 70
    pallet_x, pallet_y = 800, 400

    solution = solve_instance(box_x, box_y, pallet_x, pallet_y, solver_name="gecode")

    print(f"Solved")

    root_export_dir = Path("sample")
    schedule_export_dir = root_export_dir / Path("schedule")
    root_export_dir.mkdir(exist_ok=True)
    schedule_export_dir.mkdir(exist_ok=True)
    
    render_pallet(solution, root_export_dir / "pallet.pdf")
    render_schedule(solution, schedule_export_dir / "schedule.pdf")
    print(f"Wrote pallet.pdf ({len(solution['groups'])} groups) and "
          f"schedule.pdf ({len(solution['schedule'])} steps)")

if __name__ == "__main__":
    main()