from .argparser import ArgumentParser


def _init_logger():
    import logging
    import colorlog

    log_format = '{log_color}[{levelname:1.1s}] {message_log_color}{message}'

    log_colors = {
        'DEBUG':    'reset',
        'INFO':     'white',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bold',
    }
    secondary_log_colors = {'message': {'INFO': 'reset'}}

    lh = colorlog.StreamHandler()
    lh.setFormatter(colorlog.ColoredFormatter(
        log_format,
        log_colors=log_colors,
        secondary_log_colors=secondary_log_colors,
        style='{')
    )

    lg = logging.getLogger('PlatformIO Dependabot')
    lg.addHandler(lh)
    lg.setLevel(logging.INFO)
    return lg


def die(msg=None, *args, code=1):
    if msg is not None:
        logger.error(str(msg), *args)
    import sys
    sys.exit(code)


logger = _init_logger()
argp = ArgumentParser()
