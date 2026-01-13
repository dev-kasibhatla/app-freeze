perfect, now write me an outline and checklist of a cli

i want the cli to be very simple and do the following


Main page
1. when phone is connected, show that it is connected, when disconnected show that
2. When multiple devices are connected, Show a selector to select a device. 

Device page
1. Show device information (model, android version, etc) in a small window
2. Show list of installed apps. User should be able to scroll using keyboard. Show status (enabled/disabled) of each app. And total size in MB.
3. User should be able to select or deselect apps using keyboard (spacebar to toggle selection)
4. when user presses enter, show a confirmation dialog with list of selected apps to disable/enable in 2 neat columns.
5. On confirmation, run the adb commands to disable/enable the selected apps and show status as commands execute. Dark green for success, red for failure.
6. Show a progress bar during the operation.
7. In the end hide progress bar and show a summary of the operation (number of apps disabled/enabled, number of failures)
8. q to return to device page
9. q again to return to main page
10. store report.md file with device-id=timestamp of the operation with details of apps disabled/enabled and their status.

General
1. ? to view keybindings and full help
2. Always show relevant keybindings at the bottom of the screen. (space, enter, q, ?)
3. Draw beautiful borders and use colors to enhance UX.
4. Separate sections with headers. And should be possible to navigate using keyboard (tab/shift+tab)
5. even better if mouse can be used for navigation and selection.