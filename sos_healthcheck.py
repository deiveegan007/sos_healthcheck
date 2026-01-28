#!/usr/bin/env python3

import os
import time
import subprocess

# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def run(cmd):
    return subprocess.getoutput(cmd).strip()

def meminfo_value(key):
    """
    Safe single-value reader for proc/meminfo.
    Prevents multiline / NUMA issues.
    """
    try:
        with open("proc/meminfo") as f:
            for line in f:
                if line.startswith(key + ":"):
                    return line.split()[1]
    except Exception:
        pass
    return "0"

# --------------------------------------------------
# OS Detection
# --------------------------------------------------
OS_VER = "Linux"
st_uname = run("cat uname")

if "el10" in st_uname:
    OS_VER = "OL10"
elif "el9" in st_uname:
    OS_VER = "OL9"
elif "el8" in st_uname:
    OS_VER = "OL8"
elif "el7" in st_uname:
    OS_VER = "OL7"
elif "el6" in st_uname:
    OS_VER = "OL6"
elif "el5" in st_uname or "xen" in st_uname:
    OS_VER = "OL5"

print("")

# --------------------------------------------------
# Uptime
# --------------------------------------------------
st_hostname = run("cat hostname")

if OS_VER in ("OL6", "OL7"):
    st_date = run("cat date")
    st_year = run("cat date | awk '{print $NF}'")
    st_timezone = run("cat date | awk '{print $5}'")
else:
    st_date = run("cat ./sos_commands/date/date")
    st_year = run("cat ./sos_commands/date/date | awk '{print $NF}'")
    st_timezone = st_year

st_uptime1 = run("cat uptime | awk -F',' '{print $1}'")
st_uptime2 = st_uptime1[st_uptime1.index("up") + 3:]

print(f"[INFO] Host {st_hostname} already running for {st_uptime2} till \"{st_date}\"")
print("")

# --------------------------------------------------
# Load Average
# --------------------------------------------------
st_load15 = float(run("cat uptime | awk -F',' '{print $NF}'"))
st_load5 = float(run("cat uptime | awk -F',' '{print $(NF-1)}'"))
st_load1 = run("cat uptime | awk -F',' '{print $(NF-2)}'")
st_load1 = float(st_load1[st_load1.index(':') + 1:])

f_max_load = max([st_load15, st_load5, st_load1])
n_core = int(run("cat proc/cpuinfo | grep processor | tail -1 | awk '{print $3}'")) + 1

st_res = "INFO"
if f_max_load > ((n_core + 1) / 2):
    st_res = "WARNING"

print(f"[{st_res}] Max load in last 15 minutes is {f_max_load}, total cpu cores {n_core}")
print("")

# --------------------------------------------------
# kdump / chrony / firewall / ntp
# --------------------------------------------------
if OS_VER == "OL6":
    st_runlevel = run("cat ./sos_commands/startup/runlevel | awk '{print $2}'")

    print("[INFO] kdump enabled" if f"{st_runlevel}:on" in run("cat chkconfig | grep kdump")
          else "[INFO] kdump not enabled")

    print("[INFO] ntp enabled" if f"{st_runlevel}:on" in run("cat chkconfig | grep ntp")
          else "[INFO] ntp not enabled")

    print("[INFO] iptables enabled" if f"{st_runlevel}:on" in run("cat chkconfig | grep iptables")
          else "[INFO] iptables not enabled")

else:
    print("[INFO] kdump enabled" if "enabled" in run(
        "cat ./sos_commands/systemd/systemctl_list-unit-files | grep kdump")
        else "[INFO] kdump not enabled")

    print("[INFO] chrony enabled" if "enabled" in run(
        "cat ./sos_commands/systemd/systemctl_list-unit-files | grep chronyd")
        else "[INFO] chrony not enabled")

    print("[INFO] firewall enabled" if "enabled" in run(
        "cat ./sos_commands/systemd/systemctl_list-unit-files | grep firewalld")
        else "[INFO] firewall not enabled")

print("")

# --------------------------------------------------
# sysrq
# --------------------------------------------------
st_sysrq = run("cat sos_commands/kernel/sysctl_-a | grep sysrq | awk '{print $3}'")
print("[INFO] sysrq enabled" if st_sysrq != "0" else "[INFO] sysrq not enabled")

# --------------------------------------------------
# SELinux
# --------------------------------------------------
if os.path.exists("etc/sysconfig/selinux"):
    st_selinux = run(
        "cat etc/sysconfig/selinux | grep -v '^#' | grep SELINUX= | awk -F= '{print $2}'")
    print("[INFO] SELinux disabled" if st_selinux == "disabled"
          else "[WARNING] SELinux not disabled")

print("")

# --------------------------------------------------
# MEMORY (EXTRA SAFE)
# --------------------------------------------------
total_mem = float(meminfo_value("MemTotal"))
mem_cache = float(meminfo_value("Cached"))
mem_buff = float(meminfo_value("Buffers"))
mem_free = float(meminfo_value("MemFree"))
mem_anon = float(meminfo_value("AnonPages"))
mem_pagetable = float(meminfo_value("PageTables"))

hugepage_nr = int(meminfo_value("HugePages_Total"))
hugepage_sz = int(meminfo_value("Hugepagesize"))

if hugepage_nr == 0:
    print("[INFO] No HugePage memory")
else:
    hugepage_ratio = (hugepage_nr * hugepage_sz / total_mem) * 100
    print(f"[INFO] HugePage memory {hugepage_ratio:.2f}% of total memory")

f_mem_avail = 100 * (mem_cache + mem_buff + mem_free) / total_mem
print(f"[INFO] Available memory (free+cached+buffer) {f_mem_avail:.2f}% of total memory")

f_mem_anon = 100 * mem_anon / total_mem
print(f"[INFO] Anonymous memory {f_mem_anon:.2f}% of total memory")

f_mem_pagetable = 100 * mem_pagetable / total_mem
print(f"[INFO] PageTables memory {f_mem_pagetable:.2f}% of total memory")

print("")

# --------------------------------------------------
# Swap
# --------------------------------------------------
st_swap_total = int(run("cat free | grep Swap | awk '{print $2}'"))
if st_swap_total == 0:
    print("[WARNING] Zero size swap space")

print("")

# --------------------------------------------------
# Disk usage (>90%)
# --------------------------------------------------
bDf = False
st_volumes = run(
    "cat df | awk '{print $5}' | grep '%' | grep -v Use | awk -F'%' '{print $1}'"
)

for vol in st_volumes.splitlines():
    if vol.strip() and int(vol) > 90:
        bDf = True
        break

if bDf:
    print("[WARNING] Some file system usage > 90%")
else:
    print("[INFO] All file systems usage < 90%")

print("")

# --------------------------------------------------
# Process checks
# --------------------------------------------------
st_stateD = int(run("cat ps | awk '$8~/D.*/ {print}' | wc -l"))
if st_stateD != 0:
    print("[WARNING] D state processes existing")
    print("")

st_osw = int(run("cat ps | grep -v USER | egrep -i 'osw|Exawat' | wc -l"))
if st_osw > 0:
    print("[INFO] OSWatcher (or ExaWatcher) is running")
else:
    print("[WARNING] No OSWatcher running")

print("")
