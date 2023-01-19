
import time

from platformio_dependabot import logger

_time_start = time.time()


def time_format_us(us: float, prec=3) -> str:
    if us < 1000:
        return '{:.{precision}f} us'.format(us, precision=prec)
    return time_format_ms(us / 1000, prec)


def time_format_ms(ms: float, prec=3) -> str:
    if ms < 1:
        return time_format_us(ms * 1000, prec)
    if ms < 1000:
        return '{:.{precision}f} ms'.format(ms, precision=prec)
    return time_format_s(ms / 1000, prec)


def time_format_s(s: float, prec=3) -> str:
    if s < 1:
        return time_format_ms(s * 1000, prec)
    return '{:.{precision}f} seconds'.format(s, precision=prec)


def print_execution_time():
    logger.info('Execution took %s', time_format_s(time.time() - _time_start, prec=0))
