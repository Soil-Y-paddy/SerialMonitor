// メンテツール 描画スクリプト

/********************グローバル変数とプロパティ*******************/
var lstItems = false;
var isConnect = false;
var baudList = [110, 300, 600, 1200, 2400, 4800, 9600,
				 14400, 19200, 38400, 57600, 74880, 115200,
				  128000, 230400, 250000, 256000, 460800, 500000,
				 921600, 1000000, 2000000];
var ElementData = {}
var Elements = ["baud","autosc","timestamp","lfcode"];


// 該当の入力コントロールのメモリ情報を取得する。
function GetMemItem(inputObj)
{
	return lstItems[ inputObj.attr("id").substr(4) ];

}

/**************************キー入力規則************************/

$(function () {
 	//キーボード入力
	$(document).keydown(
		function(event)
		{
 
			// クリックされたキーコードを取得する
			var keyCode = event.keyCode;
			var obj = event.target;
			var jqObjects = $(":input[type=text], textarea"); // テキストボックス or テキストエリア
			var index = jqObjects.index(obj); // 現在のオブジェクトが該当？
			switch(keyCode)
			{
				case 116://F5
					return false;
				break;
				case 8: //BackSpace
					return (index != -1 ); // テキストボックス内の場合true
				case 9: //tab
					return true;
				case 37:
				case 38:
				case 89:
				case 40:	// 十字キー
					return true;
				case 13:	// Enterキー
					SendMsg();
			} 
		}
	);
	

});


/**************************pythonから呼ばれる処理************************/


// コンボボックスにシリアルポート一覧を表示
eel.expose(CreateComBox);
function CreateComBox(objCom)
{
	var selVal = ""
	for( var nCnt in objCom )
	{
		$('#portName').append( 
			$('<option>').html(objCom[nCnt]["name"]).val(objCom[nCnt]["value"]) 
		);
		// 選択候補？
		if( objCom[nCnt]["selected"] )
		{
			selVal = objCom[nCnt]["value"];
		}
	}
	// 選択候補あり？
	if( selVal != "" )
	{
		$('#portName').val(selVal);
	}
}

// 受信データを表示する
eel.expose(PrintRcv)
function PrintRcv( data, timestamp )
{
	var m = $("#rcvPanel").html();
	if( $("#timestamp").prop("checked") )
	{
		data = timestamp + data;
	}
	$("#rcvPanel").html( m + escapeHTML( data ) );
	
	if( $("#autosc").prop("checked") )
	{
		var element = document.documentElement;
		var bottom = element.scrollHeight - element.clientHeight;
		window.scroll(0, bottom);
	}
}


// 状態を表示する
eel.expose(SetStatus)
function SetStatus(info)
{
	$("#Status").html(info);
	setTimeout(RemoveStatus, 1000);
}


// 初期設定を設定する
eel.expose(SetInitSetting)
function SetInitSetting(items)
{
	
	// ボーレートセレクト
	for( var i in baudList )
	{
		$("#baud").append( $( "<option>" ).html( baudList[i]+" bps" ).val( baudList[i] ) );
	}
	$("#baud").val("115200");

	
	// 定義された設定項目でループ
	for( var id=0 ;  id < Elements.length; id++ )
	{
		var elm = Elements[id];
		
		// iniのアイテムに該当の項目がある場合
		if( elm in items )
		{
			ElementData[elm] = items[elm];
			setElementData( elm, items[elm] );
		}
		else
		{
			ElementData[elm] = getElementData( elm )
		}
		
	}
	eel.getInitData(ElementData)
	
}

eel.expose(SetHistory)
function SetHistory(items)
{
	for( var nCnt = 0 ;nCnt < items.length; nCnt++ )
	{
		$("#sendHistory").append(
			$('<option>').val( items[nCnt] ) 
		);
	}
}

/*********************************内部イベント***********************************/

function RemoveStatus()
{
	$("#Status").html("");
	
}


// [接続]ボタンが押されたとき
function Connect()
{
	// 接続中？
	if( isConnect )
	{
		$("#conBtn").val("接続");
		$("#conBtn").removeClass("ConnectedBtn");
		isConnect = false;
	}
	else
	{
		$("#conBtn").val("切断");
		$("#conBtn").addClass("ConnectedBtn");
		isConnect = true;
	}
	eel.Connect( $("#portName").val(), parseInt( $("#baud").val() ) );
}

// [出力をクリア]ボタンが押されたとき
function ClearLog()
{
	 $("#rcvPanel").html("");
}

// 設定変更通知処理
function sendChangeMsg(obj)
{
	var jqObj = $(obj);
	var id = $(obj).attr("id")
	ElementData[id] = getElementData( id )
	eel.getInitData(ElementData)


}

// [送信]ボタンが押されたとき
function SendMsg()
{
	var lfCodes = [ "","\r","\n","\r\n" ];
	var msg = $("#sendText").val();

	// 履歴探索
	var opts = $("#sendHistory option");
	var exists = false;
	for( var nCnt = 0; nCnt < opts.length; nCnt++ )
	{
		if( opts[nCnt].value == msg )
		{
			exists = true;
			break;
		}
	}
	// 新規の場合履歴を保存
	if( !exists )
	{
		
		$("#sendHistory").append(
			$('<option>').val(msg) 
		);
		eel.getInitSendHistory( msg );
	}
	lfCd = lfCodes[ parseInt( $("#lfcode").val() ) ];
	eel.SendData( msg + lfCd  );
	$("#sendText").val("")
}



/*********************************ユーティリティ***********************************/


function GetMaxMin(objItem)
{
	var retVal ={};
	retVal["max"] = objItem["Signed"] ?  Math.pow(2, (8*objItem["Size"] -1) )-1 : Math.pow(2, 8*objItem["Size"] )-1 ;
	retVal["min"] =  objItem["Signed"] ? -1*Math.pow(2, (8*objItem["Size"]-1))  : 0;
	return retVal;
}

function DefaultValue(objItem)
{
	switch(objItem["Type"])
	{
		case "I":
		case "H":
		case "Q":
			return "0";
		case "N":
			return "0.0.0.0";
		case "C":
			return "0000/00/00 00:00:00";
		default:
			return "";
	}
}
function fillZero(val,len){
	var l =val.length;
	if(val!="NaN"){
		for(var i=0;i<len-l;i++){
			val = "0" + val;
		}
	}
	return val;
}

function toHex(val){
	var val2=parseInt(val)>>>0;

	return fillZero(val2.toString(16),4).toUpperCase();

}

function escapeHTML(str)
{
    return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
}

function setElementData( elm, item )
{
	var jqObj = $("#"+elm);
	// 型を調べる
	if( jqObj.prop("tagName")=="INPUT" )
	{
		switch( jqObj.attr("TYPE") )
		{
			case "checkbox":
				jqObj.prop("checked", item.toLowerCase()=='true' || item == '1' );
			break;
			default:
				jqObj.val(item);
			}
	}
	else
	{
		jqObj.val(item);
	}
	
}

function getElementData( elm )
{
	var jqObj = $("#"+elm);
	var retVal = jqObj.val();
	// 型を調べる
	if( jqObj.prop("tagName")=="INPUT" )
	{
		switch( jqObj.attr("TYPE") )
		{
			case "checkbox":
				retVal = jqObj.prop("checked" );
			break;
			}
	}
	return retVal;

}