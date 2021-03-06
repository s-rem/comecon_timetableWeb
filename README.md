# comecon_timetableWeb
# 米魂 企画タイムテーブルCGI

## Web機能は以下の3つ  
(デプロイ先が、www.comecon.sakura.ne.jpの <WebHome>/come_timetable の場合)
#### 公開タイムテーブル  
    http://www.comecon.sakura.ne.jp/come_timetable/?X  
        X 日の指定 0:初日 1:二日目 省略時:0   
#### スタッフ用タイムテーブル  
    http://www.comecon.sakura.ne.jp/come_timetable/staff/  
#### 企画管理ファイルアップロード  
    http://www.comecon.sakura.ne.jp/come_timetable/staff/upload/  

## 事前準備用ツール  
    comecon.sakura.ne.jp にtty loginして実行  
    配置場所は、~comecon/www/come-timetable/tools  
#### timetable_dbinit  
    タイムテーブル機能が使用するtableの大半(6つ)を作成  
    固定値table(2つ)に値設定  
    設定する値は、事前に以下のファイルとして作成する(ツールと同じ場所)
        * pg_role_master.csv  
            koiconの同名tableと同じ値  
        * pg_person_status_master.csv  
            koiconの同名tableと同じ値
#### timetable_roomset  
    部屋情報tableを作成し、値設定  
    設定する値は、事前に以下のファイルとして作成する(ツールと同じ場所)  
        * room_name_master.csv  
            企画管理ファイルの場所コードシートに基いて作成
#### timetable_personset  
    参加者情報table(2つ)を作成し、値設定  
    設定する値は任意の2つのcsvファイルで作成し、ツール起動引数で指定  
        * 1つめ: pg_person_infoに設定するデータ  
        * 2つめ: pg_person_open_infoに設定するデータ  
    これらのデータはセンシティブな情報を含むため、git管理対象外とする。  
    (テンプレート pg_person_info.tpl, pg_person_open_info.tpl を管理)  

----

## 以下、移植作業内容  

#### 下記の既存コードをベースに、移植作成  
- file://comecon.sakura.ne.jp/~comecon/www/timetable/*  
    具体的には、下記ファイルを使用  
    - timetablebyday_print.cgi -> index.cgi  
    - timetable.css & timetablePrint.css -> timetable.css (まとめる)  
    - person_detail.cgi -> person_detail.cgi  
- file://comecon.sakura.ne.jp/~comecon/www/sftaff_timetable/*  
    具体的には、下記ファイルを使用  
    - timetable_full.cgi -> staff/index.cgi  
    - timetable.css -> staff/timetable.css  
    - person_detail.cgi -> staff/person_detail.cgi  
- file://comecon.sakura.ne.jp/~comecon/www/management_test2/*  
    具体的には、下記ファイルを使用  
    - kikaku_upload.html -> staff/upload/index.html  
    - kikaku_upload.cgi ->  staff/upload/kikaku_upload.cgi

#### 上記移植に加え、全体で使っている定数や確実に共通のサブルーチンを共通化  
    まとめたファイルは timetableCmn.pl  

#### タイムテーブルからのリンク先  
    "http://www.comecon.jp/aj?alias=p54_NNN" を指定(NNN:企画番号)  
    -> 下記ファイルに既に組み込み済みだった  
        * file://koicon.sakura.ne.jp/~koicon/www/timetable/timetablebyday2_pring.cgi  
        * file://koicon.sakura.ne.jp/~koicon/www/staff_timetable/timetable_full.cgi  
    URLのドメインのみ変更(共通定数化)  

#### DBアクセス等固有共通ライブラリ  
    ~comecon/local/lib/perl5/SFCONを使用(comecon_regProgWebと一緒)  

#### 既にデータが格納されているのが前提のDBtableが有る  
    そのtableへのデータ格納方法は以下のとおり  
        * pg_role_master, pg_person_status_master  
            固定値(koiconのDB参照)  
        * room_name_master  
            企画管理ファイルの場所コードシートを元に設定  
        * pg_person_info, pg_person_open_info  
            koiconのDBと同じ内容にする  

#### staffへのアクセス制御  
    timetable/staff/.htaccessで制御する。(BASIC認証)  
    認証情報は ~comecon/auth/timetable_staff/passwdに格納  

#### staff/uploadへのアクセス制御  
    timetable/staff/upload/.htaccess で制御する。(BASIC認証)  
    認証情報は ~comecon/auth/timetable_upload/passwdに格納
