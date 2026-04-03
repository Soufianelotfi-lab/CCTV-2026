#!/usr/bin/env bash
set -uo pipefail

DISPLAY_NUM=":0"
LOCK_FILE="/tmp/.X0-lock"
XORG_CONF="/etc/X11/xorg-jetson.conf"
XAUTH_FILE="/tmp/.Xauthority-jetson"

handle_existing_lock() {
    local lock_pid
    lock_pid=$(cat "${LOCK_FILE}" | tr -d '[:space:]')

    if ! kill -0 "${lock_pid}" 2>/dev/null; then
        echo "Stale X lock file found, removing..."
        rm -f "${LOCK_FILE}"
        return 1
    fi

    local proc_name
    proc_name=$(ps -p "${lock_pid}" -o comm= 2>/dev/null || echo "unknown")

    if [[ "${proc_name}" == "Xorg" || "${proc_name}" == "X" ]]; then
        echo "Xorg already running on ${DISPLAY_NUM} (PID ${lock_pid})"
        return 0
    else
        echo "WARNING: ${DISPLAY_NUM} is owned by '${proc_name}' (display manager?)." >&2
        echo "         Stop the display manager and re-run this script." >&2
        return 0
    fi
}

start_xorg() {
    if [ ! -f "${XORG_CONF}" ]; then
        echo "ERROR: ${XORG_CONF} not found." >&2
        echo "       sudo cp xorg-jetson.conf /etc/X11/xorg-jetson.conf" >&2
        exit 1
    fi

    touch "${XAUTH_FILE}"
    chmod 600 "${XAUTH_FILE}"
    if command -v mcookie &>/dev/null; then
        xauth -f "${XAUTH_FILE}" add "${DISPLAY_NUM}" . "$(mcookie)" 2>/dev/null || true
    else
        xauth -f "${XAUTH_FILE}" generate "${DISPLAY_NUM}" . trusted 2>/dev/null || true
    fi

    sudo Xorg "${DISPLAY_NUM}" \
        -config "${XORG_CONF}" \
        -auth "${XAUTH_FILE}" \
        -nolisten tcp \
        -logfile /tmp/Xorg.jetson.log \
        &

    local retries=0
    while [ ! -f "${LOCK_FILE}" ] && [ "${retries}" -lt 10 ]; do
        sleep 0.5
        retries=$((retries + 1))
    done

    if [ ! -f "${LOCK_FILE}" ]; then
        echo "ERROR: Xorg failed to start. Check /tmp/Xorg.jetson.log" >&2
        exit 1
    fi
}

if [ -f "${LOCK_FILE}" ]; then
    handle_existing_lock || start_xorg
else
    start_xorg
fi

export DISPLAY="${DISPLAY_NUM}"
export XAUTHORITY="${XAUTH_FILE}"

if ! DISPLAY="${DISPLAY_NUM}" XAUTHORITY="${XAUTH_FILE}" xrandr 2>/dev/null | grep -q "DP-0 connected"; then
    echo "ERROR: DP-0 not detected by xrandr" >&2
    exit 1
fi

echo "Display :0 ready on DP-0"
