include "globals.mzn";

par int: n_packs = 187;

par int: packs_x_dim = 70;
par int: packs_along_x = 11;
par int: packs_along_y = 17;
par int: grip_size = 3 * packs_x_dim;

par int: max_pkble_packs = (grip_size + packs_x_dim) div packs_x_dim;
par int: n_groups = (n_packs + max_pkble_packs - 1) div max_pkble_packs;

array[1..n_groups, 1..max_pkble_packs] of var 0..n_packs: groups;

% Il primo elemento deve essere 1
constraint groups[1,1] = 1;

% Solo l'ultima riga può contenere 0
constraint
  forall(i in 1..n_groups-1, j in 1..max_pkble_packs) (
    groups[i,j] != 0
  );

%% to avoid this  | 185, 187,   0, 186
constraint groups[n_groups,max_pkble_packs] = n_packs \/ groups[n_groups,max_pkble_packs] = 0;


% Ogni valore 1..n_packs compare esattamente una volta
constraint
  forall(v in 1..n_packs) (
    count(array1d(groups), v) = 1
  );

% Ordinamento strettamente crescente nelle righe,
% con eventuali 0 solo in coda nell'ultima riga
constraint
  forall(i in 1..n_groups, j in 1..max_pkble_packs-1) (
    (groups[i,j] < groups[i,j+1] /\ groups[i,j+1] != 0) \/
    (i = n_groups /\ groups[i,j+1] = 0)
  );

% Ordinamento tra righe
constraint
  forall(i in 2..n_groups) (
    groups[i,1] > groups[i-1,max_pkble_packs]
  );

solve satisfy;