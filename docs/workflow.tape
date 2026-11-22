# The recording of the README: the markers in the source, then list,
# flash, capture, report and figure. Needs vhs and ffmpeg, a west
# workspace with Zephyr and this module, samples/profiling built in
# ./build, and the PPK2 wired in Source meter mode. From the sample's
# folder:
#   vhs <module>/docs/workflow.tape
# then `just demo-figure` appends the figure that `west ppk2 plot` wrote.
# The hidden lines mask the serial number of the dev kit's debugger, as
# --mask-serial does for the PPK2's.
Output workflow-terminal.gif
Set Shell zsh
Set FontSize 15
Set Width 1500
Set Height 880
Set TypingSpeed 30ms
Set Theme "GitHub Dark"

Hide
Type `west() { if [[ "$*" == *flash* ]]; then command west "$@" 2>&1 | sed -E 's/board [0-9]+([0-9]{4})/board ********\1/'; else command west "$@"; fi }`
Enter
Type "PS1='$ ' && clear"
Enter
Show

Type "grep -n PPK2_TRACE src/*.c"
Enter
Sleep 5s

Type "west ppk2 list --mask-serial"
Enter
Sleep 4s

Type "west ppk2 run --source --vdd 3.3 -- west -q flash --no-rebuild"
Enter
Sleep 12s

Type "west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 10"
Enter
Sleep 14s

Type "west ppk2 attribute trace.csv"
Enter
Sleep 9s

Type "west ppk2 plot trace.csv --window 3.1 4.5 --out cycle.png"
Enter
Sleep 12s
