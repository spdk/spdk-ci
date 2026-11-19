#!/usr/bin/env bash
# Run autorun.sh with its output in a log file, and copy the file to stdout.
#
# CIJoe reads the output of a running command one byte at a time. Tests that
# log faster than that would block on it, so they write to the file and only
# follow_log writes to CIJoe.

log=/opt/output/autorun.log

# Copy the log to stdout while the tests run, then copy what is left.
# stdin is the log. Each cat continues where the previous one stopped.
follow_log() {
	local tests_pid=$1

	while kill -0 "$tests_pid" 2> /dev/null; do
		sleep 1
		cat
	done
	cat
}

: > "$log" || exit
(
	# cat keeps stderr a pipe. gen_conf in test/dd/common.sh runs
	# tee /dev/stderr, which truncates a file that stderr is redirected to.
	/opt/spdk/autorun.sh "$@" 2>&1 | cat > "$log"
	exit "${PIPESTATUS[0]}"
) &
tests_pid=$!

follow_log "$tests_pid" < "$log" &

# Exit with the tests and leave follow_log running. CIJoe reads what is left
# of the output in blocks once this script has exited.
wait "$tests_pid"
