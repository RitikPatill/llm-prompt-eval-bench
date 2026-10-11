Output demo/demo.gif

Set Theme "Dracula"
Set FontSize 14
Set Width 1200
Set Height 600
Set Padding 20

# show the suite first so viewers understand the input
Type "cat examples/demo_suite.yaml"
Enter
Sleep 2s

# run the eval
Type "eval run examples/demo_suite.yaml"
Enter
Sleep 20s        # leave room for real API latency

# open the report path (don't open browser in headless)
Type "ls -1 .eval_reports/"
Enter
Sleep 1s
