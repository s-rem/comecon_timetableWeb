# comecon_timetableWeb
米魂 企画タイムテーブルCGI

- 下記の既存コードをベースに、移植作成
  - file://comecon.sakura.ne.jp/~comecon/www/management_test2/*
  - file://comecon.sakura.ne.jp/~comecon/www/timetable/*
  - file://comecon.sakura.ne.jp/~comecon/www/ftaff_timetable/*
- タイムテーブルからのリンク先には "http:// www .comecon.jp/aj?alias=p54_NNN" を指定(NNN:企画番号)
- DBアクセス等固有共通ライブラリは~comecon/local/lib/perl5/SFCONを使用(comecon_regProgWebと一緒)
