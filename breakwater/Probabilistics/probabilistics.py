import numpy as np
import pandas as pd

from breakwater.Probabilistics.zfunctions import z_vdmeer, z_hudson
from breakwater.utils.exceptions import InputError

def MonteCarlo(Pf, zfunc, **kwargs):
    """
    Perform a crude Monte Carlo simulation

    Parameters
    ----------
    Pf: float
        The failure probability over the lifetime of the structure
    kwargs: np.ndarray
        random samples. For example numpy.random.normal(..., ..., ...)
    zfunc: str
        'VdMeer', 'Hudson', 'Overtopping'
    Returns
    -------
    str

    """

    if zfunc == 'VdMeer':
        Z = z_vdmeer(**kwargs)
    elif zfunc == 'Hudson':
        Z = z_hudson(**kwargs)
    else:
        raise InputError(f'{zfunc} is not a z-function. Choose one of: "VdMeer", "Hudson" or "Overtopping"')

    Zabove0 = np.where(Z > 0)

    Pf_mc = len(Zabove0) / len(Z)

    return pd.DataFrame(data={'Pf': [Pf], 'Pf_mc': [Pf_mc], 'Pf < Pf_mc': [Pf_mc < Pf]})


def FORM():
    pass
