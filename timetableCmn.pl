#!/usr/bin/perl
# タイムテーブル共通
#
use lib ((getpwuid($<))[7]) . '/local/lib/perl5';
use strict;
use warnings;
use utf8;
use SFCON::Register_db;

# 定数定義
our $PrgURL = 'http://www.comecon.com/aj?alias=p';
our @SETime = (
    {               # 1日目
        's' => 9,   # 開始時刻
        'e' => 21,  # 終了時刻
    },
    {               # 2日目
        's' => 9,
        'e' => 20,
    },
);
our @TrgDate = (
    '2015-08-29',
    '2015-08-30',
);
our $Tspan=15;
our $Maxwidth = 1600;
our $Roomwidth = 80;
our $Maxcol;
our $Colsize_h;
our $Colsize;

# テーブル名定数
our $LCDT = 'pg_location_detail';
our $NMMT = 'pg_name_master';
our $RLMT = 'pg_role_master';
our $PSMT = 'pg_person_status_master';
our $RNMT = 'room_name_master';
our $PSIF = 'pg_person_info';
our $PSDT = 'pg_person_detail';
our $PSOPIF = 'pg_person_open_info';
our $PSOPDT = 'pg_person_open_detail';

#-----以下共通DB操作定義
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
sub db_disconnect {
    my (
        $dbobj,     # Register_dbオブジェクト
       ) = @_;
    $dbobj->{database}->disconnect;
}

1;
