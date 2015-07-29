#!/usr/bin/perl
# スタッフ用タイムテーブル表示
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
require('../timetableCmn.pl');
our(  $PrgURL, @SETime, @TrgDate, $Tspan, $Maxwidth, $Roomwidth );

# 定数定義
my $acttime = $SETime[0]->{'e'} - $SETime[0]->{'s'} +
              $SETime[1]->{'e'} - $SETime[1]->{'s'};
our $Maxcol = int( $acttime * 60 / $Tspan ) + 1;
our $Colsize_h = $Maxwidth - ( $Roomwidth * 2 ) / $acttime; # *2 の意味不明
our $Colsize = $Colsize_h / 60 * $Tspan;

sub main {
    # 出力開始
    outputHtmlHeadBodytop();
    outputTimeTblHead();

    # タイムテーブル本体取得
    my $dbobj = db_connect();
    my $sth = dbGetProg( $dbobj );
    # タイムテーブル本体出力
    my $col = 0;        # 出力済カラム数
    my $linenum = 0;    # 出力行数?
    while(my @row = $sth->fetchrow_array ) {
        my $oldloc_seq = 0;
        my $oldroom_name = '';
        my $oldroom_row = '';
        outputTimeTbl( \@row, $linenum,
                       \$col, \$oldloc_seq, \$oldroom_name, \$oldroom_row );
        $linenum++;
    }
    $sth->finish;

    # 本体と未配置の間出力
    outputTimeTblMidle( $Maxcol - $col );

    # 未配置企画取得
    $sth = dbGetProgDeny( $dbobj );
    # 未配置企画出力
    my $oldprogram_code = '';
    while( my @row = $sth->fetchrow_array ) {
        outputTimeTblDeny( \@row, \$oldprogram_code );
    }
    $sth->finish;
    db_disconnect( $dbobj );

    # 出力終了
    outputTimeTblTail();
    outputHtmlTail();
}

# HTMLヘッダ出力
sub outputHtmlHeadBodytop {
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print << "EOT";
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <TITLE>タイムテーブル(staff用)</TITLE>
  <link rel="stylesheet" href="timetable.css" type="text/css">
</head>
<body>
<center>
EOT
}

## タイムテーブルヘッダ出力
sub outputTimeTblHead {
    print '<TABLE border="0" cellpadding="2" cellspacing="1" ' .
          ' bgcolor="#cccccc" width="' . $Maxwidth . '">' . "\n";
    print '<thead>' . "\n";
    ## 時刻帯出力
    my $colspanval = 60 / $Tspan;
    print '<TR align="center" height="20">' . "\n";
    print '<TD rowspan="2" width ="' . $Roomwidth . '">' . $TrgDate[0] .
          '</TD>' . "\n";
    for ( my $c = $SETime[0]->{'s'}; $c < $SETime[0]->{'e'}; $c++ ) {
        print '<TD bgcolor="#FFFFFF" width="' . $Colsize_h . '" ' .
              'colspan="' . $colspanval . '" align="left">' .
              '<FONT color="#000000">' . $c . '</font></td>' . "\n";
    }
    print '<TD rowspan="2" width ="' . $Roomwidth . '">' . $TrgDate[1] .
          '</TD>' . "\n";
    for ( my $c = $SETime[1]->{'s'}; $c < $SETime[1]->{'e'}; $c++ ) {
        print '<TD bgcolor="#FFFFFF" width="' . $Colsize_h . '" ' .
              'colspan="' . $colspanval . '" align="left">' .
              '<FONT color="#000000">' . $c . '</font></td>' . "\n";
    }
    print "</TR>\n";
    ## 15分区切り出力
    print '<TR align="center" height="1">' . "\n";
    my $ticstart = ( $SETime[0]->{'s'} + $SETime[1]->{'s'} ) * 4;
    my $ticend   = ( $SETime[0]->{'e'} + $SETime[1]->{'e'} ) * 4;
    for ( my $c = $ticstart; $c < $ticend; $c++ ) {
        print '<TD bgcolor="#FFFFFF" width="' . $Colsize . '" colspan="1" ' .
              'align="left"><FONT color="#000000"></font></td>' . "\n";
    }
    print "</tr>\n";
    print "</thead>\n";
}

# タイムテーブル本体表示
sub outputTimeTbl {
    my (
        $pArow,
        $linenum,
        $p_col,
        $p_oldloc_seq,
        $p_oldroom_name,
        $p_oldroom_row,
       ) = @_;
    my ( $day, $stime )  = split( /\s/, $pArow->[0] );
    my ( $day2, $etime ) = split( /\s/, $pArow->[1] );

    return unless ( $day ne $TrgDate[0] && $day ne $TrgDate[1] );
    my $room_name       = $pArow->[2];
    my $program_code    = $pArow->[3];
    my $program_name    = $pArow->[4];
    my $loc_seq         = $pArow->[5];
    my $role_code       = $pArow->[6];
    my $person_name     = $pArow->[7];
    my $person_count    = $pArow->[8];
    my $room_row        = $pArow->[9];
    my $person_code     = $pArow->[10];
    my $status_code     = $pArow->[11];
    my $status_name     = $pArow->[12];
    my $pg_options      = $pArow->[13];
    # 不要のはず
    # utf8::decode($room_name);
    # utf8::decode($program_name);
    # utf8::decode($person_name);
    # utf8::decode($status_name);
    # utf8::decode($pg_options);
    if($room_name ne $$p_oldroom_name || $room_row ne $$p_oldroom_row){
        if ( $linenum != 0 ) {
            print "</font></td>\n";
            my $leftcolval = $Maxcol - $$p_col;
            if ( $leftcolval > 0 ) {
                print '<td colspan="' . $leftcolval . '" rowspan="1" ' .
                      'bgcolor="#c0c0c0"></td>' . "\n";
            }
            print "</tr>\n";
            $$p_col = 0;
        }
        print '<tr height="32">' . "\n" .
              '<td width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
                'bgcolor="#E6FF8E">' . $room_name. '<BR></td>' . "\n";
        $$p_oldroom_name = $room_name;
        $$p_oldroom_row  = $room_row;
    }
    my ( $s_tm_h, $s_tm_m ) = split(/:/, $stime);
    my ( $e_tm_h, $e_tm_m ) = split(/:/, $etime);
    my ( $s_col, $e_col );
    if ( $day eq  $TrgDate[0] ) {
        my $wkt = $SETime[0]->{'s'};
        $s_col = int( ( ( $s_tm_h - $wkt ) * 60 + $s_tm_m ) / $Tspan );
        $e_col = int( ( ( $e_tm_h - $wkt ) * 60 + $e_tm_m ) / $Tspan );
    }
    else {
        my $wkt = $SETime[1]->{'s'} - $SETime[0]->{'s'} + $SETime[0]->{'e'};
        $s_col = int( ( ( $s_tm_h - $wkt ) * 60 + $s_tm_m ) / $Tspan ) + 1;
        $e_col = int( ( ( $e_tm_h - $wkt ) * 60 + $e_tm_m ) / $Tspan ) + 1;
    } 
    my $leftcolval = $s_col - $$p_col;
    if ( $leftcolval > 0) {
        print '<td colspan="' . $leftcolval . '" rowspan="1" ' .
              'bgcolor="#c0c0c0"></td>' . "\n";
    }
    if ( $loc_seq ne $$p_oldloc_seq ) {
        if ( $$p_oldloc_seq != 0 ) {
            print "</font></td>\n";
        }
        my $cwidth = $Colsize * ( $e_col - $s_col );
        my $cspan  = $e_col - $s_col;
        my $bgcolor = ( $pg_options ne '公開' ) ? '#ffe0e0' : '#e0ffe0';
        print '<td width = "' . $cwidth . '" colspan="' . $cspan .
              '" rowspan="1" bgcolor="' . $bgcolor . '">' .
              '<font size = "-1">' .
              '<INPUT TYPE="CHECKBOX" name="PLS" value="' . $loc_seq . '">' .
              $stime . '-<br>';
        print '<a href ="' . $PrgURL . $program_code . '">' . $program_code .
              '</a> ' . $program_name. '[' . $pg_options . ']<br>';
        $$p_oldloc_seq = $loc_seq;
    }
    my $bl_s = "</SPAN>";
    my $pp_cls = 'pp';
    if ( $status_code eq 'NG-01' || $status_code eq 'NG-02' ) {
        $pp_cls = 'pp_ng';
    }
    if ( $person_count != 0 ) {
        $bl_s = '<BLINK>★</BLINK></SPAN>' 
    }
    if ( $role_code eq 'PP' ) {
        $status_name = '状況不明' if ( $status_name eq '' );
        print '<SPAN CLASS="pp">出:';
        print $bl_s .
                '<A HREF="./person_detail.cgi?' . $person_code .
                  '" CLASS="' . $pp_cls . '" > ' .
                $person_name . '[' . $status_name . ']</a><BR>';
    } elsif ( $role_code eq 'PO' ) {
        print '<SPAN CLASS="po">主:';
        print $bl_s .
                '<A HREF="./person_detail.cgi?' . $person_code .
                  '" CLASS="po" >' . $person_name . '</a><BR>';
    } elsif ( $role_code eq 'PR' ) {
        print '<SPAN CLASS="pr">担:';
        print $bl_s . 
                '<A HREF="./person_detail.cgi?' . $person_code .
                  ' "CLASS="pr" >' . $person_name . '</a><BR>';
    } else {
        print '<SPAN CLASS="pr">＊:';
        print $bl_s . 
                '<A HREF="./person_detail.cgi?' . $person_code .
                  ' "CLASS="pr" >' . $person_name . '</a><BR>';
    }
    $$p_col = $e_col;
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
          '<td width="' . $Roomwidth . '" colspan="1" rowspan="1" ' .
            ' bgcolor="#E6FF8E">未配置企画<BR></td>' . "\n";
    print '<td colspan="1" rowspan="1" bgcolor="#c0c0c0"></td>' . "\n";
    print '<td colspan="' . $Maxcol - 2 . '" rowspan="1" bgcolor="#ffffff">';
}

# 未配置企画出力
sub outputTimeTblDeny {
    my (
        $pArow,
        $p_oldprogram_code,
       ) = @_;

    my $program_code   = $pArow->[0];
    my $program_name   = $pArow->[1];
    my $program_option = $pArow->[2];
    my $role_code      = $pArow->[3];
    my $person_name    = $pArow->[4];
    my $person_code    = $pArow->[5];
    # 不要のはず
    # utf8::decode($program_name);
    # utf8::decode($person_name);
    # utf8::decode($program_option);

    if ( $program_code ne $$p_oldprogram_code ) {
        print "<br>\n" if ( $$p_oldprogram_code );
        print
            '<font size = "-1">' .
            '<INPUT TYPE="CHECKBOX" name="PPC" value="' . $program_code . '">' .
            '<a href ="' . $PrgURL . $program_code . '">' . $program_code .
            '</a>' . $program_name . '<br>' . $program_option;
        $$p_oldprogram_code = $program_code;
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
    print $person_name . '</SPAN></font> ';
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
    my $pgLcDt = $dbobj->prefix() . $LCDT;
    my $pgNmMt = $dbobj->prefix() . $NMMT;
    my $pgRlMt = $dbobj->prefix() . $RLMT;
    my $pgPsMt = $dbobj->prefix() . $PSMT;
    my $pgRnMt = $dbobj->prefix() . $RNMT;
    my $pgPsIf = $dbobj->prefix() . $PSIF;
    my $pgPsDt = $dbobj->prefix() . $PSDT;

    my $sth = $db->prepare(
        'SELECT a.start_time, a.end_time, b.room_name, ' .
               'c.pg_code, c.pg_name, a.seq, e.role_code, f.name, ' .
               '( SELECT count(y.person_key) ' .
                   'FROM ' . $pgLcDt . ' z ' .
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
    my $pgLcDt = $dbobj->prefix() . $LCDT;
    my $pgPsDt = $dbobj->prefix() . $PSDT;
    my $pgNmMt = $dbobj->prefix() . $NMMT;
    my $pgRlMt = $dbobj->prefix() . $RLMT;
    my $pgPsIf = $dbobj->prefix() . $PSIF;

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
