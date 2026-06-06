from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import cm


def _cell_xy(y_row, x_col, cell_w, cell_h):
    """Pixel coords of the top-left of pallet cell (x_col, y_row). 1-indexed."""
    return (x_col - 1) * cell_w, (y_row - 1) * cell_h


def _group_color(g_idx):
    return cm.tab20(g_idx % 20)


def _group_bbox(y_row, x_start, length, cell_w, cell_h):
    x0, y0 = _cell_xy(y_row, x_start, cell_w, cell_h)
    return x0, y0, length * cell_w, cell_h


def _draw_boxes(ax, groups, placements, placed_set, current_idx, cell_w, cell_h):
    """placements[g] = (y_row, x_start) for group g (0-indexed)."""
    for g_idx, group in enumerate(groups):
        y_row, x_start = placements[g_idx]
        for offset, box in enumerate(group):
            x, y = _cell_xy(y_row, x_start + offset, cell_w, cell_h)
            if g_idx in placed_set or g_idx == current_idx:
                color = _group_color(g_idx)
                alpha = 0.75
            else:
                color = "lightgray"
                alpha = 0.25
            ax.add_patch(patches.Rectangle(
                (x, y), cell_w, cell_h,
                linewidth=0.6, edgecolor="black", facecolor=color, alpha=alpha
            ))


def render_pallet(solution, out_path):
    """Render the full pallet, colored by group, with group labels."""
    px = solution["boxes_along_x"]
    py = solution["boxes_along_y"]
    cw = solution["cell_w"]
    ch = solution["cell_h"]
    groups     = solution["groups"]
    placements = solution["placements"]

    width_in  = 10
    height_in = max(3.0, width_in * (py * ch) / (px * cw))
    fig, ax = plt.subplots(figsize=(width_in, height_in))

    _draw_boxes(ax, groups, placements,
                placed_set=set(range(len(groups))),
                current_idx=-1, cell_w=cw, cell_h=ch)

    for g_idx, group in enumerate(groups):
        y_row, x_start = placements[g_idx]
        x0, y0, w, h = _group_bbox(y_row, x_start, len(group), cw, ch)
        ax.add_patch(patches.Rectangle(
            (x0, y0), w, h, linewidth=2.0, edgecolor="black", facecolor="none"
        ))
        ax.text(x0 + w/2, y0 + h/2, f"G{g_idx + 1}",
                ha="center", va="center", fontsize=11, fontweight="bold")
        for offset, box in enumerate(group):
            x, y = _cell_xy(y_row, x_start + offset, cw, ch)
            ax.text(x + cw*0.92, y + ch*0.92, str(box),
                    ha="right", va="bottom", fontsize=6, color="black", alpha=0.6)

    ax.set_xlim(-cw*0.1, px * cw + cw*0.1)
    ax.set_ylim(-ch*0.1, py * ch + ch*0.1)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(Path(out_path).with_suffix(".pdf"), format="pdf", dpi=600)
    plt.close(fig)


def render_schedule(solution, out_path):
    """Render the step-by-step drop schedule as one PDF per step."""
    px = solution["boxes_along_x"]
    py = solution["boxes_along_y"]
    cw = solution["cell_w"]
    ch = solution["cell_h"]
    groups     = solution["groups"]
    placements = solution["placements"]
    schedule   = solution["schedule"]

    cell_aspect = (py * ch) / (px * cw)
    sub_w = 6.0

    base = Path(out_path).with_suffix("")
    base.parent.mkdir(parents=True, exist_ok=True)
    paths = []

    placed = set()
    for step in schedule:
        cur_g = step["group_index"] - 1
        y_row, x_start = placements[cur_g]
        length = len(groups[cur_g])

        fig, ax = plt.subplots(figsize=(sub_w, sub_w * cell_aspect))
        _draw_boxes(ax, groups, placements, placed, cur_g, cw, ch)

        x0, y0, w, h = _group_bbox(y_row, x_start, length, cw, ch)
        ax.add_patch(patches.Rectangle(
            (x0, y0), w, h, linewidth=2.5, edgecolor="red", facecolor="none"
        ))
        arrow_len = max(cw, ch) * 0.9
        if step["open_plate"] == "up":
            ax.annotate("", xy=(x0 + w/2, y0 - arrow_len),
                        xytext=(x0 + w/2, y0),
                        arrowprops=dict(arrowstyle="->", color="blue", lw=2.2))
        else:
            ax.annotate("", xy=(x0 + w/2, y0 + h + arrow_len),
                        xytext=(x0 + w/2, y0 + h),
                        arrowprops=dict(arrowstyle="->", color="blue", lw=2.2))

        ax.set_xlim(-cw*0.2, px * cw + cw*0.2)
        ax.set_ylim(-ch, py * ch + ch)
        ax.invert_yaxis()
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])

        plt.tight_layout()
        step_path = base.with_name(f"{base.name}_step_{step['step']:02d}.pdf")
        plt.savefig(step_path, format="pdf", dpi=600)
        plt.close(fig)
        paths.append(step_path)

        placed.add(cur_g)

    return paths