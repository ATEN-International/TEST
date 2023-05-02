# import magic
import requests
import json

from .config import Settings
from .config import ConverterConfig
from .enums import Voice

class RestfulApiHandler(object):
    _server_url:str
    _token:str
    voice:Voice
    _ssml_version:str
    _ssml_lang:str

    _server_support_json_status_code = [200, 400, 500, 503] # 401 server回傳會少帶code參數，所以暫時移除

    def __init__(self, config:ConverterConfig) -> None:
        self._server_url = config.get_server()
        self._token = config.get_token()
        self.voice = config.get_voice()
        self._ssml_version = config.get_ssml_version()
        self._ssml_lang = config.get_ssml_lang()


    def _restful_sender(self, api_url:str, payload:map) -> requests.models.Response:
        url = f"{self._server_url}{api_url}"
        headers = {'content-type': 'application/json', 'Authorization': f'Bearer {self._token}'}
        return requests.post(url, headers=headers, json=payload, timeout=10)


    def _response_error_handler(self, result:requests.models.Response) -> json:
        """
        將不是json格式或缺少資訊的response格式化
        """
        if result.status_code == 404:
            return {"data": "Not Found", "code": result.status_code}
        elif result.status_code == 401:
            return {"data": {"status": "Not authorized."}, "code": result.status_code}
        elif result.status_code == 200:
            return { "data": "Unknown error. Can not get Restful API response, maybe 'server url' is wrong.", "code": 40499 }
        else:
            return {"data": result.text, "code": result.status_code}


    def _response_handler(self, result:requests.models.Response) -> json:
        if result.status_code in self._server_support_json_status_code:
            if result.headers['Content-Type'] == "application/json":
                if Settings.print_log:
                    print(f"Restful API: Success{result.status_code}")
                return result.json()
            else:
                if Settings.print_log:
                    print(f"Error in 200")
                return self._response_error_handler(result)
        else:
            if Settings.print_log:
                print(f"Error in undefined status code: {result.status_code}")
            return self._response_error_handler(result)


    def add_text_task(self, text:str) -> json:
        if self.voice == None:
            raise RuntimeError("Converter voice is 'None'")

        api_url = "/api/v1.0/syn/syn_text"
        payload = {
            # "orator_name": self._voice.value,
            "orator_name": self.config.voice.value,
            "text": text
        }

        # print(f"payload length(text): {len(payload['orator_name'])+len(payload['text'])}, content length: {len(payload['text'])}")
        if len(payload['text']) > 2000:
            return {"data": "字數超過限制值", "code": 40010}

        # result = self._restful_sender(api_url, payload)
        try:
            result = self._restful_sender(api_url, payload)
            return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")

        # if result.status_code in self._server_support_json_status_code:
        #     return result.json()
        # else:
        #     return self._response_to_json(result)

    def add_ssml_task(self, ssml_text:str) -> json:
        if self.voice == None:
            raise RuntimeError("Converter voice is 'None'")

        api_url = "/api/v1.0/syn/syn_ssml"
        payload = {
            "ssml": f'<speak xmlns="http://www.w3.org/2001/10/synthesis" version="{self._ssml_version}" xml:lang="{self._ssml_lang}">\
<voice name="{self.voice.value}">\
{ssml_text}\
</voice></speak>'
        }

        # ssml default length = 191
        # print(f"payload length(ssml): {len(payload['ssml'])}, content length: {len(ssml_text)}")
        if len(payload['ssml']) > 2000:
            return {"data": "字數超過限制值", "code": 40010}

        # print(f"ssml payload: {payload.get('ssml')}")

        try:
            result = self._restful_sender(api_url, payload)
            return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")

        # if result.status_code in self._server_support_json_status_code:
        #     return result.json()
        # else:
        #     return self._response_to_json(result)
        # return self._response_handler(result)


    def get_task_status(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/task_status"
        payload = {
            "task_id": task_id
        }

        # result = self._restful_sender(api_url, payload)
        try:
            result = self._restful_sender(api_url, payload)
            return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")

        # if result.status_code in self._server_support_json_status_code:
        #     return result.json()
        # else:
        #     return self._response_to_json(result)


    def get_task_audio(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/get_file"
        payload = {
            "filename": f"{task_id}.wav"
        }

        # result = self._restful_sender(api_url, payload)
        try:
            result = self._restful_sender(api_url, payload)
            if result.headers['Content-Type'] == "audio/wav":
                return {"data": result.content, "code": 20001}
            else:
                return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")

        # if result.status_code in self._server_support_json_status_code:
        #     if result.headers['Content-Type'] == "audio/wav":
        #         return {"data": result.content, "code": 20001}
        #     else:
        #         return result.json()
        # else:
        #     return self._response_to_json(result)



    def update_config(self, config:ConverterConfig):
        self._server_url = config.get_server()
        self._token = config.get_token()
        self.voice = config.get_voice()
        self._ssml_version = config.get_ssml_version()
        self._ssml_lang = config.get_ssml_lang()


class Tools(object):

    def __init__(self) -> None:
        self._support_file_type = Settings.support_file_type


    def save_wav_file(self, file_name:str, data:bytes):
        try:
            with open(f"{file_name}.wav", 'wb') as write_index:
                write_index.write(data)
                write_index.close()
        except:
            raise OSError("Save wav file fail.")



    # def _check_wav_type(self, wav_content:bytes) -> bool:
    #     if magic.from_buffer(wav_content, mime=True) == "audio/x-wav":
    #         return True
    #     return False


    def check_file_type(self, file_path:str) -> bool:
        extension = file_path[file_path.rfind('.'):]
        if extension in self._support_file_type:
            return True
            # if magic.from_file(file_path, mime=True) == 'text/plain':
            #     # print(f"extension: {extension}, {magic.from_file(file_path, mime=True)}")
            #     return True
        return False