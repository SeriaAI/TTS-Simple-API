import torch

import numpy as np
import gradio as gr
from scipy.io import wavfile
import datetime
from pydub import AudioSegment
from common.tts_model import ModelHolder
from infer import InvalidToneError
from text.japanese import g2kata_tone, kata_tone2phone_tone, text_normalize
from common.log import logger
from typing import Optional
import json
#import emoji

class StyleBertVits2Manager:

    def __init__(self,wave_save_path_arg):
        self.wave_save_path = wave_save_path_arg
        self.model_dir = "モデルの格納ディレクトリのパス" #例'E:\\Develop\\style-bert-vits2_API\\Style-Bert-VITS2\\Style-Bert-VITS2\\model_assets' 
        self.model_name = 'モデル名(上記モデル格納パスディレクトリ内に格納されているモデル事のフォルダ名から音声合成に利用したいモデルのフォルダ名を指定)'
        self.model_file_name = "model_assetsフォルダ内の利用したいモデル名のディレクトリ内の格納されている、どのモデルファイルを利用するかモデルファイルのパスを指定する。"

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_holder = ModelHolder(self.model_dir, self.device)

        #self.model_holder.update_model_names_gr()
        self.model_holder.refresh()
        self.model_holder.update_model_names_gr()

        self.model_holder.update_model_files_gr(self.model_name)
        self.model_holder.load_model_gr(self.model_name,self.model_file_name)
        #self.model_holder.current_model = 'G_50000.pth'



    def tts_fn(
        self,
        arg_text: str,
        reference_audio_path="",
        sdp_ratio=0.2,
        noise_scale=0.6,
        noise_scale_w=0.8,
        length_scale=0.9,
        line_split=True,
        split_interval=0.5,
        assist_text="",
        assist_text_weight=0.5,
        use_assist_text=False,
        style="Neutral",
        style_weight=0.4,
        kata_tone_json_str="",
        use_tone=False,
        speaker="seria",
        language='JP',        
    ):
        assert self.model_holder.current_model is not None

        #text = emoji.replace_emoji(arg_text)
        text = self.spliteSentence(arg_text)

        wrong_tone_message = ""
        kata_tone: Optional[list[tuple[str, int]]] = None
        if use_tone and kata_tone_json_str != "":
            if language != "JP":
                logger.warning("Only Japanese is supported for tone generation.")
                wrong_tone_message = "アクセント指定は現在日本語のみ対応しています。"
            if line_split:
                logger.warning("Tone generation is not supported for line split.")
                wrong_tone_message = (
                    "アクセント指定は改行で分けて生成を使わない場合のみ対応しています。"
                )
            try:
                kata_tone = []
                json_data = json.loads(kata_tone_json_str)
                # tupleを使うように変換
                for kana, tone in json_data:
                    assert isinstance(kana, str) and tone in (0, 1), f"{kana}, {tone}"
                    kata_tone.append((kana, tone))
            except Exception as e:
                logger.warning(f"Error occurred when parsing kana_tone_json: {e}")
                wrong_tone_message = f"アクセント指定が不正です: {e}"
                kata_tone = None

        # toneは実際に音声合成に代入される際のみnot Noneになる
        tone: Optional[list[int]] = None
        if kata_tone is not None:
            phone_tone = kata_tone2phone_tone(kata_tone)
            tone = [t for _, t in phone_tone]

        speaker_id = self.model_holder.current_model.spk2id[speaker]

        start_time = datetime.datetime.now()

        try:
            samplingRate, audio = self.model_holder.current_model.infer(
                text=text,
                language=language,
                reference_audio_path=reference_audio_path,
                sdp_ratio=sdp_ratio,
                noise=noise_scale,
                noisew=noise_scale_w,
                length=length_scale,
                line_split=line_split,
                split_interval=split_interval,
                assist_text=assist_text,
                assist_text_weight=assist_text_weight,
                use_assist_text=use_assist_text,
                style=style,
                style_weight=style_weight,
                given_tone=tone,
                sid=speaker_id,
            )
        except InvalidToneError as e:
            logger.error(f"Tone error: {e}")
            return f"Error: アクセント指定が不正です:\n{e}", None, kata_tone_json_str
        except ValueError as e:
            logger.error(f"Value error: {e}")
            return f"Error: {e}", None, kata_tone_json_str

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()

        if tone is None and language == "JP":
            # アクセント指定に使えるようにアクセント情報を返す
            norm_text = text_normalize(text)
            kata_tone = g2kata_tone(norm_text)
            kata_tone_json_str = json.dumps(kata_tone, ensure_ascii=False)
        elif tone is None:
            kata_tone_json_str = ""
        message = f"Success, time: {duration} seconds."
        if wrong_tone_message != "":
            message = wrong_tone_message + "\n" + message
        
        print('message:'+str(message))
        #return (samplingRate, audio)


        waveSavePath = self.wave_save_path + '\\' + self.make_mill_datatext() + '.wav'
        wavfile.write(waveSavePath, samplingRate, audio)

        return  waveSavePath #self.hps.data.sampling_rate, audio_concat


    def make_mill_datatext(self):
        # 現在の日付と時刻を取得
        now = datetime.datetime.now()

        # ファイル名に使用するフォーマットを設定（例：20231231_235959_999）
        formatted_date = now.strftime("%Y%m%d_%H%M%S_") + f"{now.microsecond // 1000:03d}"

        return formatted_date


    def getVoicePlayTime(self, waveFilepathList):
        voicePlayTime = 0
        #waveFilePathList = []
        for waveFilePath in waveFilepathList:
            #waveFilePath = feature.result()
            print("wave time count :" + waveFilePath)
            #waveFilePathList.append(waveFilePath)
            sound = AudioSegment.from_file(waveFilePath, "wav")
            wavePlayTime = sound.duration_seconds 

            print("voice paly time : " + str(wavePlayTime) + "秒")

            # 合成した音声の合計再生時間を求める
            if wavePlayTime != None:
                voicePlayTime = voicePlayTime + wavePlayTime
                
        print("合計 voice paly time " + str(voicePlayTime) + "秒")
        return voicePlayTime
    

    def spliteSentence(self, text):
        
        # 句読点のリスト
        punctuation_marks = ['。', '！', '!', '.', '？', '?']

        # 新しい文字列を作成
        new_text = ""
        for char in text:
            new_text += char
            if char in punctuation_marks:
                # 句読点の後に改行を追加
                new_text += '\n'

        return new_text



    def sanitizeText(self, text):
        if text == None:
            return ""
        
            # 「...」を「．．．」に置換
        text = text.replace('...', '．．．')
        
        # 「！！」（複数の「！」）を「！」に置換
        text = text.replace('！！', '！').replace('！！', '！')
        
        # 「!!」（複数の「!」）を「!」に置換
        text = text.replace('!!', '!').replace('!!', '!')

        # 「？？」（複数の「？」）を「？」に置換
        text = text.replace('？？', '？').replace('？？', '？')

        # 「??」（複数の「?」）を「?」に置換
        text = text.replace('??', '?').replace('??', '?')

        return text