# The recording of the README: the markers in the source, a capture, the
# report and the figure. Needs vhs and ffmpeg, a west workspace with
# this module, the ble_advertising sample built in ./build and flashed,
# and the PPK2 wired in Source meter mode. From the sample's folder:
#   vhs <module>/docs/workflow.tape
# then `just demo-figure` appends the figure that `west ppk2 plot` wrote.
Output workflow-terminal.gif
Set Shell zsh
Set FontSize 15
Set Width 1500
Set Height 700
Set TypingSpeed 30ms
Set Theme "GitHub Dark"

Hide
Type "PS1='$ ' && clear"
Enter
Show

Type "grep -n -e PPK2_TRACE_CLAIM -e PPK2_TRACE_SCOPE src/main.c"
Enter
Sleep 4s

Type "grep PPK2 prj.conf"
Enter
Sleep 4s

Type "west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 10"
Enter
Sleep 14s

Type "west ppk2 attribute trace.csv"
Enter
Sleep 9s

Type "west ppk2 plot trace.csv --window 5.3 5.8 --out ble.png"
Enter
Sleep 12s
