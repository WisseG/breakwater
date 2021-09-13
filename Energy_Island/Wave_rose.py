class Waverose:
    # Wave conditions from different direcitons

    def __init__(self):
        Hm0_315, Tp_315, Tm_315 = (
            14.2,
            17.6,
            13.5,
        )  # 1/10.000 yrs from 315 degrees North
        Hm0_270, Tp_270, Tm_270 = (
            13.9,
            16.4,
            12.3,
        )  # 1/10.000 yrs from 270 degrees North
        Hm0_225, Tp_225, Tm_225 = (
            12.7,
            14.4,
            11.1,
        )  # 1/10.000 yrs from 225 degrees North
        Hm0_180, Tp_180, Tm_180 = (
            11.2,
            13.7,
            10.6,
        )  # 1/10.000 yrs from 180 degrees North
        Hm0_135, Tp_135, Tm_135 = (
            8.40,
            10.5,
            8.30,
        )  # 1/10.000 yrs from 135 degrees North
        Hm0_090, Tp_090, Tm_090 = (
            7.60,
            9.40,
            8.00
        )   # 1/10.000 yrs from 90 degrees North
        Hm0_045, Tp_045, Tm_045 = (
            10.0,
            12.3,
            9.40
        )   # 1/10.000 yrs from 45 degrees North
        Hm0_000, Tp_000, Tm_000 = (
            9.60,
            13.8,
            9.70
        )   # 1/10.000 yrs from 0 degrees North

        self.wave_conditions = {
            "315": {"Hm0": Hm0_315, "Tp": Tp_315, "Tm": Tm_315},
            "270": {"Hm0": Hm0_315, "Tp": Tp_315, "Tm": Tm_315},
            "225": {"Hm0": Hm0_225, "Tp": Tp_225, "Tm": Tm_225},
            "180": {"Hm0": Hm0_180, "Tp": Tp_180, "Tm": Tm_180},
            "135": {"Hm0": Hm0_135, "Tp": Tp_135, "Tm": Tm_135},
            "090": {"Hm0": Hm0_090, "Tp": Tp_090, "Tm": Tm_090},
            "045": {"Hm0": Hm0_045, "Tp": Tp_045, "Tm": Tm_045},
            "000": {"Hm0": Hm0_000, "Tp": Tp_000, "Tm": Tm_000},
        }

    def wave_direction(self, direction):
        return (
            self.wave_conditions[direction]["Hm0"],
            self.wave_conditions[direction]["Tp"],
            self.wave_conditions[direction]["Tm"],
        )
