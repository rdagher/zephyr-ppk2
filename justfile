# zephyr-ppk2: local recipes.
#
# Toolchain: the nrfutil-managed NCS install at /opt/nordic/ncs
# (NCS_VERSION picks the version; NCS_WORKSPACE overrides the path).
# Host side: capture with ppk2-lib, report with scripts/. See the README.

NCS_VERSION   := env_var_or_default("NCS_VERSION", "v3.3.1")
NCS_WORKSPACE := env_var_or_default("NCS_WORKSPACE", "/opt/nordic/ncs/" + NCS_VERSION)
DK_SERIAL     := env_var_or_default("DK_SERIAL", "")

BOARD_54LM20 := "nrf54lm20dk/nrf54lm20b/cpuapp"
BOARD_52840  := "nrf52840dk/nrf52840"
BOARD_54L15  := "nrf54l15dk/nrf54l15/cpuapp"

SAMPLES := "profiling wrap_profiling"
CAPTURES := "d5f74762de50988b90c8e89ec59aee44e19d6ebf"
ROOT    := justfile_directory()

# Show available recipes.
_default:
    @just --list --unsorted

# Toolchain wrapper: runs args inside the NCS toolchain context with
# CWD set to the workspace so west finds its manifest.
_tc *args:
    @cd "{{NCS_WORKSPACE}}" && nrfutil sdk-manager toolchain launch --ncs-version {{NCS_VERSION}} -- {{args}}

# Build one sample for one board (default: profiling on the nRF54LM20 DK).
build sample="profiling" board=BOARD_54LM20:
    @just _tc west build --board "{{board}}" --pristine=auto --build-dir "{{ROOT}}/samples/{{sample}}/build/$(echo '{{board}}' | cut -d/ -f1)" "{{ROOT}}/samples/{{sample}}" -- -DZEPHYR_EXTRA_MODULES="{{ROOT}}"

# Build every sample for the boards it supports.
build-all:
    @for s in {{SAMPLES}}; do just build $s "{{BOARD_54LM20}}" && just build $s "{{BOARD_52840}}" || exit 1; done
    @just build ble_advertising "{{BOARD_54LM20}}"
    @just build ble_advertising "{{BOARD_54L15}}"

# Put the captures in evidence/ (104 MB): the commit of the branch
# `captures` that evidence/README.md names, fetched if it is not here.
captures:
    git cat-file -e {{CAPTURES}}^{commit} 2>/dev/null || git fetch origin captures
    git archive {{CAPTURES}} '*.csv.xz' > "{{ROOT}}/evidence/.captures.tar"
    tar -x -C "{{ROOT}}/evidence" -f "{{ROOT}}/evidence/.captures.tar"
    rm "{{ROOT}}/evidence/.captures.tar"

# Redraw the figures of the documentation from the captures in evidence/.
plots:
    uv run --no-project --with matplotlib --with numpy python scripts/plot.py evidence/profiling.csv.xz --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit --window 8.75 10.15 --title "One cycle of samples/profiling on an nRF54LM20 DK" --out docs/img/profiling.png
    uv run --no-project --with matplotlib --with numpy python scripts/plot.py evidence/ble_advertising.csv.xz --name 0=radio --name 1=sensor --window 5.32 5.78 --title "samples/ble_advertising on an nRF54LM20 DK" --out docs/img/ble_advertising.png

# DK_SERIAL=… targets a specific dev kit (`nrfutil device list`);
# empty means the only attached DK. The DUT must be powered through the
# PPK2 meanwhile: `ppk2 run --source --vdd 3.3 -- just flash` (without
# --source in Ampere meter mode).
# Flash a sample's most recent hex via host nrfutil.
flash sample="profiling" board=BOARD_54LM20:
    @tag="$(echo '{{board}}' | cut -d/ -f1)" && hex="{{ROOT}}/samples/{{sample}}/build/$tag/merged.hex" && if [ ! -f "$hex" ]; then echo "build first: just build {{sample}} {{board}}"; exit 1; fi && nrfutil device program --firmware "$hex" --options chip_erase_mode=ERASE_ALL {{ if DK_SERIAL == "" { "" } else { "--serial-number " + DK_SERIAL } }}

# Wipe all build trees.
clean:
    rm -rf "{{ROOT}}"/samples/*/build

# Print resolved settings (debug helper).
which:
    @echo "NCS_WORKSPACE = {{NCS_WORKSPACE}}"
    @echo "NCS_VERSION   = {{NCS_VERSION}}"
    @echo "DK_SERIAL     = {{DK_SERIAL}}"
    @echo "samples       = {{SAMPLES}}"
    @echo "boards        = {{BOARD_54LM20}} | {{BOARD_52840}} | {{BOARD_54L15}}"

# Append the figure of `west ppk2 plot` to the terminal recording made by
# docs/workflow.tape: the README's recording. Needs ffmpeg.
demo-figure terminal="workflow-terminal.gif" figure="cycle.png":
    ffmpeg -loglevel error -y -i "{{terminal}}" -loop 1 -t 6 -i "{{figure}}" -filter_complex "[0:v]fps=20,tpad=stop_mode=clone:stop_duration=1,setsar=1[a];[1:v]fps=20,scale=1500:880:force_original_aspect_ratio=decrease,pad=1500:880:(ow-iw)/2:(oh-ih)/2:color=0xfcfcfb,setsar=1[b];[a][b]concat=n=2:v=1,split[x][y];[x]palettegen[p];[y][p]paletteuse=dither=none" docs/img/workflow.gif
