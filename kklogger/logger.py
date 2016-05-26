#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @date     Dec 13 2015
# @brief
#

import sys
import threading

import logging
from logging.handlers import (
    TimedRotatingFileHandler,
    SocketHandler,
    DatagramHandler,
    SysLogHandler,
    SMTPHandler,
    HTTPHandler,
)
from logging import LoggerAdapter

try:
    from six import with_metaclass
except:
    def with_metaclass(meta, *bases):
        """Create a base class with a metaclass. copy from six """
        class metaclass(meta):
            def __new__(cls, name, this_bases, d):
                return meta(name, bases, d)
        return type.__new__(metaclass, 'temporary_class', (), {})

from .util import (
    read_from_yaml,
    read_from_etcd,
    parse_config,
)

PY2 = sys.version_info[0] == 2


class IntField(int):
    """ the instance have both int type and other attributes """
    def __new__(cls, value=0, name=None, **kwargs):
        obj = int.__new__(cls, value)
        kwargs['name'] = name
        obj.__dict__.update(**kwargs)
        return obj


class StrField(str):
    """ the instance have both str type and other attributes """
    def __new__(cls, value=0, name="", **kwargs):
        obj = str.__new__(cls, value)
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
                field_dict[k] = namespace[k]
        namespace["FIELD_DICT"] = field_dict
        return type.__new__(mcs, name, bases, namespace)


class _Const(with_metaclass(ConstMetaClass)):
    FIELD_DICT = NotImplemented


class Logger(LoggerAdapter):
    """
    inspired from log4j2
    Technical Terms:
        Java        Python
        Appender -> Handler
        Layout   -> Formatter
        Logger   -> Logger
        Layout   -> format
    """

    # [ 16.6.7. LogRecord attributes -Python docs ](https://docs.python.org/3/library/logging.html#logrecord-attributes)
    DEFAULT_FORMAT = '[%(levelname)s %(process)d:%(asctime)s:%(funcName)s:%(lineno)d] %(message)s'
    DEFAULT_DATE_FORMAT = '%Y%m%d %H:%M:%S'  # display as local zone

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

    def __init__(self, logger, formatter, extra=None):
        """
        :param logger:
        :param formatter:
        :param extra:
            for logging.LoggerAdapter specify contextual
        :return:
        """
        self._formatter = formatter
        super(Logger, self).__init__(logger, extra=extra)

    def set_extra(self, extra):
        if not isinstance(extra, dict):
            raise TypeError("extra not dict")
        self.extra = extra

    def update_extra(self, update_extra):
        if not isinstance(update_extra, dict):
            raise TypeError("update_extra not dict")
        self.extra.update(update_extra)

    def config_file_handler(self, filename, level=None, rotate_mode=RotateMode.DAYS):
        self.add_handler(TimedRotatingFileHandler(filename, when=rotate_mode, utc=True), level=level)

    def config_tcp_handler(self, host, port, level=None):
        self.add_handler(SocketHandler(host, port), level=level)

    def config_udp_handler(self, host, port, level=None):
        self.add_handler(DatagramHandler(host, port), level=level)

    def config_syslog_handler(self, *args, **kwargs):
        # should known SysLogHandler params
        level = kwargs.pop('level', None)
        self.add_handler(SysLogHandler(*args, **kwargs), level=level)

    def config_smtp_handler(self, *args, **kwargs):
        # should known SMTPHandler params
        level = kwargs.pop('level', None)
        self.add_handler(SMTPHandler(*args, **kwargs), level=level)

    def config_http_handler(self, *args, **kwargs):
        # should known HTTPHandler params
        level = kwargs.pop('level', None)
        self.add_handler(HTTPHandler(*args, **kwargs), level=level)

    def add_handler(self, handler, **kwargs):
        level = kwargs.get('level')
        handler.setFormatter(self._formatter)
        if level:
            handler.setLevel(level)
        self.logger.addHandler(handler)


class LogManager(object):
    _lock = threading.RLock()
    _REGISTERED_LOGGER_DICT = {}

    # config options:
    CONFIG_YAML = 1
    CONFIG_ETCD = 2
    CONFIG_READ_HANDLER_DICT = {
        CONFIG_YAML: read_from_yaml,
        CONFIG_ETCD: read_from_etcd,
    }

    _META_CONFIG = NotImplemented

    @classmethod
    def register_meta_config(cls, config_type, **kwargs):
        """
        register your meta config:
        1. tell LogManager way do want to read from
        2. tell the specified config type with parameters that you can correctly read the config data
        :param config_type:
        :param kwargs: config read_handler with read the parameters
        """
        if config_type not in cls.CONFIG_READ_HANDLER_DICT.keys():
            raise ValueError("no support config_type= {0} it should be defined in LogManager.ConfigType".format(
                config_type))

        with cls._lock:
            cls._META_CONFIG = {'type': config_type, 'kwargs': kwargs}

    @classmethod
    def load(cls):
        """
        Recommendation:
        just load once at the startup of the process/app

        eg:
        LogManager.register_meta_config(LogManager.ConfigType.YAML, host="127.0.0.1", port=2379)
        LogManager.load()

        # your app start running
        app.run()
        """
        with cls._lock:
            config_type = cls._META_CONFIG['type']
            read_handler = cls.CONFIG_READ_HANDLER_DICT[config_type]
            config_data = read_handler(**cls._META_CONFIG['kwargs'])
            parse_config(cls, config_data)

    @staticmethod
    def get_root_logger():
        return logging.getLogger()

    @staticmethod
    def create_logger(
            name=None, level=logging.INFO, propagate=True,
            date_fmt=Logger.DEFAULT_DATE_FORMAT, fmt=Logger.DEFAULT_FORMAT
    ):
        """
        :param name: default None
        :param level: default logging.INFO
        :param propagate: default True
        :param date_fmt:
        :param fmt:
        :return: Logger instance
        """
        logger = logging.getLogger(name)
        formatter = logging.Formatter(datefmt=date_fmt, fmt=fmt)
        logger.setLevel(level)
        logger.propagate = propagate
        return Logger(logger, formatter)

    @classmethod
    def get_logger(cls, name):
        registered_logger = cls._REGISTERED_LOGGER_DICT.get(name)
        if registered_logger:
            return registered_logger
        else:
            root_logger = cls.get_root_logger()
            root_logger.warning("not found logger by name= {0}".format(name))
            return root_logger

