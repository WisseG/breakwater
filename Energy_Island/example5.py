import pandas as pd

import breakwater as bw
from Cubipod import Cubipod
from Wave_rose import Waverose
"""
How to use the C02 Footprint functions for the Revetment at Energy Island
"""

#The standard grading for Energy Island
grading_EI = {
    "LMA_60/300": {"M50": [120, 190], "NLL": 60, "NUL": 300},
    "HMA_300/1000": {"M50": [540, 690], "NLL": 300, "NUL": 1000},
    "HMA_1000/3000": {"M50": [1700, 2100], "NLL": 1000, "NUL": 3000},
    "HMA_3000/6000": {"M50": [4200, 4800], "NLL": 3000, "NUL": 6000},
}

#Wave conditions for a certain direciton
condition1 = Waverose()
Hm0, Tp, Tm = condition1.wave_direction(direction= '090')

battjes = bw.BattjesGroenendijk(Hm0= Hm0, h=27.71, slope_foreshore=(1, 100))
H2_per = battjes.get_Hp(0.02)

# define a limit state with hydraulic parameters, and the allowed damage
ULS = bw.LimitState(
    h=27.71,
    Hm0=Hm0,
    H2_per=H2_per,
    Tp=Tp,
    Tm=Tm,
    T_m_min_1= (Tp + Tm) / 2,
    Sd=5,
    Nod=4,
    q=10,
    label="ULS",
)

NEN = bw.RockGrading(rho=2650, grading= grading_EI)  # standard gradings

cubipod = Cubipod()

# Design the Energy Island case with Cubipods. Filter rule for single layer armoured Cubipod -> W/20

configs = bw.Configurations(
    structure=["CRMR"],
    LimitState=ULS,
    rho_w=1025,
    slope_foreshore=(1, 100),
    Grading=NEN,
    slope=(1, 3),
    B=(5, 8, 4),
    Dn50_core=(3, 4, 5),
    N=2100,
    ArmourUnit=cubipod,
    filter_rule="XblocPlus",
)

material_cost = {
    "type": "Material",
    "price": {
        "LMA_60/300": 9000,
        "HMA_300/1000": 10000,
        "HMA_1000/3000": 11000,
        "HMA_3000/6000": 12000,
    },
    "core_price": 400,
    "unit_price": 500,
    "concrete_price": 600,
    "fill_price": 700,
    "transport_cost": 1000,
    "Investment": None,
    "length": None,
}

c02_cost = {
    "type": "C02",
    "price": {
        "LMA_60/300": 50,
        "HMA_300/1000": 60,
        "HMA_1000/3000": 70,
        "HMA_3000/6000": 80,
    },
    "core_price": 100,
    "unit_price": 300,
    "concrete_price": 50,
    "fill_price": 30,
    "transport_cost": None,
    "Investment": None,
    "length": None,
}

cost_dicts = [material_cost, c02_cost]

for i in range(len(cost_dicts)):
    NEN.add_cost(type=cost_dicts[i]["type"], cost=cost_dicts[i]["price"])
    configs.add_cost(
        type=cost_dicts[i]["type"],
        core_price=cost_dicts[i]["core_price"],
        unit_price=cost_dicts[i]["unit_price"],
        concrete_price=cost_dicts[i]["concrete_price"],
        fill_price=cost_dicts[i]["fill_price"],
        transport_cost=cost_dicts[i]["transport_cost"],
        investment=cost_dicts[i]["Investment"],
        length=cost_dicts[i]["length"],
    )
    configs.cost_influence(cost_dicts[i]["type"])

save = False

if save:
    # check if, and which, warnings have been encountered
    configs.show_warnings()

    # export concepts to the design explorer
    configs.to_design_explorer(
        params=["c02_cost", "material_cost", "slope", "class armour", "B", "Rc"]
    )

    # save the configs to a .breakwaters file
    configs.to_breakwaters("example3")
