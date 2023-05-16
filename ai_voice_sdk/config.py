from typing import Callable

from .enums import Voice

class Settings(object):
    text_limit = 1500
    elastic_value = 200
    support_file_type = [".txt", ".ssml", ".xml"]
    task_each_text_limit = text_limit + elastic_value
    print_log = False

class ConverterConfig(object):
    _token:str
    _server_url:str

    voice = None # 聲音預設值為None
    _ssml_version = "1.0.demo"
    _ssml_lang = "zh-TW"

    def __init__(self, token = "", server_url = "https://www.aivoice.com.tw") -> None:
        if type(token) != str:
            raise TypeError("Parameter 'token(str)' type error.")

        self._token = token
        self.set_server(server_url)


    def set_token(self, token = "") -> None:
        if type(token) != str:
            raise TypeError("Parameter 'token(str)' type error.")

        self._token = token


    def get_token(self) -> str:
        return self._token


    def set_server(self, server_url = "") -> None:
        if type(server_url) != str:
            raise TypeError("Parameter 'server_url(str)' type error.")

        if server_url.find("http") == 0:
            self._server_url = server_url
        else:
            raise ValueError("Please check url, it should be with 'http' or 'https'.")


    def get_server(self) -> str:
        return self._server_url


    def set_voice(self, voice:Voice) -> None:
        if type(voice) != Voice:
            raise TypeError("Parameter 'voice(Voice)' type error.")

        self.voice = voice


    def get_voice(self) -> str:
        return self.voice


    def get_ssml_version(self) -> str:
        return self._ssml_version


    def get_ssml_lang(self) -> str:
        return self._ssml_lang


class ConverterConfigInternal(ConverterConfig):
    __notice_value_update: Callable[[], None] = None

    def __init__(self, config:ConverterConfig, callback: Callable[[], None]) -> None:
        self._token = config.get_token()
        self._server_url = config.get_server()
        self.voice = config.get_voice()
        self._ssml_version = config.get_ssml_version()
        self._ssml_lang = config.get_ssml_lang()
        self.__notice_value_update = callback

    def set_server(self, server_url = "") -> None:
        super().set_server(server_url)
        self.__notice_value_update()

    def set_token(self, token = "") -> None:
        super().set_token(token)
        self.__notice_value_update()

    def set_voice(self, voice: Voice) -> None:
        super().set_voice(voice)
        self.__notice_value_update()
