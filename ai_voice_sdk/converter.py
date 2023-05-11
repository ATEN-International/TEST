import json
import time

from .enums import ConverterStatus
from .config import ConverterConfig, Settings
from .textedit import TextEditor
from .units import RestfulApiHandler, Tools

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
    40199: 'Do not support self-signed certificate server.',
    40499: 'Unknown error. Can not get Restful API response, maybe "server url" is wrong.',
}


class ConverterResult(object):
    """
    status：轉換器的狀態\n
    data：[{"id": (int)task_id, "data": (byte)auido_data}]\n
    detail：結果說明\n
    error_msg：error message
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
                    Tools().save_wav_file(filename + file_number, each_data['data'])
                count += 1


class VoiceConverter(object):
    config:ConverterConfig
    text:TextEditor
    _api_handler:RestfulApiHandler

    _text = []

    _task_list = [] # [{"id": "0~XX", "text": "paragraphs"}]
    _task_ssml_temp = [] # workaround for ssml file
    _task_each_text_limit = Settings.task_each_text_limit


    def __init__(self, config = ConverterConfig()):
        self._api_handler = RestfulApiHandler(config)
        self.text = TextEditor(self._text)


    def _translate_result_code(self, result_json:json) -> str:
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
        # task_list = [{"id": "123", "text": "msg"}, {"id": "456", "text": "msgg"}, {"id": "789", "text": "msggg"}]
        self._task_list.clear()

        length = 0
        count = 0
        i = 0
        self._task_list.append({"id": "", "text": ""})
        for i in range(len(self._text)-1):
            length += self._text[i]._length
            self._task_list[count]["text"] += (self._text[i]._text)
            if length + self._text[i+1]._length > self._task_each_text_limit:
                # print(f"over limit in {i} | {self._text[i]._text} | {length}")
                self._task_list.append({"id": "", "text": ""})
                count += 1
                length = 0

        if len(self._text) > 1:
            i += 1
        if length + self._text[i]._length > self._task_each_text_limit:
            self._task_list.append({"id": "", "text": self._text[i]._text})
        else:
            self._task_list[count]["text"] += self._text[i]._text

        # print(f"{i} {len(self._task_list)}\n")
        # for l in self._task_list:
        #     print(l, len(l["text"]))

    # ---------- Config ----------
    def update_config(self, config:ConverterConfig):
        self._api_handler.update_config(config)


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

                result_json = self._api_handler.add_ssml_task(task['text'])

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
                error_msg = f"{self._translate_result_code(result_json)}"
                break

            if is_wait_speech == True:
                task_status = "RUNNING"
                while task_status == "RUNNING":
                    result_json = self._api_handler.get_task_status(task['id'])
                    task_status = result_json['data']['status']
                    time.sleep(1)
                    # ConverVoiceRunning

                if result_json['code'] == 20001:
                    status = ConverterStatus.ConverVoiceCompleted
                else:
                    status = ConverterStatus.ConverVoiceFail
                    error_msg = f"{self._translate_result_code(result_json)} (In process {task_count}/{task_number})"
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
            result_json = self._api_handler.get_task_status(task['id'])

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
                    error_msg = self._translate_result_code(result_json)
                    status = ConverterStatus.ConverVoiceFail
            else:
                error_msg = self._translate_result_code(result_json)
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
            result_json = self._api_handler.get_task_audio(task['id'])

            if result_json['code'] != 20001:
                error_msg = self._translate_result_code(result_json)
                task_data.append({"id": task['id'], "data": None})
                return ConverterResult(ConverterStatus.GetSpeechFail, task_data, "", error_msg)

            task_data.append({"id": task['id'], "data": result_json['data']})
        return ConverterResult(ConverterStatus.GetSpeechSuccess, task_data, "", error_msg)
