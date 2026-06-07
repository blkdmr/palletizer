include "globals.mzn";   % for global_cardinality, diffn

%% ==== Parameters ====
par int: n_boxes;
par int: boxes_x_dim;
par int: boxes_per_row;
par int: pallet_rows;
par int: grip_size;

par int: max_pkble_boxes = (grip_size + boxes_x_dim) div boxes_x_dim; % max boxes in one pick

par int: chunks_per_row = (boxes_per_row + max_pkble_boxes - 1) div max_pkble_boxes; % picks per row
par int: n_chunks       = pallet_rows * chunks_per_row;

%% ==== chunking ====
array[1..n_chunks] of var 1..n_boxes: chunk_start;
array[1..n_chunks] of var 1..max_pkble_boxes: chunk_len;

constraint chunk_start[1] = 1;

constraint forall(g in 2..n_chunks)(
  chunk_start[g] = chunk_start[g-1] + chunk_len[g-1]
);
constraint chunk_start[n_chunks] + chunk_len[n_chunks] - 1 = n_boxes;

%% ==== placement ====
array[1..n_chunks] of var 1..pallet_rows: y_row;
array[1..n_chunks] of var 1..boxes_per_row: x_start;

% Each pick stays within the pallet width.
constraint forall(g in 1..n_chunks)(
  x_start[g] + chunk_len[g] - 1 <= boxes_per_row
);

% No two picks overlap on the pallet grid (chunks are 1 row tall).
constraint diffn(x_start, y_row, chunk_len, [1 | g in 1..n_chunks]);

% Each row holds exactly chunks_per_row picks.
constraint global_cardinality(y_row,
  [r | r in 1..pallet_rows],
  [chunks_per_row | r in 1..pallet_rows]);

%% ==== Drop collision rule ====
array[1..n_chunks] of var 0..1: plate;   % 0 = open upward (row r-1), 1 = downward (row r+1)
array[1..n_chunks] of var 0..pallet_rows+1: target;

constraint forall(g in 1..n_chunks)(
  target[g] = y_row[g] - 1 + 2*plate[g]
);

constraint forall(g in 2..n_chunks, g2 in 1..g-1)(
  not(
       y_row[g2] = target[g]
    /\ x_start[g2] < x_start[g]  + chunk_len[g]
    /\ x_start[g]  < x_start[g2] + chunk_len[g2]
  )
);

%% ==== Search ====
par int: branch_ub = max([pallet_rows, boxes_per_row, max_pkble_boxes]);
array[1..4*n_chunks] of var 0..branch_ub: branch;

constraint forall(g in 1..n_chunks)(
  branch[4*g-3] = y_row[g]                       /\
  branch[4*g-2] = max_pkble_boxes - chunk_len[g] /\
  branch[4*g-1] = x_start[g]                     /\
  branch[4*g]   = 1 - plate[g]
);

solve :: int_search(branch, input_order, indomain_min)
      satisfy;