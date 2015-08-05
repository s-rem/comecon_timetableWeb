#!/usr/bin/perl
# スタッフ用タイムテーブル出演者詳細表示
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

sub main {
    my $person_code = $ENV{'QUERY_STRING'};
    # 出力開始
    outputHtmlHeadBodyTop();
    unless ( $person_code =~ /\d+/ ) {
        print '<H1><Font color="red">Wrong Parameter</font></H1>' . "\n";
        outputHtmlTail();
        return;
    }
    # 出演者情報取得
    my $dbobj = db_connect();
    my $sth = dbGetPerson( $dbobj, $person_code );
    # 出演者情報出力
    my $oldloc_seq = 0;
    my $oldperson_name = '';
    while(my @row = $sth->fetchrow_array) {
        outputPerson( $person_code, \@row, \$oldloc_seq, \$oldperson_name );
    }
    $sth->finish;
    db_disconnect( $dbobj );

    # 出力終了
    print '</TD></TR></TABLE>';
    outputHtmlTail();
}

# HTMLヘッダ部分出力
sub outputHtmlHeadBodyTop {
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print << "EOT";
<!DOCTYPE html>
<HTML lang="ja">
<HEAD>
  <meta charset="utf-8">
  <TITLE>Person detail(staff用)</TITLE>
</HEAD>
<BODY>
<center>
EOT
}

# HTML完了出力
sub outputHtmlTail {
    print "</center>\n</body>\n</html>\n";
}

# 出演者情報出力
sub outputPerson {
    my (
        $person_code,
        $pArow,
        $p_oldloc_seq,
        $p_oldperson_name,
       ) = @_;
    my $stime           = $pArow->[0];
    my $etime           = $pArow->[1];
    my $room_name       = decode('utf8', $pArow->[2]);
    my $program_code    = $pArow->[3];
    my $program_name    = decode('utf8', $pArow->[4]);
    my $loc_seq         = $pArow->[5];
    my $role_code       = $pArow->[6];
    my $person_name     = decode('utf8', $pArow->[7]);
    my $status_code     = $pArow->[11];
    my $status_name     = decode('utf8', $pArow->[12]);

    if ( $person_name ne $$p_oldperson_name ) {
        print '<TABLE BORDER="1">' .
                '<TR><TD COLSPAN="3">' . $person_code .
                ' <STRONG>' . $person_name . '</STRONG>';
        $$p_oldperson_name = $person_name;
    }
    if ( $loc_seq ne $$p_oldloc_seq ) {
        print "</TD></TR>\n<TR>" .
                '<TD>' . $stime . '-' . $etime . '</td>' .
                '<td>' . $room_name . '</td>' .
                '<td>' . $program_code . ' ' . $program_name . '</td><TD>';
        $$p_oldloc_seq = $loc_seq;
    }
    if ( $role_code eq 'PP' ) {
        if ( $status_code eq 'NG-01' || $status_code eq 'NG-02' ) {
            print '<font size = "-1" color="green"><strike>出演[' .
                    $status_name . ']</strike></FONT>';
        } else {
            print '<font size = "-1" color="green">出演[' .
                    $status_name . ']</FONT>';
        }
    }
    if ( $role_code eq 'PO' ) {
        print '<font size = "-1" color="blue">主催 </FONT>';
    }
    if ( $role_code eq 'PR' ) {
        print '<font size = "-1" color="red">担当 </FONT>';
    }
}

#-----以下DB操作
#  本来はRegister_dbの中に隠蔽されるべき処理

# テーブル名定数
our ( $LCDT, $NMMT, $RLMT, $PSMT, $RNMT, $PSIF, $PSDT, );

# 出演者情報取得
sub dbGetPerson {
    my (
        $dbobj,     # SFCON::Register_dbオブジェクト
        $person_code,
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
        "SELECT DATE_FORMAT(a.start_time, '%m/%d %H:%i'), " .
               "DATE_FORMAT(a.end_time, '%H:%i'), " .
               'b.room_name, c.pg_code, c.pg_name, a.seq, ' .
               'e.role_code, f.name, ' .
               '( SELECT count(y.person_key) ' .
                   'FROM '        . $pgLcDt . ' z ' .
                    'INNER JOIN ' . $pgPsDt . ' y ON z.pg_key = y.pg_key ' .
                    'INNER JOIN ' . $pgRlMt . ' x ON y.role_key = x.role_key ' .
                    'WHERE a.start_time < z.end_time ' .
                      'AND z.start_time < a.end_time ' .
                      'AND a.seq != z.seq ' .
                      'AND d.person_key = y.person_key ' .
                      "AND (   x.role_code = 'PP' " .
                          " OR e.role_code = 'PO' and x.role_code = 'PO' " .
                          " OR e.role_code = 'PR' ) " .
                '), a.room_row, f.seq, g.ps_code, g.ps_name ' .
         'FROM ' . $pgLcDt .        ' a ' .
          'INNER JOIN ' . $pgRnMt . ' b ON a.room_key = b.seq ' .
          'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key = c.pg_key ' .
          'INNER JOIN ' . $pgPsDt . ' d ON a.pg_key = d.pg_key ' .
          'INNER JOIN ' . $pgRlMt . ' e ON d.role_key = e.role_key ' .
          'INNER JOIN ' . $pgPsIf . ' f ON d.person_key = f.seq ' .
          'LEFT JOIN  ' . $pgPsMt . ' g ON d.ps_key = g.ps_key ' .
         'WHERE d.person_key = ? ' .
         'ORDER BY a.start_time, b.room_code, a.room_row, e.role_code' );
    $sth->execute($person_code);
    return $sth;
}

main();
exit;
1;
