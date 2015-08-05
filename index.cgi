#!/usr/bin/perl
# 一般用タイムテーブル表示
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
require( dirname(File::Spec->rel2abs($0)) . '/timetableCmn.pl');
our ( $PrgURL, @SETime, @TrgDate, $Tspan, $Maxwidth, $Roomwidth, $CellSpc, );
my  ( $Maxcol, $Colsize, );

sub main {
    my $dayNo = $ENV{'QUERY_STRING'};
    $dayNo = 0 if ( !defined( $dayNo ) || $dayNo eq '' );

    # 定数値設定
    my $acttime = $SETime[$dayNo]->{'e'} - $SETime[$dayNo]->{'s'};
    $acttime ++ if ( $SETime[$dayNo]->{'em'} > 0 );
    # 列数
    $Maxcol = int( $acttime * 60 / $Tspan ) + 1; # +1は日付列
    # 1時間分列幅
    my $colsize_h = ( $Maxwidth - $Roomwidth ) / $acttime;
    # 1スパン分列幅
    $Colsize = int( $colsize_h / ( 60 / $Tspan ) ) - $CellSpc;

    # 出力開始
    outputHtmlHeadBodytop();
    unless ( $dayNo =~ /[01]/ ) {
        print '<H1><Font color="red">Wrong Parameter</font></H1>' . "\n";
        outputHtmlTail();
        return;
    }


    # タイムテーブルヘッダ出力
    outputTimeTblHead( $dayNo );

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
                       \$oprg_code, \$oloc_seq, \$oroom_name, \$oroom_row, 
                       $dayNo );
    }
    $sth->finish;
    db_disconnect( $dbobj );

    # 出力終了
    outputTimeTblTail( $Maxcol - $col );
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
  <title>タイムテーブル</title>
  <link rel="stylesheet" href="./timetable.css" type="text/css">
</head>
<body>
<center>
EOT
}

# タイムテーブルヘッダ部分出力
sub outputTimeTblHead {
    my (
        $dayNo,        # 日付コード(0|1)
       ) = @_;
    print '<table border="0" cellpadding="0" cellspacing="' . $CellSpc . '" ' .
          ' bgcolor="#cccccc">' . "\n";
    print "<thead>\n";
    ## 時刻帯出力
    my $colspanval = 60 / $Tspan;
    my $ticcnt = 1; # 部屋名分
    print '<tr align="center" height="20">' . "\n";
    print '<th rowspan="2" width ="' . $Roomwidth . '" class="time">' .
          $TrgDate[$dayNo] . '</th>' . "\n";
    my $lasthour = $SETime[$dayNo]->{'e'};
    $lasthour++ if ( $SETime[$dayNo]->{'em'} > 0 );
    for ( my $c = $SETime[$dayNo]->{'s'}; $c < $lasthour; $c++ ) {
        print '<th colspan="' . $colspanval . '" align="left" ' .
              'class="time"> ' .
              sprintf( '%02d', $c ) . '</th>' . "\n";
        $ticcnt += $colspanval;
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
        $dayNo
       ) = @_;
    my ( $day,  $stime ) = split( /\s/, $pArow->[0] );
    my ( $day2, $etime ) = split( /\s/, $pArow->[1] );
    
    return unless ( $day eq $TrgDate[$dayNo] );
    my $room_name   = decode('utf8', $pArow->[2]);
    my $prg_code    = $pArow->[3];
    my $prg_name    = decode('utf8', $pArow->[4]);
    my $loc_seq     = $pArow->[5];
    my $role_code   = $pArow->[6];
    my $psn_name    = decode('utf8', $pArow->[7]);
    my $room_row    = $pArow->[8];
    my $psn_code    = $pArow->[9];
    my $sts_code    = $pArow->[10];
    $sts_code = '' unless defined($sts_code);

    if ( $prg_code ne $$p_oldprg_code ) {
        if ( $room_name ne $$p_oldroom_name || $room_row ne $$p_oldroom_row ) {
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
            print '<tr height="32">' . "\n";
            print '<th width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
                  'class="room">' . $room_name . "</th>\n";
            $$p_oldroom_name = $room_name;
            $$p_oldroom_row = $room_row;
            $$p_oldloc_seq = 0;
        }
        my ( $s_tm_h, $s_tm_m ) = split( /:/, $stime );
        my ( $e_tm_h, $e_tm_m ) = split( /:/, $etime );
        my ( $s_col, $e_col );
        my $wkt = $SETime[$dayNo]->{'s'};
        $s_col = int( ( ( $s_tm_h - $wkt ) * 60 + $s_tm_m ) / $Tspan );
        $e_col = int( ( ( $e_tm_h - $wkt ) * 60 + $e_tm_m ) / $Tspan );
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
                my $cspan = $e_col - $s_col; 
                print '<td colspan="' . $cspan . '" rowspan="1" ' .
                      'class="use">' . "\n";
            } else {
                print "<hr>\n";
            }
            $$p_oldloc_seq = $loc_seq;
            print $stime . '-<br>';
            print '<a href ="' . $PrgURL . $prg_code . '">' .  $prg_code .
                  '</a> ' . $prg_name . '<br>';
        }
        $$p_oldprg_code = $prg_code;
        $$p_col = $e_col;
        $$p_linenum++;
    }
    if ( $role_code eq 'PP' ) {
        my $sts_name;
        if ( $sts_code eq 'OK-01' ) {
            $sts_name = '出演:';
        } elsif ( $sts_code eq 'NG-04' ) {
            $sts_name = 'バーチャル出演:';
        }
        if ( defined( $sts_name ) ) {
            print '<span class="pp">' . $sts_name . 
                  '<a href="./person_detail.cgi?' . $psn_code . '">' .
                  $psn_name . '</a></span>' . "\n";
        }
    }
}

# テーブル完了出力
sub outputTimeTblTail {
    my (
        $leftcol,   # 後始末カラム数
       ) = @_;
    if ( $leftcol > 0 ) {
        print "</td>\n";
        print '<td colspan="' . $leftcol . '" rowspan="1" ' .
              'class="no-use"></td>' . "\n";
    }
    print "</tr>\n</table>\n";
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
our ( $LCDT, $NMMT, $RLMT, $RNMT, $PSMT, $PSOPIF, $PSOPDT, );

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
    my $pgPsIf = $prefix . $PSOPIF;
    my $pgPsDt = $prefix . $PSOPDT;

    my $sth = $db->prepare(
        'SELECT a.start_time, a.end_time, b.room_name, ' .
               'c.pg_code, c.pg_name, a.seq, e.role_code, f.name, ' .
               'a.room_row, f.seq, g.ps_code ' .
          'FROM '        . $pgLcDt . ' a ' .
            'INNER JOIN ' . $pgRnMt . ' b ON a.room_key     = b.seq ' .
            'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key       = c.pg_key ' .
            'LEFT JOIN '  . $pgPsDt . ' d ON a.pg_key       = d.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' e ON d.role_key     = e.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' f ON d.person_key   = f.seq ' .
            'LEFT JOIN '  . $pgPsMt . ' g ON d.ps_key       = g.ps_key ' .
          "WHERE c.pg_options = '公開' " .
          'ORDER BY b.room_code, a.room_row, a.start_time, e.role_code, ' .
                   'd.ps_key, d.seq');
    $sth->execute();
    return $sth;
}

main();
exit;
1;
