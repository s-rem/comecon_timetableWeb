#!/usr/bin/perl
# タイムテーブル用企画管理ファイルアップロード
#
use lib ((getpwuid($<))[7]) . '/local/lib/perl5';
use strict;
use warnings;
use utf8;
use CGI;
use CGI::Session;
use CGI::Carp qw(fatalsToBrowser);
use HTML::Template;
use HTML::FillInForm;
use SFCON::Register_db;

use Encode::Guess qw/ shiftjis euc-jp 7bit-jis /;
use Encode qw/ decode encode from_to/;

use File::Copy;
use File::Basename;
use Spreadsheet::ParseExcel;
use Spreadsheet::ParseExcel::FmtJapan;

# 最終結果出力バッファ
my $gs_print = '';

# 定数
my $upload_dir  = 'upload';      # 保存先のディレクトリ

# メイン処理
sub main {
    my $book = upload_excel();

    # 経過表示のためのヘッダ創出
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print "<body>\n<H1>解析開始</H1>\n";

    # シート選択
    my ( $Sprogram, $Sperson ) = getSheet( $book );

    # 企画シート解析(経過表示含む)
    my $programHash = analyzeSprogram( $Sprogram );

    my $dbobj = db_connect();

    # 企画をDBに登録(経過表示含む)
    registProgram2DB( $dbobj, $Sprogram, $programHash );

    # 出演者シート解析&DB追加(経過表示含む)
    registPerson2DB( $dbobj, $Sperson );

    print "<pte>" . $gs_print . "</pre>";
    db_dissconnect( $dbobj );
}

# アップロードしたファイルをExcel-Bookとして読み込む
# 本当なら解析後のファイルは不要なので削除したほうが良いのだが、
# オリジナルが削除していないのでそのままにする
#   戻り値: PerseしたExcelBookオブジェクト
sub upload_excel {
    my $q  = CGI->new();
    my $fh = $q->upload('filename');
    my $temp_path = $q->tmpFileName($fh);
    fileparse_set_fstype('MSDOS');   # WinIE用パス文字設定(File::Basename)
    my $filename    = basename($fh);
    my $upload_path = "$upload_dir/$filename";     # 保存先フルパス
    move ($temp_path, $upload_path) or die $!;
    close($fh);                      # アップロードしたファイルをclose

    my $excel = new Spreadsheet::ParseExcel;
    my $book = $excel->Parse($upload_path);

    return $book;
}

# Excelブックオブジェクトから、必要なシートオブジェクトを取り出す
#   戻り値 ( 企画シートオブジェクト, 出演者シートオブジェクト )
sub getSheet {
    my (
        $book,      # Excelブックオブジェクト
       ) = @_;
    my $program_sheet;
    my $person_sheet;

    for my $sheet ($book->worksheets()){
        my $sheetname = decode('utf8',encode('utf8',$sheet->get_name));
        print $sheetname;
        if( $sheetname eq '企画シート'){
            $program_sheet = $sheet;
            print "match<br>";
        }
        if( $sheetname eq '出演者シート'){
            my $person_sheet = $sheet;
            print "match<br>";
        }
    }
    return ( $program_sheet, $person_sheet );
}

# 企画シート解析
sub analyzeSprogram {
    my (
        $sheet,     # 企画シートオブジェクト
       ) = @_;

    my %coltable = (
        "ID"                => 'c_p_code',
        "企画名称"          => 'c_name',
        "企画名称ふりがな"  => 'c_name_f',
        "実行ステータス"    => 'c_status',
        "企画担当スタッフ"  => 'c_staff',
        "決定日付"          => 'c_date',
        "決定\n開始時刻"    => 'c_s_time',
        "決定\n終了時刻"    => 'c_e_time',
        "決定日付２"        => 'c_date2',
        "決定\n開始時刻２"  => 'c_s_time2',
        "決定\n終了時刻２"  => 'c_e_time2',
        "決定場所"          => 'c_place',
        "決定場所\nコード"  => 'c_place_code',
        "申込者"            => 'c_owner',
        "表示順序"          => 'c_room_row',
    );
    my $pHash = {};

    print "<pre>\n";
    my $maxCol = $sheet->{"MaxCol"};
    for( my $col=0; $col<=$maxCol; $col++) {
        my $val = getExcelVal($sheet,0,$col);
        if ( exists( $coltable{$val} ) ) {
            $pHash->{$coltable{$val}} = $col;
            print "$col:$val ";
        }
    }
    print "\n";
    print "</pre>\n";

    return $pHash;
}

# 企画をDBに登録(経過表示含む)
sub registProgram2DB {
    my (
        $dbobj,     # Register_DBオブジェクト
        $sheet,     # 企画シートオブジェクト
        $pHash,     # 企画情報ハッシュ
       ) = @_;

    printf("<table>");
    my $maxRow = $sheet->{"MaxRow"};
    for(my $row=1; $row<=$maxRow; $row++) {
        my $room_row = 0;
        if ($pHash->{'c_room_row'}) {
            $room_row = encode('utf8',
                            getExcelVal($sheet,$row,$pHash->{'c_room_row'}));
        }
        program_add($dbobj,
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_p_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_name'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_name_f'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_status'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_place_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_date'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_s_time'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_e_time'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_date2'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_s_time2'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_e_time2'})),
            $room_row
        );
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_p_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_staff'})),
            '-','','-','PR', 0);
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_p_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_staff'})),
            '-','','-','PR', 1);
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_p_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_owner'})),
            '-','','-','PO', 0);
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_p_code'})),
            encode('utf8', getExcelVal($sheet,$row,$pHash->{'c_owner'})),
            '-','','-','PO', 1);
    }
    print "</TABLE>\n";
}

# 出演者シート解析&DB追加(経過表示含む)
#  なぜかこちらはカラム番号決め打ちになっているが
#  オリジナルのままとする
sub registPerson2DB {
    my (
        $dbobj,     # Register_DBオブジェクト
        $sheet,     # 出演者シートオブジェクト
       ) = @_;

    print "<pre>";

    my $maxRow = $sheet->{"MaxRow"};
    my $maxCol = $sheet->{"MaxCol"};

    for(my $row=1; $row<=$maxRow; $row++) {
        print $row."  ";
        for(my $col=0; $col<=$maxCol; $col++) {
            my $cell = $sheet->{"Cells"}[$row][$col];
            my $val = "";
            if ($cell) {
                $val = $cell->Value;
            }
            print "$col:$val ";
        }
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,0)),
            encode('utf8', getExcelVal($sheet,$row,3)),
            encode('utf8', getExcelVal($sheet,$row,4)),
            encode('utf8', getExcelVal($sheet,$row,9)),
            encode('utf8', getExcelVal($sheet,$row,8)),
            'PP', 0);
        person_search($dbobj,
            encode('utf8', getExcelVal($sheet,$row,0)),
            encode('utf8', getExcelVal($sheet,$row,21)),
            encode('utf8', getExcelVal($sheet,$row,22)),
            encode('utf8', getExcelVal($sheet,$row,9)),
            encode('utf8', getExcelVal($sheet,$row,8)),
            'PP', 1);
        print "\n";
    }
    print "</pre>";
}

# Excelシートオブジェクトから値を得る
sub getExcelVal{
    my (
        $sheet,     # シートオブジェクト
        $row,       # 行番号
        $col,       # 列番号
       ) = @_;
    my $cell = $sheet->{"Cells"}[$row][$col];
    my $val = ($cell) ? decode('utf8',encode('utf8',$cell->Value))
                      : "";
    return $val;
}

#-----以下DB操作
#  本来はRegister_dbの中に隠蔽されるべき処理

# DB接続
#   戻り値: Register_dbオブジェクト
sub db_connect {
    my $dbobj = SFCON::Register_db->new;
    my $db = DBI->connect($dbobj->{ds}, $dbobj->{user}, $dbobj->{pass})
        || die "Got error $DBI::errstr when connecting to $dbobj->{ds}\n";
    $dbobj->{database} = $db;

    my $sth = $dbobj->{database}->prepare('SET NAMES utf8');
    $sth->execute;
    return $dbobj;
}

# DB切断
sub db_dissconnect {
    my (
        $dbobj,     # Register_dbオブジェクト
       ) = @_;
    $dbobj->{database}->disconnect;
}

# テーブル名定数
my $LCDT = 'pg_location_detail';
my $NMMT = 'pg_name_master';
my $RLMT = 'pg_role_master';
my $PSMT = 'pg_person_status_master';
my $RMMT = 'room_master';
my $PSIF = 'pg_person_info';
my $PSDT = 'pg_person_detail';
my $PSOPIF = 'pg_person_open_info';
my $PSOPDT = 'pg_person_open_detail';

# 企画をDBに登録する
sub program_add{
    my (
        $dbobj,         # Register_DBオブジェクト
        $p_code,        # 企画ID
        $name,          # 企画名称
        $name_f,        # 企画名称ふりがな
        $status,        # 実行ステータス
        $room_code,     # 決定場所コード
        $date1,         # 決定日付
        $start_time1,   # 決定開始時刻
        $end_time1,     # 決定終了時刻
        $date2,         # 決定日付２
        $start_time2,   # 決定開始時刻２
        $end_time2,     # 決定終了時刻２
        $room_row,      # 表示順序
       ) = @_;

    my $db = $dbobj->{database};
    my $pgPsDt = $dbobj->prefix() . $PSDT;
    my $pgLcDt = $dbobj->prefix() . $LCDT;
    my $pgNmMt = $dbobj->prefix() . $NMMT;
    my $sth;

    $sth = $db->prepare(
        'DELETE FROM ' . $pgPsDt . ' WHERE pg_key IN ' .
        '(SELECT pg_key FROM ' . $pgNmMt . ' WHERE pg_code = ?)'
        );
    $sth->execute($p_code);

    $sth = $db->prepare(
        'DELETE FROM ' . $pgLcDt . 'WHERE pg_key IN ' .
        '(SELECT pg_key FROM ' . $pgNmMt . ' WHERE pg_code = ?)'
        );
    $sth->execute($p_code);

    $sth = $db->prepare('DELETE FROM ' . $pgNmMt . ' WHERE pg_code = ?');
    $sth->execute($p_code);

    $sth = $db->prepare(
        'INSERT INTO ' . $pgNmMt .
        ' (pg_code, pg_name, pg_name_f, pg_options) VALUES(?, ?, ?, ?)'
        );
    $sth->execute($p_code, $name, $name_f, $status);

    printf("<TR>\n");
    printf("<TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD>",
            $p_code, $name, $name_f, $status);
    printf("<TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD>",
            $room_code, $date1, $start_time1, $end_time1);
    printf("<TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD>",
            $date2, $start_time2, $end_time2, $room_row);
    time_add($dbobj, $p_code, $room_code, $date1, $start_time1, $end_time1,
             $date2, $start_time2, $end_time2, $room_row);
    print "</TR>\n";
}

# 時刻を調整して登録
sub time_add{
    my (
        $dbobj,         # Register_DBオブジェクト
        $program_code,  # 企画ID
        $room_code,     # 決定場所コード
        $date1,         # 決定日付
        $start_time1,   # 決定開始時刻
        $end_time1,     # 決定終了時刻
        $date2,         # 決定日付２
        $start_time2,   # 決定開始時刻２
        $end_time2,     # 決定終了時刻２
        $room_row,      # 表示順序
       ) = @_;

    my $stime;
    my $etime;

    print '<td><font size = "-1">';
    if(($stime, $etime) = time_calc($date1, $start_time1, $end_time1)) {
        time_add_db($dbobj,
                    $program_code, $room_code, $stime, $etime, $room_row);
    }
    if(($stime, $etime) = time_calc($date2, $start_time2, $end_time2)) {
        time_add_db($dbobj,
                    $program_code, $room_code, $stime, $etime, $room_row);
    }
    print"</font></td>\n";
}

# 時刻調整
#   おそらく、開始終了時刻が省略された時の処理
#   埋め込みにも程があるが、今回はオリジナルのまま(値は変更)
sub time_calc{
    my (
        $date,          # 日付
        $start_text,    # 開始時刻
        $end_text,      # 終了時刻
       )= @_;

    my $stat;
    my $hour;
    my $min;

    $date =~ s/\//-/g;

    my($start_hour,$start_min,$end_hour,$end_min);
    if($date eq "2015-08-29"){
        ($start_hour,$start_min,$end_hour,$end_min) = (10,0,21,30);
    } elsif($date eq "2015-08-30"){
        ($start_hour,$start_min,$end_hour,$end_min) = (9,30,16,0);
    } else {
        return ();
    }
    $stat = ($hour, $min) = $start_text =~/([0-9]+):([0-9]+)/;
    print $stat . " [" . $hour . "][" . $min ."]";
    if($stat == 2){
        $start_hour = $hour;
        $start_min  = $min;
    }
    $stat = ($hour, $min) = $end_text =~/([0-9]+):([0-9]+)/;
    print $stat . " [" . $hour . "][" . $min ."]";
    if($stat == 2){
        $end_hour = $hour;
        $end_min  = $min;
    }
    my $st = sprintf("%s %02d:%02d:00", $date, $start_hour, $start_min);
    my $et = sprintf("%s %02d:%02d:00", $date, $end_hour, $end_min);
    return($st, $et);
}

# 企画開始終了時刻をDBに登録
sub time_add_db{
    my (
        $dbobj,         # Register_DBオブジェクト
        $program_code,  # 企画ID
        $room_code,     # 決定場所コード
        $start_time,    # 決定開始日時
        $end_time,      # 決定終了日時
        $room_row,      # 表示順序
       ) = @_;

    my $db = $dbobj->{database};
    my $pgLcDt = $dbobj->prefix() . $LCDT;
    my $pgRmMt = $dbobj->prefix() . $RMMT;

    my $sth = $db->prepare(
        'SELECT ' .
            'if ( ( select count(seq) from ' . $pgLcDt . ' ) = 0,1, ' .
            '       ( if ( ( select MIN(seq) from ' . $pgLcDt . ' ) <> 1, ' .
            '                1, ' .
            '                MIN(seq + 1)' .
            '            )' .
            '       )' .
            '   ) as seq_no ' .
         'FROM ' . $pgLcDt .  ' WHERE' .
         '  (seq_no + 1) NOT IN ( SELECT seq_no FROM seqtest ); ' .
         '  AND room_key IN ( SELECT seq FROM ' . $pgRmMt .
         '                       WHERE room_code = ?)' .
         '  AND end_time > ? ' .
         '  AND start_time < ? )'
        );

    my @row = $sth->fetchrow_array;
    my $room_row_gap = $room_row;
    print "ROOM: " . $room_code . "GAP: " . $room_row_gap . "<BR>";
    print "ADD ".  $start_time .",". $end_time ."<br/>";
    $sth->execute($room_code, $start_time, $end_time);

    my $pgNmMt = $dbobj->prefix() . $NMMT;
    $sth = $db->prepare(
        'INSERT INTO ' . $pgLcDt . 
        ' (pg_key, room_key, room_row, start_time, end_time) ' .
        'VALUES( ' .
            '(SELECT pg_key FROM ' . $pgNmMt . ' WHERE pg_code   = ?) , ' .
            '(SELECT seq    FROM ' . $pgNmMt . ' WHERE room_code = ?) , ' .
            '?, ?, ? )'
        );
    my $stat = $sth->execute(
            $program_code,
            $room_code,
            $room_row_gap, $start_time, $end_time);
    if(!$stat){
        print $sth->errstr;
    } elsif ($stat == 0) {
        print "No data inserted";
    } else {
        printf("%s record inserted", $stat);
    }
}

# 出演者を探して登録
#   戻り値を誰も使っていない上、意味がはっきりしないので戻り値なしにする
sub person_search {
    my (
        $dbobj,         # Register_DBオブジェクト
        $p_code,        # 企画ID
        $name,          # 出演者名前
        $name_f,        # 出演者名前ふりがな
        $p_status,      # 出演ステータス
        $p_guest,       # ゲスト申請
        $p_role,        # 役割コード PR:担当スタッフ PO:申込者 PP:出演者
        $openflg,       # 公開情報登録か否か
       ) = @_;

    # 既にutf8-decode済のはずなので以下は不要
    #   utf8::decode($name);
    #   utf8::decode($name_f);
    #   utf8::decode($p_status);
    #   utf8::decode($p_guest);
    #   utf8::decode($p_role);

    my $gsmk = $openflg ? 'O' : 'S';

    # 最終出力バッファに受け取った値を追加書き込み
    $gs_print .= sprintf(
        '<font color="blue">[' . $gsmk . ']CHECK</font>:' .
        "\t%s\t----\t%s\t%s\t%s<BR>\n",
         $p_code, $name, $name_f, $p_role);

    my $db = $dbobj->{database};
    my $sth;
    my @row;

    # 役割コードで役割マスタを検索してrole_keyとrole_nameを得る
    my $pgRlMt = $dbobj->prefix() . $RLMT;
    my $role_key;
    my  $role_name;
    $sth = $db->prepare(
            'SELECT role_key, role_name FROM ' . $pgRlMt .
            ' WHERE role_code = ?'
        );
    $sth->execute($p_role);
    while(@row = $sth->fetchrow_array) {
        $role_key = $row[0];
        # 既にutf8-decode済のはずなので以下は不要
        # utf8::decode($row[1]);
        $role_name = $row[1];
    }

    # 出演ステータスでステータスマスタを検索して、sutatus_keyを得る
    my $pgPsMt = $dbobj->prefix() . $PSMT;
    my $status_key = 0;
    $sth = $db->prepare(
            'SELECT ps_key, ps_code FROM ' . $pgPsMt . ' WHERE ps_name = ?'
        );
    $sth->execute($p_status);
    while(@row = $sth->fetchrow_array) {
        $status_key = $row[0];
    }
    if($status_key == 0 && $p_status ne ''){
        # キーが見つからなかったらエラーを最終出力バッファに追加書き込み
        $gs_print .= sprintf(
            '<font color="red">Person status not found: %s</font><BR>' . "\n",
            $p_status
        );
    }

    # 名前と役割の分割
    my $role;
    $name =~ tr/\(（\[/\t\t\t/;
    $name =~ s/\]|\)|）|\s|　//g;
    ($name, $role) = split(/\t+/,$name);

    # 名前ふりがなの取り出し
    $name_f =~ tr/あ-ん/ア-ン/;
    $name_f =~ tr/\(（/\t\t/;
    $name_f =~ s/\)|）|\s|　//g;
    ($name_f) = split(/\t+/,$name_f, 1);

    # 名前 and 名前ふりがなで出演者情報を検索して、person_idを得る
    my $pgPsIf = $dbobj->prefix();
    $pgPsIf .= $openflg ? $PSOPIF : $PSIF;
    my $person_id = 0;
    $sth = $db->prepare(
            'SELECT seq, name, name_f, name_p FROM ' . $pgPsIf .
            ' WHERE name_f = ? AND name = ?'
        );
    $sth->execute($name_f, $name);
    my $match = 0;
    while(@row = $sth->fetchrow_array) {
        $match ++;
        # 意味がわからん
        # my $row1 = $row[0];
        # utf8::decode($row[1]);
        # utf8::decode($row[2]);
        # utf8::decode($row[3]);
        # my $row2 = $row[1];
        # my $row3 = $row[2];
        # my $row4 = $row[3];

        # 取得した内容を最終出力バッファに追加書き込み
        $gs_print .= sprintf(
                "FULL MATCH:\t%s\t%s\t%s\t%s\t%s\t%s\t%s<BR>\n",
                $role_name, $p_code, $row[0], $row[1], $row[2], $row[3]
            );
        $person_id = $row[0];
    }
    if( $match == 0) { # 見つからなかったら
        # 名前 or 名前ふりがなで出演者情報を検索して、person_idを得る
        $sth = $db->prepare(
                'SELECT seq, name, name_f, name_p FROM ' . $pgPsIf .
                ' WHERE name_f = ? AND name = ?'
            );
        $sth->execute($name_f, $name);
        while(@row = $sth->fetchrow_array) {
            $match ++;
            # 意味がわからん
            # my $row1 = $row[0];
            # utf8::decode($row[1]);
            # utf8::decode($row[2]);
            # utf8::decode($row[3]);
            # my $row2 = $row[1];
            # my $row3 = $row[2];
            # my $row4 = $row[3];
        
            # 取得した内容を最終出力バッファに追加書き込み
            $gs_print .= sprintf(
                    "SEMI MATCH:\t%s\t%s\t%s\t%s\t%s\t%s\t%s<BR>\n",
                    $role_name, $p_code, $row[0], $row[1], $row[2], $row[3]
                );
            $person_id = $row[0];
        }
    }
    if ( $match == 0 ) { # それでも見つからなかったら
        # 取得失敗を最終出力バッファに追加書き込み
        $gs_print .= sprintf(
                '<font color="red">[' . $gsmk . ']NO MATCH</font>:' . 
                    "\t%s\t----\t%s\t%s\t%s<BR>\n",
                $p_code, $name, $name_f, $role
            );
        if($name_f eq '' or $name_f eq '-'){
            $name_f = '-' . $name;
        }
        if($name ne '' and $name ne '-'){
            # 新たに出演者情報を登録して、出演者を登録
            $person_id = person_info_add($dbobj, $name, $name_f, $openflg);
            person_add($dbobj, $p_code, $person_id, $role_key, $status_key,
                       $openflg);
        }
    }
    elsif ( $match > 1 ) { # 複数見つかっていたら
        # 取得失敗を最終出力バッファに追加書き込み
        $gs_print .= sprintf(
                '<font color="red">[' . $gsmk . ']TOO MATCH</font>:' .
                    "\t%s\t----\t%s\t%s\t%s<BR>\n",
                $p_code, $name, $name_f, $role
            );
    }
    else { # 一件だけ見つかっていたら
           #    ($matchは単調増加なので、$match == 1 は省略
        # 取得した内容を最終出力バッファに追加書き込み
        $gs_print .= sprintf(
                "[$gsmk]ONE MATCH:\t%s\t%s\t%s\t%s\t%s\t%s\t%s<BR>\n",
                $role_key, $p_code, $name, $name_f, $p_status, $status_key,
                $p_guest
            );
        # 出演者を登録
        person_add($dbobj, $p_code, $person_id, $role_key, $status_key,
                   $openflg);
    }
}

# 出演者をDBに登録
sub person_add {
    my(
        $dbobj,         # Register_DBオブジェクト
        $pg_code,       # 企画ID
        $ps_code,       # 参加者ID
        $ps_role,       # 役割キー
        $ps_status,     # 出演ステータスキー
        $openflg,       # 公開情報登録か否か
       ) = @_;

    my $db = $dbobj->{database};
    my $pgNmMt = $dbobj->prefix() . $NMMT;
    my $pgPsDt = $dbobj->prefix();
    $pgPsDt .= $openflg ? $PSOPDT : $PSDT;

    my $sth = $db->prepare(
            'INSERT INTO ' . $pgPsDt .
            '   (pg_key, ' .
            '    person_key, role_key, ps_key) '.
            ' VALUES ( ' .
            '    (SELECT pg_key FROM ' . $pgNmMt . ' WHERE pg_code = ?), ' .
            '    ?,          ?,        ?     ) '
        );
        $sth->execute($pg_code, $ps_code,  $ps_role, $ps_status);
}

# 新たに出演者情報を登録
#   戻り値 参加者ID
sub person_info_add {
    my (
        $dbobj,         # Register_DBオブジェクト
        $name,          # 出演者名前
        $name_f,        # 出演者名前ふりがな
        $openflg,       # 公開情報登録か否か
       ) = @_;

    my $gsmk = $openflg ? 'O' : 'S';
    my $db = $dbobj->{database};
    my $pgPsIf = $dbobj->prefix();
    $pgPsIf .= $openflg ? $PSOPIF : $PSIF;

    my $sth = $db->prepare(
            'INSERT INTO ' . $pgPsIf . ' (name, name_f) VALUES(?, ?)'
        );
    $sth->execute($name, $name_f);

    # 登録したAI番号=参加者IDを得る
    $sth = $db->prepare('SELECT LAST_INSERT_ID()');
    $sth->execute();
    my $seq_a = [$sth->fetchrow_array()]->[0];
    $gs_print .= sprintf(
            '<font color="red">[' . $gsmk . ']ADD</font>:' .
            "\t%s\t<BR>\n", $seq_a);
    return $seq_a;
}

main();
exit;
1;
