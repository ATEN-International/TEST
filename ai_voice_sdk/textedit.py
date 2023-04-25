# -*- coding:utf-8 -*-

import re

from .config import Settings
from .tools import Tools

class TextParagraph(object):
    _text:str
    _length:int


    def __init__(self, text:str) -> None:
        self._text = text
        self._length = len(text)


    def update(self, text:str):
        self._text = text
        self._length = len(text)


class TextEditor(object):
    text = []
    # _text_limit = 1500
    __text_limit = Settings.text_limit

    # _support_file_type = [".txt"]
    _support_file_type = Settings.support_file_type

    def __init__(self, text:list) -> None:
        self.text = text


    def __check_reserved_word(self, text:str) -> str:
        if "</phoneme>" in text: # workaround
            return text
        if "<break" in text: # workaround
            return text
        if "</prosody>" in text: # workaround
            return text
        if '"' in text:
            # print("[DEBUG] Find reserved_word " + '"')
            text = text.replace('"', "&quot;")
        if '&' in text:
            # print("[DEBUG] Find reserved_word " + '&')
            text = text.replace('&', "&amp;")
        if "'" in text:
            # print("[DEBUG] Find reserved_word " + "'")
            text = text.replace("'", "&apos;")
        if '<' in text:
            # print("[DEBUG] Find reserved_word " + '<')
            text = text.replace('<', "&lt;")
        if '>' in text:
            # print("[DEBUG] Find reserved_word " + '>')
            text = text.replace('>', "&gt;")
        return text


    def __check_text_length(self, text:str) -> list:
        """
        檢查傳入的文字有沒有超出限制，如果超出限制會以標點符號分割字串
        """
        result = []
        text_length = len(text)
        merge_start_position = 0
        split_position = self.__text_limit
        punctuation = ['。', '！', '!', '？', '?', '\n', '\t', '，', ',', '、', '　', ' ', '（', '）', '(', ')', '「', '」', '；', '﹔']

        while(split_position < text_length):
            # 從分割點開始向前尋找標點符號
            for i in range(split_position-1, merge_start_position, -1):
                if text[i] in punctuation:
                    split_position = i
                    break
            # print(split_position)
            # 分段儲存文字
            # result.append(text[merge_start_position:split_position])
            result.append(TextParagraph(text[merge_start_position:split_position]))
            # 實際分割點(標點符號位置)設為新分割點
            merge_start_position = split_position

            split_position += self.__text_limit
        # result.append(text[merge_start_position:])
        result.append(TextParagraph(text[merge_start_position:]))
        return result


    def __add_phoneme(self, text:str, ph:str):
        """
        text：加入的文字\n
         ph ：指定的發音
        """

        alphabet = "bopomo"
        lang = "TW"
        return f'<phoneme alphabet="{alphabet}" lang="{lang}" ph="{ph}">{self.__check_reserved_word(text)}</phoneme>'


    def __add_break(self, break_time:int):
        """
        break_time：停頓的時間 (最大值為5000，單位ms)\n
        若輸入值大於上限值，以最大值替代
        """

        if break_time > 5000:
            # print("[DEBUG] Out of range, break_time max value = 5000")
            break_time = 5000
        return f'<break time="{break_time}ms"/>'


    def __add_prosody(self, text:str, rate:float, pitch:int, volume:float):
        """
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代
        """
        tag_rate = ""
        tag_pitch = ""
        tag_volume = ""

        rate_max = 1.2
        rate_min = 0.8
        rate_default = 1.0
        pitch_max = 2
        pitch_min = -2
        pitch_default = 0
        volume_max = 6.0
        volume_min = -6.0
        volume_default = 0.0

        if type(pitch) != int:
            # print("[DEBUG] Pitch type wrong")
            pitch = int(pitch)

        if rate != rate_default:
            if rate > rate_max:
                # print("[DEBUG] Rate out of range, use the maximum to translate.")
                tag_rate = f' rate="{rate_max}"'
            elif rate < rate_min:
                # print("[DEBUG] Rate out of range, use the minimum to translate.")
                tag_rate = f' rate="{rate_min}"'
            else:
                tag_rate = f' rate="{rate}"'

        if pitch != pitch_default:
            if pitch > pitch_max:
                # print("[DEBUG] Pitch out of range, use the maximum to translate.")
                tag_pitch = f' pitch="+{pitch_max}st"'
            elif pitch < pitch_min:
                # print("[DEBUG] Pitch out of range, use the minimum to translate.")
                tag_pitch = f' pitch="{pitch_min}st"'
            else:
                if pitch > 0:
                    tag_pitch = f' pitch="+{pitch}st"'
                else:
                    tag_pitch = f' pitch="{pitch}st"'

        if volume != volume_default:
            if volume > volume_max:
                # print("[DEBUG] Volume out of range, use the maximum to translate.")
                tag_volume = f' volume="+{volume_max}dB"'
            elif volume < volume_min:
                # print("[DEBUG] Volume out of range, use the minimum to translate.")
                tag_volume = f' volume="{volume_min}dB"'
            else:
                if volume > 0:
                    tag_volume = f' volume="+{volume}dB"'
                else:
                    tag_volume = f' volume="{volume}dB"'

        return f'<prosody{tag_rate}{tag_pitch}{tag_volume}>{self.__check_reserved_word(text)}</prosody>'


    # ---------- Text ----------
    def add_text(self, text:str, position = -1):
        """
        text：加入的文字\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self.__check_reserved_word(text_each._text))

        self.text[position:position] = text_list


    def add_webpage_text(self, text:str, rate:float=1.0, pitch:int=0, volume:float=0.0, position = -1):
        """
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        if position == -1:
            position = len(self.text) + 1

        # 現階段有可能轉換2次保留字
        text = self.__check_reserved_word(text)
        text_list = self.__check_text_length(text)

        # limit = 200
        count = 0
        for text_each in text_list:
            tags = [(match.start(), match.end()) for match in re.finditer(r'\[:(.*?)\]', text_each._text)]
            length = len(text_each._text)
            for tag in tags:
                if text_each._text[tag[1]-2] == "秒":
                    length += 15 # ssml break tag 長度最大為22 比原本多15
                else:
                    length += 51 # ssml break tag 長度最大(單一文字)為58 比原本多51

                # if length > limit:
                if length > self.__text_limit:
                    text_list[count+1:count+1] = [TextParagraph(text_each._text[tag[1]:])]
                    text_each._text = text_each._text[:tag[1]]
                    break
            count += 1

            # rematch
            shift = 0
            new_tag = ""
            new_text = text_each._text
            for rematch in re.finditer(r'\[:(.*?)\]', text_each._text): # 作用與 for tag in tags: 相同
                if text_each._text[rematch.end()-2] == "秒":
                    break_time = float(text_each._text[rematch.start()+2:rematch.end()-2]) * 1000
                    new_tag = self.__add_break(int(break_time))
                    new_text = new_text[:rematch.start()+shift] + new_tag + new_text[rematch.end()+shift:]
                else:
                    if text_each._text[rematch.start()-1] == ']':
                        new_tag = ""
                        # print("!!")
                        continue
                    word = text_each._text[rematch.start()-1]
                    ph = text_each._text[rematch.start()+2:rematch.end()-1]
                    new_tag = self.__add_phoneme(word, ph)
                    new_text = new_text[:rematch.start()+shift-1] + new_tag + new_text[rematch.end()+shift:]
                    shift -= 1
                shift += len(new_tag) - rematch.end() + rematch.start()

            text_each.update(new_text)

        self.text[position:position] = text_list

    def get_text(self) -> list:
        if len(self.text) < 1:
            print("Text is empty.")

        result = []
        for text_paragraph in self.text:
            result.append(text_paragraph._text)
        return result


    def show(self):
        if len(self.text) < 1:
            print("Text is empty.")

        for i in range(len(self.text)):
            print(f"{i:^3}: {self.text[i]._text}")


    def delete_paragraph(self, position:int) -> bool:
        """
        position：要刪除的段落
        return：[True, False]
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        text_length = len(self.text)
        if text_length == 0:
            print("[INTO] Text is enpty.")
            return True

        if text_length < position:
            raise ValueError("Parameter 'position(int)' value more than number of sentences.")

        del self.text[position]
        return True


    def clear(self):
        self.text.clear()


    def insert_phoneme(self, text:str, ph:str, position = -1):
        """
        text：加入的文字\n
         ph ：指定的發音\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self.__add_phoneme(text_each._text, ph))

        self.text[position:position] = text_list


    def insert_break(self, break_time:int, position = -1):
        """
        break_time：停頓的時間 (最大值為5000，單位ms)\n
        若輸入值大於上限值，以最大值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        if position == -1:
            position = len(self.text) + 1

        self.text.insert(position, TextParagraph(self.__add_break(break_time)))


    def insert_prosody(self, text:str, rate:float=1.0, pitch:int=0, volume:float=0.0, position = -1):
        """
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self.__add_prosody(text_each._text, rate, pitch, volume))

        self.text[position:position] = text_list


    def insert_prosody_and_phoneme(self, text:str, ph:str, rate:float=1.0, pitch:int=0, volume:float=0.0, position = -1):
        """
        text：需要修改發音的文字\n
         ph ：指定的發音\n
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self.__add_prosody(self.__add_phoneme(text_each._text, ph), rate, pitch, volume))
        self.text[position:position] = text_list


    def open_text_file(self, file_path:str, encode = "utf-8"):
        """
        retrun：["SUCCESS", "FAIL"]
        暫不支援ssml檔
        """
        if Tools().check_file_type(file_path) == False:
            print(f"[ERROR] Open file:{file_path} fail.")

        text = ""
        with open(file_path, 'r', encoding = encode) as f:
            text = f.read()
            f.close()
        # print(f"[INFO] Open file:{file_path} success.")
        self.add_text(text)
