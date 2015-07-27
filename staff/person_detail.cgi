#!/usr/bin/perl
# スタッフ用タイムテーブル出演者詳細表示
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

sub main {
    my $dbobj;
    my $sth;

    my $person_code = $ENV{'QUERY_STRING'};
    # 出力開始
    outputHtmlHeadBodytop();
    unless ( $person_code =~ /\d+/ ) {
        print '<H1><Font color="red">Wrong Parameter</font></H1>' . "\n";
        outputHtmlTail();
        return;
    }
    # 出演者情報取得
    $dbobj = db_connect();
    $sth = dbGetPerson( $dbobj, $person_code );
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

# HTMLヘッダ～タイムテーブルヘッダ部分出力
sub outputHtmlHeadBodytop {
    my $q  = CGI->new();
    print $q->header( -type=>'text/html', -charset=>'UTF-8', );
    print << "EOT";
<!DOCTYPE html>
<HTML lang="ja">
<HEAD>
  <meta charset="utf-8">
  <TITLE>Person detai(staff用)</TITLE>
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
	my ( $day, $stime  ) = split(/\s/,$pArow->[0]);
	my ( $day2, $etime ) = split(/\s/,$pArow->[1]);
	my $room_name       = $pArow->[2];
	my $program_code    = $pArow->[3];
	my $program_name    = $pArow->[4];
	my $loc_seq         = $pArow->[5];
	my $role_code       = $pArow->[6];
	my $person_name     = $pArow->[7];
	my $status_code     = $pArow->[11];
	my $status_name     = $pArow->[12];
	# utf8::decode($room_name);
	# utf8::decode($program_name);
	# utf8::decode($person_name);
	# utf8::decode($status_name);

	if ( $person_name ne $$p_oldperson_name ) {
		print '<TABLE BORDER="1">' .
		        '<TR><TD COLSPAN="3">' . $person_code . ' ' . $person_name;
		$$p_oldperson_name = $person_name;
	}
	if ( $loc_seq ne $$p_oldloc_seq){
		print '</TD></TR><TR>' .
                '<TD>' .  $day . ' ' . $stime . ' ' . $etime . '</td>' .
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
my $RNMT = 'room_name_master';
my $PSIF = 'pg_person_info';
my $PSDT = 'pg_person_detail';

# 出演者情報取得
sub dbGetPerson {
    my (
        $dbobj,     # SFCON::Register_dbオブジェクト
        $person_code,
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
        'SELECT a.start_time, a.end_time, b.room_name, c.pg_code, c.pg_name, ' .
               'a.seq, e.role_code, f.name, ' .
		       '( SELECT count(y.person_key) ' .
		           'FROM ' . $pgLcDt . ' z ' .
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
	     'FROM ' . $pgLcDt . ' a ' .
	      'INNER JOIN ' . $pgRnMt . ' b ON a.room_key = b.seq ' .
	      'INNER JOIN ' . $pgNmMt . ' c ON a.pg_key = c.pg_key ' .
	      'INNER JOIN ' . $pgPsDt . ' d ON a.pg_key = d.pg_key ' .
	      'INNER JOIN ' . $pgRlMt . ' e ON d.role_key = e.role_key ' .
	      'INNER JOIN ' . $pgPsIf . ' f ON d.person_key = f.seq ' .
	      'LEFT JOIN  ' . $pgPsMt . ' g ON d.ps_key = g.ps_key ' .
	     'WHERE d.person_key = ? ' .
	     'ORDER BY a.start_time, b.room_code, a.room_row, e.role_code');
    $sth->execute($person_code);
    return $sth;
}

main();
exit;
1;
