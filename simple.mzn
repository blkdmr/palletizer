include "globals.mzn";

%% ==== Parameters ====
par int: n_boxes;
par int: boxes_x_dim;
par int: boxes_along_x;
par int: boxes_along_y;
par int: grip_size;

par int: max_pkble_boxes = (grip_size + boxes_x_dim) div boxes_x_dim;

par int: chunks_per_row = (boxes_along_x + max_pkble_boxes - 1) div max_pkble_boxes;
par int: n_chunks = boxes_along_y * chunks_per_row;

%% ==== chunking strategy ====
array[1..n_chunks] of var 1..max_pkble_boxes: chunk_len;
array[1..n_chunks] of var 1..n_boxes: chunk_start;

constraint chunk_start[1] = 1;

constraint forall(i in 1..n_chunks - 1)(
  chunk_start[i + 1] = chunk_start[i] + chunk_len[i]
);
constraint chunk_start[n_chunks] + chunk_len[n_chunks] - 1 = n_boxes;

%% ==== chunk placement on the pallet ====
array[1..n_chunks] of var 1..boxes_along_y: y_row;
array[1..n_chunks] of var 1..boxes_along_x: x_start;

% each chunk fits inside its assigned row
constraint forall(g in 1..n_chunks)(
  x_start[g] + chunk_len[g] - 1 <= boxes_along_x
);

% no two chunks overlap on the pallet grid
constraint forall(g1, g2 in 1..n_chunks where g1 < g2)(
  y_row[g1] != y_row[g2]                              \/
  x_start[g1] + chunk_len[g1] <= cx_start[g2]          \/
  x_start[g2] + chunk_len[g2] <= x_start[g1]
);

% each pallet row is exactly filled
constraint forall(r in 1..boxes_along_y)(
  sum(g in 1..n_chunks)(bool2int(y_row[g] = r) * chunk_len[g]) = boxes_along_x
);

%% ==== open plate choice ====
array[1..n_chunks] of var 0..1: plate;

constraint forall(g, g2 in 1..n_chunks where g != g2)(
  (
    ( (plate[g] = 0 /\ y_row[g2] = y_row[g] - 1) \/
      (plate[g] = 1 /\ y_row[g2] = y_row[g] + 1) )
    /\
    x_start[g2] < x_start[g] + chunk_len[g] /\
    x_start[g2] + chunk_len[g2] > x_start[g]
  )
  -> g2 > g
);

solve satisfy;