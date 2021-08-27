"""
Breakwater Design with Python
"""

__version__ = "v1.0.2e"
__author__ = "S. Winkel"

from .caisson import Caisson
from .conditions import LimitState

# import hydraulic conditions
from .core.battjes import BattjesGroenendijk
from .core.goda import goda_wave_heights

# import the soil
from .core.soil import Soil

# file loader
# import breakwaters
from .design import Configurations, read_breakwaters, read_configurations

# interactive design tool (tkinter app)
from .interactive import interactive_design

# excel input
# import materials
from .material import (
    ConcreteArmour,
    RockGrading,
    Xbloc,
    XblocPlus,
    read_grading,
    read_units,
)
from .rubble import ConcreteRubbleMound, RockRubbleMound, RubbleMound
from .utils.input_generator import generate_excel
from .utils.wave import dispersion, shoaling_coefficient
