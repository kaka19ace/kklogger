#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @file     __init__.py
# @date     Dec 23 2015
# @brief     
#


import os
import json


def read_from_yaml(path):
    from ..util.yaml_helper import YamlHelper
    return YamlHelper.get_config_data(path)


def read_from_etcd(
    read_type='env',
    env_host_key="KKLOGGER_ETCD_HOST",
    env_port_key="KKLOGGER_ETCD_PORT",
    env_etcd_username_key='KKLOGGER_ETCD_USERNAME',
    env_etcd_password_key='KKLOGGER_ETCD_PASSWORD',
    env_etcd_service_key='KKLOGGER_ETCD_KEY',
    json_path=None,
):
    """
    default read from sys environment variables

    :param read_type:
        'env': read from sys environment variables, only support version 2, protocol=http
        'json': recommend way, read from json, if set 'json', you need pass json_path to find the config data

        read_type priority:
            env, json

    the following parameters prefix with "env_" are valid when read_type == 'env'
    :param env_host_key:
    :param env_port_key:
    :param env_etcd_username_key:
    :param env_etcd_password_key:
    :param env_etcd_service_key:

    if set read_type 'json'
    :param json_path:
        the json example:
        {
            'client': {
                'host': '192.168.0.1',
                'port': 2379,
                'username': 'samurai',
                'password': 'champloo',
                'protocol': 'http',
                'allow_reconnect': False,
            }
            'key': 'Mugen'
        }
    :return: dict data
    """
    import etcd

    if read_type == 'etcd':
        host = os.environ[env_host_key]
        port = int(os.environ[env_port_key])
        username = os.environ.get(env_etcd_username_key)
        password = os.environ.get(env_etcd_password_key)
        key = os.environ.get(env_etcd_service_key)
        client = etcd.Client(host=host, port=port, username=username, password=password)
    elif read_type == 'json':
        with open(json_path, 'r') as f:
            content = f.read()
        client_kwargs = json.loads(content['client'])
        client = etcd.Client(**client_kwargs)
        key = content['key']
    else:
        raise ValueError(u"not support read_type= {0}".format(read_type))

    result = client.get(key)
    return json.loads(result.value)


def parse_config(manager, config_data):
    registered_logger_dict = manager._REGISTERED_LOGGER_DICT
    # TODO: load and register
    raise NotImplementedError
