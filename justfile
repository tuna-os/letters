# Letters — build & run as a Flatpak using org.flatpak.Builder (himachal pipeline).
# Part of the suite migration: consumes suite-common as a meson subproject.

app_id := "org.tunaos.letters"
manifest := app_id + ".json"

default:
    @just --list

setup:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p subprojects
    if [ -d subprojects/suite-common/.git ]; then
        git -C subprojects/suite-common fetch --depth 1 origin main
        git -C subprojects/suite-common reset --hard origin/main
    else
        rm -rf subprojects/suite-common
        git clone --depth 1 https://github.com/hanthor/suite-common.git subprojects/suite-common
    fi

build: setup
    #!/usr/bin/env bash
    set -euo pipefail
    state="$HOME/.cache/letters-flatpak"; mkdir -p "$state"
    flatpak run --cwd="$PWD" --filesystem=host org.flatpak.Builder \
        --force-clean --user --install --install-deps-from=flathub \
        --state-dir="$state/state" --repo="$state/repo" \
        "$state/build" "{{manifest}}"

run:
    flatpak run {{app_id}}

# Confirm Letters launches unchanged AND the suite-common package is importable.
verify: build
    #!/usr/bin/env bash
    set -uo pipefail
    flatpak kill {{app_id}} 2>/dev/null || true; sleep 1
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export WAYLAND_DISPLAY="$(ls "$XDG_RUNTIME_DIR" 2>/dev/null | grep -m1 -E '^wayland-[0-9]+$' || echo wayland-0)"
    imp=$(flatpak run --command=sh {{app_id}} -c \
        'python3 -c "import sys; sys.path.insert(0,\"/app/share/letters\"); import suite_common; print(\"suite_common import OK\")"' 2>&1)
    echo "import check: $imp"
    log=$(mktemp)
    timeout 7 flatpak run {{app_id}} >"$log" 2>&1 &
    pid=$!; sleep 5
    alive=no; kill -0 "$pid" 2>/dev/null && alive=yes
    flatpak kill {{app_id}} 2>/dev/null; kill "$pid" 2>/dev/null || true
    echo "launched(alive=$alive)"; tail -3 "$log"
    if echo "$imp" | grep -q "suite_common import OK" && [ "$alive" = yes ]; then
        echo "VERIFY: PASS (Letters runs unchanged; suite-common importable)"
    else echo "VERIFY: FAIL"; exit 1; fi

clean:
    rm -rf subprojects/suite-common "$HOME/.cache/letters-flatpak"

# Lint Python source files.
lint:
    python3 -m py_compile src/main.py
    python3 -m py_compile src/window.py
