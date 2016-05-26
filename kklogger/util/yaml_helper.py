#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @file     util.py
# @author   kaka_ace <xiang.ace@gmail.com>
# @date     Dec 20 2015
# @brief     
#


import os
import yaml


class YamlLoader(yaml.Loader):
    """
    reference:
    http://stackoverflow.com/questions/528281/how-can-i-include-an-yaml-file-inside-another
    """
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(YamlLoader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, YamlLoader)

YamlLoader.add_constructor('!include', YamlLoader.include)


class YamlHelper(object):
    @staticmethod
    def get_config_data(cls, config_path):
        filename = os.path.join(config_path)
        with open(filename, 'r') as f:
            data = yaml.load(f, YamlLoader)
            return data
