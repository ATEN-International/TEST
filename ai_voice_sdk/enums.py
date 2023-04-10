from enum import Enum

# orator
class Voice(Enum):
    NOETIC = 'Aurora_noetic'
    LITERARY = 'Aaron_literary'
    CHEERFUL = 'Bill_cheerful'
    HOST = 'Bella_host'
    VIVID = 'Bella_vivid'
    GRACEFUL = 'Bella_graceful'


class SsmlVersion(Enum):
    V1 = '1.0.demo'


class SsmlLanguage(Enum):
    TW = 'zh-TW'


class SsmlPhoneme(Enum):
    TW = 'bopomo'


class ConverterStatus(Enum):
    ConverterStartUp = 0
    ConverVoiceStart = 10
    ConverVoiceRunning = 11
    ConverVoiceCompleted = 12
    ConverVoiceFail = 13
    ServerBusy = 21
    GetSpeechSuccess = 91
    GetSpeechFail = 92
