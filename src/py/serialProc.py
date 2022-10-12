from enum import Enum
from serial.tools import list_ports
import serial
import threading
import time
from datetime import datetime



class SerialProc:
    
    """ シリアル制御クラス"""
    class Stat(Enum):
        Ready       = 0   # 起動準備完了
        Connected   = 1   # 接続済み
        Closing     = 2   # 切断中


    """ シリアル制御状態enum"""

    def __init__(self, callback):
        self.__stat = SerialProc.Stat.Ready
        self.callback = callback
        pass
    
    
    
    @staticmethod
    def ComportsList(p_selPid = 0):
        """ COMポートの一覧を取得し、辞書を生成 """
        ports = list_ports.comports()
        lsRetval = []
        for nP in ports:
            name = nP.description if nP.description != 'n/a' else nP.name
            dic = {"name": name , "value":nP.device , "vid":nP.vid, "pid":nP.pid }
            dic["selected"] = ( nP.pid == p_selPid )
            lsRetval.append( dic )
            
        return lsRetval
    
    def Connect( self, p_strPort, p_nBaudrate ):
        """ 接続"""
        if( self.__stat == SerialProc.Stat.Ready ):
            self.__stat = SerialProc.Stat.Connected
            ser = serial.Serial( timeout = 0.1 )
            ser.port = p_strPort
            ser.baudrate = p_nBaudrate
            ser.open()
            self.__ser = ser
            self.__start = True
            self.__thread = threading.Thread(target = self.mainLoop )
            self.__thread.setDaemon(True)
            self.__thread.start()

        
        
    def Close( self ):
        """ 切断 """
        if( self.__stat == SerialProc.Stat.Connected ):
            self.__stat = SerialProc.Stat.Closing
            self.__ser.close()
            self.__thread.join()

    
    def mainLoop( self ):
        while(1):
            if self.__stat == SerialProc.Stat.Connected:
                c = self.__ser.readline()
                if( len(c) > 0 ):
                    strTime =  datetime.now().strftime("%H:%M:%S.%f")[:12] + " -> " if ( self.__start ) else "" 
                    self.__start =  ( ( b'\n' in c ) or ( b'\r' in c ) )
                    if self.callback is not None:
                        self.callback( c.decode(), strTime )
                    
            elif self.__stat == SerialProc.Stat.Closing:
               print("Closed")
               break
               pass
    
            time.sleep(0.01)
            
            
    def Transmit( self, data ):
        """送信"""

        retVal = False
        if self.__stat == SerialProc.Stat.Connected:
            retVal = True
            self.__ser.write( data.encode() )

        return retVal

    def Status( self ):
        return self.__stat
        
    def isConnected( self ):
        """ 接続中状態 :TRUE """
        return ( self.__stat == SerialProc.Stat.Connected )
        
    def isReady( self ):
        """ 接続前状態 :TRUE"""
        
        return ( self.__stat == SerialProc.Stat.Ready ) 


if __name__ == "__main__":
    onRecieve = False
    
    def RecieveCallback( data, timestamp ):
        global onRecieve
        # 引数： data : 受信データ(文字列)
        #       timestamp :  受信時間(HH:MM:SS.mm)
        print("{}{}".format( timestamp, data ) )
        onRecieve = True
    
    comProc = SerialProc( RecieveCallback )
    comProc.Connect("COM3", 115200) # COMポートと、通信速度を指定
    print("{} : Start ".format( datetime.now().strftime("%H:%M:%S.%f")[:12] ) )
    comProc.Transmit("Hwllow") # データ送信
    while(1):
        if onRecieve :
            comProc.Close() # 受信したら閉じる
            break
        time.sleep(1)
