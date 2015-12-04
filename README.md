# ceph-zabbix
A zabbix probe to get performance counters of ceph

Installation
============

Copy the script into /usr/local/bin/zabbix/ for instance.

Then, add the following zabbix parameter in /etc/zabbix/zabbix_agentd.conf.d/zabbix_ceph.conf for instance:
      UserParameter=ceph.discovery,sudo /usr/local/sbin/zabbix/check_ceph.py --cache 5 discover
      UserParameter=ceph.monitor[*],sudo /usr/local/sbin/zabbix/check_ceph.py --cache 5 monitor --id $1 --section $2 --key $3

Finally in zabbix setup the discovery rule and related items you need.