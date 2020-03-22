Prometheus exporter for Per-User usage from Cisco LNSs

Exporter for Promethus allows you to graph traffic usage on "per username" basis.  It provide metric in formate listed bellow. 

# TYPE ifOutOctets counter
ifOutOctets{ user="user1@exaample.com" } 1912961758
# TYPE ifInOctets counter
ifInOctets{ user="user1@exaample.com" } 1241623498
# TYPE total_l2tp_sessions summary
total_l2tp_sessions 1
# TYPE request_processing_seconds summary
request_processing_seconds 7.061648626986425

Requrements:
* Python 3.7
* pysnmp

Usage:
per-user-usage.py -c Asi8SnM3
