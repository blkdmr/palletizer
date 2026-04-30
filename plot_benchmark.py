import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import cm


ROOT_DIR = Path("benchmark") 
INPUT_FILE = ROOT_DIR / "results.json"
OUTPUT_DIR = ROOT_DIR / Path("plots") 

TIME_FLOOR  = 1e-4  # safety lower bound for solvers that report solve_time = 0

# Field used as X axis on scaling plots.
# One of: "n_boxes", "n_groups", "box_x", "box_y"
X_AXIS = "n_boxes"

# Solvers to exclude from plots (e.g. {"highs", "chuffed"}).
SKIP_SOLVERS = set()#{"highs"}


def load_results(path):
    with open(path) as f:
        data = json.load(f)
    rows = []
    for r in data["results"]:
        if r["status"] == "ERROR":
            continue
        t = r.get("solve_time")
        if t is None:
            t = r.get("wall_time")
        if t is None:
            continue
        rows.append({
            "solver":         r["solver"],
            "pallet":         r["pallet_preset"],
            "box":           f"{r['box_x']}x{r['box_y']}",
            "n_boxes":        r["n_boxes"],
            "n_groups":       r["n_groups"],
            "box_x":          r["box_x"],
            "box_y":          r["box_y"],
            "grip_size":      r["grip_size"],
            "grip_mult":      r.get("grip_multiplier", 3),
            "time":           max(t, TIME_FLOOR),
            "wall":           r["wall_time"],
            "status":         r["status"],
        })
    return data, rows


def solver_color_map(solvers):
    palette = cm.tab10
    return {s: palette(i % 10) for i, s in enumerate(sorted(solvers))}


def plot_scaling_overall(rows, colors, out_path, x_axis):
    """Solve time vs <x_axis>, one line per solver."""
    by_solver = defaultdict(list)
    for r in rows:
        by_solver[r["solver"]].append((r[x_axis], r["time"]))

    fig, ax = plt.subplots(figsize=(10, 6))
    for solver, points in sorted(by_solver.items()):
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, "o-", label=solver, color=colors[solver],
                markersize=5, linewidth=1.4, alpha=0.85)

    ax.set_xlabel(x_axis)
    ax.set_ylabel("solve_time (s, log scale)")
    ax.set_yscale("log")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


def plot_scaling_per_pallet(rows, colors, out_dir, x_axis):
    """One file per pallet preset: solve_time vs <x_axis>, lines per solver."""
    pallets = sorted({r["pallet"] for r in rows})
    written = []
    for pallet in pallets:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        by_solver = defaultdict(list)
        for r in rows:
            if r["pallet"] != pallet:
                continue
            by_solver[r["solver"]].append((r[x_axis], r["time"]))
        for solver, points in sorted(by_solver.items()):
            points.sort()
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, "o-", label=solver, color=colors[solver],
                    markersize=6, linewidth=1.6, alpha=0.85)
        ax.set_xlabel(x_axis)
        ax.set_ylabel("solve_time (s, log scale)")
        ax.set_yscale("log")
        ax.legend()
        plt.tight_layout()
        out_path = out_dir / f"scaling_{pallet}_{x_axis}.pdf"
        plt.savefig(out_path, format="pdf", dpi=600)
        plt.close(fig)
        written.append(out_path)
    return written


def plot_solver_summary(rows, colors, out_path):
    """Bar chart: mean solve_time per solver, with std-deviation whiskers (log y)."""
    by_solver = defaultdict(list)
    for r in rows:
        by_solver[r["solver"]].append(r["time"])

    solvers = sorted(by_solver.keys())
    means = []
    stds = []
    for s in solvers:
        ts = by_solver[s]
        m = sum(ts) / len(ts)
        var = sum((t - m) ** 2 for t in ts) / len(ts)
        means.append(m)
        stds.append(var ** 0.5)

    fig, ax = plt.subplots(figsize=(8, 5))
    xs = list(range(len(solvers)))
    bar_colors = [colors[s] for s in solvers]
    # Clip the lower whisker to TIME_FLOOR so log scale stays well-defined.
    lo_err = [min(s, max(m - TIME_FLOOR, 0)) for m, s in zip(means, stds)]
    hi_err = stds
    ax.bar(xs, means, color=bar_colors, alpha=0.8,
           yerr=[lo_err, hi_err], capsize=4, ecolor="black")
    ax.set_yscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels(solvers)
    ax.set_ylabel("solve_time (s, log scale)")
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


def plot_scaling_by_grip(rows, colors, out_path):
    """Mean solve_time vs grip multiplier, one line per solver."""
    by_solver_grip = defaultdict(list)
    for r in rows:
        by_solver_grip[(r["solver"], r["grip_mult"])].append(r["time"])

    fig, ax = plt.subplots(figsize=(8, 5.5))
    solvers = sorted({s for (s, _) in by_solver_grip})
    for solver in solvers:
        grips = sorted({g for (s, g) in by_solver_grip if s == solver})
        xs, ys = [], []
        for g in grips:
            ts = by_solver_grip[(solver, g)]
            xs.append(g)
            ys.append(sum(ts) / len(ts))
        ax.plot(xs, ys, "o-", label=solver, color=colors[solver],
                markersize=6, linewidth=1.6, alpha=0.85)

    ax.set_xlabel(r"grip multiplier $k$ (grip_size = $k \cdot$ boxes_x_dim)")
    ax.set_ylabel("solve_time (s, mean, log scale)")
    ax.set_yscale("log")
    ax.set_xticks(sorted({r["grip_mult"] for r in rows}))
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


def plot_scaling_overall_per_grip(rows, colors, out_dir, x_axis):
    """One file per grip multiplier: solve_time vs <x_axis>, lines per solver."""
    grips = sorted({r["grip_mult"] for r in rows})
    written = []
    for g in grips:
        sub = [r for r in rows if r["grip_mult"] == g]
        if not sub:
            continue
        fig, ax = plt.subplots(figsize=(9, 5.5))
        by_solver = defaultdict(list)
        for r in sub:
            by_solver[r["solver"]].append((r[x_axis], r["time"]))
        for solver, points in sorted(by_solver.items()):
            points.sort()
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, "o-", label=solver, color=colors[solver],
                    markersize=5, linewidth=1.4, alpha=0.85)
        ax.set_xlabel(x_axis)
        ax.set_ylabel("solve_time (s, log scale)")
        ax.set_yscale("log")
        ax.legend()
        plt.tight_layout()
        out_path = out_dir / f"scaling_overall_{x_axis}_grip{g}x.pdf"
        plt.savefig(out_path, format="pdf", dpi=600)
        plt.close(fig)
        written.append(out_path)
    return written


def plot_wall_vs_solve(rows, colors, out_path):
    """Scatter wall_time vs solve_time per solver — shows MiniZinc/flattening overhead."""
    fig, ax = plt.subplots(figsize=(8, 6))
    by_solver = defaultdict(list)
    for r in rows:
        by_solver[r["solver"]].append((r["time"], r["wall"]))

    for solver, pts in sorted(by_solver.items()):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.scatter(xs, ys, label=solver, color=colors[solver], s=30, alpha=0.75, edgecolor="black", linewidth=0.3)

    lim_lo = TIME_FLOOR
    lim_hi = max(max(r["wall"] for r in rows), max(r["time"] for r in rows)) * 1.05
    ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi], "k--", alpha=0.4, label="y = x")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim_lo, lim_hi)
    ax.set_ylim(lim_lo, lim_hi)
    ax.set_xlabel("solve_time (s, log scale)")
    ax.set_ylabel("wall_time (s, log scale)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


def main():
    data, rows = load_results(INPUT_FILE)
    if SKIP_SOLVERS:
        rows = [r for r in rows if r["solver"] not in SKIP_SOLVERS]
    if not rows:
        print("No usable rows in benchmark_results.json")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    solvers = {r["solver"] for r in rows}
    
    colors = solver_color_map(solvers)

    skipped = sum(1 for r in data["results"] if r["status"] == "ERROR")
    print(f"Loaded {len(rows)} successful runs ({skipped} ERROR rows skipped)")
    print(f"Solvers: {sorted(solvers)}")

    valid_axes = {"n_boxes", "n_groups", "box_x", "box_y"}
    if X_AXIS not in valid_axes:
        raise SystemExit(f"X_AXIS must be one of {valid_axes}, got {X_AXIS!r}")

    plot_scaling_overall   (rows, colors, OUTPUT_DIR / f"scaling_overall_{X_AXIS}.pdf", X_AXIS)
    per_pallet = plot_scaling_per_pallet(rows, colors, OUTPUT_DIR, X_AXIS)
    plot_solver_summary    (rows, colors, OUTPUT_DIR / "solver_summary.pdf")
    plot_wall_vs_solve     (rows, colors, OUTPUT_DIR / "wall_vs_solve.pdf")
    plot_scaling_by_grip   (rows, colors, OUTPUT_DIR / "scaling_by_grip.pdf")
    per_grip = plot_scaling_overall_per_grip(rows, colors, OUTPUT_DIR, X_AXIS)

    print(f"Wrote {4 + len(per_pallet) + len(per_grip)} plots to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
