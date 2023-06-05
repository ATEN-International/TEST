import requests
import json
import wave
import io

from .config import Settings
from .config import ConverterConfig
from .enums import Voice

class RestfulApiHandler(object):
    _config:ConverterConfig

    _server_support_json_status_code = [200, 400, 500, 503] # 401 server回傳會少帶code參數，所以暫時移除

    def __init__(self, config:ConverterConfig) -> None:
        self._config = config

    def _restful_sender(self, api_url:str, payload:map) -> requests.models.Response:
        url = f"{self._config.get_server()}{api_url}"
        headers = {'content-type': 'application/json', 'Authorization': f'Bearer {self._config.get_token()}'}
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
        if self._config.voice.value == None:
            raise RuntimeError("Converter voice is 'None'")

        api_url = "/api/v1.0/syn/syn_text"
        payload = {
            "orator_name": self._config.voice.value,
            "text": text
        }

        if len(payload['text']) > 2000:
            return {"data": "字數超過限制值", "code": 40010}

        try:
            result = self._restful_sender(api_url, payload)
            return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")


    def add_ssml_task(self, ssml_text:str) -> json:
        if self._config.voice.value == None:
            raise RuntimeError("Converter voice is 'None'")

        api_url = "/api/v1.0/syn/syn_ssml"
        payload = {
            "ssml": f'<speak xmlns="http://www.w3.org/2001/10/synthesis" version="{self._config.get_ssml_version()}" xml:lang="{self._config.get_ssml_lang()}">\
<voice name="{self._config.voice.value}">\
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


    def get_task_status(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/task_status"
        payload = {
            "task_id": task_id
        }

        try:
            result = self._restful_sender(api_url, payload)
            return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")


    def get_task_audio(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/get_file"
        payload = {
            "filename": f"{task_id}.wav"
        }

        try:
            result = self._restful_sender(api_url, payload)
            if result.headers['Content-Type'] == "audio/wav":
                return {"data": result.content, "code": 20001}
            else:
                return self._response_handler(result)
        except Exception as error:
            raise Exception(f"An unexpected error occurred: {error}")


class Tools(object):

    def __init__(self) -> None:
        self._support_file_type = Settings.support_file_type


    def save_wav_file(self, file_name:str, data:bytes):
        try:
            with open(f"{file_name}.wav", 'wb') as write_index:
                write_index.write(data)
                write_index.close()
        except Exception:
            raise IOError("Save wav file fail.")


    def merge_wav_file(self, filename:str, audio_data_list:list):
        try:
            merge_data = []
            for audio_data in audio_data_list:
                reader = wave.open(io.BytesIO(audio_data), 'rb')
                merge_data.append([reader.getparams(), reader.readframes(reader.getnframes())])
                reader.close()

            writer = wave.open(f"{filename}.wav", 'wb')
            writer.setparams(merge_data[0][0])
            for data in merge_data:
                writer.writeframes(data[1])
            writer.close()
        except Exception:
            raise IOError("Merge wav file fail.")


    def open_file(self, file_path:str, encode = "utf-8") -> str:
        text = ""
        try:
            with open(file_path, 'r', encoding = encode) as f:
                text = f.read()
                f.close()
        except FileNotFoundError as error:
            raise FileNotFoundError(f"No such file or directory: {file_path}")
        except Exception:
            raise Exception(f"An unexpected error occurred: {error}")

        return text
