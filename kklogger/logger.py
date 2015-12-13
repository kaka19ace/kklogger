#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @date     Dec 13 2015
# @brief
#

import sys

import logging
from logging.handlers import (
    TimedRotatingFileHandler,
    SocketHandler,
    DatagramHandler,
    SysLogHandler,
    SMTPHandler,
    HTTPHandler,
)

try:
    from six import with_metaclass
except:
    def with_metaclass(meta, *bases):
        """Create a base class with a metaclass. copy from six """
        class metaclass(meta):
            def __new__(cls, name, this_bases, d):
                return meta(name, bases, d)
        return type.__new__(metaclass, 'temporary_class', (), {})

PY2 = sys.version_info[0] == 2


class cached_property(object):
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class IntField(int):
    """ the instance have both int type and other attributes """
    def __new__(cls, value=0, name=None, **kwargs):
        obj = type.__new__(value)
        kwargs['name'] = name
        obj.__dict__.update(**kwargs)
        return obj


class StrField(str):
    """ the instance have both str type and other attributes """
    def __new__(cls, value=0, name="", **kwargs):
        obj = type.__new__(value)
        kwargs['name'] = name
        obj.__dict__.update(**kwargs)
        return obj


class ConstMetaClass(type):
    def __new__(mcs, name, bases, namespace):
        field_dict = {}
        for k, v in namespace.items():
            if k.isupper() and isinstance(v, (int, str)):
                if isinstance(v, int) and not isinstance(v, IntField):
                    # default name is k
                    namespace[k] = IntField(v, name=k)
                elif isinstance(v, str) and not isinstance(v, StrField):
                    namespace[k] = StrField(v, name=k)
                field_dict[k] = v
        namespace["FIELD_DICT"] = field_dict
        return type.__new__(mcs, name, bases, namespace)


class _Const(with_metaclass(ConstMetaClass)):
    FIELD_DICT = NotImplemented


class Logger(object):
    # '[%(levelname)s %(asctime)s %(pathname)s %(funcName)s:%(lineno)d] %(message)s' may be too long ~
    _DEFAULT_FORMAT = '[%(levelname)s %(asctime)s %(funcName)s:%(lineno)d] %(message)s'
    _DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # display as local zone

    class Level(_Const):
        CRITICAL = logging.CRITICAL
        ERROR = logging.ERROR
        WARN = logging.WARN
        INFO = logging.INFO
        DEBUG = logging.DEBUG
        NOTSET = logging.NOTSET

    class RotateMode(_Const):
        """
            https://docs.python.org/3/library/logging.handlers.html
            need learn about TimedRotatingFileHandler rotate type
            not support Weekday 'W0' - 'W6'
        """
        SECONDS = 'S'
        MINUTES = 'M'
        HOURS = 'H'
        DAYS = 'D'
        MIDNIGHT = 'midnight'

    def __init__(self, logger, formatter):
        self._logger = logger
        self._formatter = formatter

    def add_file_handler(self, filename, rotate_mode=RotateMode.DAYS):
        handler = TimedRotatingFileHandler(filename, when=rotate_mode, utc=True)
        handler.setFormatter(self._formatter)
        self._logger.addHandler(handler)

    def add_tcp_handler(self, host, port):
        self._add_handler(SocketHandler(host, port))

    def add_udp_handler(self, host, port):
        self._add_handler(DatagramHandler(host, port))

    def add_syslog_handler(self, *args, **kwargs):
        # should known SysLogHandler params
        self._add_handler(SysLogHandler(*args, **kwargs))

    def add_smtp_handler(self, *args, **kwargs):
        # should known SMTPHandler params
        self._add_handler(SMTPHandler(*args, **kwargs))

    def add_http_handler(self, *args, **kwargs):
        # should known HTTPHandler params
        self._add_handler(HTTPHandler(*args, **kwargs))

    def _add_handler(self, handler):
        handler.setFormatter(self._formatter)
        self._logger.addHandler(handler)

    @cached_property
    def info(self):
        return self._logger.info

    @cached_property
    def warn(self):
        return self._logger.warning

    @cached_property
    def error(self):
        return self._logger.error

    @cached_property
    def exception(self):
        return self._logger.exception

    @property
    def debug(self):
        return self._logger.debug

    @cached_property
    def critical(self):
        return self._logger.critical

    @classmethod
    def get_logger(
            cls, log_type, level=Level.INFO, propagate=False, date_fmt=_DEFAULT_DATE_FORMAT, fmt=_DEFAULT_FORMAT
    ):
        if not isinstance(level, IntField):
            raise TypeError("level: {0} not Logger.Level const type".format(type(level)))
        if level not in cls.Level.FIELD_DICT.values():
            raise ValueError("level= {0} not support".format(level))

        logger = logging.getLogger(log_type)
        formatter = logging.Formatter(datefmt=date_fmt, fmt=fmt)
        logger.setLevel(level)
        logger.propagate = propagate
        return cls(logger, formatter)
