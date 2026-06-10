include "globals.mzn";   % for global_cardinality, diffn

%% ==== Parameters ====
par int: n_boxes;
par int: boxes_per_row;
par int: pallet_rows;
par int: boxes_x_dim;
par int: grip_size;

par int: max_pkble_boxes = (grip_size + boxes_x_dim) div boxes_x_dim;
par int: chunks_per_row = (boxes_per_row + max_pkble_boxes - 1) div max_pkble_boxes;
par int: n_chunks       = pallet_rows * chunks_per_row;

%% ==== chunking ====
array[1..n_chunks] of var 1..n_boxes: chunk_start;
array[1..n_chunks] of var 1..max_pkble_boxes: chunk_len;

constraint chunk_start[1] = 1;

constraint forall(n in 2..n_chunks)(
  chunk_start[n] = chunk_start[n-1] + chunk_len[n-1]
);

constraint chunk_start[n_chunks] + chunk_len[n_chunks] - 1 = n_boxes;

%% ==== placement ====
array[1..n_chunks] of var 1..pallet_rows: y_row;
array[1..n_chunks] of var 1..boxes_per_row: x_start;

constraint forall(g in 1..n_chunks)(
  x_start[g] + chunk_len[g] - 1 <= boxes_per_row
);

constraint diffn(x_start, y_row, chunk_len, [1 | c in 1..n_chunks]);

constraint global_cardinality(y_row,
  [r | r in 1..pallet_rows],
  [chunks_per_row | r in 1..pallet_rows]);

%% ==== Drop collision rule ====
array[1..n_chunks] of var 0..1: plate;
array[1..n_chunks] of var 0..pallet_rows+1: target;

constraint forall(n in 1..n_chunks)(
  target[n] = y_row[n] - 1 + 2*plate[n]
);

constraint forall(curr_chunk in 2..n_chunks, pred_chunk in 1..curr_chunk-1)(
  not(
       y_row[pred_chunk] = target[curr_chunk]
    /\ x_start[pred_chunk] < x_start[curr_chunk]  + chunk_len[curr_chunk]
    /\ x_start[curr_chunk]  < x_start[pred_chunk] + chunk_len[pred_chunk]
  )
);

%% ==== Search ====
par int: branch_ub = max([pallet_rows, boxes_per_row, max_pkble_boxes]);
array[1..4*n_chunks] of var 0..branch_ub: branch;

constraint forall(n in 1..n_chunks)(
  branch[4*n-3] = y_row[n]                       /\
  branch[4*n-2] = max_pkble_boxes - chunk_len[n] /\
  branch[4*n-1] = x_start[n]                     /\
  branch[4*n]   = 1 - plate[n]
);

solve :: int_search(branch, input_order, indomain_min) satisfy;