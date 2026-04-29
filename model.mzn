include "globals.mzn";

%% ── Parameters ────────────────────────────────────────────────────────────────
par int: n_boxes;
par int: boxes_x_dim;
par int: boxes_along_x;
par int: boxes_along_y;
par int: grip_size;

par int: max_pkble_boxes  = (grip_size + boxes_x_dim) div boxes_x_dim;
par int: groups_per_row   = (boxes_along_x + max_pkble_boxes - 1) div max_pkble_boxes;
par int: n_groups         = boxes_along_y * groups_per_row;

%% ── Part 1: grouping ──────────────────────────────────────────────────────────
array[1..n_groups] of var 1..n_boxes:         group_start;
array[1..n_groups] of var 1..max_pkble_boxes: group_len;

% First group starts at pack 1
constraint group_start[1] = 1;

% Groups are contiguous — no gaps, no overlaps
constraint forall(i in 1..n_groups - 1)(
  group_start[i + 1] = group_start[i] + group_len[i]
);

% All boxes covered
constraint group_start[n_groups] + group_len[n_groups] - 1 = n_boxes;

% x-boundary: all boxes in a group must lie in the same x-row
constraint forall(i in 1..n_groups)(
  (group_start[i] - 1)                    div boxes_along_x =
  (group_start[i] + group_len[i] - 2)     div boxes_along_x
);

%% ── Part 2: neighbor computation (pure par, from group index structure) ───────
%
%  Within each y-row, groups are numbered consecutively.
%  Group g occupies position  (g-1) mod groups_per_row  within its row.
%  Left  neighbor = g-1  unless g is the leftmost in its row
%  Right neighbor = g+1  unless g is the rightmost in its row
%
array[1..n_groups] of par int: left_neighbor =
  [ if (g - 1) mod groups_per_row > 0
    then g - 1
    else 0
    endif
  | g in 1..n_groups ];

array[1..n_groups] of par int: right_neighbor =
  [ if (g - 1) mod groups_per_row < groups_per_row - 1
    then g + 1
    else 0
    endif
  | g in 1..n_groups ];

%% ── Part 2: drop scheduling ───────────────────────────────────────────────────
array[1..n_groups] of var 1..n_groups: drop_order; % at which step group g is placed
array[1..n_groups] of var 0..1:        plate;       % 0 = left plate opens, 1 = right

% drop_order is a permutation of 1..n_groups
constraint alldifferent(drop_order);

% When releasing group g, the opening plate must face a free direction:
%   plate=0 (left):  no left neighbor, OR left neighbor not yet placed
%   plate=1 (right): no right neighbor, OR right neighbor not yet placed
constraint forall(g in 1..n_groups)(
  (plate[g] = 0 /\
    (left_neighbor[g]  = 0 \/ drop_order[left_neighbor[g]]  > drop_order[g]))
  \/
  (plate[g] = 1 /\
    (right_neighbor[g] = 0 \/ drop_order[right_neighbor[g]] > drop_order[g]))
);

solve satisfy;