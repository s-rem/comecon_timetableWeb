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
    my $acttime = 0;
    $acttime += $SETime[$dayNo]->{'e'} - $SETime[$dayNo]->{'s'};
    $acttime ++ if ( $SETime[$dayNo]->{'em'} > 0 );
    # 日付列数
    my $daycolcnt = 1;  
    # 列数
    $Maxcol = int( $acttime * 60 / $Tspan ) + $daycolcnt;
    # 1時間分列幅
    my $colsize_h = ( $Maxwidth - ( $Roomwidth * $daycolcnt ) ) / $acttime; 
    # 1スパン分列幅
    $Colsize = int( $colsize_h / ( 60 / $Tspan ) ) - $CellSpc;

    # 出力開始
    outputHtmlHeadBodytop('タイムテーブル');
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
    my $oloc_seq = 0;   # 企画情報レコード番号退避
    my $oroom_name = '';    # 部屋名退避
    while( my @row = $sth->fetchrow_array ) {
        outputTimeTbl( \@row, \$linenum, \$col,
                       \$oloc_seq, \$oroom_name, $dayNo );
    }
    $sth->finish;
    db_disconnect( $dbobj );
    # 出力終了
    outputTimeTblTail( $Maxcol - $col );
    outputHtmlTail();
}

# タイムテーブルヘッダ部分出力
sub outputTimeTblHead {
    my (
        $dayNo,        # 日付コード(0|1)
       ) = @_;
    print '<table cellspacing="' . $CellSpc . '">' . "\n";
    print "<thead>\n";
    ## 時刻帯出力
    my $colspanval = 60 / $Tspan;
    my $ticcnt = 1; # 部屋名分
    print '<tr class="roomname">' . "\n";
    print '<th rowspan="2" width ="' . $Roomwidth . '" class="timeroom">' .
          $TrgDate[$dayNo] . '</th>' . "\n";
    my $lasthour = $SETime[$dayNo]->{'e'};
    $lasthour++ if ( $SETime[$dayNo]->{'em'} > 0 );
    for ( my $c = $SETime[$dayNo]->{'s'}; $c < $lasthour; $c++ ) {
        print '<th colspan="' . $colspanval . '" class="time">' .
              sprintf( '%02d', $c ) . '</th>' . "\n";
        $ticcnt += $colspanval;
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
        $dayNo,
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
    my $psn_code    = $pArow->[9];
    my $sts_code    = $pArow->[10];
    $sts_code = '' unless defined($sts_code);

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
    my $wkt = $SETime[$dayNo]->{'s'};
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
            my $cspan = $e_col - $s_col; 
            my $cls = 'use';
            print '<td colspan="' . $cspan . '" rowspan="1" ' .
                  'class="' . $cls . '">' . "\n";
            print $s_tm_h . ':' . $s_tm_m . '-' . $e_tm_h . ':' .  $e_tm_m . '<br>';
        } else {
            print "\n"; # 重複企画の間
        }
        $$p_oldloc_seq = $loc_seq;
        print '<a href ="' . $PrgURL . $prg_code . '">' .
              $prg_name . '</a><br>';
    }
    $$p_col = $e_col;
    $$p_linenum++;
    
    my $cls = '';
    my $wksts = '';
    my $bl_s = '';
    if ( $role_code eq 'PP' ) {
        $cls = 'pp';
        if ( $sts_code eq 'OK-01' ) {
            $wksts = '出演:';
        } elsif ( $sts_code eq 'NG-04' ) {
            $wksts = 'バーチャル出演:';
        }
    }
    if ( $wksts ne '' ) {
        print '<span class="' . $cls . '">&nbsp;' . $wksts . $bl_s .
              '<a href="./person_detail.cgi?' . $psn_code . '">' .
              $psn_name . '</a></span>' . "\n";
    }
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
               '0, ' .  # 重複数のダミー
               'f.seq, g.ps_code ' .
          'FROM '        . $pgLcDt . ' a ' .
            'INNER JOIN ' . $pgRnMt . ' b ON a.room_key     = b.seq ' .
            'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key       = c.pg_key ' .
            'LEFT JOIN '  . $pgPsDt . ' d ON a.pg_key       = d.pg_key ' .
            'INNER JOIN ' . $pgRlMt . ' e ON d.role_key     = e.role_key ' .
            'INNER JOIN ' . $pgPsIf . ' f ON d.person_key   = f.seq ' .
            'LEFT JOIN '  . $pgPsMt . ' g ON d.ps_key       = g.ps_key ' .
          "WHERE c.pg_options = '公開' " .
          'ORDER BY b.room_code, a.start_time, a.room_row, e.role_code, ' .
                   'd.ps_key, d.seq' );
    $sth->execute();
    return $sth;
}

main();
exit;
1;
