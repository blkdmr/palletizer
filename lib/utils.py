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