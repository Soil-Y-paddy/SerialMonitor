import time
from datetime import datetime

import eel
import sys
import json
import math
from distutils.util import strtobool

from src.py.serialProc import SerialProc
from src.py.iniSerialize import IniSerializer, IniSection

PID = 24577

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

    print(page + 'が閉じられました。プログラムを終了します。')
    comProc.Close()
    config.Save()
    
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

def main():
    global comProc
    global config
    
    config = Conf.Load()
    
    
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
    
    eel.start("html/main.html", size = (660,730), close_callback=onCloseWindow, suppress_error=True)
    
    comProc.Close()
    
    config.Save()



if __name__ == '__main__':
    main()