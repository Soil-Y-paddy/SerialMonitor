# INIシリアライザ
import configparser

class IniSerializer:
    
    __encoding__ = "utf-8"
    
    @staticmethod
    def Load(fileName, className = None ):
        """ ConfigParserでiniファイルを読み込む"""
        """　セクションをメンバー変数としてセットする"""
        """ 引数 filenName : iniファイル名 """
        """       className : デフォルト値を持つIniSerializerを基底にもつクラス """
        
        # 初期化
        
        if( className is None ):
            className = IniSerializer
        
        if issubclass(className, IniSerializer ) == False : 
            raise ValueError("class does not inherit `IniSerializer`")
        
        retVal = className()

        # ConfigParserをロード
        retVal.__conf__ = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        retVal.__conf__.read( fileName , encoding=IniSerializer.__encoding__ )
        
        # 変数を追加
        retVal.Add( dict(retVal.__conf__) )
        return retVal
    
    def Save( self, fileName):
        # メンバ変数をConfigParserに格納し、iniファイルに書き込む
        for sName, sVal in self.__dict__.items():
            
            # プライベートメンバ?
            if sName[0] == "_" :
                continue

            if isinstance( sVal, IniSection ):
                for Key, Val in sVal.__dict__.items():
                    self.__store( sName, Key, Val )
        # 保存
        with open( fileName , 'w', encoding = IniSerializer.__encoding__ ) as cF:
            self.__conf__.write( cF )


    def __store( self, section, key, value ):
        """ ConfigParserに値を格納する"""

        # セクションが存在しない？
        if self.__conf__.has_section( section ) == False: 
            self.__conf__.add_section( section )

        self.__conf__[section][key] = str(value)
    
    
    def Add( self, params:dict ):
        """ セクションをメンバー変数として追加する"""

        if isinstance( params, dict ) == False:
            return None
            
        for k, v in params.items():
            # コメント行？
            if k[0] =="#" or k[0] ==";" : 
                continue
            
            if isinstance( v, configparser.SectionProxy ):
                v = dict( v )
                setattr( self, k, IniSection(v) )

        return self
        
class IniSection :
    """ セクションクラス"""
    """ キーをメンバー変数として設定する"""
    
    def __init__( self, p_dic:dict  = None ):
        """ コンストラクタ """
        """ p_dic : 格納するデータ """
        self.Add( p_dic )
    
    def Add( self, params:dict  ):
        """ 辞書形式の各値を、メンバー変数に設定する """
        
        if isinstance( params, dict ) == False:
            return None

        for k, v in params.items():

            # コメント行？
            if k[0] =="#" or k[0] ==";" : 
                continue

            setattr( self, k, IniSection().Add( v ) if isinstance ( v, dict ) else v )

    
    def __repr__(self):
        return str( vars( self ) )
        

if __name__ == "__main__":
	
	# サンプルコード
    class ClsA(IniSerializer):
        
        def __init__(self):
            self.TestSection = IniSection( {"TestKey1":123,"TestKey2":"Hellow"} )
            self.BlankSection =IniSection( )
            pass
    
    
    c = IniSerializer.Load("test.ini", ClsA )
    print(vars(c))
    
    c.TestSection.TestKey1=100
    c.TestSection.TestKey3 = "world"
    setattr( c.TestSection, "Find", "you")
    
    print(vars(c))
    
    
    c.Save( "test.ini" )