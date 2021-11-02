- [ ] Fix glitchy icon flashing
  - Seems that getting a given icon by name from the current theme is nondeterministic. Not sure of a solution.
- [x] Choose better fallback icon (media-record is not subtle enough (it's big and red) in Ubuntu's default theme)
- [ ] Hide disabled snaps from the installed snaps window.
- [x] Create basic man page.
- [ ] Use single log file instead of one per run.

### Remaining Integration Testing
 - Installed snaps are properly listed (and shown).
 - Refreshable snaps are properly listed (and selected?)
 - wasta-offline folder is properly found in all supported locations.
 - Choosing a folder properly highlights updatable snaps and properly populates the "Available" list.

 - Clicking "Settings" properly opens snap-settings.
 - Clicking "Remove..." properly opens snap-store.
 - Clicking "Update" attempts to install selected snaps sequentially.
 - Clicking "Install" attempts to install a snap's core, prereqs, and itself.
