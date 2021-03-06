"""Common utilities."""

import os
import logging
import numpy as np
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta


def get_delta_seconds(year, st_mon, st_day, end_mon, end_day):
    """Returns the delta seconds between `year:st_mon:st_day:0:0:0` and
    `year:end_mon:end_day:24:0:0`.

    Args:
        st_year (int): Year.
        st_mon (int): Start month.
        st_day (int): Start day.
        end_mon (int): End month.
        end_day (int): End day.

    Returns:
        float: Time difference in seconds.
    """

    startTime = datetime(year, st_mon, st_day, 0, 0, 0)
    endTime = datetime(year, end_mon, end_day, 23, 0, 0) + timedelta(0, 3600)
    delta_sec = (endTime - startTime).total_seconds()
    return delta_sec


def get_current_time_info(epm, sec_elapsed, sim_year=1991):
    """Returns the current day, month and hour given the seconds elapsed since the simulation started.

    Args:
        epm (opyplus.Epm): EnergyPlus model object.
        sec_elapsed (int): Seconds elapsed since the start of the simulation
        sim_year (int, optional): Year of the simulation. Defaults to 1991.

    Returns:
        (int, int, int): A tuple composed by the current day, month and hour in the simulation.
    """

    start_date = datetime(
        year=sim_year,  # epm.RunPeriod[0]['start_year'],
        month=epm.RunPeriod[0]['begin_month'],
        day=epm.RunPeriod[0]['begin_day_of_month']
    )

    current_date = start_date + timedelta(seconds=sec_elapsed)

    return (current_date.day, current_date.month, current_date.hour)


def parse_variables(var_file):
    """Parse observation to dictionary.

    Args:
        var_file (str): Variables file path.

    Returns:
        list: A list with the name of the variables.
    """

    tree = ET.parse(var_file)
    root = tree.getroot()

    variables = []
    for var in root.findall('variable'):
        if var.attrib['source'] == 'EnergyPlus':
            variables.append(var[0].attrib['type'])

    return variables


def create_variable_weather(weather_data, original_epw_file, columns: list = ['drybulb'], variation: tuple = None):
    """Create a new weather file adding gaussian noise to the original one.

    Args:
        weather_data (opyplus.WeatherData): Opyplus object with the weather for the simulation.
        original_epw_file (str): Path to the original EPW file.
        columns (list, optional): List of columns to be affected. Defaults to ['drybulb'].
        variation (tuple, optional): Tuple with the mean and standard desviation of the Gaussian noise. Defaults to None.

    Returns:
        str: Name of the file created in the same location as the original one.
    """

    if variation is None:
        return None
    else:
        # Get dataframe with weather series
        df = weather_data.get_weather_series()

        # Generate random noise
        shape = (df.shape[0], len(columns))
        mu, std = variation
        noise = np.random.normal(mu, std, shape)
        df[columns] += noise

        # Save new weather data
        weather_data.set_weather_series(df)
        filename = original_epw_file.split('.epw')[0]
        filename += '_Random_%s_%s.epw' % (str(mu), str(std))
        weather_data.to_epw(filename)
        return filename


class Logger():
    def getLogger(self, name, level, formatter):
        logger = logging.getLogger(name)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logging.Formatter(formatter))
        logger.addHandler(consoleHandler)
        logger.setLevel(level)
        logger.propagate = False
        return logger
