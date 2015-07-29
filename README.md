# comecon_timetableWeb
米魂 企画タイムテーブルCGI

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

- staff以下へのアクセス制御
    timetable/staff/.htaccessで制御する
    /home/comecon/auth/[passwd,group] で認証(BASIC)
    -> 誰を登録するかを決める必要がある

- 既にデータが格納されているのが前提のDBテーブルが有る
    データ格納方法不明
