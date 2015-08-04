#!/usr/bin/perl
# 公開用タイムテーブル出演者詳細表示
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

require( dirname(File::Spec->rel2abs($0)) . '/timetableCmn.pl');

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
    while(my @row = $sth->fetchrow_array) {
        my $oldloc_seq = 0;
        my $oldperson_name = '';
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
  <TITLE>Person detail</TITLE>
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
    my $status_code     = $pArow->[8];
    my $status_name     = decode('utf8', $pArow->[9]);

    if ( $person_name ne $$p_oldperson_name ) {
        print '<TABLE BORDER="1">' .
                '<TR><TD COLSPAN="3">' . $person_code . ' ' . $person_name;
        $$p_oldperson_name = $person_name;
    }
    if ( $loc_seq ne $$p_oldloc_seq ) {
        print '</TD></TR><TR>' .
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
our ( $LCDT, $NMMT, $RLMT, $PSMT, $RNMT, $PSOPIF, $PSOPDT, );

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
    my $pgPsIf = $prefix . $PSOPIF;
    my $pgPsDt = $prefix . $PSOPDT;

    my $sth = $db->prepare(
        "SELECT DATE_FORMAT(a.start_time, '%m/%d %H:%i'), " .
               "DATE_FORMAT(a.end_time, '%H:%i'), " .
               'b.room_name, c.pg_code, c.pg_name, a.seq, ' .
               'e.role_code, f.name, f.seq, g.ps_code ' .
         'FROM '        . $pgLcDt . ' a ' .
          'INNER JOIN ' . $pgRnMt . ' b ON a.room_key = b.seq ' .
          'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key = c.pg_key ' .
          'INNER JOIN ' . $pgPsDt . ' d ON a.pg_key = d.pg_key ' .
          'INNER JOIN ' . $pgRlMt . ' e ON d.role_key = e.role_key ' .
          'INNER JOIN ' . $pgPsIf . ' f ON d.person_key = f.seq ' .
          'LEFT JOIN  ' . $pgPsMt . ' g ON d.ps_key = g.ps_key ' .
         'WHERE d.person_key = ? ' .
           "AND ( e.role_code = 'PP' AND g.ps_code IN ('OK-01' , 'NG-04') ) " .
         'ORDER BY a.start_time, b.room_code, a.room_row, e.role_code' );
    $sth->execute($person_code);
    return $sth;
}

main();
exit;
1;
