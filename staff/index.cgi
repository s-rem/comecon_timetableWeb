#!/usr/bin/perl
# スタッフ用タイムテーブル表示
#
use lib ((getpwuid($<))[7]) . '/local/lib/perl5';
use strict;
use warnings;
use utf8;
use CGI;
use CGI::Carp qw(fatalsToBrowser); 
use Encode::Guess qw/ shiftjis euc-jp 7bit-jis /;
use Encode qw/ decode /;
use File::Spec;
use File::Basename;
use SFCON::Register_db;
binmode STDIN,  ":utf8";
binmode STDOUT, ":utf8";

# 共通定義
require( dirname(File::Spec->rel2abs($0)) . '/../timetableCmn.pl');
our ( $PrgURL, @SETime, @TrgDate, $Tspan, $Maxwidth, $Roomwidth, $CellSpc, );
my  ( $Maxcol, $Colsize, );

sub main {
    my $dayNo;
    # 定数値設定
    my $acttime = 0;
    foreach $dayNo ( 0, 1 ) {
        $acttime += $SETime[$dayNo]->{'e'} - $SETime[$dayNo]->{'s'};
        $acttime ++ if ( $SETime[$dayNo]->{'em'} > 0 );
    }
    # 日付列数
    my $daycolcnt = 2;  
    # 列数
    $Maxcol = int( $acttime * 60 / $Tspan ) + $daycolcnt;
    # 1時間分列幅
    my $colsize_h = ( $Maxwidth - ( $Roomwidth * $daycolcnt ) ) / $acttime; 
    # 1スパン分列幅
    $Colsize = int( $colsize_h / ( 60 / $Tspan ) ) - $CellSpc;

    # 出力開始
    outputHtmlHeadBodytop('タイムテーブル(staff用)');
    # タイムテーブルヘッダ出力
    outputTimeTblHead( $dayNo );
    # タイムテーブル本体取得
    my $dbobj = db_connect();
    my $sth = dbGetProg( $dbobj );
    # タイムテーブル本体出力
    my $col = 0;        # 出力済カラム数
    my $linenum = 0;    # 出力行数?
    my $oloc_seq = 0;   # 企画情報レコード番号退避
    my $oroom_name = '';    # 部屋名退避
    while( my @row = $sth->fetchrow_array ) {
        outputTimeTbl( \@row, \$linenum, \$col,
                       \$oloc_seq, \$oroom_name, $dayNo );
    }
    $sth->finish;
    # 未配置企画、中止企画出力
    foreach my $flg ( 0, 1 ) {   # この0,1は数値ではなく、偽,真
        # 前列後始末と列出力準備
        outputTimeTblMidle( $flg, $Maxcol - $col, \$col );
        # 未配置/中止企画取得
        $sth = dbGetProgDenyStop( $dbobj, $flg );
        # 未配置/中止企画出力
        my $oldprg_code = '';
        while( my @row = $sth->fetchrow_array ) {
            outputTimeTblDenyStop( \@row, \$oldprg_code );
        }
        $sth->finish;
    }
    db_disconnect( $dbobj );
    # 出力終了
    outputTimeTblTail( $Maxcol - $col );
    outputHtmlTail();
}

# タイムテーブルヘッダ部分出力
sub outputTimeTblHead {
    print '<table cellspacing="' . $CellSpc . '">' . "\n";
    print "<thead>\n";
    ## 時刻帯出力
    my $colspanval = 60 / $Tspan;
    my $ticcnt = 1; # 部屋名分
    print '<tr class="roomname">' . "\n";
    foreach my $dayNo ( 0, 1 ) {
        print '<th rowspan="2" width ="' . $Roomwidth . '" class="timeroom">' . 
              $TrgDate[$dayNo] . '</th>' . "\n";
        my $lasthour = $SETime[$dayNo]->{'e'};
        $lasthour++ if ( $SETime[$dayNo]->{'em'} > 0 );
        for ( my $c = $SETime[$dayNo]->{'s'}; $c < $lasthour; $c++ ) {
            print '<th colspan="' . $colspanval . '" class="time">' .
                  sprintf( '%02d', $c ) . '</th>' . "\n";
            $ticcnt += $colspanval;
        }
    }
    print "</tr>\n";
    ## Tspan分区切り出力
    print '<tr class="tspan">' . "\n";
    for ( my $c = 1; $c < $ticcnt; $c++ ) {
        print '<td class="tic" width="' . $Colsize . '"></td>' . "\n";
    }
    print "</tr>\n";
    print "</thead>\n";
}

# 企画本体出力
sub outputTimeTbl {
    my (
        $pArow,
        $p_linenum,
        $p_col,
        $p_oldloc_seq,
        $p_oldroom_name,
       ) = @_;
    my ( $day, $stime )  = split( /\s/, $pArow->[0] );
    my ( $day2, $etime ) = split( /\s/, $pArow->[1] );

    return if ( $day ne $TrgDate[0] && $day ne $TrgDate[1] );
    my $room_name   = decode('utf8', $pArow->[2]);
    my $prg_code    = $pArow->[3];
    my $prg_name    = decode('utf8', $pArow->[4]);
    my $loc_seq     = $pArow->[5];
    my $role_code   = $pArow->[6];
    my $psn_name    = decode('utf8', $pArow->[7]);
    my $psn_count   = $pArow->[8];
    my $psn_code    = $pArow->[9];
    my $sts_code    = $pArow->[10];
    $sts_code = '' unless defined($sts_code);
    my $sts_name    = decode('utf8', $pArow->[11]);
    $sts_name = '' unless defined($sts_name);
    my $pg_options  = decode('utf8', $pArow->[12]);

    if ( $room_name ne $$p_oldroom_name ) {
        if ( $$p_linenum != 0 ) {
            print "</td>\n";
            my $leftcol = $Maxcol - $$p_col;
            if ( $leftcol > 0 ) {
                print '<td colspan="' . $leftcol . '" rowspan="1" ' .
                      'class="no-use"></td>' . "\n";
            }
            print "</tr>\n";
            $$p_col = 0;
        }
        print "<tr>\n";
        print '<th width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
              'class="room">' . $room_name . "</th>\n";
        $$p_oldroom_name = $room_name;
        $$p_oldloc_seq = 0;
    }
    my ( $s_tm_h, $s_tm_m ) = split( /:/, $stime );
    my ( $e_tm_h, $e_tm_m ) = split( /:/, $etime );
    my $scol = 0;
    my $wkt;
    if ( $day eq  $TrgDate[0] ) {
        $wkt = $SETime[0]->{'s'};
    }
    else {
        $wkt = $SETime[1]->{'s'};
        my $day1Hour = $SETime[0]->{'e'} - $SETime[0]->{'s'};
        $day1Hour ++ if ( $SETime[0]->{'em'} > 0 );  # 初日の時間数
        $scol = ( ( $day1Hour * 60 ) / $Tspan ) + 1; # 二日目の日付列
    } 
    # 開始列は切り捨て、終了列は切り上げ
    my ( $s_col, $e_col );
    $s_col = int( ( (($s_tm_h-$wkt)*60+$s_tm_m ) / $Tspan )       ) + $scol;
    $e_col = int( ( (($e_tm_h-$wkt)*60+$e_tm_m ) / $Tspan ) + 0.9 ) + $scol;
    my $leftcolval = $s_col - $$p_col;
    if ( $leftcolval > 0 ) {
        print '<td colspan="' . $leftcolval . '" rowspan="1" ' .
              'class="no-use"></td>' . "\n";
    }
    if ( $loc_seq ne $$p_oldloc_seq ) {
        if ( $e_col ne $$p_col ) {
            if ( $$p_oldloc_seq != 0 ) {
                print "</td>\n";
            }
            my $cspan  = $e_col - $s_col;
            my $cls = ( $pg_options ne '公開' ) ? 'use' : 'open';
            print '<td colspan="' . $cspan . '" rowspan="1" ' .
                  'class="' . $cls . '">' . "\n";
            print $s_tm_h . ':' . $s_tm_m . '-' . $e_tm_h . ':' .  $e_tm_m . '<br>';
        } else {
            print "\n"; # 重複企画の間
        }
        $$p_oldloc_seq = $loc_seq;
        print '<a href ="' . $PrgURL . $prg_code . '">' .
              $prg_code . ' ' . $prg_name. '</a> [' . $pg_options . ']<br>';
    }
    $$p_col = $e_col;
    $$p_linenum++;

    my $cls = '';
    my $wksts = '';
    my $bl_s = ( $psn_count != 0 ) ? '<BLINK>★</BLINK>' : '';
    if ( $role_code eq 'PP' ) {
        $cls = 'pp';
        $cls = 'pp_ng' if ( $sts_code eq 'NG-01' || $sts_code eq 'NG-02' );
        $wksts = '出:';
        $psn_name .= ( $sts_name eq '' ) ? '[状況不明]' : "[$sts_name]";
    } elsif ( $role_code eq 'PO' ) {
        $cls = 'po';
        $wksts = '主:';
    } elsif ( $role_code eq 'PR' ) {
        $cls = 'pr';
        $wksts = '担:';
    } else {
        $cls = 'pr';
        $wksts = '＊:';
    }
    if ( $wksts ne '' ) {
        print '<span class="' . $cls . '">&nbsp;' . $wksts . $bl_s .
              '<a href="./person_detail.cgi?' . $psn_code . '">' .
              $psn_name . '</a></span>' . "\n";
    }
}

# 未配置/中止企画出力準備
sub outputTimeTblMidle {
    my (
        $stopflg,   # 中止企画を抽出するか?
        $leftcol,   # 後始末カラム数
        $p_col,
       ) = @_;
    if ( $leftcol > 0 ) {
        print "</td>\n";
        print '<td colspan="' . $leftcol . '" rowspan="1" ' .
              'class="no-use"></td>' . "\n";
    }
    my $roomname = ( $stopflg ) ? '中止企画' : '未配置企画';
    my $cls      = ( $stopflg ) ? 'stop'     : 'unset';
    print "</tr>\n" .
          "<tr>\n" .
          '<th width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
          ' class="room">' . $roomname . '</th>' . "\n";
    # 間は1カラム,後は2カラム開ける
    print '<td colspan="1" rowspan="1" class="no-use"></td>' . "\n";
    $$p_col = 2;
    # 先頭部屋カラムと間の1カラム後ろの2カラムを除いたものが未配置カラム数
    my $wkcol = $Maxcol - ( 1 + 1 + $$p_col );
    print '<td colspan="' . $wkcol . '" rowspan="1" class="' . $cls . '">';
}

# 未配置/中止企画出力
sub outputTimeTblDenyStop {
    my (
        $pArow,
        $p_oldprg_code,
       ) = @_;

    my $prg_code   = $pArow->[0];
    my $prg_name   = decode('utf8', $pArow->[1]);
    my $prg_option = decode('utf8', $pArow->[2]);
    my $role_code  = $pArow->[3];
    my $psn_name   = decode('utf8', $pArow->[4]);
    my $psn_code   = $pArow->[5];

    if ( $prg_code ne $$p_oldprg_code ) {
        print "<hr>\n" if ( $$p_oldprg_code );
        print '<a href ="' . $PrgURL . $prg_code . '">' .
              $prg_code . ' ' . $prg_name . '</a><br>' . $prg_option ;
        $$p_oldprg_code = $prg_code;
    }
    my $cls;
    my $wksts;
    if ( $role_code eq 'PP' ) {
        $wksts = '出:';
        $cls = 'pp';
    } elsif ($role_code eq 'PO' ) {
        $wksts = '主:';
        $cls = 'po';
    } elsif ($role_code eq 'PR' ) {
        $wksts = '担:';
        $cls = 'pr';
    } else {
        $wksts = '＊:';
        $cls = 'pr';
    }
    print '<span class="' . $cls . '">&nbsp;' . $wksts . $psn_name . '</span> ';
}

#-----以下DB操作
#  本来はRegister_dbの中に隠蔽されるべき処理

# テーブル名定数
our ( $LCDT, $NMMT, $RLMT, $PSMT, $RNMT, $PSIF, $PSDT, );

# 企画情報取得
sub dbGetProg {
    my (
        $dbobj,     # SFCON::Register_dbオブジェクト
       ) = @_;
    my $db = $dbobj->{'database'};
    my $prefix = $dbobj->prefix();
    my $pgLcDt = $prefix . $LCDT;
    my $pgNmMt = $prefix . $NMMT;
    my $pgRlMt = $prefix . $RLMT;
    my $pgPsMt = $prefix . $PSMT;
    my $pgRnMt = $prefix . $RNMT;
    my $pgPsIf = $prefix . $PSIF;
    my $pgPsDt = $prefix . $PSDT;

    my $sth = $db->prepare(
        'SELECT a.start_time, a.end_time, b.room_name, ' .
               'c.pg_code, c.pg_name, a.seq, e.role_code, f.name, ' .
               '( SELECT count(y.person_key) ' .
                   'FROM '         . $pgLcDt . ' z ' .
                     'INNER JOIN ' . $pgPsDt . ' y ON z.pg_key = y.pg_key ' .
                     'INNER JOIN ' . $pgRlMt . ' x ON y.role_key = x.role_key' .
                  ' WHERE a.start_time < z.end_time ' .
                     'AND z.start_time < a.end_time ' .
                     'AND a.seq != z.seq ' .
                     'AND d.person_key = y.person_key ' .
                     "AND (     x.role_code = 'PP' " .
                         " OR e.role_code = 'PO' and x.role_code = 'PO' " .
                         " OR e.role_code = 'PR' ) " .
               '), ' .
               'f.seq, g.ps_code, g.ps_name, c.pg_options ' .
          'FROM ' . $pgLcDt . ' a ' .
            'INNER JOIN ' . $pgRnMt . ' b ON a.room_key     = b.seq ' .
            'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key       = c.pg_key ' .
            'INNER JOIN ' . $pgPsDt . ' d ON a.pg_key       = d.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' e ON d.role_key     = e.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' f ON d.person_key   = f.seq ' .
            'LEFT JOIN '  . $pgPsMt . ' g ON d.ps_key       = g.ps_key ' .
          'ORDER BY b.room_code, a.start_time, a.room_row, e.role_code, ' .
                   'd.ps_key, d.seq' );
    $sth->execute();
    return $sth;
}

# 未配置/中止企画情報取得
sub dbGetProgDenyStop {
    my (
        $dbobj,     # SFCON::Register_dbオブジェクト
        $stopflg,   # 中止企画を抽出するか?
       ) = @_;
    my $db = $dbobj->{'database'};
    my $prefix = $dbobj->prefix();
    my $pgLcDt = $prefix . $LCDT;
    my $pgPsDt = $prefix . $PSDT;
    my $pgNmMt = $prefix . $NMMT;
    my $pgRlMt = $prefix . $RLMT;
    my $pgPsIf = $prefix . $PSIF;

    my $condstr = ( $stopflg ) ? 'AND NOT ' : 'AND ';
    my $sth = $db->prepare(
        'SELECT b.pg_code, b.pg_name, b.pg_options, c.role_code, ' .
               'd.name, d.seq ' .
          'FROM ' . $pgPsDt . ' a ' .
            'INNER JOIN ' . $pgNmMt . ' b ON a.pg_key = b.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' c ON a.role_key = c.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' d ON a.person_key = d.seq ' .
          'WHERE ' .
            'NOT EXISTS ( ' .
              'SELECT * FROM ' . $pgLcDt . ' e WHERE a.pg_key = e.pg_key ) ' .
            $condstr .
              "( b.pg_options = '公開' OR b.pg_options = '実行' " .
                "OR b.pg_options = '調整中' ) " .
          'ORDER BY b.pg_options DESC, b.pg_code, c.role_code');
    $sth->execute();
    return $sth;
}

main();
exit;
1;
