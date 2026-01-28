# sos_healthcheck
1. Dowload the script
2. Give execute permission
3. Go insise the soreport directory cd sosreport
4. ./sos_healthcheck.py 

Example:
$ sos_healthcheck

[INFO] Host <hostname>  already running for 1 days till "Tue Jan 27 14:43:24 UTC 2026"

[INFO] Max load in last 15 minutes is 13.45, total cpu cores 256

[INFO] kdump enabled
[INFO] chrony enabled
[INFO] firewall not enabled

[INFO] sysrq enabled
[INFO] SELinux disabled

[INFO] HugePage memory 90.68% of total memory
[INFO] Available memory (free+cached+buffer) 7.29% of total memory
[INFO] Anonymous memory 0.14% of total memory
[INFO] PageTables memory 0.00% of total memory

[INFO] All file systems usage < 90%

[INFO] OSWatcher (or ExaWatcher) is running

