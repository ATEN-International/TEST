from ai_voice_sdk import VoiceConverter
from ai_voice_sdk import Voice

if __name__ == "__main__":
    token = "API_ACCESS_TOKEN"
    server_url = "SERVER_URL"
    converter = VoiceConverter(server_url, token, Voice.NOETIC) # 建立轉換器，參數 token = '顯示於網頁上的token', Voice = 要使用的語音(預設為 NOETIC)

    converter.add_text("Hi 你好，以下是AI  voice   SDK  的進階範例，範例1，插入停頓300毫秒")
    converter.insert_break(300) # 加入0.3秒(300毫秒)的停頓

    converter.insert_prosody("範例2，這段文章的語速調慢、音調調低、以及音量調大。", rate=0.8, pitch=-2, volume=5.5) # 調整文章的語速、音調、音量

    converter.add_text(f"範例3，修改文章的發音，例如：大家好，變")
    converter.insert_phoneme("大家好", "ㄧㄡ ㄕㄥ ㄒㄩㄝˊ") # 修改發音，例：大家好(ㄉㄚˋ ㄐㄧㄚ ㄏㄠˇ)修改為優聲學(ㄧㄡ ㄕㄥ ㄒㄩㄝˊ)

    converter.add_text("。範例4，調整修改文章的發音並且調整將語速調快、音調調高、以及音量調小。，例如：優聲學，變")
    converter.insert_prosody_and_phoneme("優聲學", "ㄉㄚˋ ㄐㄧㄚ ㄏㄠˇ", rate=1.2, pitch=2, volume=-3.3)
    converter.show_text()
    print("\n")

    converter.add_text("在段落3插入文字", 3) # 在段落3插入文章
    converter.insert_break(500, 6) # 在段落6插入500毫秒的停頓
    converter.show_text()
    print("\n")

    converter.delete_text(3) # 刪除段落3的文章
    converter.show_text()

    converter.start_convert(wait_time = 1) # 參數wait_time = 1，表示server忙碌時，會開始排隊並每1秒確認server是否能夠開始合成

    converter.get_result("my_aivoice") # 將語音存為'my_aivoice.wav'，預設檔名為'aivoice.wav'
