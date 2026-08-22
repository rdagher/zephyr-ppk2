# zephyr-ppk2 — local recipes (multi-sample, multi-board).
#
# Toolchain: the nrfutil-managed NCS install at /opt/nordic/ncs
# (NCS_VERSION picks the version; NCS_WORKSPACE overrides the path).
# Host capture/attribution stays with ppk2-lib's CLI — see README.

NCS_VERSION   := env_var_or_default("NCS_VERSION", "v3.3.1")
NCS_WORKSPACE := env_var_or_default("NCS_WORKSPACE", "/opt/nordic/ncs/" + NCS_VERSION)
DK_SERIAL     := env_var_or_default("DK_SERIAL", "")

BOARD_54LM20 := "nrf54lm20dk/nrf54lm20b/cpuapp"
BOARD_52840  := "nrf52840dk/nrf52840"

SAMPLES := "profiling profiling_cpp wrap_profiling"
ROOT    := justfile_directory()

# Show available recipes.
_default:
    @just --list --unsorted

# Toolchain wrapper — runs args inside the NCS toolchain context with
# CWD set to the workspace so west finds its manifest.
_tc *args:
    @cd "{{NCS_WORKSPACE}}" && nrfutil sdk-manager toolchain launch --ncs-version {{NCS_VERSION}} -- {{args}}

# Build one sample for one board (default: profiling on the nRF54LM20DK).
build sample="profiling" board=BOARD_54LM20:
    @just _tc west build --board "{{board}}" --pristine=auto --build-dir "{{ROOT}}/samples/{{sample}}/build/$(echo '{{board}}' | cut -d/ -f1)" "{{ROOT}}/samples/{{sample}}" -- -DZEPHYR_EXTRA_MODULES="{{ROOT}}"

# Build every sample for both DKs.
build-all:
    @for s in {{SAMPLES}}; do just build $s "{{BOARD_54LM20}}"; just build $s "{{BOARD_52840}}"; done

# DK_SERIAL=… targets a specific dev kit (`nrfutil device list`);
# empty means the only attached DK. Power the rail first if the PPK2
# owns it: `ppk2 run --vdd 3.3 -- just flash`.
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
    @echo "boards        = {{BOARD_54LM20}} | {{BOARD_52840}}"
