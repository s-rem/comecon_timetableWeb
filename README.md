# comecon_timetableWeb
米魂 企画タイムテーブルCGI

Web機能は以下の3つ
- 公開タイムテーブル
    h ttp://www.comecon.sakura.ne.jp/timetable/?X
        X 日の指定 0:初日 1:二日目
- スタッフ用タイムテーブル
    h ttp://www.comecon.sakura.ne.jp/timetable/staff/
- 企画管理ファイルアップロード
    h ttp://www.comecon.sakura.ne.jp/timetable/staff/upload

事前準備用ツール
    comecon.sakura.ne.jp にtty loginして実行
    配置場所は、~comecon/www/come-timetable/tools
- timetable_dbinit
    タイムテーブル機能が使用するtableを作成
    固定値tableに値設定
        設定する値は、事前に以下のファイルとして作成する(ツールと同じ場所)
        - pg_role_master.csv
            koiconの同名tableと同じ値
        - pg_person_status_master.csv
            koiconの同名tableと同じ値
- timetable_roomset
    部屋情報tableに値設定
        設定する値は、事前に以下のファイルとして作成する(ツールと同じ場所)
        - room_name_master.csv
            企画管理ファイルの場所コードシートに基いて作成
- timetable_personset
    参加者情報tableに値設定
    設定する値は任意の2つのcsvファイルで作成し、ツール起動引数で指定
        1つめ: pg_person_infoに設定するデータ
        2つめ: pg_person_open_infoに設定するデータ
    これらのデータはセンシティブな情報を含むため、git管理対象外とする。
    (テンプレート pg_person_info.tpl, pg_person_open_info.tpl を管理)

以下、移植作業内容
- 下記の既存コードをベースに、移植作成
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

- 上記移植に加え、全体で使っている定数や確実に共通のサブルーチンを共通化
    まとめたファイルは
    - timetableCmn.pl

- タイムテーブルからのリンク先には "h ttp://www.comecon.jp/aj?alias=p54_NNN" を指定(NNN:企画番号)
    -> 下記ファイルに既に組み込み済みだった
    - file://koicon.sakura.ne.jp/~koicon/www/timetable/timetablebyday2_pring.cgi
    - file://koicon.sakura.ne.jp/~koicon/www/staff_timetable/timetable_full.cgi
    URLのドメインのみ変更(共通定数化)

- DBアクセス等固有共通ライブラリは~comecon/local/lib/perl5/SFCONを使用(comecon_regProgWebと一緒)

- 既にデータが格納されているのが前提のDBテーブルが有る
    データ格納方法不明
    -> pg_role_master, pg_person_status_master 固定値(koiconのDB参照)
    -> room_name_master 企画管理ファイルの場所コードシートを元に設定
    -> pg_person_info, pg_person_open_info koiconのDBと同じ内容にする

- staff以下へのアクセス制御
    timetable/staff/.htaccessで制御する
    /home/comecon/auth/[passwd,group] で認証(BASIC)
    -> 誰を登録するかを決める必要がある

