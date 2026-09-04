#!/usr/bin/env bash
set -e

want=${1:?usage: $0 <hugepages>}
nr_hp=/proc/sys/vm/nr_hugepages

for attempt in {1..5}; do
	sync
	echo 3 > /proc/sys/vm/drop_caches
	echo 1 > /proc/sys/vm/compact_memory

	echo "$want" > "$nr_hp"
	got=$(< "$nr_hp")
	((got == want)) && exit 0

	sleep 2
done

echo "FATAL: $got / $want hugepages after $attempt attempts"
for f in /proc/sys/vm/min_free_kbytes \
	/proc/uptime \
	/proc/meminfo \
	/proc/buddyinfo \
	/proc/pagetypeinfo \
	/proc/zoneinfo; do
	echo "=== $f ==="
	cat "$f"
done
exit 1
