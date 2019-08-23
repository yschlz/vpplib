"""
The ``modelchain_example`` module shows a simple usage of the windpowerlib by
using the :class:`~.modelchain.ModelChain` class. The modelchains are
implemented to ensure an easy start into the Windpowerlib. They work like
models that combine all functions provided in the library. Via parameteres
desired functions of the windpowerlib can be selected. For parameters not being
specified default parameters are used.

There are mainly three steps. First you have to import your weather data, then
you need to specify your wind turbine, and in the last step call the
windpowerlib functions to calculate the feed-in time series.


"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import pandas as pd

try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

from windpowerlib import ModelChain
from windpowerlib import WindTurbine

# You can use the logging package to get logging messages from the windpowerlib
# Change the logging level if you want more or less messages
import logging
logging.getLogger().setLevel(logging.DEBUG)

filename='./Input_House/Wind/weather.csv'

def get_weather_data(filename=filename, **kwargs):
    r"""
    Imports weather data from a file.

    The data include wind speed at two different heights in m/s, air
    temperature in two different heights in K, surface roughness length in m
    and air pressure in Pa. The file is located in the example folder of the
    windpowerlib. The height in m for which the data applies is specified in
    the second row.

    Parameters
    ----------
    filename : string
        Filename of the weather data file. Default: 'weather.csv'.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the weather data file is stored.
        Default: 'windpowerlib/example'.

    Returns
    -------
    weather_df : pandas.DataFrame
            DataFrame with time series for wind speed `wind_speed` in m/s,
            temperature `temperature` in K, roughness length `roughness_length`
            in m, and pressure `pressure` in Pa.
            The columns of the DataFrame are a MultiIndex where the first level
            contains the variable name as string (e.g. 'wind_speed') and the
            second level contains the height as integer at which it applies
            (e.g. 10, if it was measured at a height of 10 m).

    """
    
    file = filename
    
    # read csv file
    weather_df = pd.read_csv(
        file, index_col=0, header=[0, 1],
        date_parser=lambda idx: pd.to_datetime(idx, utc=True))
    # change type of index to datetime and set time zone
    weather_df.index = pd.to_datetime(weather_df.index).tz_convert(
        'Europe/Berlin')
    # change type of height from str to int by resetting columns
    l0 = [_[0] for _ in weather_df.columns]
    l1 = [int(_[1]) for _ in weather_df.columns]
    weather_df.columns = [l0, l1]
    return weather_df


def initialize_wind_turbines():
    r"""
    fetch power and/or power coefficient curve data from the OpenEnergy 
    Database (oedb), as done for the 'enercon_e126'
    Execute ``windpowerlib.wind_turbine.get_turbine_types()`` to get a table
    including all wind turbines for which power and/or power coefficient curves
    are provided.

    Returns
    -------
    WindTurbine

    """

    # specification of wind turbine where power curve is provided in the oedb
    # if you want to use the power coefficient curve change the value of
    # 'fetch_curve' to 'power_coefficient_curve'
    enercon_e126 = {
        'name': 'E-126/4200',  # turbine type as in register #
        'hub_height': 135,  # in m
        'rotor_diameter': 127,  # in m
        'fetch_curve': 'power_curve',  # fetch power curve #
        'data_source': 'oedb'  # data source oedb or name of csv file
    }
    # initialize WindTurbine object
    e126 = WindTurbine(**enercon_e126)

    return e126


def calculate_power_output(weather, e126):
    r"""
    Calculates power output of wind turbines using the
    :class:`~.modelchain.ModelChain`.

    The :class:`~.modelchain.ModelChain` is a class that provides all necessary
    steps to calculate the power output of a wind turbine. You can either use
    the default methods for the calculation steps, or choose different methods, 
    as done for the 'e126'. Of course, you can also use the default methods 
    while only changing one or two of them.

    Parameters
    ----------
    weather : pd.DataFrame
        Contains weather data time series.
    e126 : WindTurbine
        WindTurbine object with power curve from the OpenEnergy Database.

    """
    # power output calculation for e126
    # own specifications for ModelChain setup
    modelchain_data = {
        'wind_speed_model': 'logarithmic',  # 'logarithmic' (default),
                                            # 'hellman' or
                                            # 'interpolation_extrapolation'
        'density_model': 'ideal_gas',  # 'barometric' (default), 'ideal_gas' or
                                       # 'interpolation_extrapolation'
        'temperature_model': 'linear_gradient',  # 'linear_gradient' (def.) or
                                                 # 'interpolation_extrapolation'
        'power_output_model': 'power_curve',  # 'power_curve' (default) or
                                              # 'power_coefficient_curve'
        'density_correction': True,  # False (default) or True
        'obstacle_height': 0,  # default: 0
        'hellman_exp': None}  # None (default) or None
    # initialize ModelChain with own specifications and use run_model method
    # to calculate power output
    mc_e126 = ModelChain(e126, **modelchain_data).run_model(weather)
    # write power output time series to WindTurbine object
    e126.power_output = mc_e126.power_output

    return


def plot_or_print(e126):
    r"""
    Plots or prints power output and power (coefficient) curves.

    Parameters
    ----------
    my_turbine : WindTurbine
        WindTurbine object with self provided power curve.
    e126 : WindTurbine
        WindTurbine object with power curve from data file provided by the
        windpowerlib.
    dummy_turbine : WindTurbine
        WindTurbine object with power coefficient curve from example file.

    """

    # plot or print turbine power output
    if plt:
        e126.power_output.plot(legend=True, label='Enercon E126')
        plt.show()
    else:
        print(e126.power_output)

    # plot or print power curve
    if plt:
        if e126.power_curve is not None:
            e126.power_curve.plot(x='wind_speed', y='value', style='*',
                                  title='Enercon E126 power curve')
            plt.show()

    else:
        if e126.power_coefficient_curve is not None:
            print(e126.power_coefficient_curve)
        if e126.power_curve is not None:
            print(e126.power_curve)


def run_example():
    r"""
    Runs the basic example.

    """
    weather = get_weather_data(filename)
    e126  = initialize_wind_turbines()
    calculate_power_output(weather, e126)
    plot_or_print(e126)


if __name__ == "__main__":
    run_example()