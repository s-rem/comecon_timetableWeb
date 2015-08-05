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
    # 定数値設定
    my $acttime = $SETime[0]->{'e'} - $SETime[0]->{'s'} +
                  $SETime[1]->{'e'} - $SETime[1]->{'s'};
    $acttime ++ if ( $SETime[0]->{'em'} > 0 );
    $acttime ++ if ( $SETime[1]->{'em'} > 0 );
    # 列数
    $Maxcol = int( $acttime * 60 / $Tspan ) + 2; # +2は2つの日付列
    # 1時間分列幅
    my $colsize_h = ( $Maxwidth - ( $Roomwidth * 2 ) ) / $acttime; 
    # 1スパン分列幅
    $Colsize = int( $colsize_h / ( 60 / $Tspan ) ) - $CellSpc;

    # 出力開始
    outputHtmlHeadBodytop();
    # タイムテーブルヘッダ出力
    outputTimeTblHead();

    # タイムテーブル本体取得
    my $dbobj = db_connect();
    my $sth = dbGetProg( $dbobj );
    # タイムテーブル本体出力
    my $col = 0;        # 出力済カラム数
    my $linenum = 0;    # 出力行数?
    my $oprg_code = 0;  # 企画番号退避
    my $oloc_seq = 0;   # 企画情報レコード番号退避
    my $oroom_name = '';    # 部屋名退避
    my $oroom_row = '';     # 表示順序退避
    while( my @row = $sth->fetchrow_array ) {
        outputTimeTbl( \@row, \$linenum, \$col,
                       \$oprg_code, \$oloc_seq, \$oroom_name, \$oroom_row );
    }
    $sth->finish;

    # 本体と未配置の間出力
    outputTimeTblMidle( $Maxcol - $col );

    # 未配置企画取得
    $sth = dbGetProgDeny( $dbobj );
    # 未配置企画出力
    my $oldprg_code = '';
    while( my @row = $sth->fetchrow_array ) {
        outputTimeTblDeny( \@row, \$oldprg_code );
    }
    $sth->finish;
    db_disconnect( $dbobj );

    # 出力終了
    outputTimeTblTail();
    outputHtmlTail();
}

# HTMLヘッダ部分出力
sub outputHtmlHeadBodytop {
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print << "EOT";
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <TITLE>タイムテーブル(staff用)</TITLE>
  <link rel="stylesheet" href="./timetable.css" type="text/css">
</head>
<body>
<center>
EOT
}

# タイムテーブルヘッダ部分出力
sub outputTimeTblHead {
    print '<table border="0" cellpadding="0" cellspacing="' . $CellSpc . '" ' .
          ' bgcolor="#cccccc">' . "\n";
    print "<thead>\n";
    ## 時刻帯出力
    my $colspanval = 60 / $Tspan;
    my $ticcnt = 1; # 二日目の日付列があるので、初期値 1
    print '<tr align="center" height="20">' . "\n";
    foreach my $dayNo ( 0, 1 ) {
        print '<th rowspan="2" width ="' . $Roomwidth . '">' . 
              $TrgDate[$dayNo] . '</th>' . "\n";
        my $lasthour = $SETime[$dayNo]->{'e'};
        $lasthour++ if ( $SETime[$dayNo]->{'em'} > 0 );
        for ( my $c = $SETime[$dayNo]->{'s'}; $c < $lasthour; $c++ ) {
            print '<th colspan="' . $colspanval . '" align="left" ' .
                  'bgcolor="#FFFFFF"> ' .
                  sprintf( '%02d', $c ) . '</th>' . "\n";
            $ticcnt += $colspanval;
        }
    }
    print "</tr>\n";
    ## Tspan分区切り出力
    print '<tr align="center" height="4">' . "\n";
    for ( my $c = 1; $c < $ticcnt; $c++ ) {
        print '<td bgcolor="#FFFFFF" width="' . $Colsize . '"></td>' . "\n";
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
        $p_oldprg_code,
        $p_oldloc_seq,
        $p_oldroom_name,
        $p_oldroom_row,
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
    my $room_row    = $pArow->[9];
    my $psn_code    = $pArow->[10];
    my $sts_code    = $pArow->[11];
    $sts_code = '' unless defined($sts_code);
    my $sts_name    = decode('utf8', $pArow->[12]);
    $sts_name = '' unless defined($sts_name);
    my $pg_options  = decode('utf8', $pArow->[13]);

    if ( $prg_code ne $$p_oldprg_code ) {
        if ( $room_name ne $$p_oldroom_name || $room_row ne $$p_oldroom_row ) {
            if ( $$p_linenum != 0 ) {
                print "</font></td>\n";
                my $leftcol = $Maxcol - $$p_col;
                if ( $leftcol > 0 ) {
                    print '<td colspan="' . $leftcol . '" rowspan="1" ' .
                          'bgcolor="#c0c0c0"></td>' . "\n";
                }
                print "</tr>\n";
                $$p_col = 0;
            }
            print '<tr height="32">' . "\n";
            print '<th width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
                  'bgcolor="#E6FF8E">' . $room_name . "</th>\n";
            $$p_oldroom_name = $room_name;
            $$p_oldroom_row  = $room_row;
            $$p_oldloc_seq = 0;
        }
        my ( $s_tm_h, $s_tm_m ) = split( /:/, $stime );
        my ( $e_tm_h, $e_tm_m ) = split( /:/, $etime );
        my ( $s_col, $e_col );
        if ( $day eq  $TrgDate[0] ) {
            my $wkt = $SETime[0]->{'s'};
            $s_col = int( ( ( $s_tm_h - $wkt ) * 60 + $s_tm_m ) / $Tspan );
            $e_col = int( ( ( $e_tm_h - $wkt ) * 60 + $e_tm_m ) / $Tspan );
        }
        else {
            my $wkt = $SETime[1]->{'s'};
            my $scol =
                ( ( $SETime[0]->{'e'} - $SETime[0]->{'s'} + 1 ) * 60 ) / $Tspan
                + 1; # この+ 1 は二日目の日付列
            $s_col = int( ( ( $s_tm_h - $wkt ) * 60 + $s_tm_m ) / $Tspan )
                     + $scol;
            $e_col = int( ( ( $e_tm_h - $wkt ) * 60 + $e_tm_m ) / $Tspan )
                     + $scol;
        } 
        my $leftcolval = $s_col - $$p_col;
        if ( $leftcolval > 0 ) {
            print '<td colspan="' . $leftcolval . '" rowspan="1" ' .
                  'bgcolor="#c0c0c0"></td>' . "\n";
        }
        if ( $loc_seq ne $$p_oldloc_seq ) {
            if ( $e_col ne $$p_col ) {
                if ( $$p_oldloc_seq != 0 ) {
                    print "</font></td>\n";
                }
                my $cspan  = $e_col - $s_col;
                my $bgcolor = ( $pg_options ne '公開' ) ? '#ffe0e0' : '#e0ffe0';
                print '<td colspan="' . $cspan . '" rowspan="1" ' .
                      'bgcolor="' . $bgcolor . '">' . "\n";
            } else {
                print "</font><hr>\n";
            }
            $$p_oldloc_seq = $loc_seq;
            print '<font size = "-1">' .
                '<INPUT TYPE="CHECKBOX" name="PLS" value="' . $loc_seq . '">' .
                $stime . '-<br>';
            print '<a href ="' . $PrgURL . $prg_code . '">' . $prg_code .
                  '</a> ' . $prg_name. '[' . $pg_options . ']<br>';
        }
        $$p_oldprg_code = $prg_code;
        $$p_col = $e_col;
        $$p_linenum++;
    }
    my $pp_cls;
    my $wksts;
    my $bl_s = '<BLINK>★</BLINK>' if ( $psn_count != 0 ) ;
    if ( $role_code eq 'PP' ) {
        print '<SPAN CLASS="pp">出:';
        $wksts = ( $sts_name eq '' ) ? '[状況不明]'
                                     : "[$sts_name]";
        $pp_cls = ( $sts_code eq 'NG-01' || $sts_code eq 'NG-02' ) ? 'pp_ng'
                                                                   : 'pp';
    } elsif ( $role_code eq 'PO' ) {
        print '<SPAN CLASS="po">主:';
        $pp_cls = 'po';
    } elsif ( $role_code eq 'PR' ) {
        print '<SPAN CLASS="pr">担:';
        $pp_cls = 'pr';
    } else {
        print '<SPAN CLASS="pr">＊:';
        $pp_cls = 'pr';
    }
    print $bl_s .
            '<A HREF="./person_detail.cgi?' . $psn_code .
            '" CLASS="' . $pp_cls . '" > ' .
            $psn_name . $wksts . '</a></SPAN><BR>';
}

# タイムテーブル未配置企画出力準備
sub outputTimeTblMidle {
    my (
        $leftcol,   # 後始末カラム数
       ) = @_;

    if ( $leftcol > 0 ) {
        print '</font></td>' . "\n";
        print '<td colspan="' . $leftcol . '" rowspan="1" bgcolor="#c0c0c0">' .
              '</td>' . "\n";
    }
    print "</tr>\n" .
          '<tr height="32">' . "\n" .
          '<th width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
          ' bgcolor="#E6FF8E">未配置企画<BR></th>' . "\n";
    # 間は1カラム開ける
    print '<td colspan="1" rowspan="1" bgcolor="#c0c0c0"></td>' . "\n";
    my $wkcol = $Maxcol - 2; # 後ろは2カラム開ける
    print '<td colspan="' . $wkcol . '" rowspan="1" bgcolor="#ffffff">';
}

# 未配置企画出力
sub outputTimeTblDeny {
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
        print "<br>\n" if ( $$p_oldprg_code );
        print
            '<font size = "-1">' .
            '<INPUT TYPE="CHECKBOX" name="PPC" value="' . $prg_code . '">' .
            '<a href ="' . $PrgURL . $prg_code . '">' . $prg_code .
            '</a>' . $prg_name .
            '<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' .
            $prg_option . '&nbsp;';
        $$p_oldprg_code = $prg_code;
    }
    if($role_code eq 'PP'){
        print '<font size = "-2" color="green">出:<SPAN>';
    }
    elsif($role_code eq 'PO'){
        print '<font size = "-2" color="blue">主:<SPAN>';
    }
    elsif($role_code eq 'PR'){
        print '<font size = "-2" color="red">担:<SPAN>';
    }
    print $psn_name . '</SPAN></font> ';
}

# 未配置出力後始末出力
sub outputTimeTblTail {
    print << "EOT";
</td>
<td colspan="1" rowspan="1" bgcolor="#c0c0c0"></td>
</tr>
</table>
EOT
}

# HTML完了出力
sub outputHtmlTail {
    print << "EOT";
</center>
</BODY>
</HTML>
EOT
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
               'a.room_row, f.seq, g.ps_code, g.ps_name, c.pg_options ' .
          'FROM ' . $pgLcDt . ' a ' .
            'INNER JOIN ' . $pgRnMt . ' b ON a.room_key = b.seq ' .
            'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key = c.pg_key ' .
            'INNER JOIN ' . $pgPsDt . ' d ON a.pg_key = d.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' e ON d.role_key = e.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' f ON d.person_key = f.seq ' .
            'LEFT JOIN '  . $pgPsMt . ' g ON d.ps_key = g.ps_key ' .
          'ORDER BY b.room_code, a.room_row, a.start_time, e.role_code, ' .
                   'd.ps_key, d.seq '
    );
    $sth->execute();
    return $sth;
}

# 未配置企画情報取得
sub dbGetProgDeny {
    my (
        $dbobj,     # SFCON::Register_dbオブジェクト
       ) = @_;
    my $db = $dbobj->{'database'};
    my $prefix = $dbobj->prefix();
    my $pgLcDt = $prefix . $LCDT;
    my $pgPsDt = $prefix . $PSDT;
    my $pgNmMt = $prefix . $NMMT;
    my $pgRlMt = $prefix . $RLMT;
    my $pgPsIf = $prefix . $PSIF;

    my $sth = $db->prepare(
        'SELECT b.pg_code, b.pg_name, b.pg_options, c.role_code, ' .
               'd.name, d.seq ' .
          'FROM ' . $pgPsDt . ' a ' .
            'INNER JOIN ' . $pgNmMt . ' b ON a.pg_key = b.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' c ON a.role_key = c.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' d ON a.person_key = d.seq ' .
          'WHERE NOT EXISTS ( ' .
            'SELECT * FROM ' . $pgLcDt . ' e ' .
              'WHERE a.pg_key = e.pg_key ) ' .
          'ORDER BY b.pg_options DESC, b.pg_code, c.role_code');
    $sth->execute();
    return $sth;
}

main();
exit;
1;
