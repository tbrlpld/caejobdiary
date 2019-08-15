"""
Provides a function to easily transfer the settings from one logger to another
"""

import logging


def copy_logger_settings(source_logger_name, target_logger_name):
    """
    Make settings of target_logger the same as source_logger

    Parameters
    ----------
    source_logger, target_logger : str
        Names of the loggers
    """

    source_logger = logging.getLogger(source_logger_name)
    target_logger = logging.getLogger(target_logger_name)
    target_logger.setLevel(source_logger.level)
    target_logger.propagate = source_logger.propagate
    target_logger.handlers = source_logger.handlers
