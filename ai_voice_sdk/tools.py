# import magic

from .config import Settings

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