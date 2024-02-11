# Bert VITS2 API
import StyleBertVits2Manager
from fastapi import FastAPI,Request
from pydantic import BaseModel
import uvicorn

# リクエストのデータ構造を定義
class VoiceReq(BaseModel):
    voicetext: str


# 諸々初期化

# 合成した声の保存先
voiceSavePath = "合成した音声の保存パス"
bertVits2Manager = StyleBertVits2Manager.StyleBertVits2Manager(voiceSavePath)
port = 6666

app = FastAPI()



# メソッド定義
@app.post("/voice/synthesis")
def read_item(request: VoiceReq):
    print("POST /voice/synthesis")

    text = request.voicetext
    print("param : " + str(text))

    if text == None or text == "":
        return {"filepath": "", "voicelength":0 }

    savepath = bertVits2Manager.tts_fn(text)
    print("wave file saved : " + savepath)
    
    waveFilePathList = [savepath]
    voicePlayTime = bertVits2Manager.getVoicePlayTime(waveFilePathList)

    return {"filepath": savepath, "voicelength":voicePlayTime }


if __name__ == "__main__":
  uvicorn.run("StyleBertVist2Api:app", reload=True, port=9999)