from .enums import Voice

class Settings(object):
    text_limit = 1500

    # _support_file_type = [".txt", ".ssml"] # 暫不支援ssml
    support_file_type = [".txt"]

    task_each_text_limit = text_limit + 200
    # server_support_json_status_code = [200, 400, 500, 503] # 401 server回傳會少帶code參數，所以暫時移除

    print_log = False

class ConverterConfig(object):
    _token:str
    _server_url:str

    voice = Voice.NOETIC
    _ssml_version = ""
    _ssml_lang = ""

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


    def set_voice(self, voice = Voice.NOETIC) -> None:
        if type(voice) != Voice:
            raise TypeError("Parameter 'voice(Voice)' type error.")

        self.voice = voice


    def get_voice(self) -> str:
        return self.voice