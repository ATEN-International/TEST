import requests
import json
import time

from .enums import Voice, ConverterStatus
from .config import ConverterConfig, Settings
from .textedit import TextEditor
from .tools import Tools

status_and_error_codes = {
    20001: '成功',
    40001: 'Request 必填參數不完整。',
    40002: 'SSML 格式錯誤。',
    40003: 'SSML <speak> 格式錯誤。',
    40004: 'SSML <voice> 格式錯誤。',
    40005: 'SSML <phoneme> 格式錯誤。',
    40006: 'SSML <break> 格式錯誤。',
    40007: 'SSML <prosody> 格式錯誤。',
    40008: 'orator name 不存在。',
    40009: 'text為空、僅有空白鍵或無合法字元。',
    40010: '字數超過限制值',
    50001: '合成器發生未知錯誤',
    50002: 'API/syn_ssml中，tag解析出來的合成文字為空字串或非法字元。',
    50301: '合成器忙碌中',
    50302: '找不到檔案，請確認音檔是否合成成功。',
    50303: '查無此task_id。',
    50304: '合成失敗，請重新發送請求。',
    401: 'token認證錯誤或API Access未開啟(Web page)。',
    404: '找不到資源, url 錯誤。',
}


class ConverterResult(object):
    """
    status：轉換器的狀態
    """
    status:ConverterStatus
    task_data = [] # [{"id": (int)task_id, "data": (byte)auido_data}]
    detail:str
    error_message:str

    def __init__(self, status:ConverterStatus, data, detail, error_msg) -> None:
        self.status = status
        self.task_data = data
        self.detail = detail
        self.error_message = error_msg

    def save(self, filename = "aivoice") -> None:
        task_list_length = len(self.task_data)
        if task_list_length > 0:
            count = 1
            for each_data in self.task_data:
                file_number = "-" + str(count)
                if task_list_length == 1:
                    file_number = ""

                if each_data['data'] != None:
                    # print("Call save file.")
                    Tools().save_wav_file(filename + file_number, each_data['data'])
                    # _save_wav_file(filename + file_number, each_data['data'])
                count += 1
        # print("Save audio file.")


class VoiceConverter(object):
    config:ConverterConfig
    text:TextEditor
    # _server_url:str
    # _token:str

    # _voice:Voice
    _ssml_version = "1.0.demo"
    _ssml_lang = "zh-TW"

    _text = []
    # _text_limit = 1500

    # _task_id = ""
    _task_list = [] # [{"id": "0~XX", "text": "paragraphs"}]
    _task_ssml_temp = [] # workaround for ssml file
    # _task_each_text_limit = _text_limit + 200
    _task_each_text_limit = Settings.task_each_text_limit

    _server_support_json_status_code = [200, 400, 500, 503] # 401 server回傳會少帶code參數，所以暫時移除
    # _support_file_type = [".txt", ".ssml"] # 暫不支援ssml
    # _support_file_type = [".txt"]


    # _is_ssml_task = False


    def __init__(self, config = ConverterConfig()):
        self.config = ConverterConfig(config.get_token(), config.get_server())
        self.config.voice = config.get_voice()
        self.text = TextEditor(self._text)


    def _restful_sender(self, api_url:str, payload:map) -> requests.models.Response:
        url = f"{self.config.get_server()}{api_url}"
        # headers = {'content-type': 'application/json', 'Authorization': f'Bearer {token}'}
        headers = {'content-type': 'application/json', 'Authorization': f'Bearer {self.config.get_token()}'}
        return requests.post(url, headers=headers, json=payload, timeout=10)


    def _response_to_json(self, result:requests.models.Response) -> json:
        """
        將不是json格式或缺少資訊的response格式化
        """
        if result.status_code == 404:
            return {"data": "Not Found", "code": result.status_code}
        elif result.status_code == 401:
            return {"data": {"status": "Not authorized."}, "code": result.status_code}
        else:
            return {"data": result.text, "code": result.status_code}


    def _clear_content(self):
        self._task_list.clear()
        # self._is_ssml_task = False


    # ---------- API ----------
    def _add_text_task(self, text:str) -> json:
        api_url = "/api/v1.0/syn/syn_text"

        payload = {
            # "orator_name": self._voice.value,
            "orator_name": self.config.voice.value,
            "text": text
        }

        # print(f"payload length(text): {len(payload['orator_name'])+len(payload['text'])}, content length: {len(payload['text'])}")
        if len(payload['text']) > 2000:
            return {"data": "字數超過限制值", "code": 40010}

        result = self._restful_sender(api_url, payload)

        if result.status_code in self._server_support_json_status_code:
            return result.json()
        else:
            return self._response_to_json(result)


    def _add_ssml_task(self, ssml_text:str) -> json:
        api_url = "/api/v1.0/syn/syn_ssml"

        payload = {
            "ssml": f'<speak xmlns="http://www.w3.org/2001/10/synthesis" version="{self._ssml_version}" xml:lang="{self._ssml_lang}">\
                <voice name="{self.config.voice.value}">\
                {ssml_text}\
                </voice>\
            </speak>'
        }

        # ssml default length = 191
        # print(f"payload length(ssml): {len(payload['ssml'])}, content length: {len(ssml_text)}")
        if len(payload['ssml']) > 2000:
            return {"data": "字數超過限制值", "code": 40010}

        # print(f"ssml payload: {payload.get('ssml')}")
        result = self._restful_sender(api_url, payload)

        if result.status_code in self._server_support_json_status_code:
            return result.json()
        else:
            return self._response_to_json(result)


    def _get_task_status(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/task_status"

        payload = {
            "task_id": task_id
        }
        result = self._restful_sender(api_url, payload)

        if result.status_code in self._server_support_json_status_code:
            return result.json()
        else:
            return self._response_to_json(result)


    def _get_task_file(self, task_id:str, file_name:str) -> json:
        api_url = "/api/v1.0/syn/get_file"

        if len(file_name) < 1:
            file_name = task_id

        payload = {
            "filename": f"{task_id}.wav"
        }
        result = self._restful_sender(api_url, payload)

        if result.status_code in self._server_support_json_status_code:
            if result.headers['Content-Type'] == "audio/wav":
                # print("[INFO] Get wav file.")
                self._save_wav_file(file_name, result.content)
                return {"data": "SUCCESS", "code": 20001}
                # if self._check_wav_type(result.content) == True:
                #     self._save_wav_file(file_name, result.content)
                #     return {"data": "SUCCESS", "code": 20001}
                # else:
                #     return {"data": "Wav file check fail.", "code": 999}
            else:
                return result.json()
        else:
            return self._response_to_json(result)

    def _get_task_audio(self, task_id:str) -> json:
        api_url = "/api/v1.0/syn/get_file"

        payload = {
            "filename": f"{task_id}.wav"
        }
        result = self._restful_sender(api_url, payload)

        if result.status_code in self._server_support_json_status_code:
            if result.headers['Content-Type'] == "audio/wav":
                return {"data": result.content, "code": 20001}
            else:
                return result.json()
        else:
            return self._response_to_json(result)


    def _error_code_handler(self, result_json:json) -> str:
        code = result_json['code']
        if code in status_and_error_codes:
            if Settings.print_log:
                print(f"[ERROR] {status_and_error_codes[code]} (Error code: {code})")
            return status_and_error_codes[code]
        else:
            if Settings.print_log:
                print(f"[ERROR] Get server not define error code. (Error code: {code})\nMessage: {result_json['data']}")
            return result_json['data']


    def __create_task_list(self):
        # task_list = [{"id": "123", "text": "msg", "ssmlfile": 0}, {"id": "456", "text": "msgg", "ssmlfile": 0}, {"id": "789", "text": "msggg", "ssmlfile": 1}]
        self._task_list.clear()

        length = 0
        count = 0
        i = 0
        self._task_list.append({"id": "", "text": "", "ssmlfile": 0})
        for i in range(len(self._text)-1):
            length += self._text[i]._length
            self._task_list[count]["text"] += (self._text[i]._text)
            if length + self._text[i+1]._length > self._task_each_text_limit:
                # print(f"over limit in {i} | {self._text[i]._text} | {length}")
                self._task_list.append({"id": "", "text": "", "ssmlfile": 0})
                count += 1
                length = 0

        if len(self._text) > 1:
            i += 1
        if length + self._text[i]._length > self._task_each_text_limit:
            self._task_list.append({"id": "", "text": self._text[i]._text, "ssmlfile": 0})
        else:
            self._task_list[count]["text"] += self._text[i]._text

        # print(f"{i} {len(self._task_list)}\n")
        # for l in self._task_list:
        #     print(l, len(l["text"]))

    # ---------- Config ----------
    def update_config(self, config:ConverterConfig):
        self.config = ConverterConfig(config.get_token(), config.get_server())
        self.config.voice = config.get_voice()

    # ---------- Converter version ----------
    # def set_file_name(self, file_name:str):
    #     self._file_name = file_name


    # def get_file_name(self) -> str:
    #     return self._file_name


    # ---------- Task infomation ----------
    def get_task_list(self) -> list:
        result = []
        if len(self._task_list) < 1:
            print("[INFO] Task list is empty.")
            return result

        for task in self._task_list:
            result.append({"id": task['id'],"text": task['text']})
        return result


    # ---------- Task ----------
    def run(self, interval_time = 0, is_wait_speech = False) -> ConverterResult:
        """
        interval_time：伺服器忙碌時，重試合成任務間隔時間，最小值=0 (不重試), 最大值=10\n
        is_wait_speech：是否等待語音合成完成，True=執行後會等待語音合成結束，Result與(func)get_speech相同
        """
        if type(interval_time) != int:
            raise TypeError("Parameter 'wait_time(int)' type error.")
        if (interval_time < 0) or (interval_time > 10):
            raise ValueError("Parameter 'wait_time(int)' value error.")

        if len(self._text) < 1:
            raise ValueError("Text is empty.")

        self.__create_task_list()

        status = ConverterStatus.ConverterStartUp
        task_data = []
        detail = ""
        error_msg = ""

        task_number = len(self._task_list)
        task_count = 1
        result_json = {}
        for task in self._task_list:
            result_json = {"data": "task start", "code": 50301}
            while result_json['code'] == 50301:
                print(f"Waitting for server...")

                result_json = self._add_ssml_task(task['text'])

                if (interval_time == 0) or (result_json['code'] == 20001):
                    break

                time.sleep(interval_time)
                # ConverVoiceRunning

            if result_json['code'] == 20001:
                task['id'] = result_json['data']['task_id']
                if Settings.print_log:
                    print(f"[INFO] Task start, task id: '{task['id']}'")

                status = ConverterStatus.ConverVoiceStart
                detail = f"Start Convert: ({task_count}/{task_number})"
                task_data.append({"id": task['id'], "data": None})
            else:
                status = ConverterStatus.ConverVoiceFail
                if result_json['code'] == 50301:
                    status = ConverterStatus.ServerBusy
                error_msg = f"{self._error_code_handler(result_json)}"
                break

            if is_wait_speech == True:
                task_status = "RUNNING"
                while task_status == "RUNNING":
                    result_json = self._get_task_status(task['id'])
                    task_status = result_json['data']['status']
                    time.sleep(1)
                    # ConverVoiceRunning

                if result_json['code'] == 20001:
                    status = ConverterStatus.ConverVoiceCompleted
                else:
                    status = ConverterStatus.ConverVoiceFail
                    error_msg = f"{self._error_code_handler(result_json)} (In process {task_count}/{task_number})"
                    break

            task_count += 1

        if result_json['code'] == 20001:
            if is_wait_speech == True:
                return self.get_speech()

            return ConverterResult(status, task_data, detail, error_msg)

        if len(task_data) == 0:
            task_data.append({"id": "0", "data": None})

        # status = ConverterStatus.ConverVoiceFail
        return ConverterResult(ConverterStatus.ConverVoiceFail, task_data, "", error_msg)


    def check_status(self) -> ConverterResult:
        """
        合成任務狀態["SUCCESS", "ERROR", "RUNNING", "NOT_EXISTS"]
        """
        if len(self._task_list) < 1:
            raise RuntimeError("Converter task list is empty, Please start convert first.")

        status:ConverterStatus.ConverterStartUp
        task_data = []
        detail = ""
        error_msg = ""

        task_number = len(self._task_list)
        task_count = 1
        for task in self._task_list:
            result_json = self._get_task_status(task['id'])

            if result_json['code'] == 20001:
                if Settings.print_log:
                    print(f"[INFO] Task({task['id'][:8]}) convert status '{result_json['data']['status'].lower()}'")

                if result_json['data']['status'] == "SUCCESS":
                    status = ConverterStatus.ConverVoiceCompleted
                elif result_json['data']['status'] == "RUNNING":
                    status = ConverterStatus.ConverVoiceRunning
                    detail = f"Voice Converting: Task({task_count}/{task_number})"
                else:
                    # 待確認
                    error_msg = self._error_code_handler(result_json)
                    status = ConverterStatus.ConverVoiceFail
            else:
                error_msg = self._error_code_handler(result_json)
                status = ConverterStatus.ConverVoiceFail

            task_data.append({"id": task['id'], "data": None})
            task_count += 1
        return ConverterResult(status, task_data, detail, error_msg)


    def get_speech(self) -> ConverterResult:
        if len(self._task_list) < 1:
            raise RuntimeError("Converter task list is empty, Please start convert first.")

        task_data = []
        error_msg = ""
        for task in self._task_list:
            result_json = self._get_task_audio(task['id'])

            if result_json['code'] != 20001:
                error_msg = self._error_code_handler(result_json)
                task_data.append({"id": task['id'], "data": None})
                return ConverterResult(ConverterStatus.GetSpeechFail, task_data, "", error_msg)

            task_data.append({"id": task['id'], "data": result_json['data']})
        return ConverterResult(ConverterStatus.GetSpeechSuccess, task_data, "", error_msg)
