#!/usr/bin/perl
# 一般用タイムテーブル表示
#
use lib ((getpwuid($<))[7]) . '/local/lib/perl5';
use strict;
use warnings;
use utf8;
use CGI;
use CGI::Carp qw(fatalsToBrowser); 
use SFCON::Register_db;
binmode STDIN,  ":utf8";
binmode STDOUT, ":utf8";

# 共通定義
require('./timetableCmn.pl');
our(  $PrgURL, @SETime, @TrgDate, $Tspan, $Maxwidth, $Roomwidth, );
our(  $Maxcol, $Colsize_h, $Colsize, );

sub main {
    my $dayNo = $ENV{'QUERY_STRING'};
    # 出力開始
    outputHtmlHeadBodyTop();
    unless ( $dayNo =~ /[01]/ ) {
        print '<H1><Font color="red">Wrong Parameter</font></H1>' . "\n";
        outputHtmlTail();
        return;
    }

    # 定数値設定
    my $acttime     = $SETime[$dayNo]->{'e'} - $SETime[$dayNo]->{'s'};
    $Maxcol      = int( $acttime * 60 / $Tspan);
    $Colsize_h   = ( $Maxwidth - $Roomwidth ) / $acttime;
    $Colsize     = $Colsize_h / 60 * $Tspan;

    # タイムテーブルヘッダ出力
    outputTimetableTop( $dayNo );

    # タイムテーブル本体取得
    my $dbobj = db_connect();
    my $sth = dbGetProg( $dbobj );
    # タイムテーブル本体出力
    my $linenum=0;
    my $col=0;
    while( my @row = $sth->fetchrow_array ) {
        my $oldloc_seq = 0;
        my $oldroom_name = '';
        my $oldroom_row = '';
        outputTimeTbl( \@row, \$linenum, \$col,
                       \$oldloc_seq, \$oldroom_name, \$oldroom_row, $dayNo );
    }
    $sth->finish;
    db_disconnect( $dbobj );

    # 出力終了
    outputTimeTblTail( $Maxcol - $col );
    outputHtmlTail();
}

# HTMLヘッダ部分出力
sub outputHtmlHeadBodyTop {
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print << "EOT";
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta  charset=UTF-8">
  <title>タイムテーブル</title>
  <link rel="stylesheet" href="./timetable.css" type="text/css">
</head>
<body>
<center>
EOT
}

# タイムテーブルヘッダ部分出力
sub outputTimetableTop {
    my (
        $dayNo,        # 日付コード(0|1)
       ) = @_;
    print '<table border="0" cellpadding="0" cellspacing="0" width="auto">';
    print "\n<thead>\n<tr>\n";
    ## 時刻帯出力
    my $wkRmW = sprintf( '%1.2f', $Roomwidth / 10 );
    my $wkClH = sprintf( '%1.2f', $Colsize_h / 10 );
    print '<th rowspan="2" width ="' . $wkRmW . '%" class="time">' .
            $TrgDate[$dayNo] . '</th>' . "\n";
    for ( my $c = $SETime[$dayNo]->{'s'}; $c < $SETime[$dayNo]->{'e'}; $c++ ) {
	    print '<th bgcolor="#FFFFFF" width="' . $wkClH . '%" ' .
              'colspan="' . 60 / $Tspan . '" ' .
              'align="left" class="time"> ' .  $c . '</td>' . "\n";
    }
    print "</tr>\n";
    ## 14分区切り出力
    print '<tr align="center" height="1">' . "\n";
    my $ticstart = $SETime[$dayNo]->{'s'} * 4;
    my $ticend   = $SETime[$dayNo]->{'e'} * 4;
    my $wkCl = sprintf( '%1.2f', $Colsize / 10 );
    for ( my $c = $ticstart; $c < $ticend; $c++ ) {
	    print '<td colspan="1" width="' . $wkCl . '%"></td>' . "\n";
    }
    print "</tr>\n</thead>\n";
}

# 企画本体出力
sub outputTimeTbl {
    my (
        $pArow,
        $p_linenum,
        $p_col,
        $p_oldloc_seq,
        $p_oldroom_name,
        $p_oldroom_row,
        $dayNo
       ) = @_;
	my ( $day,  $stime ) = split(/\s/,$pArow->[0]);
	my ( $day2, $etime ) = split(/\s/,$pArow->[1]);
	my $room_name       = $pArow->[2];
	my $program_code    = $pArow->[3];
	my $program_name    = $pArow->[4];
	my $loc_seq         = $pArow->[5];
	my $role_code       = $pArow->[6];
	my $person_name     = $pArow->[7];
	my $room_row        = $pArow->[9];
	my $person_code     = $pArow->[10];
	my $status_code     = $pArow->[11];
	# utf8::decode($room_name);
	# utf8::decode($program_name);
	# utf8::decode($person_name);

	return unless ( $day eq $TrgDate[$dayNo] );
	
    if ( $room_name ne $$p_oldroom_name || $room_row ne $$p_oldroom_row ) {
		if( $$p_linenum != 0 ) {
			print '<td id="X-LINENUM-' . $$p_linenum . '">' . "\n";
            my $leftcol = $Maxcol -$$p_col;
			if ( $leftcol > 0 ){
                my $wkcl = sprintf( '%1.2f', $leftcol * $Colsize / 10 );
				print '<td width="' . $wkcl . '%" ' .
                          'colspan="' . $leftcol . '" ' .
                          'rowspan="1" class="no-use">&nbsp;</td>' . "\n";
			}
			print "</tr>\n";
			$$p_col = 0;
		}
		print "<tr>\n";
        my $wkrw = sprintf( '%1.2f', $Roomwidth / 10 );
        print '<th width="' . $wkrw . '%" colspan="1" rowspan="1" ' .
                  'bgcolor="#E6FF8E" class="room">' . $room_name . "</th>\n";
		$$p_oldroom_name = $room_name;
		$$p_oldroom_row = $room_row;
		$$p_oldloc_seq = 0;
	}
	my ( $tm_h, $tm_m ) = split( /:/, $stime );
	my $s_col = int(
        ( ( $tm_h - $SETime[$dayNo]->{'s'} ) * 60 + $tm_m + $Tspan * 1 / 3 )
        / $Tspan );
	( $tm_h, $tm_m ) = split( /:/, $etime );
	my $e_col = int(
        ( ( $tm_h - $SETime[$dayNo]->{'s'} ) * 60 + $tm_m + $Tspan * 2 / 3)
        / $Tspan );
	if ( $loc_seq ne $$p_oldloc_seq ) {
		if ( $$p_oldloc_seq != 0 ) {
			print '<td id="X-OLDLOC-' . $$p_oldloc_seq . '">' . "\n";
		}
        my $wkcol = $s_col - $$p_col;
		if ( $wkcol > 0 ) {
            my $wkcw = sprintf( '%1.2f', $Colsize * $wkcol / 10 );
			print '<td width="' . $wkcw . '%" colspan="' . $wkcol . '" ' .
                      'rowspan="1" class="no-use">&nbsp;</td>' . "\n";
		}
		( $tm_h, $tm_m ) = split( /:/, $stime );
        $wkcol = $e_col - $s_col; 
        my $wkcw = sprintf( '%1.2f', $Colsize * $wkcol / 10 );
		print '<td width="' . $wkcw . '%" ' .
                  'colspan="' . $wkcol . '" ' .
                  'rowspan="1" bgcolor="#ffffff" class="use">' .
              $stime . '-<br>';
		print '<a href ="' . $PrgURL . $program_code . '">' . 
              $program_code . '</a> ' . $program_name . '<br>';
		$$p_oldloc_seq = $loc_seq;
	}
	if ( $role_code eq 'PP' && $status_code eq 'OK-01' ) {
		print '<span class="pp">出演:';
		print '<a href="./person_detail.cgi?' . $person_code . 
                '">' . $person_name . '</a></span>';
	}
	if ( $role_code eq 'PP' && $status_code eq 'NG-04' ) {
		print '<span class="pp">バーチャル出演:';
		print '<a href="./person_detail.cgi?' . $person_code .
                '">' . $person_name . '</a></span>';
	}
	$$p_col = $e_col;
	$$p_linenum ++;
}

# テーブル完了出力
sub outputTimeTblTail {
    my (
        $leftcol,   # 後始末カラム数
       ) = @_;
    if ( $leftcol > 0 ) {
	    print "</td>\n";
        my $wkcl = sprintf( '%1.2f', $Colsize * $leftcol / 10 );
	    print '<td colspan="' . $leftcol . '" rowspan="1" ' .
                'width="' . $wkcl . '%" class="no-use">&nbsp;</td>' . "\n";
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
our ( $LCDT, $NMMT, $RLMT, $PSMT, $RNMT, $PSOPIF, $PSOPDT, );

# 企画情報取得
sub dbGetProg {
    my(
        $dbobj,     # Register_dbオブジェクト
       ) = @_;
    my $db = $dbobj->{database};
    my $pgLcDt = $dbobj->prefix() . $LCDT;
    my $pgNmMt = $dbobj->prefix() . $NMMT;
    my $pgRlMt = $dbobj->prefix() . $RLMT;
    my $pgPsMt = $dbobj->prefix() . $PSMT;
    my $pgRnMt = $dbobj->prefix() . $RNMT;
    my $pgPsIf = $dbobj->prefix() . $PSOPIF;
    my $pgPsDt = $dbobj->prefix() . $PSOPDT;

    my $sth = $db->prepare(
        'SELECT a.start_time, a.end_time, b.room_name, c.pg_code, c.pg_name, ' .
               'a.seq, 0, 0, 0, a.room_row, 0, 0, 0' .
	     'FROM ' . $pgLcDt . ' a ' .
	      'INNER JOIN ' . $pgRnMt . ' b ON a.room_key = b.seq ' .
	      'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key = c.pg_key ' .
	     'WHERE c.pg_options = ' . "'公開' " .
	     'ORDER BY b.room_code, a.start_time, a.end_time DESC, a.room_row');
    $sth->execute();
    return $sth;
}

main();
exit;
1;
