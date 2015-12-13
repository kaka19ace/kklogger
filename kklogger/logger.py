#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @date     Dec 13 2015
# @brief
#

import sys

import logging
import logging.handlers
from logging.handlers import RotatingFileHandler

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
    def __new__(cls, value=0, name="", **kwargs):
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
            if k.isupper() and isinstance(v, (int, str, IntField, StrField)):
                if isinstance(v, int):
                    # default name is k
                    namespace[k] = IntField(v, name=k)
                elif isinstance(v, str):
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

    class LoggerType(_Const):
        FILE = 1  # using TimedRotatingFileHandler
        SYSLOG = 2  # SysLogHandler
        TCP = 3  # SocketHandler
        UDP = 4  # DatagramHandler
        HTTP = 5  # HTTPHandler

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

    def __init__(
            self,
            log_type, filename,
            level=Level.INFO, rotate_mode=RotateMode.DAYS,
            console_output=False
    ):
        if level not in self.Level.FIELD_DICT.values():
            raise ValueError("level= {0} not support".format(level))

        if rotate_mode not in self.RotateMode.FIELD_DICT.values():
            raise ValueError("rotate_mode= {0} not support".format(rotate_mode))

        self._logger = logging.getLogger(log_type)
        formatter = logging.Formatter(datefmt=self._DEFAULT_DATE_FORMAT, fmt=self._DEFAULT_FORMAT)
        handler = logging.handlers.TimedRotatingFileHandler(filename, when=rotate_mode, utc=True)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(level)

        if console_output is False:
            self._logger.propagate = False

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
