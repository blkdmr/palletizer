include "globals.mzn";

par int: n_packs = 187;
par int: packs_x_dim = 70;
par int: packs_along_x = 11;
par int: packs_along_y = 17;
par int: grip_size = 3 * packs_x_dim;
par int: max_pkble_packs = (grip_size + packs_x_dim) div packs_x_dim; % = 4

% Correct n_groups: each x-row needs ceil(packs_along_x / max_pkble_packs) groups
par int: n_groups = packs_along_y * ((packs_along_x + max_pkble_packs - 1) div max_pkble_packs);
% = 17 * 3 = 51

array[1..n_groups] of var 1..n_packs: group_start;
array[1..n_groups] of var 1..max_pkble_packs: group_len;

% First group starts at pack 1
constraint group_start[1] = 1;

% Groups are consecutive — no gaps, no overlaps
constraint forall(i in 1..n_groups-1)(
  group_start[i+1] = group_start[i] + group_len[i]
);

% All packs are covered
constraint group_start[n_groups] + group_len[n_groups] - 1 = n_packs;

% x-boundary: first and last pack of a group must be in the same x-row
constraint forall(i in 1..n_groups)(
  (group_start[i] - 1) div packs_along_x =
  (group_start[i] + group_len[i] - 2) div packs_along_x
);

solve satisfy;