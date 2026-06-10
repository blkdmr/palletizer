def gen_pallet_info(box_x: int, box_y: int, pallet_x: int, pallet_y: int):
    a_cols = pallet_x // box_x
    a_rows = pallet_y // box_y
    a_count = a_cols * a_rows
    a_used_x = a_cols * box_x
    a_used_y = a_rows * box_y

    b_cols = pallet_x // box_y
    b_rows = pallet_y // box_x
    b_count = b_cols * b_rows
    b_used_x = b_cols * box_y
    b_used_y = b_rows * box_x

    if b_count > a_count:
        return {
            "n_boxes": b_count,
            "pallet_x_size": b_used_x,
            "pallet_y_size": b_used_y,
            "boxes_per_row": b_cols,
            "pallet_rows": b_rows,
            "rotated": True,
        }

    return {
        "n_boxes": a_count,
        "pallet_x_size": a_used_x,
        "pallet_y_size": a_used_y,
        "boxes_per_row": a_cols,
        "pallet_rows": a_rows,
        "rotated": False,
    }