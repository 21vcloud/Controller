# -*- coding: utf-8 -*-
"""
Common Tools
"""

import configparser as config_parser
import json
import logging
import os
import platform

import base64
import jsonpickle
from Crypto.Cipher import AES

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace


class Logger(object):
    """
    Logger Tools
    """

    def __init__(self, name='iaas', level=logging.DEBUG, log_folder=None):
        object.__init__(self)
        logging.basicConfig()

        logger_name = name
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        if not logger.handlers:
            if log_folder is None:
                log_folder = os.getcwd() + "/logs/"

            if not os.path.exists(log_folder):
                os.mkdir(log_folder)

            log_path = log_folder + name + ".log"
            fh = logging.FileHandler(log_path)
            fh.setLevel(level)

            formatter = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s"
            date_format = "%a %d %b %Y %H:%M:%S"
            formatter = logging.Formatter(formatter, date_format)

            fh.setFormatter(formatter)
            logger.addHandler(fh)

            console = logging.StreamHandler()
            console.setLevel(level)
            console.setFormatter(formatter)
            logger.addHandler(console)

        self.__logger = logger

    def get_logger(self):
        return self.__logger


# Current Performance singleton class, contains performance model
class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__instance'):
            orig = super(Singleton, cls)
            cls.__instance = orig.__new__(cls, *args, **kwargs)
        return cls.__instance


# 配置文件读取工具类
class Config:
    __config = None
    __filename = None

    def __init__(self, filename=None, file_path=None):
        if self.__config is None:
            self.__config = config_parser.ConfigParser()

        if filename is None:
            return

        self.__filename = filename

        config_path = file_path
        if file_path is None:
            sysstr = platform.system()
            if sysstr == "Windows":
                config_path = os.getcwd() + "\\conf\\"
            elif sysstr == "Linux":
                config_path = os.getcwd() + "/conf/"

        config_file = config_path + self.__filename
        self.__config.read(config_file)

    def get(self, section, name):
        if self.__config is None:
            return

        val = self.__config.get(section, name)
        return val

    def items(self, section):
        if self.__config is None:
            return

        key_val = self.__config.items(section)
        return key_val


class EncodeHandler(object):
    # Convert object into UTF-8, e.g. unicode
    @staticmethod
    def byteify(input_str):
        if isinstance(input_str, dict):
            return {EncodeHandler.byteify(key): EncodeHandler.byteify(value) for key, value in input_str.items()}
        elif isinstance(input_str, list):
            return [EncodeHandler.byteify(element) for element in input_str]
        elif isinstance(input_str, bytes):
            return input_str.encode('utf-8')
        else:
            return input_str


class JsonUtils(object):

    # Convert dict object to Python object.
    # Refer with: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
    @staticmethod
    def convert_dict_to_object(data):
        json_string = jsonpickle.dumps(data)
        return json.loads(json_string, object_hook=lambda d: Namespace(**d))

    # Convert dict object to Python object.
    # Refer with: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
    @staticmethod
    def loads(data):
        return json.loads(data, object_hook=lambda d: Namespace(**d))

    # 将Python Object转换为dict对象，以便MongoDB等执行操作
    @staticmethod
    def convert_object_to_dict(data):
        if hasattr(data, '__iter__'):
            for n, data in enumerate(data):
                data[n] = JsonUtils.convert_object_to_dict(data)
        else:
            data = dir(data)
            for i in data:
                if hasattr(i, "__dict__"):
                    i = JsonUtils.convert_object_to_dict(i)
                if hasattr(data[i], "__dict__"):
                    data[i] = JsonUtils.convert_object_to_dict(data[i])
        return data


# 请求加密、解密
class AESCipher(object):
    def __init__(self):
        self.key = u"0123456789123456".encode("utf-8")
        self.iv = u"2015030120123456".encode("utf-8")

    def __pad(self, text):
        """填充方式，加密内容必须为16字节的倍数，若不足则使用self.iv进行填充"""
        text_length = len(text)
        amount_to_pad = AES.block_size - (text_length % AES.block_size)
        if amount_to_pad == 0:
            amount_to_pad = AES.block_size
        pad = chr(amount_to_pad)
        return text + pad * amount_to_pad

    def __unpad(self, text):
        pad = ord(text[-1])
        return text[:-pad]

    def encrypt(self, raw):
        """加密"""
        raw = jsonpickle.dumps(raw)
        raw = self.__pad(raw)
        if isinstance(raw, str):
            raw = raw.encode(encoding="utf-8")
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, enc):
        """解密"""

        # str to bytes
        if isinstance(enc, str):
            enc = enc.encode(encoding="utf-8")

        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypt_info = self.__unpad(cipher.decrypt(enc).decode("utf-8"))
        decrypt_obj = jsonpickle.loads(decrypt_info)
        return decrypt_obj

