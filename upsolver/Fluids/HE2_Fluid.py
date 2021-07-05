import numpy as np
from upsolver.Hydraulics.Properties.Mishenko import Mishenko, from_oil_params
from upsolver.Tools.HE2_ABC import HE2_ABC_Fluid, oil_params
from upsolver.Tools.HE2_Logger import getLogger
logger = getLogger(__name__)


class HE2_DummyWater(HE2_ABC_Fluid):
    def __init__(self):
        self.rho_wat_kgm3 = 1000
        self.mu_wat_cp = 1

    def calc(self, P_bar, T_C):
        pass


class HE2_BlackOil(HE2_ABC_Fluid):
    def __init__(self, oil_params: oil_params):
        # check_for_nan(**oil_params)
        self.oil_params = oil_params
        self.CurrentLiquidDensity_kg_m3 = (self.oil_params.oildensity_kg_m3 * (1 - self.oil_params.volumewater_percent / 100) +
                                                      self.oil_params.waterdensity_kg_m3 * self.oil_params.volumewater_percent / 100)


    def calc(self, P_bar, T_C, X_kgsec, IntDiameter=None):
        P_for_PVT = max(abs(P_bar), 0.75)
        calc_params = self.oil_params

        tubing = {"IntDiameter": IntDiameter} if IntDiameter else None
        temp_mishenko = from_oil_params(P_for_PVT, T_C, X_kgsec, calc_params=calc_params, tubing=tubing)
        #Side effects
        self.CurrentLiquidDensity_kg_m3 = temp_mishenko.CurrentLiquidDensity_kg_m3
        self.CurrentOilViscosity_Pa_s = temp_mishenko.CurrentOilViscosity_Pa_s
        #Return for pressure gradient calculation
        return temp_mishenko


def check_all_are_the_same(arr, msg):
    max_arr = max(arr)
    if min(arr) != max_arr:
        logger.error(msg)
        raise NotImplementedError
    return max_arr


def make_fluid_vectors(fluids):
    ops = [fl.oil_params for fl in fluids]
    oil_ro_vec = np.array([op.oildensity_kg_m3 for op in ops])
    wat_ro_vec = np.array([op.waterdensity_kg_m3 for op in ops])
    gas_ro_vec = np.array([op.gasdensity_kg_m3 for op in ops])
    gf_vec = np.array([op.gasFactor for op in ops])
    wc_vec = np.array([op.volumewater_percent for op in ops])*0.01
    owg_mix_pseudo_density_vec = oil_ro_vec * (1 - wc_vec) + wat_ro_vec * wc_vec + gas_ro_vec * (1 - wc_vec) * gf_vec

    Q_owg_vec = 1 / owg_mix_pseudo_density_vec
    Qo_vec = (1 - wc_vec) * Q_owg_vec
    Qw_vec = wc_vec * Q_owg_vec
    Qg_vec = (1 - wc_vec) * gf_vec* Q_owg_vec
    Xo_vec = Qo_vec * oil_ro_vec
    Xw_vec = Qw_vec * wat_ro_vec
    Xg_vec = Qg_vec * gas_ro_vec

    return Qo_vec, Qw_vec, Qg_vec, Xo_vec, Xw_vec, Xg_vec


def dot_product(xs_vec, fluids, fluid_vectors=None, oil_ro = None, wat_ro = None, gas_ro = None, wc = None, gf = None) -> HE2_BlackOil:
    """
    :return: new fluid instance, dot product Xs and fluids
    """

    k = xs_vec.argmax()
    if xs_vec[k] == 1:
        op = fluids[k].oil_params
        return HE2_BlackOil(op)

    if fluid_vectors is None:
        fluid_vectors = make_fluid_vectors(fluids)
    _Qo_vec, _Qw_vec, _Qg_vec, _Xo_vec, _Xw_vec, _Xg_vec = fluid_vectors

    Qo, Qw, Qg = 0, 0, 0
    if oil_ro is None or wc is None or gf is None:
        Qo_vec = xs_vec * _Qo_vec
        Qo = Qo_vec.sum()
    if wat_ro is None or wc is None:
        Qw_vec = xs_vec * _Qw_vec
        Qw = Qw_vec.sum()
    if gas_ro is None or gf is None:
        Qg_vec = xs_vec * _Qg_vec
        Qg = Qg_vec.sum()

    if oil_ro is None:
        Xo_vec = xs_vec * _Xo_vec
        Xo = Xo_vec.sum()
        oil_ro = Xo / Qo
    if wat_ro is None:
        Xw_vec = xs_vec * _Xw_vec
        Xw = Xw_vec.sum()
        wat_ro = Xw / Qw
    if gas_ro is None:
        Xg_vec = xs_vec * _Xg_vec
        Xg = Xg_vec.sum()
        gas_ro = Xg / Qg
    if wc is None:
        wc = Qw / (Qo + Qw)
    if gf is None:
        gf = Qg / Qo

    op0 = fluids[0].oil_params
    sat_P = op0.sat_P_bar
    plast_T = op0.plastT_C
    oil_Visc = op0.oilviscosity_Pa_s
    Volume_keff = op0.volumeoilcoeff
    rez_oil_params = oil_params(sat_P, plast_T, gf, oil_ro, wat_ro, gas_ro, oil_Visc, wc*100, Volume_keff)
    rez = HE2_BlackOil(rez_oil_params)

    return rez


def gimme_dummy_oil_params(volumeWater=50):
    rez = oil_params(sat_P_bar = 66.7, plastT_C = 84, gasFactor = 39, oildensity_kg_m3 = 826,
                     waterdensity_kg_m3 = 1015, gasdensity_kg_m3 = 1, oilviscosity_Pa_s = 35e-3, volumewater_percent = volumeWater, volumeoilcoeff = 1.015)
    return rez


def gimme_dummy_BlackOil(VolumeWater=50):
    oil_params = gimme_dummy_oil_params(volumeWater=VolumeWater)
    rez = HE2_BlackOil(oil_params)
    return rez


if __name__ == '__main__':
    fl = HE2_DummyWater()
    fl.calc(100, 100)
    print(fl.rho_wat_kgm3)