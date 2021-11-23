import time
from datetime import datetime

import eel
import sys
import json
import math
from distutils.util import strtobool
import threading

from src.py.serialProc import SerialProc
from src.py.iniSerialize import IniSerializer, IniSection

from PIL import Image
from datetime import datetime
import base64
from io import BytesIO
import cv2
import numpy as np

PID = 24577

timerStart = True

#-----------------------------iniクラス------------------------
class Conf(IniSerializer):

    INI_FILE = "SerialMonitor.ini"

    def __init__( self ):
        self.Main = IniSection( {"pid":PID,"history":"[]"} )
        self.Element =IniSection( )
    
    @staticmethod
    def Load():
        
        return IniSerializer.Load(Conf.INI_FILE, Conf )
    
    def Save( self ):
        super().Save(Conf.INI_FILE)
    

#-----------------イベント---------------------------------------

# ウィンドウが閉じられたとき
def onCloseWindow(page, sockets):
    global comProc
    global config
    global timerStart


    print(page + 'が閉じられました。プログラムを終了します。')
    comProc.Close()
    config.Save()
    timerStart = False
    sys.exit()


@eel.expose
def Connect( strPort, nBaudrate ):
    """接続処理"""
    global comProc
    if comProc.isReady():
        # 未接続？
        comProc.Connect( strPort, nBaudrate ) # 内部で受信待ちスレッドが動く
        eel.SetStatus("Connected")
    else:
        comProc.Close() # 内部で受信待ちスレッドが開放される
        eel.SetStatus("Disconnected")
        # 再生成して待機
        comProc = SerialProc( Sender )

@eel.expose
def SendData( strData ):
    """データ送信処理"""
    global comProc
    retVal = comProc.Transmit( strData )

    if retVal == False:
        eel.SetStatus("Not Connected!")

@eel.expose
def getInitData( data ):
    """ 設定値を取得"""
    global config
    config.Element.Add( data )

@eel.expose
def getInitSendHistory( data ):
    """ 送信履歴を取得"""
    global config
    arr = json.loads( config.Main.history )

    arr.append( data )
    config.Main.history = json.dumps( arr )
    
def Sender( msg, time ):
    """ データ受信処理"""
    eel.PrintRcv(msg, time )


def pil_to_base64(img, format="png"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")

    return img_str

def cv_to_base64(img:cv2, format="png"):
    ret,data = cv2.imencode("."+format , img)
    img_str = base64.b64encode(data).decode("ascii")

    return img_str


def PrepareImage():
    # 画像ファイルを予め開いておく
    global imgs

    imgs = [
        {"src":"src/img/moji.png","center":[0,0]}, # 文字盤
        {"src":"src/img/hourNeedle.png","center":[177,18]}, # 時針
        {"src":"src/img/minNeedle.png","center":[235,15]}, # 分針
        {"src":"src/img/secNeedle.png","center":[225,13]} # 秒針
        ]
    for nCnt, info in enumerate(imgs):
        imgs[nCnt]["img"] = cv2.imread(info["src"], cv2.IMREAD_UNCHANGED)

def ImageRotate( bgImg, srcImg, angle, center):

    bg_Mask = None
    if bgImg.shape[2] == 4:
        bg_Mask = bgImg[:,:,3]
        bgImg = bgImg[:,:,:3] #cv2.cvtColor(bgImg, cv2.COLOR_BAYER_BG2BGR)

    fg3_img = srcImg[:,:,:3] # 対象RGB
    src_h, src_w = srcImg.shape[:2] # 対象のサイズ
    bg_h, bg_w = bgImg.shape[:2] # 背景のサイズ
    M = cv2.getRotationMatrix2D(center=center, angle=angle, scale=1)


    # 中心が一致するように並行移動
    M[0,2] = M[0,2] + bg_w/2 - center[0]
    M[1,2] = M[1,2] + bg_h/2 - center[1]

    # 画像にアフィン変換行列を適用する。
    src_rot = cv2.warpAffine( srcImg, M, (bg_h,bg_w)) # 前面の変形
    
    front_rot = src_rot[:,:,:3] # RGBチャンネルを切り出す
    fgM_img = src_rot[:,:,3] #Aチャンネルのみ切り出す
    mask_rot = 255 - cv2.merge( (fgM_img,fgM_img,fgM_img ) ) #マスク画像
    
    result = cv2.bitwise_and(bgImg, mask_rot)
    result = cv2.bitwise_or(result, front_rot)

    if bg_Mask is not None:
        result = cv2.merge((result[:,:,0],result[:,:,1],result[:,:,2], bg_Mask))

    return result


def DrawClock():
    global imgs
    global timerStart
    now = datetime.now()


    # 角度調整
    angles = [
        -(now.hour % 12 +1.0* now.minute / 60 ) *360.0 / 12 - 90 , #時
        -(  now.minute + 1.0*now.second/60 ) * 360.0 /60 - 90  , # 分
        -( now.second + now.microsecond/1000/1000 )* 360.0 / 60 - 90 # 秒
    ]
    imgBase = imgs[0]["img"].copy()
#    imgHour = imgs[3].rotate( -aH , expand=True)
#    imgMin = imgs[2].rotate(  -aM , expand=True )
#    imgSec = imgs[1].rotate( -aS, expand=True )

    # 針を貼り付ける
    for nCnt, angle in enumerate(angles):
        img = imgs[nCnt+1]
        imgBase = ImageRotate(imgBase, img["img"], angle, img["center"] )

    eel.showClock(cv_to_base64(imgBase))
    if timerStart:
        timer = threading.Timer(1.0/60, DrawClock)
        timer.start()


def main():
    global comProc
    global config
    global timer
    
    config = Conf.Load()
    
    PrepareImage()
    
    eel.init("src")
    
    # シリアル通信処理を待機
    comProc = SerialProc( Sender )
    
    # コンボボックスの内容生成
    p = SerialProc.ComportsList( int( config.Main.pid ) )
    print(p)
    eel.CreateComBox(  p  )
    
    # 初期設定の展開
    eel.SetInitSetting( config.Element.__dict__ )
    
    # 送信履歴の展開
    eel.SetHistory( json.loads( config.Main.history ) )

    # クロック画像生成タイマー発動
    timer = threading.Timer(0.1, DrawClock)
    timer.start()
    timerStart = True
    
    eel.start("html/main.html", size = (660,730), close_callback=onCloseWindow, suppress_error=True)
    
    comProc.Close()
    
    config.Save()



if __name__ == '__main__':
    main()