シンプルにTTSを呼び出し、音声合成するだけのAPIです。
音声合成エンジン自体はStyle-Bert-VITS2のVer 2,1を想定しています。
Style-Bert-VITS2のソースやモデルはこのリポジトリには付属しておりません。
利用時には、Style-Bert-VITS2のリポジトリよりソースを取得いただき、本リポジトリ内のソースファイルを、Style-Bert-VITS2のapp.pyなどが格納されている階層に配置ください。

その後、StyleBertVist2Api.pyを起動することでAPIが起動します。

HTTPのPOSTリクエストでBODYにvoicetextパラメータとして音声合成したいテキストを含めたデータを送信することで、音声合成ができます。

例：
◆HTTP POST

http://127.0.0.1:6666/voice/synthesis

◆body

{
  "voicetext":"おはようございます！ お目覚めはいかがですか？"
}
