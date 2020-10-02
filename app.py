from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage, AudioMessage, StickerMessage
)
import requests
import json
import re
import configparser

app = Flask(__name__)
#WEBサーバーの起動
if __name__ == "__main__":
    app.run()
#設定ファイルのロード
config = configparser.ConfigParser()
config.read('set.ini')
#設定ファイルセクション
SECTION = 'SECRETS'
#splatoon2 API
URL = "https://spla2.yuu26.com/"
#ナワバリ
URL_REGULAR = 'regular'
#ガチマ
URL_GACHI = 'gachi'
#リグマ
URL_LEAGUE = 'league'
#現在の情報
URL_NOW = '/now'
#次の情報
URL_NEXT = '/next'
#アクセストークン
ACCESS_TOKEN = LineBotApi(config.get(SECTION, 'ACCESS_TOKEN'))
#チャンネルシークレット
CHANNEL_SECRET = WebhookHandler(config.get(SECTION, 'CHANNEL_SECRET'))
#定型メッセージ
MESSAGE_REQUEST = "ナワバリ\nガチマ\nリグマ\nのどれかを入力してください。\n" \
    + "次の情報が見たい場合は、「次の」と先頭につけてください。\n" \
    + "例：次のナワバリ"

"""
署名検証を行い、handleに定義されている関数を呼び出す。
"""
@app.route("/callback", methods=['POST'])
def callback():
    #リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']

    #リクエストボディを取得
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)

    #署名を検証し、問題なければhandleに定義されている関数を呼び出す
    try:
        CHANNEL_SECRET.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

"""
個別handle関数
テキストメッセージが送られた場合、
返答メッセージを生成し、LINEに送る
"""
@CHANNEL_SECRET.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #ユーザからのメッセージを取得
    message = event.message.text
    #メッセージbody
    body = ""

    if "ナワバリ" == message:
        body = create_stage_body(URL_REGULAR, URL_NOW)
    elif "次のナワバリ" == message:
        body = create_stage_body(URL_REGULAR, URL_NEXT)
    elif "ガチマ" == message:
        body = create_stage_body(URL_GACHI, URL_NOW)
    elif "次のガチマ" == message:
        body = create_stage_body(URL_GACHI, URL_NEXT)
    elif "リグマ" == message:
        body = create_stage_body(URL_LEAGUE, URL_NOW)
    elif "次のリグマ" == message:
        body = create_stage_body(URL_LEAGUE, URL_NEXT)
    else:
        body = MESSAGE_REQUEST

    #生成したbodyをLINEに送る
    ACCESS_TOKEN.reply_message(event.reply_token,TextSendMessage(body))

"""
個別handle関数
音声・画像・スタンプが送られた場合、
返答メッセージを生成し、LINEに送る
"""
@CHANNEL_SECRET.add(MessageEvent, message=(StickerMessage, ImageMessage, AudioMessage))
def handle_other_messages(event):
    body = MESSAGE_REQUEST
    #生成したbodyをLINEに送る
    ACCESS_TOKEN.reply_message(event.reply_token,TextSendMessage(body))

"""
ステージ情報APIからルールとステージを取得する
"""
def create_stage_body(rule, time):
    #HPPTレスポンスを受け取る
    response = requests.get(URL + rule + time)

    #正常に受け取れたかどうか(正常:200)
    if response.status_code == 200:
        #JSONの取得
        data = response.json()
        #JSONデータをパース
        results = data['result']
        body = "🦑ルール：\n"
        for result in results:
            body = body + "　" + result['rule_ex']['name'] + "\n" \
            + "🦑ステージ：\n" \
            + "　" + result['maps_ex'][0]['name'] + "\n" \
            + "　" + result['maps_ex'][1]['name']
        return body