import numpy as np

from breakwater.core.stability import xi_critical

def z_vdmeer(Cpl, Cs, P, Sd, N, T, alpha, Hs, rho_w, rho_s, dn50):
    """
    Z-function for the Vd Meer equation (Van der Meer, 1988)

    Parameters
    ----------
    Cpl: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    Cs: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    P: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    Sd: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    N: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    T: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    alpha: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    Hs: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    rho_w: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    rho_s: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    dn50: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.

    Returns
    -------
    numpy.array
    """
    xi_cr = xi_critical(Cpl= Cpl, Cs= Cs, P= P, alpha= alpha)

    L0 = (9.81 * T**2) / (2 * np.pi)
    xi_0 = np.tan(alpha) / (np.sqrt(Hs / L0))

    delta = (rho_s - rho_w) / rho_w
    Z = np.zeros(len(xi_cr))

    for i in range(len(xi_cr)):
        if xi_0[i] < xi_cr[i]:
            Z[i] = Cpl[i] * P[i]**0.18 * (Sd[i] / np.sqrt(N[i]))**0.2 * xi_0[i]**(-0.5) - Hs[i] / (delta[i] * dn50[i])

        else:
            Z[i] = Cs[i] * P[i]**-0.13 * (Sd[i] / np.sqrt(N[i]))**0.2 * xi_0[i]**P[i] * np.sqrt(1/np.tan(alpha[i])) - Hs[i] / \
                   (delta[i] * dn50[i])

    return Z

def z_hudson(Hs, Kd, alpha, rho_w, rho_s, dn50):
    """
    Z-function for the hudson equation (Hudson, 1959)

    Parameters
    ----------
    Hs: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    Kd: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    alpha: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    rho_w: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    rho_s: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.
    dn50: numpy.array, float, int
        numpy.array with random samples from a distribution. float or int for a deterministic value.

    Returns
    -------
    numpy.array
    """
    delta = (rho_s - rho_w) / rho_w
    Z = (Kd * (1 / np.tan(alpha)))**(1/3) - Hs / (delta * dn50)
    return Z

def z_overtopping():
    pass
