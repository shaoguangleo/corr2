import logging
import termcolors
from casperfpga import CasperLogHandlers

# region --- Logger configuration methods ---

LOGGER = logging.getLogger(__name__)
console_handler = CasperLogHandlers.CasperConsoleHandler(name=__name__)
LOGGER.addHandler(console_handler)
LOGGER.setLevel(logging.ERROR)

def get_logger_group(logger_dict=None, group_name=None):
    """
    Method to fetch all logger entities that match the group_name specified
    :param logger_dict: Dictionary of loggers - {logger_name, logging_entity}
    :param group_name: String that is found in loggers to be fetched
    :return: Dictionary of logger entities whose keys match group_name
    """
    if group_name is None or group_name is '':
        # Problem
        errmsg = 'Logger group name cannot be empty'
        LOGGER.error(errmsg)
        return None
    if logger_dict is None:
        logger_dict = logging.Logger.manager.loggerDict
    keys = logger_dict.keys()

    logger_group = {}

    for value in keys:
        if value.find(group_name) >= 0:
            logger_group[value] = logger_dict[value]
            # else: pass

    return logger_group


def set_logger_group_level(logger_group, log_level=logging.DEBUG):
    """
    ** Take in log_level as an INTEGER **
    Method to set the log-level of a group of loggers
    :param logger_group: Dictionary of logger and logging entities
    :param log_level: Effectively of type integer E logging.{CRITICAL,ERROR,WARNING,DEBUG,INFO}
    :return: Boolean - Success/Fail - True/False
    """

    # First, error-check the log_level specified
    # result, log_level_numeric = check_logging_level(log_level)
    result = isinstance(log_level, int)
    if not result:
        # Problem
        errmsg = 'Error with log_level specified: {}'.format(log_level)
        LOGGER.error(errmsg)
        return False

    for logger_key, logger_value in logger_group.items():
        # logger_value.setLevel(log_level_numeric)
        logger_value.setLevel(log_level)

    debugmsg = 'Successfully updated log-level of {} SKARABs to {}'.format(str(len(logger_group)), log_level)
    LOGGER.debug(debugmsg)
    return True


def add_handler_to_loggers(logger_dict, log_handler):
    """
    Adds a log handler to a group of loggers
    :param logger_dict: dictionary of logger objects
    :param log_handler: log-handler specified/instantiated by the user
    :return: Boolean - True/False, Success/Fail
    """

    # Need to error-check that the log_handler specified is actually
    # of type logging.Handler
    if not hasattr(log_handler, 'emit'):
        # Impostor!
        errmsg = 'Log-handler specified is not of type logging.Handler. ' \
                 'Unable to add Handler {} to logger group'.format(log_handler)
        LOGGER.error(errmsg)
        return False

    for logger_key, logger_value in logger_dict.items():
        if not _add_handler_to_logger(logger_value, log_handler):
            # Problem
            return False
            # else: Continue
    debugmsg = 'Successfully added log_handler to group of {} loggers'.format(str(len(logger_dict)))
    LOGGER.debug(debugmsg)

    return True


def _add_handler_to_logger(logger, log_handler):
    """
    Abstracted method from adding log-handler to group to localise error-checking
    :param logger: logging entity
    :param log_handler: log-handler specified/instantiated by the user
    :return: Boolean - True/False, Success/Fail
    """
    # First check if the log_handler has already been added to the logger
    # Or if the logger already has a log-handler with the same name
    handlers = logger.handlers
    for handler in handlers:
        # ** We don't care what type of handler it is **
        # if hasattr(handler, 'baseFilename'):
        #     # It's a FileHandler, not a StreamHandler(/KatcpHandler)
        #     continue
        # else:
            # StreamHandler, probably
        if handler.name.upper() == log_handler.name.upper():
            # Problem
            errmsg = 'skarab "{}" have multiple log-handlers with ' \
                     'the same name: {}'.format(logger.name, log_handler.name)
            LOGGER.error(errmsg)
            return False
        # else: All good

    # Separate method to set the log-level
    logger.addHandler(log_handler)

    debugmsg = 'Successfully added log_handler to logger-{}'.format(logger.name)
    LOGGER.debug(debugmsg)
    return True

# endregion