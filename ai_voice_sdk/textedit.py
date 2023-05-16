# -*- coding:utf-8 -*-

import re
import xml.etree.ElementTree as ET
from typing import Callable

from .config import Settings
from .units import Tools

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
    __text_limit = Settings.text_limit
    __elastic_value = Settings.elastic_value
    _support_file_type = Settings.support_file_type

    __notice_value_update: Callable[[dict], None] = None

    def __init__(self, text:list, callback = None) -> None:
        self.text = text

        if callback != None:
            self.__notice_value_update = callback


    def __check_reserved_word(self, text:str) -> str:
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


    def __count_reserved_word(self, text:str) -> int:
        count = 0
        reserved_word_list = [r'"', r'&', r"'", r'<', r'>']
        for key_word in reserved_word_list:
            count += len(re.findall(key_word, text))

        return count*6


    def __check_text_length(self, text:str) -> list:
        """
        檢查傳入的文字有沒有超出限制，如果超出限制會以標點符號分割字串
        """
        limit = self.__text_limit
        result = []
        text_length = len(text)
        merge_start_position = 0
        split_position = limit
        punctuation = ['。', '！', '!', '？', '?', '\n', '\t', '，', ',', '、', '　', ' ', '（', '）', '(', ')', '「', '」', '；', '﹔']

        reserved_lenth = 0
        while(split_position < text_length):
            reserved_lenth = self.__count_reserved_word(text[merge_start_position:split_position])
            if reserved_lenth >= limit:
                raise ValueError("Use too much reserved word.")

            split_position -= reserved_lenth
            # 從分割點開始向前尋找標點符號
            for i in range(split_position-1, merge_start_position, -1):
                if text[i] in punctuation:
                    split_position = i
                    break

            # 分段儲存文字
            # result.append(text[merge_start_position:split_position])
            result.append(TextParagraph(text[merge_start_position:split_position]))
            # 實際分割點(標點符號位置)設為新分割點
            merge_start_position = split_position

            split_position += limit

        # result.append(text[merge_start_position:])
        if self.__count_reserved_word(text[merge_start_position:]) > self.__elastic_value: # elastic_value = 200
            raise ValueError("Use too much reserved word.")

        result.append(TextParagraph(text[merge_start_position:]))

        return result


    def _add_phoneme(self, text:str, ph:str):
        """
        text：加入的文字\n
         ph ：指定的發音
        """

        alphabet = "bopomo"
        lang = "TW"
        return f'<phoneme alphabet="{alphabet}" lang="{lang}" ph="{ph}">{text}</phoneme>'


    def _add_break(self, break_time:int):
        """
        break_time：停頓的時間 (最大值為5000，單位ms)\n
        若輸入值大於上限值，以最大值替代
        """

        if break_time > 5000:
            if Settings.print_log:
                print("[DEBUG] Out of range, break_time max value = 5000")
            break_time = 5000
        return f'<break time="{break_time}ms"/>'


    def _add_prosody(self, text:str, rate:float, pitch:int, volume:float):
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

        is_default_value = True

        if type(pitch) != int:
            # print("[DEBUG] Pitch type wrong")
            pitch = int(pitch)

        if rate != rate_default:
            is_default_value = False
            if rate > rate_max:
                # print("[DEBUG] Rate out of range, use the maximum to translate.")
                tag_rate = f' rate="{rate_max}"'
            elif rate < rate_min:
                # print("[DEBUG] Rate out of range, use the minimum to translate.")
                tag_rate = f' rate="{rate_min}"'
            else:
                tag_rate = f' rate="{rate}"'

        if pitch != pitch_default:
            is_default_value = False
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
            is_default_value = False
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

        if is_default_value:
            tag_rate = ' rate="1.0"'

        return f'<prosody{tag_rate}{tag_pitch}{tag_volume}>{text}</prosody>'


    def _get_ssml_all_tags(self, element:ET.Element, layer = 1) -> list:
        """
        element: 套件解析後的element tree\n
        layer: 第幾層的節點(default layer = 1)
        """
        ssml_tags:list = [] # [layer, tag, attrib, text]
        tag:str = element.tag[element.tag.rfind('}')+1:]
        text:str = ""

        if element.text:
            text = element.text

        # Add ssml tag to list
        ssml_tags.append({"layer": layer, "tag": tag, "attrib": element.attrib, "text": text})

        for child in element:
            ssml_tags += self._get_ssml_all_tags(child, layer+1)
            if child.tail:
                ssml_tags.append({"layer": layer, "tag": "tail", "attrib": None, "text": child.tail})

        return ssml_tags



    def ssml_tag_to_text(self, ssml_tag:dict) -> str:
        if ssml_tag['tag'] == "voice":
            return ssml_tag['text']
        elif ssml_tag['tag'] == "phoneme":
            return self._add_phoneme(ssml_tag['text'], ssml_tag['attrib']['ph'])
        elif ssml_tag['tag'] == "break":
            return self._add_break(int(ssml_tag['attrib']['time'][:-2]))
        elif ssml_tag['tag'] == "prosody":
            return self._add_prosody(ssml_tag['text'], float(ssml_tag['attrib']['rate']), \
                                     int(ssml_tag['attrib']['pitch'][:-2]), float(ssml_tag['attrib']['volume'][:-2]))
        elif ssml_tag['tag'] == "tail":
            return ssml_tag['text']
        else:
            return ""


    def _format_ssml_text(self, ssml_element:ET.Element) -> list:
        limit = self.__text_limit

        ssml_tag_list = self._get_ssml_all_tags(ssml_element, 1)
        text_list = [""]

        count = 0
        length = 0
        i = 0
        is_prosody = False
        prosody_layer = 1
        prosody_start_tag = ""

        ssml_tag_list_after_check_length = []
        for tag in ssml_tag_list:
            # check is get voice tag and call converter to update config info as the same time
            if tag['tag'] == "voice":
                if self.__notice_value_update != None:
                    self.__notice_value_update({"config_voice": tag['attrib']['name']})

            # 檢查文字長度，同時檢查保留字，並存為新的text list
            text_paragraph_list = self.__check_text_length(tag['text'])

            for text in text_paragraph_list:
                ssml_tag_list_after_check_length.append({"layer": tag['layer'], "tag": tag['tag'], "attrib":tag['attrib'], \
                                                          "text": self.__check_reserved_word(text._text)})

        for i in range(len(ssml_tag_list_after_check_length)-1):
            ssml_text = self.ssml_tag_to_text(ssml_tag_list_after_check_length[i])

            if ssml_tag_list_after_check_length[i]['tag'] == "prosody":
                # 偵測到prosody tag，針對prosody情境處裡tag
                is_prosody = True

                prosody_layer = ssml_tag_list_after_check_length[i]['layer']
                ssml_text = ssml_text[:ssml_text.rfind("</prosody")] # remove '</prosody>'
                prosody_start_tag = ssml_text[:ssml_text.find(">")+1]
                # print("--> start", prosody_start_tag)

            length += len(ssml_text)
            text_list[count] += ssml_text

            if is_prosody == True:
                if (ssml_tag_list_after_check_length[i+1]['layer'] <= prosody_layer) and (ssml_tag_list_after_check_length[i+1]['tag']!= "tail"):
                    # 偵測prosody tag結尾
                    is_prosody = False
                    prosody_start_tag = ""
                    # print("--> add end tad </prosody>")
                    length += len("</prosody>")
                    text_list[count] += "</prosody>"

            if length + len(self.ssml_tag_to_text(ssml_tag_list_after_check_length[i+1])) > limit:
                # Add new text element
                text_list.append("")
                count += 1
                length = 0

                # Add prosody end tag to previous text
                if is_prosody == True:
                    text_list[count-1] += "</prosody>"
                    text_list[count] += prosody_start_tag # Add prosody header tag
                # ========================================

        if len(ssml_tag_list_after_check_length) > 1:
            i += 1

        end_tag = ""
        if is_prosody == True:
            end_tag = "</prosody>"

        last_text = self.ssml_tag_to_text(ssml_tag_list_after_check_length[i])
        if length + len(last_text) > limit:
            text_list.append((last_text + end_tag))
        else:
            text_list[count] = text_list[count] + last_text + end_tag

        return text_list


    # ---------- Text ----------
    def add_text(self, text:str, position = -1):
        """
        text：加入的文字\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self.__check_reserved_word(text_each._text))

        self.text[position:position] = text_list


    def add_webpage_text(self, text:str, rate:float = 1.0, pitch:int = 0, volume:float = 0.0, position = -1):
        """
        text    : 加入的文字\n
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")

        if position == -1:
            position = len(self.text) + 1

        text_list = self.__check_text_length(text)

        limit = self.__text_limit
        count = 0
        for text_each in text_list:
            text_each.update(self.__check_reserved_word(text_each._text))

            tags = [(match.start(), match.end()) for match in re.finditer(r'\[:(.*?)\]', text_each._text)]
            length = len(text_each._text)
            for tag in tags:
                if text_each._text[tag[1]-2] == "秒":
                    length += 15 # ssml break tag 長度最大為22 比原本多15
                else:
                    length += 51 # ssml break tag 長度最大(單一文字)為58 比原本多51

                if length > limit:
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
                    new_tag = self._add_break(int(break_time))
                    new_text = new_text[:rematch.start()+shift] + new_tag + new_text[rematch.end()+shift:]
                else:
                    if text_each._text[rematch.start()-1] == ']':
                        new_tag = ""
                        continue
                    word = text_each._text[rematch.start()-1]
                    ph = text_each._text[rematch.start()+2:rematch.end()-1]
                    new_tag = self._add_phoneme(word, ph)
                    new_text = new_text[:rematch.start()+shift-1] + new_tag + new_text[rematch.end()+shift:]
                    shift -= 1
                shift += len(new_tag) - rematch.end() + rematch.start()

            text_each.update(self._add_prosody(new_text, rate, pitch, volume))

        self.text[position:position] = text_list


    def add_ssml_text(self, text:str, position = -1):
        """
        text：加入的文字\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")

        ssml_element:ET.Element
        try:
            ssml_element = ET.fromstring(text)
        except Exception as error:
            if type(error) == ET.ParseError:
                raise ValueError(f"Ssml string {error}")
            else:
                raise RuntimeError(f"Read ssml string fail.")

        ssml_text = self._format_ssml_text(ssml_element)
        text_list = []

        if position == -1:
            position = len(self.text) + 1

        for text in ssml_text:
            text_list.append(TextParagraph(text))

        self.text[position:position] = text_list


    def get_text(self) -> list:
        if len(self.text) < 1:
            print("Text is empty.")

        result = []
        for text_each in self.text:
            result.append(text_each._text)
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
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")
        if type(ph) != str:
            raise TypeError("Parameter 'ph(str)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self._add_phoneme(\
                             self.__check_reserved_word(text_each._text), ph))

        self.text[position:position] = text_list


    def insert_break(self, break_time:int, position = -1):
        """
        break_time：停頓的時間 (最大值為5000，單位ms)\n
        若輸入值大於上限值，以最大值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(break_time) != int:
            raise TypeError("Parameter 'break_time(int)' type error.")

        if position == -1:
            position = len(self.text) + 1

        self.text.insert(position, TextParagraph(self._add_break(break_time)))


    def insert_prosody(self, text:str, rate:float = 1.0, pitch:int = 0, volume:float = 0.0, position = -1):
        """
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self._add_prosody(\
                             self.__check_reserved_word(text_each._text), rate, pitch, volume))

        self.text[position:position] = text_list


    def insert_prosody_and_phoneme(self, text:str, ph:str, \
                                   rate:float = 1.0, pitch:int = 0, volume:float = 0.0, position = -1):
        """
        text：需要修改發音的文字\n
         ph ：指定的發音\n
        rate    : 調整語速, 最小值=0.8, 最大值=1.2\n
        pitch   : 調整音調, 最小值=-2, 最大值=2\n
        volume  : 調整音量, 最小值=-6, 最大值=6\n
        若輸入超過範圍值，皆以最大/最小值替代\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")
        if type(text) != str:
            raise TypeError("Parameter 'text(str)' type error.")
        if type(ph) != str:
            raise TypeError("Parameter 'ph(str)' type error.")
        if type(rate) != float:
            raise TypeError("Parameter 'rate(float)' type error.")
        if type(pitch) != int:
            raise TypeError("Parameter 'pitch(int)' type error.")
        if type(volume) != float:
            raise TypeError("Parameter 'volume(float)' type error.")

        text_list = self.__check_text_length(text)

        if position == -1:
            position = len(self.text) + 1

        for text_each in text_list:
            text_each.update(self._add_prosody(self._add_phoneme(\
                             self.__check_reserved_word(text_each._text), ph), rate, pitch, volume))
        self.text[position:position] = text_list


    def open_text_file(self, file_path:str, encode = "utf-8", position = -1):
        """
        file_path：檔案路徑\n
         encode：檔案編碼格式\n
        position：文字加入的位置，position = -1 或大於段落總數時會加在最後\n
        """
        if type(position) != int:
            raise TypeError("Parameter 'position(int)' type error.")

        extension = file_path[file_path.rfind('.'):]
        if extension in self._support_file_type == False:
            raise TypeError(f"Open file '{file_path}' fail.")

        text = Tools().open_file(file_path, encode)

        if extension == ".ssml" or extension == ".xml":
            self.add_ssml_text(text, position)
        else:
            self.add_text(text, position)
