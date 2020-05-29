# LTCLI Guide

[Installing Prerequisites](#installing-prerequisites)

[LTCLI Install](#LTCLI-install)

[LTCLI 실행하기](#LTCLI-실행하기)

[Deploy](#deploy)

[클러스터 생성](#클러스터-생성)

[Lightning DB Version Update](#lightningdb-version-update)

[Re-Deploy](#re-deploy)

[Add Slave](#add-slave)

[Thrift Server](#thrift-server)

[Logging in file](#logging-in-file)

[PYPI 등록 가이드](https://tde.sktelecom.com/wiki/pages/viewpage.action?spaceKey=BDFLASH&title=LTCLI&)

</br>
</br>

## Installing Prerequisites

* Installing prerequisites for lightningdb

* Python ==2.7, >=3.5

</br>
</br>

## LTCLI Install

```
$ pip insatll ltcli --upgrade --user
```

</br>
</br>

## LTCLI 실행하기

실행하기 전에 환경변수 FBPATH 설정이 필요합니다. 미설정시 아래와 같이 에러메시지가 발생합니다.

```
To start using LTCLI, you should set env FBPATH
ex)
export FBPATH=$HOME/.flashbase
```

</br>

설치 및 설정완료 후 아래와 같이 `ltcli` 을 입력하면 LTCLI이 실행됩니다.
```
$ ltcli
```

</br>

LTCLI 최초접속시 base_directory를 물어봅니다. base_directory는 lightningdb의 root path 입니다.

```
Type base directory of LightningDB [~/tsr2]
~/tsr2
OK, ~/tsr2
```
> 대괄호 안의 값은 default value이며 아무값도 입력하지 않으면 default value가 선택됩니다.
>
> 질의에 따라 default value가 없을 수도 있습니다.

 `edit` 명령어를 이용하거나 `$FBPAHT/.flashbase/config` 파일을 열어 base_directory 를 수정할 수 있습니다.

</br>

정상적으로 접속이 되면 가장 최근에 접속했던 cluster에 접속되며, 없는 경우 `-` 로 표시됩니다.

LTCLI의 prompt 형식은 `<user-name>@lightningdb:<cluster-id>>` 입니다.

ex)

```
root@lightningdb:->
root@lightningdb:1>
```

</br>
</br>

## Deploy

deploy는 lightningdb 설치과정입니다. 클러스터마다 deploy가 이루어져야 합니다.

```
> deploy 1
```

</br>

정보 입력 시 아래의 값들은 가장 최근에 입력했던 값을 default value로 보여줍니다.

* host
* number of master
* replicas
* number of ssd
* prefix of (redis data / redis db path / flash db path)

현재 입력하는 값이 default value로 저장되지 않도록 하려면  `--history-save` 옵션을 사용하세요.
```
> deploy --history-save=False
```

</br>

### installer 선택

```
Select installer

    [ INSTALLER LIST ]
    (1) tsr2-installer.bin.lightningdb_v1.1.10.centos
    (2) tsr2-installer.bin.lightningdb_v1.1.09.centos
    (3) tsr2-installer.bin.lightningdb_v1.1.08.centos

Please enter the number, file path or url of the installer you want to use.
you can also add file in list by copy to '$FBPATH/releases/'
1
OK, tsr2-installer.bin.lightningdb_v1.1.10.centos
```

installer를 선택합니다. 숫자입력을 통해 리스트에서 선택할 수 있으며, 파일의 경로나 url을 통해서도 선택할 수 있습니다.


```
Select installer

    [ INSTALLER LIST ]
    (empty)

Please enter file path or url of the installer you want to use
you can also add file in list by copy to '$FBPATH/releases/'
```

위와 같이 목록이 비어있는 경우에는 파일 경로를 입력하거나 url 입력을 통해서만 installer를 선택할 수 있습니다.

url을 통해 installer를 다운로드 하거나 `$FBPATH/releases/` 경로 아래에 installer 파일을 복사하면 리스트에 추가됩니다.


</br>

### host 입력

```
Please type host list separated by comma(,) [127.0.0.1]
nodeA, nodeB, nodeC, nodeD
OK, ['nodeA', 'nodeB', 'nodeC', 'nodeD']
```

ip주소 혹은 hostname을 입력합니다. 여러 개를 입력하는 경우 쉼표(,)를 구분자로 사용하세요.


</br>

### master 정보 입력

```
How many masters would you like to create on each host? [1]
1
OK, 1
Please type ports separate with comma(,) and use hyphen(-) for range. [18100]
18100
OK, ['18100']
```

각 host에 몇 개의 master 를 생성할지 입력합니다. 

만약 4개 host를 선택했고 1를 입력한다면 총 4개의 master가 생성됩니다. 

port 입력은 쉼표(,)를 구분자로 사용하며 범위를 입력하고 싶은 경우 하이픈(-)을 사용하세요. 

ex) `18100-18101`

port는 cluster id와 master의 개수를 기반으로 추천해줍니다.


</br>

### slave 정보 입력

```
How many replicas would you like to create on each master? [2]
2
OK, 2
Please type ports separate with comma(,) and use hyphen(-) for range. [18150-18151]
18150-18151
OK, ['18150-18151']
```

각 master 마다 몇 개의 slave를 생성할 지 입력합니다. 

만약 4개의 마스터를 생성하고 2를 입력한다면 총 8개의 slave가 생성됩니다. 

slave를 사용하지 않으려면 0을 입력하세요. 

port 입력은 쉼표(,)를 구분자로 사용하며 범위를 입력하고 싶은 경우 하이픈(-)을 사용하세요. 

ex) `18150-18151`

port는 cluster id와 slave의 개수를 기반으로 추천해줍니다.


</br>

### 그 외 정보 입력

```
How many ssd would you like to use? [3]
3
OK, 3
Type prefix of db path [/sata_ssd/ssd_]
/sata_ssd/ssd_
OK, /sata_ssd/ssd_
```


</br>

### 정보확인

```
+-------------------+---------------------------------------------+
| NAME              | VALUE                                       |
+-------------------+---------------------------------------------+
| installer         | tsr2-installer.bin.lightningdb_v1.1.10.centos |
| nodes             | nodeA                                       |
|                   | nodeB                                       |
|                   | nodeC                                       |
|                   | nodeD                                       |
| master ports      | 18100                                       |
| slave ports       | 18150-18151                                 |
| ssd count         | 3                                           |
| prefix_of_db_path | ~/sata_ssd/ssd_                             |
+-------------------+---------------------------------------------+
Do you want to proceed with the deploy accroding to the above information? (y/n)
y
```

모든 정보입력이 완료되면 위와 같이 입력한 정보들을 확인합니다.

</br>

### Deploy 진행

```
Check status of hosts...
+-----------+--------+
| HOST      | STATUS |
+-----------+--------+
| nodeA     | OK     |
| nodeB     | OK     |
| nodeC     | OK     |
| nodeD     | OK     |
+-----------+--------+
OK
Checking for cluster exist...
+-----------+--------+
| HOST      | STATUS |
+-----------+--------+
| nodeA     | CLEAN  |
| nodeB     | CLEAN  |
| nodeC     | CLEAN  |
| nodeD     | CLEAN  |
+-----------+--------+
OK
Transfer install and execute...
 - nodeA
 - nodeB
 - nodeC
 - nodeD
Sync conf...
Complete to deploy cluster 1
Cluster 1 selected.
```

deploy가 성공적으로 진행되면 위와 같은 메세지들과 함께 완료된 후 클러스터에 접속이 됩니다.

</br>

### Deploy 진행 중 오류 발생시

#### Host connection error

```
Check status of hosts...
+-------+------------------+
| HOST  | STATUS           |
+-------+------------------+
| nodeA | OK               |
| nodeB | SSH ERROR        |
| nodeC | UNKNOWN HOST     |
| nodeD | CONNECTION ERROR |
+-------+------------------+
There are unavailable host.
```

`SSH ERROR`: ssh 접속 오류입니다. key 교환 혹은 ssh client/server 상태를 점검하세요

`UNKNOWN HOST`: hostname을 통해 ip주소를 가져올 수 없는 경우입니다.

`CONNECTION ERROR`: host의 상태 혹은 outbound/inbound 등을 확인하세요.

</br>

#### Cluster already exist

```
Checking for cluster exist...
+-------+---------------+
| HOST  | STATUS        |
+-------+---------------+
| nodeA | CLEAN         |
| nodeB | CLEAN         |
| nodeC | CLUSTER EXIST |
| nodeD | CLUSTER EXIST |
+-------+---------------+
Cluster information exist on some hosts.
```

`CLUSTER EXIST`: 해당 host에 이미 deploy가 진행된 이력이 있는 경우입니다.

deploy가 진행 중 중단되는 경우에는 `CLUSTER EXIST` 가 뜨지 않습니다.

re-deploy의 경우 새로 추가되는 host만 검사합니다.


</br>

### Not include localhost

```
  Check status of hosts...
  +-------+------------------+
  | HOST  | STATUS           |
  +-------+------------------+
  | nodeB | OK               |
  | nodeC | OK               |
  | nodeD | OK               |
  +-------+------------------+
  Must include localhost.
```

deploy 에서 host 정보에 localhost를 포함하지 않는 경우 에러가 발생합니다. 

`localhost` 혹은 `127.0.0.1` 외에 ip주소나 hostname으로 입력해도 무방합니다.

</br>
</br>

## 클러스터 생성

deploy가 완료되었다면 클러스터 생성을 진행할 수 있습니다.

</br>

### redis conf 생성

```
> cluster configure
```

`redis-<master/slave>.conf.template` 와 `redis.properties` 를 이용해 `redis-<port>.conf` 파일들을 생성합니다.  

</br>

### redis 실행

클러스터를 구성할 redis들을 실행합니다.

```
> cluster start
Check status of hosts ...
OK
Check cluster exist...

...

OK
Backup redis master log in each MASTER hosts...

...

Starting master nodes : nodeA : 18100 ...

...

Starting slave nodes : nodeA : 18150|18151 ...

...

Wait until all redis process up...
cur: 0 / total: 12

...

cur: 12 / total: 12
Complete all redis process up.
```

</br>

### 클러스터 구성하기

 `cluster create` 명령어를 통해 클러스터를 구성합니다.

create를 시작하기 전에 구성정보를 확인하는 절차를 거칩니다.

```
> cluster create
>>> Creating cluster
+-------+-------+--------+
| HOST  | PORT  | TYPE   |
+-------+-------+--------+
| nodeA | 18100 | MASTER |
| nodeB | 18100 | MASTER |
|   .       .       .    |
|   .       .       .    |
|   .       .       .    |
| nodeD | 18150 | SLAVE  |
| nodeD | 18151 | SLAVE  |
+-------+-------+--------+
Do you want to proceed with the create according to the above information? (y/n)
y
replicas: 2.00
replicate [M] nodeA 18100 - [S] nodeA 18150
replicate [M] nodeD 18100 - [S] nodeD 18151
1 / 8 meet complete.
2 / 8 meet complete.

...

8 / 8 meet complete.
create cluster complete.
```

</br>

### 정보 확인

다음 명령어들을 통해 클러스터 상태 및 정보를 확인할 수 있습니다.

* `cli ping --all`

* `cli cluster info`

* `cli cluster nodes `


</br>

### 클러스터 구성 중 오류 발생 시

#### ClusterError

```
> cluster create
>>> Creating cluster
+-------+-------+--------+
| HOST  | PORT  | TYPE   |
+-------+-------+--------+
| nodeA | 18100 | MASTER |
| nodeB | 18100 | MASTER |
|   .       .       .    |
|   .       .       .    |
|   .       .       .    |
| nodeD | 18150 | SLAVE  |
| nodeD | 18151 | SLAVE  |
+-------+-------+--------+
Do you want to proceed with the create according to the above information? (y/n)
y
Node nodeA:18100 is already in a cluster
```

해당 redis가 이미 클러스터로 구성되어 있는 경우입니다. 

해당 redis를 포함하는 클러스터에서 `cluster clean --all` 명령어를 통해 클러스터를 해제를 먼저 해야합니다.

해당 redis들을 클러스터에서 강제로 해제시킨 후 구성하려면 `cluster restart --reset` 을 사용하세요.


</br>

#### Connection Error

```
root@lightningdb:32> cluster create
>>> Creating cluster
+-------+-------+--------+
| HOST  | PORT  | TYPE   |
+-------+-------+--------+
| nodeA | 18100 | MASTER |
| nodeB | 18100 | MASTER |
|   .       .       .    |
|   .       .       .    |
|   .       .       .    |
| nodeD | 18150 | SLAVE  |
| nodeD | 18151 | SLAVE  |
+-------+-------+--------+
Do you want to proceed with the create according to the above information? (y/n)
y
nodeD:18100 - [Errno 111] Connection refused
```

해당 redis가 실행중이 아닌 경우 발생합니다. `cluster start` 명령어를 통해 먼저 redis를 실행시켜야 합니다.

</br>
</br>

## lightningdb Version Update

lightningdb version의 변경은 `deploy` 명령어를 통해 진행할 수 있습니다.

</br>

### Deploy

```
> c 1 // alias of 'cluster use 1'
> deploy
(Watch out) Cluster 1 is already deployed. Do you want to deploy again? (y/n) [n]
y
```

> 클러스터에 접속하지 않고 클러스터 번호를 같이 입력해도 됩니다.
>
> ```
> > deploy 1
> ```

</br>

#### Installer

```
Select installer

    [ INSTALLER LIST ]
    (1) tsr2-installer.bin.lightningdb_v1.1.10.centos
    (2) tsr2-installer.bin.lightningdb_v1.1.09.centos
    (3) tsr2-installer.bin.lightningdb_v1.1.08.centos

Please enter the number, file path or url of the installer you want to use.
you can also add file in list by copy to '$FBPATH/releases/'
```

installer를 선택하거나 파일경로 혹은 url을 입력하세요.

</br>

### Restore

```
Do you want to restore conf? (y/n)
y
```

현재 설정값을 그대로 사용할 것인지 물어봅니다. `y` 를 선택해주세요.

</br>

### 정보확인 및 진행

정보확인 후 클러스터와 conf의 백업과 함께 update가 진행됩니다.

```
+-----------------+---------------------------------------------+
| NAME            | VALUE                                       |
+-----------------+---------------------------------------------+
| installer       | tsr2-installer.bin.lightningdb_v1.1.10.centos |
| nodes           | nodeA                                       |
|                 | nodeB                                       |
|                 | nodeC                                       |
|                 | nodeD                                       |
| master ports    | 18100                                       |
| slave ports     | 18150-18151                                 |
| ssd count       | 3                                           |
| redis data path | /sata_ssd/ssd_                              |
| redis db path   | /sata_ssd/ssd_                              |
| flash db path   | /sata_ssd/ssd_                              |
+-----------------+---------------------------------------------+
Do you want to proceed with the deploy accroding to the above information? (y/n)
y
Check status of hosts...
+-----------+--------+
| HOST      | STATUS |
+-----------+--------+
| nodeA     | OK     |
| nodeB     | OK     |
| nodeC     | OK     |
| nodeD     | OK     |
+-----------+--------+
Checking for cluster exist...
+------+--------+
| HOST | STATUS |
+------+--------+
Backup conf of cluster 1...
OK, cluster_1_conf_bak_<time-stamp>
Backup info of cluster 1 at nodeA...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeB...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeC...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeD...
OK, cluster_1_bak_<time-stamp>
Transfer installer and execute...
 - nodeA
 - nodeB
 - nodeC
 - nodeD
Sync conf...
Complete to deploy cluster 1.
Cluster 1 selected.
```

클러스터 백업 경로: `<base-directory>/backup/cluster_<cluster-id>_bak_<time-stamp>`

conf 백업 경로: `$FBAPTH/conf_backup/cluster_<cluster-id>_conf_bak_<time-stamp>`


</br>

### restart

```
> cluster restart
```

`cluster restart` 를 통해 재시작을 해주면 완료됩니다.


</br>
</br>

## Re-Deploy

deploy가 완료된 클러스터에서 `deploy` 명령어를 통해 다시 진행할 수 있습니다.


</br>

### Stop

host, port 등 정보가 변경된다면 deploy 이전에 반드시 중지 및 정보 리셋이 필요합니다.

```
> cluster stop
> cluster clean --all
```

</br>

### Deploy

```
> c 1 // alias of 'cluster use 1'
> deploy
(Watch out) Cluster 1 is already deployed. Do you want to deploy again? (y/n) [n]
y
```

> 클러스터에 접속하지 않고 argument로 클러스터 번호를 주어도 됩니다.
>
> ```
> > deploy 1
> ```


</br>

### Installer

```
Select installer

    [ INSTALLER LIST ]
    (1) tsr2-installer.bin.lightningdb_v1.1.10.centos
    (2) tsr2-installer.bin.lightningdb_v1.1.09.centos
    (3) tsr2-installer.bin.lightningdb_v1.1.08.centos

Please enter the number, file path or url of the installer you want to use.
you can also add file in list by copy to '$FBPATH/releases/'
```

다시 설치할 lightningdb의 installer를 선택해주세요.

변경하지 않는 경우 기존에 사용했던 installer를 선택하시면 됩니다.


</br>

### Restore

```
Do you want to restore conf? (y/n)
n
```

현재 설정값을 그대로 사용할 것인지 물어봅니다. 정보변경을 위해 `n` 을 선택합니다.


</br>

### Setup Info

```
#!/bin/bash

## Master hosts and ports
export SR2_REDIS_MASTER_HOSTS=( "nodeA" "nodeB" "nodeC" "nodeD" )
export SR2_REDIS_MASTER_PORTS=( 18100 )

## Slave hosts and ports (optional)
export SR2_REDIS_SLAVE_HOSTS=( "nodeA" "nodeB" "nodeC" "nodeD" )
export SR2_REDIS_SLAVE_PORTS=( $(seq 18150 18151) )

## only single data directory in redis db and flash db
## Must exist below variables; 'SR2_REDIS_DATA', 'SR2_REDIS_DB_PATH' and 'SR2_FLASH_DB_PATH'
#export SR2_REDIS_DATA="/nvdrive0/nvkvs/redis"
#export SR2_REDIS_DB_PATH="/nvdrive0/nvkvs/redis"
#export SR2_FLASH_DB_PATH="/nvdrive0/nvkvs/flash"

## multiple data directory in redis db and flash db
export SSD_COUNT=3
#export HDD_COUNT=3
export SR2_REDIS_DATA="~/sata_ssd/ssd_"
export SR2_REDIS_DB_PATH="~/sata_ssd/ssd_"
export SR2_FLASH_DB_PATH="~/sata_ssd/ssd_"

#######################################################
# Example : only SSD data directory
#export SSD_COUNT=3
#export SR2_REDIS_DATA="/ssd_"
#export SR2_REDIS_DB_PATH="/ssd_"
#export SR2_FLASH_DB_PATH="/ssd_"
#######################################################
```

위와 같이 기존의 `redis.properties` 파일이 열립니다. 수정하고자 하는 부분을 수정해주세요.

수정 중 정보오류 등으로 deploy가 중단된 경우 수정이력이 저장되며 아래와 같이 불러올 수 있습니다.

```
Do you want to restore conf? (y/n)
n
There is a history of modification. Do you want to load? (y/n)
y
```


</br>

### 정보확인 및 진행

정보확인 후 클러스터와 conf의 백업과 함께 update가 진행됩니다.

```
+-----------------+---------------------------------------------+
| NAME            | VALUE                                       |
+-----------------+---------------------------------------------+
| installer       | tsr2-installer.bin.lightningdb_v1.1.10.centos |
| nodes           | nodeA                                       |
|                 | nodeB                                       |
|                 | nodeC                                       |
|                 | nodeD                                       |
| master ports    | 18100                                       |
| slave ports     | 18150-18151                                 |
| ssd count       | 3                                           |
| redis data path | /sata_ssd/ssd_                              |
| redis db path   | /sata_ssd/ssd_                              |
| flash db path   | /sata_ssd/ssd_                              |
+-----------------+---------------------------------------------+
Do you want to proceed with the deploy accroding to the above information? (y/n)
y
Check status of nodes...
+-----------+--------+
| HOST      | STATUS |
+-----------+--------+
| nodeA     | OK     |
| nodeB     | OK     |
| nodeC     | OK     |
| nodeD     | OK     |
+-----------+--------+
Backup conf of cluster 1...
OK, cluster_1_conf_bak_<time-stamp>
Backup info of cluster 1 at nodeA...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeB...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeC...
OK, cluster_1_bak_<time-stamp>
Backup info of cluster 1 at nodeD...
OK, cluster_1_bak_<time-stamp>
Transfer installer and execute...
Complete to deploy cluster 1.
Cluster 1 selected.
```

클러스터 백업 경로: `<base-directory>/backup/cluster_<cluster-id>_bak_<time-stamp>`

conf 백업 경로: `$FBAPTH/conf_backup/cluster_<cluster-id>_conf_bak_<time-stamp>`



</br>
</br>

## Add Slave

You can add a slave to a cluster that is configured only with master without redundancy.

### create cluster only with master

(Procedure for configuring the test environment. If cluster with only master already exists, go to the [add slave info](#add-slave-info).)

Proceed with the deploy.

```
> deploy 3
```

Enter 0 in replicas as shown below when deploy.

```
Select installer

    [ INSTALLER LIST ]
    (1) tsr2-installer.bin.lightningdb_v1.1.10.centos

Please enter the number, file path or url of the installer you want to use.
you can also add file in list by copy to '$FBPATH/releases/'
1
OK, tsr2-installer.bin.lightningdb_v1.1.10.centos
Please type host list separated by comma(,) [127.0.0.1]
127.0.0.1
OK, ['127.0.0.1']
How many masters would you like to create on each host? [1]
1
OK, 1
Please type ports separate with comma(,) and use hyphen(-) for range. [18300]
18300
OK, ['18300']

*-----------------------------------------------------------------*
| How many replicas would you like to create on each master? [2]  |
| 0                                                               |
| OK, 0                                                           |
*-----------------------------------------------------------------*
 ↳ (a border just for emphasis)

How many ssd would you like to use? [3]
3
OK, 3
Type prefix of db path [/sata_ssd/ssd_]
/sata_ssd/ssd_
OK, /sata_ssd/ssd_
+-------------------+---------------------------------------------+
| NAME              | VALUE                                       |
+-------------------+---------------------------------------------+
| installer         | tsr2-installer.bin.lightningdb_v1.1.10.centos |
| hosts             | 127.0.0.1                                   |
| master ports      | 18300                                       |
| ssd count         | 3                                           |
| prefix_of_db_path | /sata_ssd/ssd_                              |
+-------------------+---------------------------------------------+
Do you want to proceed with the deploy accroding to the above information? (y/n)
y
```

When the deploy is complete, start and create the cluster.

```
> cluster start
...
> cluster create
...
```

<br/>


### add slave info

```
> conf cluster
```

You can modify `redis.properties` by entering the command as shown above.

```sh
  1 #!/bin/bash
  2
  3 ## Master hosts and ports
  4 export SR2_REDIS_MASTER_HOSTS=( "127.0.0.1" )
  5 export SR2_REDIS_MASTER_PORTS=( 18300 )
  6
  7 ## Slave hosts and ports (optional)
  8 #export SR2_REDIS_SLAVE_HOSTS=( "127.0.0.1" )
  9 #export SR2_REDIS_SLAVE_PORTS=( $(seq 18600 18609) )
 10
 11 ## only single data directory in redis db and flash db
 12 ## Must exist below variables; 'SR2_REDIS_DATA', 'SR2_REDIS_DB_PATH' and 'SR2_FLASH_DB_PATH'
 13 #export SR2_REDIS_DATA="/nvdrive0/nvkvs/redis"
 14 #export SR2_REDIS_DB_PATH="/nvdrive0/nvkvs/redis"
 15 #export SR2_FLASH_DB_PATH="/nvdrive0/nvkvs/flash"
 16
 17 ## multiple data directory in redis db and flash db
 18 export SSD_COUNT=3
 19 #export HDD_COUNT=3
 20 export SR2_REDIS_DATA="/sata_ssd/ssd_"
 21 export SR2_REDIS_DB_PATH="/sata_ssd/ssd_"
 22 export SR2_FLASH_DB_PATH="/sata_ssd/ssd_"
 23
 24 #######################################################
 25 # Example : only SSD data directory.
 26 #export SSD_COUNT=3
 27 #export SR2_REDIS_DATA="/ssd_"
 28 #export SR2_REDIS_DB_PATH="/ssd_"
 29 #export SR2_FLASH_DB_PATH="/ssd_"
 30 #######################################################
```

Modify `SR2_REDIS_SLAVE_HOSTS` and `SR2_REDIS_SLAVE_PORTS` as shown below.


```sh
  1 #!/bin/bash
  2
  3 ## Master hosts and ports
  4 export SR2_REDIS_MASTER_HOSTS=( "127.0.0.1" )
  5 export SR2_REDIS_MASTER_PORTS=( 18300 )
  6
  7 ## Slave hosts and ports (optional)
  8 export SR2_REDIS_SLAVE_HOSTS=( "127.0.0.1" )
  9 export SR2_REDIS_SLAVE_PORTS=( $(seq 18350 18351) )
 10
 11 ## only single data directory in redis db and flash db
 12 ## Must exist below variables; 'SR2_REDIS_DATA', 'SR2_REDIS_DB_PATH' and 'SR2_FLASH_DB_PATH'
 13 #export SR2_REDIS_DATA="/nvdrive0/nvkvs/redis"
 14 #export SR2_REDIS_DB_PATH="/nvdrive0/nvkvs/redis"
 15 #export SR2_FLASH_DB_PATH="/nvdrive0/nvkvs/flash"
 16
 17 ## multiple data directory in redis db and flash db
 18 export SSD_COUNT=3
 19 #export HDD_COUNT=3
 20 export SR2_REDIS_DATA="/sata_ssd/ssd_"
 21 export SR2_REDIS_DB_PATH="/sata_ssd/ssd_"
 22 export SR2_FLASH_DB_PATH="/sata_ssd/ssd_"
 23
 24 #######################################################
 25 # Example : only SSD data directory.
 26 #export SSD_COUNT=3
 27 #export SR2_REDIS_DATA="/ssd_"
 28 #export SR2_REDIS_DB_PATH="/ssd_"
 29 #export SR2_FLASH_DB_PATH="/ssd_"
 30 #######################################################
 ```

<br/>

### execute command add-slave

```
> cluster add-slave
Check status of hosts...
OK
sync conf
Complete edit
root@lightningdb:3> cluster add-slave
Check status of hosts...
OK
Check cluster exist...
 - 127.0.0.1
OK
Removing redis generated slave configuration files
 - 127.0.0.1
Removing flash db directory, appendonly and dump.rdb files in master
Removing flash db directory, appendonly and dump.rdb files in slave
 - 127.0.0.1
Removing master node configuration
Removing slave node configuration
 - 127.0.0.1
Backup redis slave log in each SLAVE hosts...
 - 127.0.0.1
Generate redis configuration files for slave hosts
sync conf
+-----------+--------+
| HOST      | STATUS |
+-----------+--------+
| 127.0.0.1 | OK     |
+-----------+--------+
Starting slave nodes : 127.0.0.1 : 18350|18351 ...
Wait until all redis process up...
cur: 3 / total: 3
Complete all redis process up
replicate [M] 127.0.0.1 18300 - [S] 127.0.0.1 18350
replicate [M] 127.0.0.1 18300 - [S] 127.0.0.1 18351
1 / 2 meet complete.
2 / 2 meet complete.
```

<br/>

### check configuration information

```
> cli cluster nodes
fc7d8c... 127.0.0.1:18300 myself,master - 0 1573628546000 0 connected 0-16383
f9dbb3... 127.0.0.1:18351 slave fc7d8c... 0 1573628547266 1 connected
60c723... 127.0.0.1:18350 slave fc7d8c... 0 1573628548269 1 connected
```

<br/>
<br/>

## Thrift Server


* start
* monitor
* beeline
* stop
* restart


`ths` is alias of `thriftserver`

You can modify information of thrift server by command `conf thriftserver (= conf ths)`
thrift server 관련 정보수정은 `conf thriftserver (= conf ths)` 를 이용하세요.

<br/>

### start

Run the thrift server.

```
> ths start  # alias of thriftserver start
starting org.apache.spark.sql.hive.thriftserver.HiveThriftServer2, logging to <logfile-name>
```

You can view the logs through the command [monitor](#monitor).

<br/>

### monitor

You can view the logs of the thrift server in real time.

```
> ths monitor  # alias of thriftserver monitor
Press Ctrl-C for exit.
(show log)
```

<br/>

### beeline

Connect to the thrift server

For more information, see the [link](https://cwiki.apache.org/confluence/display/Hive/HiveServer2+Clients#HiveServer2Clients-Beeline%E2%80%93CommandLineShell).

```
> ths beeline  # alias of thriftserver beeline
Connecting...
Connecting to jdbc:hive2://localhost:13000
<timestamp> INFO jdbc.Utils: Supplied authorities: localhost:13000
<timestamp> INFO jdbc.Utils: Resolved authority: localhost:13000
<timestamp> INFO jdbc.HiveConnection: Will try to open client transport with JDBC Uri: jdbc:hive2://localhost:13000
Connected to: Spark SQL (version 2.1.1)
Driver: Hive JDBC (version 1.2.1.spark2)
Transaction isolation: TRANSACTION_REPEATABLE_READ
Beeline version 1.2.1.spark2 by Apache Hive
0: jdbc:hive2://localhost:13000>
```

Default value of db url to connect is `jdbc:hive2://$HIVE_HOST:$HIVE_PORT`

You can modify `$HIVE_HOST` and `$HIVE_PORT` by command `conf ths`

<br/>

### stop

Shut down the thrift server.

```
> ths stop  # alias of thriftserver stop
stopping org.apache.spark.sql.hive.thriftserver.HiveThriftServer2
```

<br/>

### restart

Restart the thrift server.

```
> ths restart  # alias of thriftserver restart
stopping org.apache.spark.sql.hive.thriftserver.HiveThriftServer2
starting org.apache.spark.sql.hive.thriftserver.HiveThriftServer2, logging to <logfile-name>
```


</br>
</br>

## Logging in file

`$FBPATH/logs/fb-roate.log` 에 debug 수준의 로그가 저장됩니다.

최대 1GiB 만큼 저장하며 초과하는 경우 최신순으로 rolling update가 진행됩니다.

LTCLI의 로그만 저장됩니다. 클러스터, thriftserver 등의 로그는 별도의 명령어를 사용하세요.
