import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import cm


ROOT_DIR = Path("benchmark") 
INPUT_FILE = ROOT_DIR / "results.json"
OUTPUT_DIR = ROOT_DIR / Path("plots") 

TIME_FLOOR  = 1e-4  # avoid log(0) for solvers that report solve_time = 0

# Field used as X axis on scaling plots.
# One of: "n_packs", "n_groups", "pack_x", "pack_y"
X_AXIS = "n_packs"


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
            "solver":   r["solver"],
            "pallet":   r["pallet_preset"],
            "pack":     f"{r['pack_x']}x{r['pack_y']}",
            "n_packs":  r["n_packs"],
            "n_groups": r["n_groups"],
            "pack_x":   r["pack_x"],
            "pack_y":   r["pack_y"],
            "time":     max(t, TIME_FLOOR),
            "wall":     r["wall_time"],
            "status":   r["status"],
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

    ax.set_yscale("log")
    ax.set_xlabel(x_axis)
    ax.set_ylabel("solve_time (s, log scale)")
    ax.set_title(f"Solver scaling — solve time vs {x_axis}")
    ax.grid(True, which="both", alpha=0.3)
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
        ax.set_yscale("log")
        ax.set_xlabel(x_axis)
        ax.set_ylabel("solve_time (s, log scale)")
        ax.set_title(f"Solver scaling — {pallet} (x = {x_axis})")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        plt.tight_layout()
        out_path = out_dir / f"scaling_{pallet}_{x_axis}.pdf"
        plt.savefig(out_path, format="pdf", dpi=600)
        plt.close(fig)
        written.append(out_path)
    return written


def plot_solver_summary(rows, colors, out_path):
    """Bar chart: geometric mean solve_time per solver, with min/max whiskers."""
    by_solver = defaultdict(list)
    for r in rows:
        by_solver[r["solver"]].append(r["time"])

    solvers = sorted(by_solver.keys())
    means = []
    mins = []
    maxs = []
    for s in solvers:
        ts = by_solver[s]
        # geometric mean is more meaningful on log-distributed timing data
        log_mean = sum(math.log(t) for t in ts) / len(ts)
        means.append(math.exp(log_mean))
        mins.append(min(ts))
        maxs.append(max(ts))

    fig, ax = plt.subplots(figsize=(8, 5))
    xs = list(range(len(solvers)))
    bar_colors = [colors[s] for s in solvers]
    ax.bar(xs, means, color=bar_colors, alpha=0.8)
    # min/max whiskers as vertical lines
    for x, lo, hi in zip(xs, mins, maxs):
        ax.plot([x, x], [lo, hi], color="black", linewidth=1)
        ax.plot([x - 0.1, x + 0.1], [lo, lo], color="black", linewidth=1)
        ax.plot([x - 0.1, x + 0.1], [hi, hi], color="black", linewidth=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(solvers)
    ax.set_yscale("log")
    ax.set_ylabel("solve_time (s, log scale)")
    ax.set_title("Per-solver summary — geometric mean (bar) and min/max (whiskers)")
    ax.grid(True, axis="y", which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


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
    lim_hi = max(max(r["wall"] for r in rows), max(r["time"] for r in rows)) * 1.2
    ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi], "k--", alpha=0.4, label="y = x")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("solve_time (s)")
    ax.set_ylabel("wall_time (s)")
    ax.set_title("Wall time vs solve time — gap = MiniZinc flattening + IPC overhead")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, format="pdf", dpi=600)
    plt.close(fig)


def main():
    data, rows = load_results(INPUT_FILE)
    if not rows:
        print("No usable rows in benchmark_results.json")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    solvers = {r["solver"] for r in rows}
    colors = solver_color_map(solvers)

    skipped = sum(1 for r in data["results"] if r["status"] == "ERROR")
    print(f"Loaded {len(rows)} successful runs ({skipped} ERROR rows skipped)")
    print(f"Solvers: {sorted(solvers)}")

    valid_axes = {"n_packs", "n_groups", "pack_x", "pack_y"}
    if X_AXIS not in valid_axes:
        raise SystemExit(f"X_AXIS must be one of {valid_axes}, got {X_AXIS!r}")

    plot_scaling_overall   (rows, colors, OUTPUT_DIR / f"scaling_overall_{X_AXIS}.pdf", X_AXIS)
    per_pallet = plot_scaling_per_pallet(rows, colors, OUTPUT_DIR, X_AXIS)
    plot_solver_summary    (rows, colors, OUTPUT_DIR / "solver_summary.pdf")
    plot_wall_vs_solve     (rows, colors, OUTPUT_DIR / "wall_vs_solve.pdf")

    print(f"Wrote {3 + len(per_pallet)} plots to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
