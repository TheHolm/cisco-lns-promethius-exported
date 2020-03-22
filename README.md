# Prometheus exporter for Per-User usage from Cisco LNSs

Exporter for Promethus allows you to graph traffic usage on "per username" basis.  It provide metric in formate listed bellow.  Supports only LNSes based Cisco XE based routers. 

```
# TYPE ifOutOctets counter
ifOutOctets{ user="user1@exaample.com" } 1912961758
# TYPE ifInOctets counter
ifInOctets{ user="user1@exaample.com" } 1241623498
# TYPE total_l2tp_sessions summary
total_l2tp_sessions 1
# TYPE request_processing_seconds summary
request_processing_seconds 7.061648626986425
```
## Requrements:
* Python 3.7
* pysnmp

## Usage:
1. Running exporter
```
usage: per-user-usage.py [-h] -c community [-p http_port] [-i bind_to_ip] -s

Per-User traffic stats Pronethetius exporter for Cisco LNS.

positional arguments:
  -s             SNMP destination UDP port, default 161

optional arguments:
  -h, --help     show this help message and exit
  -c community   SNMPv2 community string
  -p http_port   HTTP port to listen for Promethius scrapper, default 8000
  -i bind_to_ip  IP address where HTTP server will listen, default all
                 interfaces
```
1. Configure Prometheus
Add to prometheus.yml
```
scrape_configs:
  - job_name: 'LNSes'
    scrape_interval: 60s
    scrape_timeout: 40s
    metrics_path: /
    static_configs:
      - targets:
          - lns1.example.com
          - lns2.example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:8000  # SNMP exporter.
```

## Q/A
1.  Q: Why SNMP walk not SNMP Bulk.
    A: For some reason SNMP Bulk does not return sane results, I have no idea what causing it. Walking is working just fine for me.

## To Do
1. SNMPv3 suppport
1. Register lintening port in Prometheus database.
