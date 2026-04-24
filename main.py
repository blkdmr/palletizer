from minizinc import Model, Solver, Instance
from lib.utils import gen_pallet_info
def solve():
    
    model = Model("model.mzn")
    solver = Solver.lookup("gecode")
    instance = Instance(solver, model)

    pack_x = 70
    pack_y = 70
    pallex_x_dim = 800
    pallet_y_dim = 1200

    grip_size = 3 * pack_x

    pallet_info = gen_pallet_info(pack_x, pack_y, pallex_x_dim, pallet_y_dim)

    print(f"MAX: {pallet_info["n_packs"]}")    
    # Set MiniZinc parameters from Python
    instance["n_packs"] = pallet_info["n_packs"]
    instance["packs_x_dim"] = pack_x
    instance["packs_along_x"] = pallet_info["packs_along_x"]
    instance["packs_along_y"] = pallet_info["packs_along_y"]
    instance["grip_size"] = grip_size

    result = instance.solve()

    print(result["groups"])


if __name__ == "__main__":
    solve()