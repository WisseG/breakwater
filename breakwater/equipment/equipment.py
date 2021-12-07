import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

class Equipment:
    """
    General equipment class

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}.
        Can be set to None if already encorporated in price in design type
    waterlvl: float
        At which water depth is the equipment used
    """

    def __init__(
        self, name, design_type, waterlvl, equipment_cost = None, mobilisation_cost= None
    ):

        if mobilisation_cost is None:
            mobilisation_cost = {'cost': 0, 'CO2': 0}

        if equipment_cost is None:
            equipment_cost = {'cost': 0, 'CO2': 0}

        self.name = name
        self.design_type = design_type
        self.mobilisation_cost = mobilisation_cost
        self.equipment_cost = equipment_cost
        self.waterlvl = waterlvl

    def location_equipment(
        self, *args, xpoint, section_coords, equip, y_installation_waterdepth=0, height=0, ymax=0
    ):

        """
        For Excavator, cranes and barges the location of the equipment is important.
        But dependent if we're constructing from land, or on the left or right side
        of the breakwater this location differs.

        Parameters
        ----------
        args: iterable
            variables which change the xlocation of the equipment. Can be an offset
            margin or due to the installation_waterdepth
        xpoint: float
            x-coordinate from which which has to be changed to the xloc_equip
        ymax: float
            maximum builded y-coordinate
        section_coords: list
            list of tuples of coordinates of to be build section
        equip: object
            which equipment are we using. One of Excavator, Crane or Barge.
        y_installation_waterdepth: float
            water level minus installation_waterdepth. Only when we're looking at Barge
        height: float
            height of the barge

        Returns
        -------
        tuple
        """

        x_section, y_section = zip(*section_coords)
        x_section, y_section = np.array(x_section), np.array(y_section)

        flip = False

        # In this case we're building from the water
        if isinstance(equip, Barge):
            yloc_equip = y_installation_waterdepth + height
            if all(x_section >= 0):
                # on the right side of the structure so move to the right
                xloc_equip = xpoint + sum(args)
                flip = True
            else:
                # on the left side of the structure so move to the right, xpoint is a positive value but symmetric
                xloc_equip = -xpoint - sum(args)

        # In this case we're building from land into the depth or on same level. In the latter the location does not matter
        else:
            yloc_equip = ymax
            if all(x_section >= 0):
                # on the right side of structure so move to left on top
                xloc_equip = xpoint - sum(args)
            else:
                # on the left side of structure so move to right on top, xpoint is a positive value but symmetric
                xloc_equip = -xpoint + sum(args)
                flip = True

        return xloc_equip, yloc_equip, flip

    def get_price(self, layer, grading_layer, key):
        """
        What is the price per cubic meter to construct for a given equipment and grading

        Parameters
        ----------
        layer: str
            name of the layer which is build
        grading_layer: str
            grading of the layer which is build
        key: str
            Either 'cost' or 'CO2'
        Returns
        -------
        float
        """

        # In this case the production rate, transport is already encorporated in the price [EUR/m3]
        if 'cost' in  self.design_type[grading_layer].keys():
            return self.design_type[grading_layer][key]

        # Production rate and price of equipment are split [EUR/hr] / [m3/hr] = [EUR/m3]
        else:
            return self.equipment_cost[key] / self.design_type[grading_layer]['production_rate']

    def get_production_rate(self, layer, grading_layer):

        """
        What is the time [hrs] per cubic meter to construct for a given equipment and grading

        Parameters
        ----------
        layer: str
            name of the layer which is build
        grading_layer: str
            grading of the layer which is build
        Returns
        -------
        float
        """
        #In this case the production rate is encorporated in the price
        if 'production_rate' not in self.design_type[grading_layer]:
            self.design_type[grading_layer]["production_rate"] = 1
            raise UserWarning('There is no value given for the production rate and is therefore set to 1. \n'
                              'The duration of installation is not reliable')

        return self.design_type[grading_layer]["production_rate"]


class Truck(Equipment):
    """
    Truck class (land based equipment)
    Truck type of equipment such as wheel loaders and dump trucks

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    waterlvl: float
        At which water depth is the equipment used
    required_length: float
        minimum length of the level the equipment is standing on.
    h_dry: int
        Margin which account for wave overtopping so the equipment is not damaged.
    """

    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        required_length,
        h_dry,
        type = 'land',
        mobilisation_cost = None,
        equipment_cost = None,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        self.h_dry = h_dry
        self.waterlvl = waterlvl
        self.type = type
        self.required_length = required_length

    def install(self, layer, grading_layer, ymax, section_coords, length_top, plot=False):
        """

        Parameters
        ----------
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        ymax: float
            max height installed section
        section_coords: list
            coordinates of the section
        revetment: bool
            is the structure a revetment
        plot: bool
            Do we want to make a plot. Default is False
        Returns
        -------
        bool
        """

        install = False
        x, y = list(zip(*section_coords))
        y_start = min(y)

        self.level = max([(y_start - self.waterlvl), (ymax - self.waterlvl)])

        if (
            grading_layer in self.design_type.keys()
        ):
            if (self.level >= self.h_dry and length_top >= self.required_length):
                install = True

        if plot:
            self.plot(
                section_coords=section_coords,
                layer=layer,
                grading_layer=grading_layer,
                ymax=ymax,
                install=install,
                top_length= length_top
            )

        return install

    def plot(self, section_coords, layer, grading_layer, ymax, install, top_length):

        fig, ax = plt.subplots(figsize=(15, 5))
        ax.axhline(self.waterlvl, color="b", label="waterlevel")
        ax.arrow(
            0,
            self.waterlvl,
            dx=0,
            dy=self.h_dry,
            length_includes_head=True,
            color="red",
            head_width=0.3,
            label="h_dry",
        )
        plt.axhline(
            self.waterlvl + self.h_dry,
            color="brown",
            linestyle="--",
            label="HW + h_dry",
        )
        x, y = list(zip(*section_coords))
        ax.fill(x, y, color="brown", label=f"section {layer} ({grading_layer})")
        y_start = min(y)

        ax.set_title(f"Install = {install}\n", fontweight="bold")

        facecolor = "r"
        if install:
            facecolor = "g"
        plt.figtext(
            0.5,
            -0.1,
            f"1. The {self.name} can build the layer: {layer in self.design_type.keys() and grading_layer in self.design_type[layer].keys()} AND\n"
            f"2. y_start >= water level + h_dry: {(y_start - self.waterlvl) >= self.h_dry} OR\n"
            f"3. ymax >= water level + h_dry: {(ymax - self.waterlvl) >= self.h_dry} AND\n"
            f"4. required_length <= layer length {(top_length >= self.required_length)}",
            ha="center",
            fontsize=18,
            bbox={"facecolor": facecolor, "alpha": 0.5, "pad": 5},
        )

        ax.plot((min(x) + max(x)) / 2, ymax, "ko", label="ymax")

        fig.set_size_inches(15, 7, forward=True)
        plt.grid()
        plt.legend()

class PlateFeeder(Equipment):
    """
    Platefeeder class (land based equipment)
    Platefeeder type of equipment

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    top_installation: float
        max height at which it can install
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    waterlvl: float
        At which water depth is the equipment used
    h_dry: int
        Margin which account for wave overtopping so the equipment is not damaged.

    """

    def __init__(
        self,
        name,
        design_type,
        top_installation,
        waterlvl,
        h_dry,
        type = 'Land',
        mobilisation_cost = None,
        equipment_cost = None,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        self.h_dry = h_dry
        self.top_installation = top_installation
        self.type = type

    def install(self, layer, grading_layer, ymax, section_coords, level=None, plot=False):
        """

        Parameters
        ----------
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        y_start: int
            The lower limit of the to be constructed section
        ymax: int
            Maximum height which is already build
        plot: bool
            Do we want to make a plot. Default is False
        Returns
        -------
        bool
        """

        install = False
        x, y = list(zip(*section_coords))
        y_start = min(y)
        y_top = max(y)

        if level == None:
            level = max([(y_start - self.waterlvl), (ymax - self.waterlvl)])

        if (
            grading_layer in self.design_type.keys()
        ):
            if (level >= self.h_dry and (y_top <= level + self.top_installation)):
                install = True

        if plot:
            self.plot(
                section_coords=section_coords,
                layer=layer,
                grading_layer=grading_layer,
                ymax=ymax,
                install=install,
            )

        return install

    def plot(self, section_coords, layer, grading_layer, ymax, install):

        fig, ax = plt.subplots(figsize=(15, 5))
        ax.axhline(self.waterlvl, color="b", label="waterlevel")
        ax.arrow(
            0,
            self.waterlvl,
            dx=0,
            dy=self.h_dry,
            length_includes_head=True,
            color="red",
            head_width=0.3,
            label="h_dry",
        )
        plt.axhline(
            self.waterlvl + self.h_dry,
            color="brown",
            linestyle="--",
            label="HW + h_dry",
        )
        x, y = list(zip(*section_coords))
        ax.fill(x, y, color="brown", label=f"section {layer} ({grading_layer})")
        y_start = min(y)

        ax.set_title(f"Install = {install}\n", fontweight="bold")

        facecolor = "r"
        if install:
            facecolor = "g"
        plt.figtext(
            0.5,
            -0.1,
            f"1. The {self.name} can build the layer: {grading_layer in self.design_type.keys()} AND\n"
            f"2. y_start >= water level + h_dry: {(y_start - self.waterlvl) >= self.h_dry} OR\n"
            f"3. ymax >= water level + h_dry: {(ymax - self.waterlvl) >= self.h_dry}\n",
            ha="center",
            fontsize=18,
            bbox={"facecolor": facecolor, "alpha": 0.5, "pad": 5},
        )

        ax.plot((min(x) + max(x)) / 2, ymax, "ko", label="ymax")

        fig.set_size_inches(15, 7, forward=True)
        plt.grid()
        plt.legend()

class Excavator(Equipment):

    """
    Excavator class (Land based equipment)

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    waterlvl: float
        Water level at which the equipment is used
    required_length: float
        minimum length of the level the equipment is standing on.
    loading_chart: dict
        Give the coordinates with the according maximum stone weight from the loading chart,
        sorted from high to low y.
        {2: {'x': [14, 18, 22, ...] 'w': [9.6, 10, 12 ...]}, 1: {'x': [...], 'w': [...]}]
    h_dry: int
        Margin which account for wave overtopping so the equipment is not damaged.
    offset: int
        Margin from the edge at which the equipment is placed. 3 meter by default
    """

    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        loading_chart,
        h_dry,
        required_length,
        type = 'land',
        mobilisation_cost = None,
        equipment_cost = None,
        offset=3,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        self.loading_chart = loading_chart
        self.h_dry = h_dry
        self.offset = offset
        self.type = type
        self.required_length = required_length

    def rotate_loading_chart(self, points_chart, xloc_equip, yloc_equip):
        """
        The loading chart is defined by a Excavator moving on it's left side (2D) so needs to be flipped if it is not the case
        Parameters
        ----------
        points_chart: list
            x and y coordinates of the loading chart
        xloc_equip: float
            x-location of the equipment
        yloc_equip: float
            y-location of the equipment

        Returns
        -------
        tuple
        """

        # Rotate the chart 180 degrees around the location of the equipment
        x, y = np.array(list(zip(*points_chart)))
        dx = 2 * abs(x - xloc_equip)

        # Create a flipped polygon
        new_points = list(zip(x - dx, y))
        loading_polygon = Polygon(new_points)

        # Create a flipped loading chart
        loadingchart_flip = {}
        for key, items in self.loading_chart.items():
            dx2 = 2 * (np.array(items["x"]) - xloc_equip)

            loadingchart_flip[key + yloc_equip] = {
                "x": np.array(items["x"]) - dx2 - xloc_equip,
                "w": np.array(items["w"]),
            }

        return loading_polygon, loadingchart_flip

    def chart_location(self, xloc_equip, yloc_equip, x_section, y_section, flip=False):

        """
        Function to see whether the section falls within the reach of the loading chart
        and if so what the minimum weight is that can be placed.

        Parameters
        ----------
        xloc_equip: float
            x-coordinate of the equipment
        yloc_equip: float
            y-coordinate of the equipment
        x_section: list
            x-coordinates of the section
        y_section: list
            y_coordinates of the section
        flip: bool
            Decides if the chart and polygon have to be flipped. Default is False.

        Returns
        -------
        tuple
        """

        x_section = np.array(x_section)
        y_section = np.array(y_section)
        points_max, points_min = [], []
        ycoords = []

        # Create the loading polygon
        for key, items in self.loading_chart.items():
            xmin, xmax = max(items["x"]), min(items["x"])
            ycoords.append(key)
            points_min.append((xmin + xloc_equip, key + yloc_equip))
            points_max.append((xmax + xloc_equip, key + yloc_equip))

        points = sorted(points_max, key=lambda tup: tup[1])
        points_min = sorted(points_min, key=lambda tup: tup[1], reverse=True)
        points.extend(points_min)

        # Do we need to flip the polygon and chart?
        if flip:
            loading_polygon, loadingchart = self.rotate_loading_chart(
                points_chart=points, xloc_equip=xloc_equip, yloc_equip=yloc_equip
            )
        else:
            loading_polygon = Polygon(points)
            loadingchart = {}
            for key, items in self.loading_chart.items():

                loadingchart[key + yloc_equip] = {
                    "x": np.array(items["x"]) + xloc_equip,
                    "w": np.array(items["w"]),
                }

        section_polygon = Polygon(list(zip(x_section, y_section)))

        within = section_polygon.within(loading_polygon)

        return within, loading_polygon, loadingchart, section_polygon

    def install(
        self,
        layer,
        grading_layer,
        ymax,
        section_coords,
        xmax_top,
        mass,
        length_top,
        slope,
        plot=False,
        xloc_equip=None,
        yloc_equip=None,
    ):
        """

        Parameters
        ----------
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        ymax: int
            Maximum height which is already build
        section_coords: list
            The coordinates of the section
        xmax_top: float
            Upper left corner of the highest build layer
        mass: float
            Mass of the material of the layer
        length_top: float
            length of the the heighest build layer (at ymax)
        plot: bool
            Do we want to make a plot. Default is False
        Returns
        -------
        bool
        """

        install = False
        all_reach = []
        new_xequiploc = []
        x_section, y_section = zip(*section_coords)
        flip = False


        # In this case we're building from land into the depth and we need to define the location of the equipment
        if xloc_equip == None:
            xloc_equip, yloc_equip, flip = self.location_equipment(
                self.offset,
                xpoint=xmax_top,
                section_coords=section_coords,
                equip=self,
                ymax=ymax,
            )

        # From which depths in the chart do we need information regarding the mass, stored in ychart
        dy = np.unique(y_section)
        within, loading_polygon, load_chart, section_polygon = self.chart_location(
            xloc_equip, yloc_equip, x_section, y_section, flip
        )
        yload_chart = np.array(list(load_chart.keys()))
        ychart = []
        for d_y in dy:
            if d_y < 0:
                r = yload_chart[yload_chart <= d_y]
                if len(r) == 0:
                    return False
                else:
                    ychart.append(max(r))
            else:
                r = yload_chart[yload_chart >= d_y]
                if len(r) == 0:
                    return False
                else:
                    ychart.append(min(r))

        # What are the x-coordinates at the levels with smallest distance from xloc_equip
        xlevels = []
        for y in np.unique(y_section):
            if not flip:
                xm = min([x[0] for x in section_coords if x[1] == y])
            else:
                xm = max([x[0] for x in section_coords if x[1] == y])
            xlevels.append(xm)

        xy = list(zip(xlevels, ychart))
        for x, y in xy:
            masses = np.array(load_chart[y]["w"])
            # At what reaches do the masses suffice
            xreaches = np.array(load_chart[y]["x"])[np.where(masses >= mass)[0]]
            xdiff = abs(xreaches) - abs(x)


            # Are the reaches larger than the minimum distance between equipment and section (=x) AND
            # Is the distance which we will have to move back the equipment smaller than the length of the top layer
            if any(xdiff >= 0):
                all_reach.append(True)
                new_xequiploc.append(min(xdiff[np.where(xdiff >= 0)]))
            else:
                all_reach.append(False)

        y_start = min(y_section)

        # Minimum handle of grading for the layer
        if (
            grading_layer in self.design_type.keys()
        ):
            if (y_start - self.waterlvl) >= self.h_dry or (
                (ymax - self.waterlvl) >= self.h_dry and all(all_reach) and length_top >= self.required_length
            ):
                install = True

        if ymax > (self.waterlvl + self.h_dry) and not install and slope != (0,0):
            dy = ymax - (self.waterlvl + self.h_dry)
            V, H = slope
            xmax_top = xmax_top - H/V * dy
            install = self.install(
                layer= layer,
                grading_layer = grading_layer,
                ymax = self.waterlvl + self.h_dry,
                section_coords = section_coords,
                xmax_top = xmax_top,
                mass = mass,
                length_top = 2*abs(xmax_top), #symmetric so twice this distance
                slope = slope,
            )



        if plot:
            self.plot(
                xloc_equip=xloc_equip,
                yloc_equip=yloc_equip,
                length_top=length_top,
                x_section=x_section,
                y_section=y_section,
                section_coords=section_coords,
                ymax=ymax,
                new_xequiploc=new_xequiploc,
                loading_chart=load_chart,
                mass=mass,
                loading_polygon=loading_polygon,
                install=install,
                layer=layer,
                grading_layer=grading_layer,
                all_reach=all_reach,
            )
        return install

    def plot(
        self,
        xloc_equip,
        yloc_equip,
        length_top,
        x_section,
        y_section,
        section_coords,
        ymax,
        new_xequiploc,
        loading_chart,
        mass,
        loading_polygon,
        install,
        layer,
        grading_layer,
        all_reach,
    ):

        fig, ax = plt.subplots(figsize=(15, 7.5))
        plt.axhline(self.waterlvl, color="b", label="waterlevel")
        ax.plot(xloc_equip, yloc_equip, "ko", label=f"location {self.name}")
        x, y = loading_polygon.exterior.xy
        ax.fill(np.array(x), np.array(y), "r", alpha=0.3, label="loading_chart")
        y_start = min(y)

        ax.set_title(f"Install = {install}\n", fontweight="bold")

        if len(new_xequiploc) > 0:
            xloc_equip2, yloc_equip2, flip = self.location_equipment(
                max(new_xequiploc),
                xpoint=xloc_equip,
                section_coords=section_coords,
                equip=self,
                ymax=ymax,
            )

            ax.plot(xloc_equip2, yloc_equip, "ro", label=f"location {self.name}")
            (
                within,
                loading_polygon2,
                loading_chart,
                section_polygon2,
            ) = self.chart_location(
                xloc_equip2, yloc_equip, x_section, y_section, flip=flip
            )

            x, y = loading_polygon2.exterior.xy
            # if xloc_equip > xloc_equip2:
            #     ax.hlines(
            #         yloc_equip,
            #         xloc_equip,
            #         xloc_equip - length_top,
            #         linestyles="--",
            #         color="r",
            #         label="length top layer",
            #     )
            # else:
            #     ax.hlines(
            #         yloc_equip,
            #         xloc_equip,
            #         xloc_equip + length_top,
            #         linestyles="--",
            #         color="r",
            #         label="length top layer",
            #     )
            ax.fill(np.array(x), np.array(y), "g", label=f"loading_chart 2", alpha=0.8)

        ax.fill(np.array(x_section), y_section, "b", label=f"section (M = {mass})")
        for key, items in loading_chart.items():
            for j in range(len(loading_chart[key]["x"])):
                plt.plot(loading_chart[key]["x"][j], key, "ko", markersize=2)
                ax.annotate(
                    loading_chart[key]["w"][j],
                    (loading_chart[key]["x"][j], key),
                    fontsize=7,
                )

        facecolor = "r"
        if install:
            facecolor = "g"
        plt.figtext(
            0.5,
            -0.1,
            f"1. The {self.name} can build the layer: {grading_layer in self.design_type.keys()} AND\n"
            f"2. y_start >= water level + h_dry: {(y_start - self.waterlvl) >= self.h_dry} OR\n"
            f"3. ymax >= water level + h_dry: {(ymax - self.waterlvl) >= self.h_dry} AND\n"
            f"4. The {self.name} can reach the section: {all(all_reach)} AND\n"
            f"5. required_length <= layer length {(length_top >= self.required_length)}",
            ha="center",
            fontsize=18,
            bbox={"facecolor": facecolor, "alpha": 0.5, "pad": 5},
        )

        # resize the figure to match the aspect ratio of the Axes
        fig.set_size_inches(15, 7, forward=True)

        plt.legend()
        plt.gca().set_aspect("equal", adjustable="box")
        plt.grid()


class Caterpillar345(Excavator):

    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        h_dry,
        required_length,
        mobilisation_cost = None,
        equipment_cost = None,
        offset=3,
    ):
        lchart = {
            9: {
                "x": [7.5],
                "w": [6.88]},
            7.5: {
                "x": [7.5],
                "w": [7.83]},
            6: {
                "x": [7.5, 9.0],
                "w": [8.41, 6.88]},
            4.5: {
                "x": [4.5, 6.0, 7.5, 9.0],
                "w": [15.09, 11.32, 9.32, 6.72]},
            3: {
                "x": [4.5, 6.0, 7.5, 9.0],
                "w": [18.88, 12.89, 8.95, 6.49],
            },
            1.5: {
                "x": [4.5, 6.0, 7.5, 9.0],
                "w": [18.62, 12.13, 8.53, 6.27]},
            0: {
                "x": [4.5, 6.0, 7.5, 9.0],
                "w": [18.32, 11.66, 8.23, 6.09],
            },
            -1.5: {
                "x": [3, 4.5, 6.0, 7.5, 9.0],
                "w": [12.98, 18.25, 11.46, 8.08, 6.02],
            },
            -3: {
                "x": [3, 4.5, 6.0, 7.5],
                "w": [20.08, 18.45, 11.5, 8.09],
            },
            -4.5: {
                "x": [3, 4.5, 6.0, 7.5],
                "w": [20.75, 15.74, 11.76, 8.33],
            },
        }

        super().__init__(
            name=name,
            design_type=design_type,
            mobilisation_cost=mobilisation_cost,
            equipment_cost=equipment_cost,
            waterlvl=waterlvl,
            required_length = required_length,
            h_dry=h_dry,
            offset=offset,
            loading_chart=lchart,
        )

class HITACHI_EX1200(Excavator):
    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        h_dry,
        required_length,
        mobilisation_cost = None,
        equipment_cost = None,
        offset=3,
    ):
        lchart = {
            22: {"x": [16, 18],
                 "w": [15.5, 13.0]},
            20: {"x": [18, 20],
                 "w": [15.1, 12.0]},
            18: {"x": [18, 20],
                 "w": [16.5, 14.3]},
            16: {"x": [18, 20, 22],
                 "w": [17.7, 16.0, 13.0]},
            14: {
                "x": [16, 20, 24],
                "w": [19.8, 17.3, 10.7],
            },
            12: {
                "x": [14, 18, 22],
                "w": [21.5, 19.2, 15.9],
            },
            10: {
                "x": [12, 16, 20, 24],
                "w": [23.6, 21.8, 17.6, 14.4],
            },
            8: {
                "x": [10, 14, 18, 22, 26],
                "w": [34.7, 25.4, 19.7, 16.0, 10.8],
            },
            6: {
                "x": [12, 16, 20, 24],
                "w": [30.7, 22.6, 17.7, 14.3],
            },
            4: {
                "x": [11, 14, 18, 22, 26],
                "w": [28.2, 26.4, 20.0, 15.8, 11.4],
            },
            2: {
                "x": [12, 16, 20, 24],
                "w": [28.6, 22.8, 17.6, 13.8],
            },
            0: {
                "x": [10, 14, 18, 22, 26],
                "w": [6.9, 26.1, 19.6, 15.2, 11.2],
            },
            -2: {
                "x": [12, 14, 18, 22],
                "w": [17, 21.8, 16.7, 12.4],
            },
            -4: {
                "x": [10, 14, 18, 22, 25],
                "w": [8.7, 23.9, 18.1, 13.5, 10.0],
            },
            -6: {"x": [8, 12, 16, 20, 24],
                 "w": [6.5, 18.8, 19.2, 14.4, 9.4]
                 },
            -8: {"x": [10, 14, 18, 22],
                 "w": [13.2, 19.5, 14.8, 10.1]
                 },
            -10: {"x": [10, 14, 18, 22],
                  "w": [15.9, 16.3, 12.3, 6.8]
                  },
            -12: {"x": [14, 16],
                  "w": [12.4, 8.7]
                  },
        }

        super().__init__(
            name=name,
            design_type=design_type,
            mobilisation_cost=mobilisation_cost,
            equipment_cost=equipment_cost,
            waterlvl=waterlvl,
            required_length = required_length,
            h_dry=h_dry,
            offset=offset,
            loading_chart=lchart,
        )

class HITACHI_EX1900(Excavator):
    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        h_dry,
        required_length,
        mobilisation_cost = None,
        equipment_cost = None,
        offset=3,
    ):
        lchart = {
            10: {"x": [30], "w": [16.8]},
            8: {"x": [28, 32], "w": [21.1, 13.3]},
            6: {"x": [26, 30, 32], "w": [23, 20.3, 14.0]},
            4: {"x": [20, 24, 28, 30, 32], "w": [30.4, 25.4, 22.0, 20.2, 14.5]},
            2: {
                "x": [14, 18, 22, 26, 28, 30, 32],
                "w": [47, 33.9, 28.5, 24, 22.3, 20.8, 14.7],
            },
            0: {
                "x": [16, 20, 24, 26, 28, 30, 32],
                "w": [41.8, 32.4, 26.6, 24.4, 22.6, 21, 14.5],
            },
            -2: {
                "x": [14, 18, 22, 26, 28, 30, 32],
                "w": [43.9, 37.4, 29.8, 24.7, 22.8, 21.0, 14.5],
            },
            -4: {
                "x": [12, 16, 20, 24, 26, 28, 30, 31],
                "w": [16.6, 43.6, 33.6, 27.3, 24.9, 22.8, 21.3, 15.4],
            },
            -6: {
                "x": [10, 14, 18, 22, 24, 26, 28, 30],
                "w": [11.4, 37.7, 38.2, 30, 27.3, 24.8, 22.6, 19.4],
            },
            -8: {
                "x": [8, 12, 16, 20, 22, 24, 26, 28, 30],
                "w": [9.6, 18.5, 43.4, 33.6, 30.1, 27.1, 24.4, 22, 17.9],
            },
            -10: {
                "x": [6, 10, 14, 18, 20, 22, 24, 26, 27.5, 29],
                "w": [9.2, 14.8, 29.3, 37.2, 33.0, 29.4, 26.4, 23.7, 21.7, 19.5],
            },
            -12: {
                "x": [8, 12, 16, 18, 20, 22, 24, 26, 28],
                "w": [13.2, 22, 40.8, 35.9, 31.8, 28.3, 25.2, 22.3, 19.8],
            },
            -14: {
                "x": [10, 14, 16, 18, 20, 22, 24, 26],
                "w": [18.6, 34.4, 38.4, 33.9, 30.3, 26.5, 23.3, 19.9],
            },
            -16: {
                "x": [12, 14, 16, 18, 20, 22, 24],
                "w": [27.1, 39.1, 35.0, 30.8, 27.1, 23.7, 20.1],
            },
            -18: {"x": [14, 16, 18, 20, 22], "w": [35.8, 30.6, 26.6, 23.4, 20.9]},
        }

        super().__init__(
            name=name,
            design_type=design_type,
            mobilisation_cost=mobilisation_cost,
            equipment_cost=equipment_cost,
            waterlvl=waterlvl,
            required_length = required_length,
            h_dry=h_dry,
            offset=offset,
            loading_chart=lchart,
        )


class Crane(Equipment):
    """
    Crane class (Land based equipment)

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    loading_chart: Dataframe
        Per boom length and radius a maximum lift capacity is given. Column names are [radius, boom length 1, boom length 2 etc].
        The rows are the corresponding values for the radius and then the lift capacities
    waterlvl: float
        At which water depth is the equipment used
    required_length: float
        minimum length of the level the equipment is standing on.
    h_dry: int
        Margin which account for wave overtopping so the equipment is not damaged.
    offset: int
        Margin from the edge at which the equipment is placed. 3 meter by default
    """

    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        required_length,
        loading_chart,
        h_dry,
        type = 'land',
        mobilisation_cost = None,
        equipment_cost = None,
        offset=3,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        self.waterlvl = waterlvl
        self.loading_chart = loading_chart
        self.h_dry = h_dry
        self.offset = offset
        self.type = type
        self.required_length = required_length

    def install(
        self,
        layer,
        grading_layer,
        ymax,
        section_coords,
        xmax_top,
        mass,
        slope,
        length_top,
        xloc_equip=None,
        yloc_equip=None,
        plot=False,
    ):
        """

        Parameters
        ----------
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        ymax: int
            Maximum height which is already build
        xmax_top: float
            Upper left corner of the highest build layer
        section_coords: list
            the coordinates of the section
        mass: float
            mass of the material of the layer
        plot: bool
            Do we want to make a plot. Default is False
        Returns
        -------
        Bool
        """
        install = False

        x_section, y_section = zip(*section_coords)
        y_start, y_end = min(y_section), max(y_section)


        # If xloc_equip is None we're building from land so we need to define it
        if xloc_equip == None:
            xloc_equip, yloc_equip, flip = self.location_equipment(
                self.offset,
                xpoint=xmax_top,
                section_coords=section_coords,
                equip=self,
                ymax=ymax,
            )


        # Maximum length between exuipment and section
        max_dist_x = max(abs(np.array(x_section) - xloc_equip))

        # Search the maximum possible mas for a reach (reach = radius)
        radii = self.loading_chart.index
        r = radii[radii >= max_dist_x].min()
        df = self.loading_chart[self.loading_chart.index == r]

        df = df.stack()
        df = df[df >= mass].sort_values()

        # What is the maximum reach and boom length at our material mass
        if len(df) == 0:
            M_max = float("-inf")
            r, l_boom = 0, 0
        else:
            r, l_boom = max(df.index)
            M_max = max(df)

        # How high can we reach with our reach and boom (use pythagoras)
        hmax = np.sqrt(float(l_boom) ** 2 - r ** 2)
        # Difference betweeen y-location equipment and highest section, should be smaller than hmax
        h = yloc_equip - y_end
        if (
            grading_layer in self.design_type.keys()
        ):
            if (y_start - self.waterlvl) >= self.h_dry or (
                (ymax - self.waterlvl) >= self.h_dry and mass <= M_max and h <= hmax and length_top >= self.required_length
            ):
                install = True

        if ymax > (self.waterlvl + self.h_dry) and not install and slope != (0,0):
            dy = ymax - (self.waterlvl + self.h_dry)
            V, H = slope
            xmax_top = xmax_top - H/V * dy
            install = self.install(
                layer= layer,
                grading_layer = grading_layer,
                ymax = self.waterlvl + self.h_dry,
                section_coords = section_coords,
                length_top= 2*abs(xmax_top),
                xmax_top = xmax_top,
                mass = mass,
                slope= slope
            )


        if plot:
            self.plot(
                layer=layer,
                grading_layer=grading_layer,
                section_coords=section_coords,
                ymax=ymax,
                xloc_equip=xloc_equip,
                yloc_equip=yloc_equip,
                install=install,
                length_top= length_top,
                mass=mass,
                M_max=M_max,
            )
        return install

    def plot(
        self,
        layer,
        grading_layer,
        section_coords,
        ymax,
        xloc_equip,
        yloc_equip,
        length_top,
        install,
        mass,
        M_max,
    ):

        fig, ax = plt.subplots(figsize=(15, 5))
        ax.set_title(f"Install = {install}\n", fontweight="bold")

        x, y = list(zip(*section_coords))
        y_start = min(y)
        ax.fill(x, y, color="k", label=f"{layer} layer ({grading_layer})")
        plt.axhline(self.waterlvl, color="b", label="water level")
        ax.arrow(
            xloc_equip,
            self.waterlvl,
            dx=0,
            dy=self.h_dry,
            length_includes_head=True,
            head_width=0.3,
        )
        plt.axhline(
            self.waterlvl + self.h_dry,
            linestyle="--",
            color="k",
            label="water level + h_dry",
        )
        plt.plot(xloc_equip, yloc_equip, "ko", label=f"location {self.name}")

        facecolor = "r"
        if install:
            facecolor = "g"
        plt.figtext(
            0.5,
            -0.1,
            f"1. The {self.name} can build the layer: {grading_layer in self.design_type.keys()} AND\n"
            f"2. y_start >= water level + h_dry: {(y_start - self.waterlvl) >= self.h_dry} OR\n"
            f"3. ymax >= water level + h_dry: {(ymax - self.waterlvl) >= self.h_dry} AND\n"
            f"4. Mass layer <= M_max: {mass <= M_max} AND\n"
            f"5. required_length <= layer length {(length_top >= self.required_length)}",
            ha="center",
            fontsize=18,
            bbox={"facecolor": facecolor, "alpha": 0.5, "pad": 5},
        )

        # resize the figure to match the aspect ratio of the Axes
        fig.set_size_inches(15, 7, forward=True)

        plt.legend()
        plt.gca().set_aspect("equal", adjustable="box")
        plt.grid()


class Vessel(Equipment):
    """
    Vessel class (marine based equipment)
    Side stone dumpers and split barge

    Parameters
    ----------
    name: str
        name of the equipment
    design_type: dict
        Which layers can be designed with what grading at what cost and at what speed,
        {grading: {'cost': ... [EUR], 'CO2': ... [kg] , production_rate: ...}}, production rate [m3/hr]
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    waterlvl: float
        Water level at which the equipment is used
    installation_waterdepth: int
        Minimum water depth required for installation
    ukc: float
        under keel clearance

    """

    def __init__(
        self,
        name,
        design_type,
        waterlvl,
        installation_waterdepth,
        type = 'Marine',
        mobilisation_cost = None,
        equipment_cost = None,
        ukc = None,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        self.installation_waterdepth = installation_waterdepth
        self.ukc = ukc

        if self.ukc == None:
            self.ukc = 0

        self.type = type

    def install(self, section_coords, layer, grading_layer, plot=False):
        """

        Parameters
        ----------
        section_coords: list
            the coordinates of the section
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        plot: bool
            Do we want to make a plot. Default is False

        Returns
        -------
        bool
        """
        x, y = list(zip(*section_coords))
        end = max(y)
        install = False
        if (
            grading_layer in self.design_type.keys()
        ):
            if (self.waterlvl - (self.installation_waterdepth + self.ukc)) >= end:
                install = True
        if plot:
            self.plot(
                section_coords=section_coords,
                install=install,
                layer=layer,
                grading_layer=grading_layer,
            )
        return install

    def plot(self, section_coords, install, layer, grading_layer):

        fig, ax = plt.subplots(figsize=(15, 5))
        x, y = list(zip(*section_coords))
        end_section = max(y)
        plt.fill(x, y, color="brown", label=f"{layer} section ({grading_layer})")
        ax.arrow(
            2.5,
            self.waterlvl,
            dx=0,
            dy=-self.installation_waterdepth,
            length_includes_head=True,
            head_width=0.1,
            color="b",
            label="installation_waterdepth",
        )
        ax.arrow(
            3,
            end_section,
            dx=0,
            dy=self.ukc,
            length_includes_head=True,
            head_width=0.1,
            color="r",
            label="ukc",
        )
        ax.axhline(self.waterlvl, label="LW")

        facecolor = "r"
        if install:
            facecolor = "g"
        plt.figtext(
            0.5,
            -0.1,
            f"1. The {self.name} can build the layer: {grading_layer in self.design_type.keys()} AND\n"
            f"2. waterlevel - installation_waterdepth >= yend + margin: {(self.waterlvl - (self.installation_waterdepth + self.ukc)) >= end_section}\n",
            ha="center",
            fontsize=18,
            bbox={"facecolor": facecolor, "alpha": 0.5, "pad": 5},
        )

        # resize the figure to match the aspect ratio of the Axes
        fig.set_size_inches(15, 7, forward=True)
        ax.set_title(f"Install = {install}\n", fontweight="bold")
        plt.legend()
        plt.gca().set_aspect("equal", adjustable="box")
        plt.grid()


class Barge(Equipment):
    """

    Parameters
    ----------
    name: str
        name of the equipment
    mobilisation_cost: dict
        Cost of transportation to site in EUR and/or CO2 emission. e.g. {'cost': ... [EUR], 'CO2': ... [kg]}
    equipment_cost: dict
        What is the cost of usage of the equipment per hour in EUR and/or CO2 emmission. e.g. {'cost': ... [EUR/hr], 'CO2': ... [kg/hr]}
    waterlvl: float
        Water level at which the equipment is used
    other: object
        Object Excavator or Crane. Depends which equipment is mounted on the barge.
    installation_waterdepth: float
        installation_waterdepth of the barge
    height: float
        Total height of the barge
    ukc: float
        under keel clearance
    margin_x: float
        distance of barge from structure
    """

    def __init__(
        self,
        name,
        waterlvl,
        other,
        installation_waterdepth,
        height,
        downtime_production,
        extra_cost,
        type = 'Marine',
        ukc = None,
        margin_x=2,
        design_type=None,
        mobilisation_cost = None,
        equipment_cost = None,
    ):

        super().__init__(
            name=name, design_type= design_type, equipment_cost= equipment_cost,
            waterlvl= waterlvl, mobilisation_cost= mobilisation_cost
        )
        # Inherit either from Standard_Excavator or Dragline_Excavator
        self.instance = other
        self.mobilisation_cost = {'cost': self.mobilisation_cost['cost'] + self.instance.mobilisation_cost['cost'],
                                  'CO2': self.mobilisation_cost['CO2'] + self.instance.mobilisation_cost['CO2']}

        self.equipment_cost = {'cost': self.equipment_cost['cost'] + self.instance.equipment_cost['cost'],
                                  'CO2': self.equipment_cost['CO2'] + self.instance.equipment_cost['CO2']}
        self.waterlvl = waterlvl
        self.installation_waterdepth = installation_waterdepth
        self.height = height
        self.margin_x = margin_x
        self.ukc = ukc
        self.type = type

        if self.ukc == None:
            self.ukc = 0

        self.design_type = {}

        for grading, dict in self.instance.design_type.items():

            self.design_type[grading] = {'cost': dict['cost'] + extra_cost, 'CO2': dict['CO2'],
                                         'production_rate': dict['production_rate'] - downtime_production}

    def install(
        self,
        layer,
        grading_layer,
        slope,
        section_coords,
        xmax_top,
        mass,
        plot=False,
    ):
        """

        Parameters
        ----------
        layer: str
            The name of the layer. e.g. 'core' or 'armour'
        grading_layer: str
            The grading of the layer. e.g. HMA60_300
        slope: tuple
            Slope of the breakwater
        section_coords: list
            The coordinates of the layer
        xmax_top: float
            Upper left corner of the highest build layer
        mass: float
            Mass of the material of the section


        Returns
        -------
        Bool
        """
        install = False

        xtop = max(section_coords)[0]

        x_section, y_section = zip(*section_coords)
        y_end = max(y_section)

        V, H = slope
        y_installation_waterdepth = self.waterlvl - self.installation_waterdepth
        # It is possible that the barge hit's the construction and we need to keep an extra offset
        if (
            grading_layer in self.instance.design_type.keys()
        ):
            if y_end >= y_installation_waterdepth - self.ukc:
                if isinstance(self.instance, Crane):
                    xequip, yequip, flip = self.location_equipment(
                        (y_end - y_installation_waterdepth) * H / V,
                        self.margin_x,
                        self.instance.offset,
                        xpoint=xtop,
                        section_coords=section_coords,
                        equip=self,
                        y_installation_waterdepth=y_installation_waterdepth,
                        height=self.height,
                    )

                    self.instance.waterlvl = self.waterlvl
                    self.instance.h_dry = 0
                    install = self.instance.install(
                        layer=layer,
                        grading_layer=grading_layer,
                        ymax= self.waterlvl + self.height,
                        section_coords=section_coords,
                        xmax_top=xmax_top,
                        mass=mass,
                        length_top=float("inf"),
                        xloc_equip=xequip,
                        yloc_equip=yequip,
                        plot=plot,
                        slope= (0, 0)
                    )

                elif isinstance(self.instance, Excavator):
                    # This is the location closest to the section but not always the optimal location
                    xequip, yequip, flip = self.location_equipment(
                        (y_end - y_installation_waterdepth) * H / V,
                        self.margin_x,
                        self.instance.offset,
                        xpoint=xtop,
                        section_coords=section_coords,
                        equip=self,
                        y_installation_waterdepth=y_installation_waterdepth,
                        height=self.height,
                    )
                    self.instance.waterlvl = self.waterlvl
                    self.instance.h_dry = 0
                    install = self.instance.install(
                        layer=layer,
                        grading_layer=grading_layer,
                        ymax= self.waterlvl + self.height,
                        section_coords=section_coords,
                        xmax_top=xmax_top,
                        mass=mass,
                        length_top=float("inf"),
                        xloc_equip=xequip,
                        yloc_equip=yequip,
                        plot=plot,
                        slope= (0, 0)
                    )
            if isinstance(self.instance, PlateFeeder) or isinstance(self.instance, Truck):
                install = self.instance.install(layer= layer,
                                                grading_layer = grading_layer,
                                                ymax = self.waterlvl + self.height,
                                                section_coords = section_coords,
                                                level = self.waterlvl + self.height,

                )
            else:
                if isinstance(self.instance, Crane):
                    # In this case we can always install as we can freely manouevre the vessel and the crane can reach everywhere
                    install = True
                    self.instance.install(
                        layer=layer,
                        grading_layer=grading_layer,
                        ymax= self.waterlvl + self.height,
                        section_coords=section_coords,
                        xmax_top=xmax_top,
                        length_top=float("inf"),
                        mass=mass,
                        xloc_equip=(min(x_section) + max(x_section)) / 2,
                        yloc_equip=y_installation_waterdepth + self.height,
                        plot=plot,
                        slope= (0, 0)
                    )
                elif isinstance(self.instance, Excavator):
                    # The Excavator searches the optimal location on a top layer with length infinity (the water level)
                    yequip = y_installation_waterdepth + self.height
                    xequip = max(x_section)
                    self.instance.waterlvl = self.waterlvl
                    self.instance.h_dry = 0
                    install = self.instance.install(
                        layer=layer,
                        grading_layer=grading_layer,
                        ymax= self.waterlvl + self.height,
                        section_coords=section_coords,
                        xmax_top=xmax_top,
                        mass=mass,
                        length_top=float("inf"),
                        xloc_equip=xequip,
                        yloc_equip=yequip,
                        plot=plot,
                        slope= (0, 0)
                    )
        return install