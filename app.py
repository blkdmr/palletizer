from flask import Flask, render_template, request, jsonify
from minizinc import Model, Solver, Instance

app = Flask(__name__)


def gen_pallet_info(pack_x: int, pack_y: int, pallet_x: int, pallet_y: int):
    a_cols = pallet_x // pack_x
    a_rows = pallet_y // pack_y
    a_count = a_cols * a_rows
    a_used_x = a_cols * pack_x
    a_used_y = a_rows * pack_y

    b_cols = pallet_x // pack_y
    b_rows = pallet_y // pack_x
    b_count = b_cols * b_rows
    b_used_x = b_cols * pack_y
    b_used_y = b_rows * pack_x

    if b_count > a_count:
        return {
            "n_packs": b_count,
            "pallet_x_size": b_used_x,
            "pallet_y_size": b_used_y,
            "packs_along_x": b_cols,
            "packs_along_y": b_rows,
            "rotated": True,
        }
    return {
        "n_packs": a_count,
        "pallet_x_size": a_used_x,
        "pallet_y_size": a_used_y,
        "packs_along_x": a_cols,
        "packs_along_y": a_rows,
        "rotated": False,
    }


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/schedule")
def schedule_page():
    return render_template("schedule.html")

@app.route("/solve", methods=["POST"])
def solve():
    try:
        data      = request.get_json()
        pack_x    = int(data["pack_x"])
        pack_y    = int(data["pack_y"])
        pallet_x  = int(data["pallet_x"])
        pallet_y  = int(data["pallet_y"])
        grip_size = data.get("grip_size", 3 * pack_x)

        pallet_info = gen_pallet_info(pack_x, pack_y, pallet_x, pallet_y)
        packs_x_dim = pack_x if not pallet_info["rotated"] else pack_y

        model    = Model("model.mzn")
        solver   = Solver.lookup("gecode")
        instance = Instance(solver, model)

        instance["n_packs"]       = pallet_info["n_packs"]
        instance["packs_x_dim"]   = packs_x_dim
        instance["packs_along_x"] = pallet_info["packs_along_x"]
        instance["packs_along_y"] = pallet_info["packs_along_y"]
        instance["grip_size"]     = grip_size

        result = instance.solve()

        group_start = list(result["group_start"])
        group_len   = list(result["group_len"])
        drop_order  = list(result["drop_order"])
        plate       = list(result["plate"])

        # Reconstruct groups and pack→group mapping
        groups     = []
        pack_group = {}
        for g_idx, (start, length) in enumerate(zip(group_start, group_len)):
            group = list(range(start, start + length))
            groups.append(group)
            for pack_num in group:
                pack_group[pack_num] = g_idx

        # Build step-by-step schedule (sorted by drop order)
        schedule = sorted(
            [
                {
                    "step":       drop_order[g],
                    "group_index": g + 1,
                    "packs":      groups[g],
                    "open_plate": "left" if plate[g] == 0 else "right",
                }
                for g in range(len(group_start))
            ],
            key=lambda x: x["step"],
        )

        return jsonify({
            "ok":          True,
            "groups":      groups,
            "pack_group":  pack_group,
            "schedule":    schedule,
            "pallet_info": pallet_info,
            "pack_x":      pack_x,
            "pack_y":      pack_y,
            "pallet_x":    pallet_x,
            "pallet_y":    pallet_y,
            "grip_size":   grip_size,
            "n_groups":    len(groups),
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)