# Idiograph manual

A local writing surface for Interpretative Phenomenological Analysis (IPA) and reflexive thematic
analysis, free, open source and flexible, on a Mac, Windows or Linux, your files staying on your computer. A project is one or the
other, chosen when it is made.

In an IPA project, Idiograph is step 3 of IPA and the steps after it, the route from transcript to
experiential statements to PETs to GETs, the detail reduced and its complexity kept, in three screens:
Experiential statements, where a participant is read one participant passage at a time, and each
passage gets its experiential statements with exploratory notes and quotes beside them, PETs, where
the participant's statements are grouped into personal experiential themes on a canvas, and GETs,
where every participant's PETs are grouped into group experiential themes. Experiential statements
writes straight into the same `EN & ES` workbook Excel opens, PETs keeps its boards in a file beside
it, GETs keeps its own at the project's root, and nothing else in the pipeline changes.

A thematic analysis project follows Braun and Clarke's reflexive thematic analysis, in three screens:
Coding, where a participant is read one passage at a time and each extract gets its codes, Code list,
every code with its extracts across the participants, where a code is renamed, described or merged, and
Themes, the thematic map of every participant's codes. It has no PETs, timepoints or trajectories, and
its extracts and their codes go into the same workbook, and the code list into a file at the project's
root. A codebook approach, such as template or framework analysis, or coding reliability with a second
coder, is a different method.

Sift, which screens a systematic review's records, and Trace, which holds each claim a manuscript makes
of a reference against the reference, are apps of their own on the same code, each with its own manual.
How to install and start it is in the [README](../README.md), and how it works underneath in
[docs/internals.md](internals.md).

**Three apps from one page (20 October).** Idiograph, Sift and Trace are apps of their own on one
codebase, and each shows only its own screens. Idiograph is the app for IPA and thematic analysis: its Home
holds your projects of both and the demo under Projects, an IPA project's screens Experiential statements,
PETs and GETs, and a thematic analysis project's Coding, Code list and Themes. Sift's Home holds
your Sift projects and Trace's your Trace projects, each under Projects in the same shape. Each Home opens
with its app's wordmark and one line, and ends with the other two apps, each with its icon, its name, one
line and Open when it is installed or Download when not, which opens its releases page. Run from its
folder, every app is there, and Open starts it. The analysis no longer carries a name of its own beside
the app's: Idiograph's own mark, the dot between brackets, stands on its bars, and
each app has its colour, Idiograph blue, Sift plum and Trace sea green, for its mark and its tab in
Settings. Each app keeps its own settings, Appearance among them, and Sift's and Trace's first start
copy what they share from Idiograph's, never its demo. Idiograph's Home says under its line "Free, open source, flexible, your files stay on
your computer."

**Participant, and Quote (20 October).** Every screen says participant where it said case: the
Participants panel on GETs, the participant list on a project's page, the participant picker, Back to
the participants, "Participant complete." on the card at the end of a transcript, and a This participant
search. A quote is what was a key quote, on the statements screen, on cards, in the Inspector, in
Search, on the status bar's Quotes on cards and in the prints. The command line and the MCP tools
keep their names, case, cases and key_quote, so nothing that reads them breaks. Since 22 October the
last three places say Quote too: the workbook's own column in a new participant's workbook, the
statements CSV's last column, and the lines a new AI board on GETs wrote until 11 November 2026. A workbook whose column says Key quotes, made before then, reads and saves as it always
did, and Idiograph leaves its heading as it is. Since 23 October an AI agent can rename that heading to
Quote at his word, one participant's workbook or every one in the project, through Idiograph's own
command line or MCP tool, with a dry run first. Only the heading changes, and a copy of the workbook as it
was goes into the participant's `_Archive` folder first. A board's History says "Before Rowan's changes came in" for the
revision kept as a participant's changes come into the GETs. The Offset card under the player says
"Your time codes are not changed." under its seconds (21 October). When Sift or Trace runs as itself, its own lines say its name, "Sift is closed." and Quit
Sift among them, and Help opens its own manual.

Every save writes the whole workbook back, and a cell the save does not change comes back as it
was: each run of its formatting, a highlight, bold, italic, an underline, a strike, a colour, a size
and a font, each space, a run or a cell of spaces alone among them, and each line break, the same in
the app as installed as in a run from source (17 October).

**Passages and rounds.** A passage is one person's stretch of talk, one row of the transcript, and the
interviewer's passages are context. The word is the IPA book's: Smith, Flowers and Larkin (2022,
*Interpretative Phenomenological Analysis: Theory, Method and Research*, 2nd edn) speak of a passage of
the participant's account in Chapter 5, at the exploratory notes, and use "turn in the conversation"
only in passing, in Chapter 4's advice on transcription, so the app says passage where it said "turn"
until 15 October. Rounds, ten minutes of transcript at a time with a daily target, a streak and the time
left, are a pace of his own and not a step of the method, so they are a setting, Work in rounds, off on
a new install (see Rounds).

Every Remove or Delete button with words, in Sift, Idiograph and Trace, a confirm card's among them, is
drawn alike: a red outline with a small bin before its word, so a button that takes something away
reads the same wherever it stands (12 October, later). The Remove on each pair of statement and key
quote was one of them from 14 to 18 October, when it became a bin alone at the pair's top right (see
Pairs). So are the entries of the canvas's menus that take something away,
Delete this label and Delete note, and the board menu's Delete this board, each its
red word and bin, outlined only under the pointer as a menu's entries are (16 October). Take out of PET,
Remove from PET until 20 October, moves a card and bins nothing, so it carries an arrow out of a frame in
the ink.

**Every tick from its whole row.** Every checkbox and radio in Idiograph ticks from anywhere on its
row, its words as well as its box, in Sift, Idiograph and Trace alike, with a pointer over the row and the
row shaded under it (13 October). A row that holds other controls too, a name box, Remove or a
handle, ticks from anywhere but on them. Every radio is the app's own, a ring with nothing in it until
it is chosen and then a dot in its middle, in light and dark alike, where in dark the browser's own
filled an unchosen one with grey so that it looked almost chosen (17 October, later). Every tick and
radio is in the ink, Sift's filters and its Export to Zotero card among them since 17 October, later,
where they stood in the crux orange, which is kept for a crux, a quote and the filled button. A card that keeps each change as you make it, Set columns
among them, ends with Done at its foot right, which closes it as the X at its top right does, and a
card with its own Save or confirm never has one.

**In a window of its own (17 October, not shipped yet).** Idiograph is becoming an app with a window of
its own and its icon in the Dock or the taskbar, in place of a browser tab. In the window, Print opens
the system's print panel, Save as PDF among it, and each print view opens in a window of its own that
prints the same way. Saving a file, the PRISMA map's SVG or PNG, opens the system's save panel with the
file's name already in it, and a file that cannot be written there says so. A link to another site
opens in the browser. Opening Idiograph
while it is open brings its window forward. New Window, Cmd or Ctrl+N, opens another window on what
the window in front shows, the same participant, board or project, so two can sit side by side, one
on each screen. Since 20 October Open in a new window opens a participant's statements, from
each participant in the participant switcher on PETs, the one on the screen too, or a board, from the board
menu under the board's name, in a window of its own, in the browser as well as the app, so a transcript can
stand on one screen and a board on another. Two windows keep each other up to date with nothing to press:
a passage's statements, notes or quotes saved in one show in the other a moment later, where it
stands, each statement that changed under a brief wash of the crux orange that fades, the place in the
column and the passage being worked on kept, and a change on a board, a statement reworded on it among
them, comes onto the same board in the other window by itself (see Changes made elsewhere). A field
holding words not yet saved waits for them to be saved first. One window stays the default, with no
floating panels. Closing the last window quits Idiograph, and Quit in Settings closes its
windows. Since 31 October, Quit and closing the last window finish Idiograph's work first and then end
it with its windows put away, and should the window ever close without Quit, as in a crash, the part
behind it closes by itself within about fifteen seconds, where it waited five minutes before.
Idiograph run from its folder, by `server.py`, keeps the browser tab as it was.

**The window's menus (17 October, later, not shipped yet).** On a Mac the menu bar is a Mac app's own.
Idiograph holds About Idiograph (see About Idiograph, under Settings), Settings… on Cmd+comma, Hide and
Quit. File holds New Window, Open Recent, Project History, Project Settings… and Close Window. Open Recent lists Home's projects, and
each opens in a new window where its card opens. Project History opens the History of the project that is open in the window, as Home's project menu does, and is grey on Home and in the demos. Project Settings… opens that project's Project settings and is grey on Home. Edit holds Undo,
Redo, Cut, Copy, Paste and Select All, and Undo and Redo take back a move on a board or the last words
in a field, whichever has the focus, then Find… (Cmd+F), which opens Search on any screen, and Find and Replace…
(Cmd+Shift+F), which opens Experiential statements' Find and replace card and is grey on every other screen (6 November
2026), then Spelling and Grammar, where Check Spelling While Typing is on,
so a misspelt word is underlined as in a browser. View holds Home, Cmd+Shift+H (Alt+Home on Windows), which
goes to Home from any screen, then Bigger Text, Smaller Text and Actual Size, Cmd with +, - and 0, which
zoom every window together and are kept for the next time, the same as Text size in Settings (see Text
size). A line at the foot of the window says the new size for a few seconds, as "Text size 110%". View also
holds Status Bar, which turns the status bar of the PETs and GETs boards on or off, Reload, and on a Mac Enter Full Screen. In a print view or the manual they zoom that window alone, and on a Mac Cmd+S in a print view opens its print
panel, where Save as PDF is. Window holds
the Mac's own items, the tab items among them, and Help holds the manual, What's New in Idiograph, the
notes of the version you have (see Updates, under Settings), Keyboard Shortcuts and Send Feedback. On
Windows each window carries a menu bar of File, Edit, View and Help with the same items and Windows's
keys, Ctrl+Y for Redo among them, Find and Find and Replace in Edit on Ctrl+F and Ctrl+Shift+F, Settings in
File, Exit at its foot and About and What's New in Help, and the windows stay separate windows. Linux has Windows's
menus, and there Edit's Undo, Redo, Cut, Copy, Paste and Select All show no keys, while Ctrl+Z, Ctrl+Y, Ctrl+X, Ctrl+C,
Ctrl+V and Ctrl+A work in a field and on a board as they always do. Every window opens whole on its screen, made smaller when the
screen is smaller than the window, and a new window opens a step down and right of the last, never with
its foot under the taskbar or the Dock. Each window is named for the app first and then for what is in it, as in
"Idiograph - Living with a dog - Juno - Experiential statements": the project, the participant where the screen is one
participant's, and the screen. Home is just Idiograph, a project's page is Idiograph and the project, and Sift's and
Trace's windows are the app and the project. So two participants in two windows tell apart in the Dock, the taskbar and
Alt+Tab. Choose beside a folder opens the
system's own folder dialog on either system. The window opens at the size and place it had when
Idiograph quit, and on the screen it was on when it opens again within ten minutes, after an update for
one, as a Restart does. Settings kept on the computer, the folds, the filters and Sift's step among them,
follow Idiograph whichever port it starts on. Closing a window saves what is typed first, and when that
cannot be saved asks before it closes. Printing keeps the date, the title and the page's address off
paper, and General's Closing tick, which speaks of tabs, is not shown in the window. Should Idiograph
stop without being asked, the window says so once, over the page, "Idiograph stopped unexpectedly. What
you saved is kept. Close this window and open Idiograph again." Should it not start at all, a small
notice says "Idiograph could not start. What you saved is kept. Open Idiograph again." A file dragged
onto the window from Explorer or the Finder lands as it does in a browser.

## Installing it

On a Mac, download `Idiograph.dmg` and open it. It is for Apple Silicon Macs (M1 or later). A Mac with an
Intel processor keeps the version it has, which goes on working, and gets no newer one. Its window shows Idiograph at the left and Applications
at the right with an arrow between them: drag Idiograph onto Applications and open it there. While
the build is not signed, macOS says the first time that it cannot check the app, and System Settings,
Privacy and Security, Open Anyway opens it, once. On Windows, download `Idiograph-Setup.exe` and run
it. Windows says the first time that it protected your PC, and More info, Run anyway runs it, once. It
installs for you alone, with no administrator's password and no restart, as its first page says, puts
Idiograph in the Start menu, and on its last page offers a shortcut on the desktop. A newer version
installs over the one you have the same way, and every project, participant and setting stays where it was,
through an uninstall too. Its last page's tick, Open Idiograph, opens it as Setup closes. Run Setup for
the version you already have and it offers to install it again or uninstall it, and run one older than
yours and it says "A newer version of Idiograph is installed. This Setup is older.", and asks what to
do. Should Windows lack Microsoft's WebView2, which Idiograph needs, Setup installs it first, and says
plainly if it could not download or install it, then to run Setup again. The uninstaller's one tick, Also
clear the window's size, zoom, appearance and folded sections, clears only what the window remembers,
and your participants, transcripts and projects stay either way. On Linux, download
`Idiograph-x86_64.AppImage`, make it executable and run it (Ubuntu 24.04 needs `libfuse2t64` for that),
or on Ubuntu, Debian or Mint install `Idiograph-amd64.deb`, which does not update itself. Each download is
the newest version, from Idiograph's page on GitHub, github.com/Pharkie/idiograph.
Once installed, Idiograph can update itself (see Updates, under Settings).

**From 0.9.0.** Idiograph 0.9.0 opened in your browser. On a Mac, quit it first from Settings, Quit
Idiograph, then drag the new Idiograph to Applications and choose Replace. On Windows, run the new
`Idiograph-Setup.exe`, which stops 0.9.0 and removes it before it puts the window in its place. Your
projects, participants and settings are there when it opens. On Windows, if you had added Idiograph to Claude
Desktop, choose Add Idiograph to Claude Desktop again in Project settings, since the program it
names has moved. On a Mac the entry 0.9.0 wrote still works.

## The loop

**Open a participant.** Idiograph's Home opens with its wordmark and the Preview Edition stamp, the
panel saying what the preview means right under them, then its line, "Software for Interpretative
Phenomenological Analysis", and under it four short items in a row, Free, Open
source, No cloud and Flexible. When the row wraps, Free and its Ko-fi button keep together, and so do Open source,
No cloud and Flexible, so no word is left alone on a line. Sift's and Trace's Homes carry four under their own
lines, Free, Open source, Flexible and No cloud (22 October). Beside Free stands a
small pale blue button, "Support me on Ko-fi", Ko-fi's own, its cup with a heart giving a little wiggle every few
seconds, which opens Adam's Ko-fi page in your browser. The cup stays still when your computer is set to
reduce motion. The button is kept in the app, so nothing comes from Ko-fi until you press it. On a phone Free and the button have a line of
their own. The head stands on the same grid as the projects under it (5 November): the lockup at the top left, with
room above it, at least the height of its mark (32 pixels for the Preview Edition's lockup, 24 for Sift's and Trace's) below the
top of the window's own title bar (6 November), and the page keeps a margin of 32 pixels at each side whatever the width of the window, level with Search, Send feedback and Settings at the top right, which show their words as they do on a project's screens and
give them up the same way when the window is narrow, the target squares under them, and the preview's panel as wide as
the column beside the squares allows, so it reads in four lines. Then
comes Projects, a card for each project, in the order the projects were added (see Projects). Its head folds
the section to the head alone and opens it again, the fold kept in this browser, so a reload keeps it. A card carries the project's name in the serif, its
research question under it, as Project settings has them, and in the small type where it stands: its
participants and how many have PETs, a board or PETs marked complete, "3 participants, 2 with PETs", and
under that its GETs, "GETs not started", the group themes on its Current board, "GETs: 4 group themes", or
"GETs complete" once marked. The demo's card has no GETs line. Each card's dots, at its top right, open
its menu (see A project card's menu). New project, Open project, its tooltip "Open a project folder
already on this computer", and Open a shared copy, its tooltip "Open a project someone has shared with
you, as a copy", stand under the cards (see Projects). Under Projects stands Demo projects, a section of its
own holding the two demos, apart from your projects: Living with a dog tagged "IPA demo", and Living with a dog
tagged "Thematic analysis demo", the same three invented participants coded in a thematic analysis project, so
the two methods can be compared on the same words. Demo projects starts folded to its head. Open it or fold it
and Home keeps it that way, as Projects keeps its fold. On a Home with no project of yours yet, and before you
have opened or folded it, it starts open, so the demos are there to find. Each demo's card opens its page, and
its menu holds Project settings, read-only. At the foot of Home stand the other two apps under
the heading "Sift and Trace", each with its icon, its name, one line, and Open when it is installed or
Download when not, which opens its releases page (see Three apps from one page, above). Settings, the cog
and its word, at the head of Home over the days, opens Settings on General. Sift's Home and Trace's
are the same shape, each with its own projects under Projects and the other two apps at its foot (see
Sift's manual and Trace's manual).

A card opens its project's page. At its head the way back to Home, a round arrow, with
the project's name and question beside it, then in the order of the work a row for each participant,
the full width of the column, the project's GETs across all participants in a wide card after them
(see GETs), where until 18 October the card stood over the rows, and Add transcripts under them. Back, the mouse's back button or Cmd + [ from a participant, from Experiential statements, PETs or
GETs, lands on its project's page, and a reload keeps the screen in front of him, Home, a
project's page or a participant on its passage. A run with `--root` opens straight on its one project's page.
A participant is a participant's folder under the project's root, and a workbook
sitting in the root itself is a row of its own, named by its stem. A row's title is the participant by
its P-number and pseudonym, "P8 Wren": a folder named `P<n> - Pseudonym-Secondname` shows by its
pseudonym alone, and the second name reaches the page only inside the paths the server needs to
find the file, which are never drawn.

Each row holds the participant, its tags and the three dots, then two halves side by side, each a button.
On a phone, under 560px, the halves stack under the name, and nothing scrolls sideways.
Experiential statements opens the participant
at the passage after the last one he was on, and says under it, in the small type, the passages decided of
the passages there, "64 of 207 passages", with "complete" after them once the phase is marked complete
(see Complete). PETs opens the participant's PETs and says under it the Current board's name (see The
Current board), "Mornings apart", then "PETs complete" once that phase is marked and "in GETs" once
the GETs file holds the participant, the first two read from the themes file. A participant with boards
and none of them Current says "No Current board" there, and one with no board at all "No PETs yet".
While Excel has the workbook open the row carries the tag "open in Excel" and the Statements half
is disabled, and PETs still opens, since that screen only reads the workbook. A participant with no
annotated workbook reads "Not started" and carries one button, Start experiential statements, which
opens the create card on its newest raw source, or with none the make a workbook card on its newest
transcript in another shape (both below).

A participant's workbook is its annotated one, and of two in its folder the one opened last, else the
newest. The three dots after its name open a small menu holding Edit participant profile, then Show files (see A participant's picture, label and
pen portrait, which is also where Rename lives), and Show files lists
under the row every file of the participant, the annotated workbooks, the raw sources and the
transcripts, each a row with its tag that does what it always did, and Hide files, as the item then reads, folds it away.
An annotated workbook's row opens the participant and carries PETs beside it, with its sheets and marks in
the small type, "Initial, 2d · Statements complete" once the statements are marked, "PETs complete"
once the PETs are, and "Participant complete" in their place once both are. The date sits in the tooltip,
"Experiential statements marked complete, 3 Oct 2026" or "PETs marked complete, 4 Oct 2026, on
Board 3", and both for Participant complete. Its Current board follows, "Current: Mornings apart", with
"The Current board, the one you are going with" in its tooltip. A raw source's row is
marked "create annotated workbook" and a transcript's "make a workbook", each in the soft ink on its
own border, where until 17 October, later, they stood in the crux orange.

**A participant's picture, label and pen portrait (11 November 2026, pbiobuild, layout A).** Each participant
of every project, IPA and thematic analysis alike, has a picture, a label of a few words and a pen portrait, a
short paragraph to remind him who they were, beside the number and pseudonym their folder gives them. The real
name is never kept here. A row shows the picture before the name, one of the app's 40 drawn portraits or his own
file, or with none the participant's initial in their colour, the label under the name, and the pen portrait's
first two lines across the row under them, the whole in its tooltip. A double-click on the name, the label or
the pen portrait, or Edit participant profile, first in the dots, opens the fields across the row: the picture with Change picture...,
Choose from the set and Remove, the participant greyed with Rename... after it (on a participant in a folder of
its own, never the demo's, and it opens the Rename card below), Label and Pen portrait, each kept as it is left, and
Done at the foot. Choose from the set opens the drawn portraits under the fields, four rows of ten. Since 12
November (peeps) they are forty heads and shoulders from Open Peeps, Pablo Stanley's drawings, in black and
white, with a range of ages, hair, headscarves and turbans, beards and glasses. A picture chosen from the 24
before shows as the nearest of the forty until another is chosen. His own picture is cut
square, made small and kept in the project folder's `pictures/`, the one it replaces moved to that folder's
`_Archive`, never deleted. A label is up to 60 characters and a pen portrait up to 800, its line breaks folded
into spaces. A label or pen portrait holding a name from the project's list of names to replace is refused in
one line, "The pen portrait holds a name from the project's list of names to replace, entry 3, so nothing was
changed.", nothing kept. The demo's three have theirs and are fixed. The participant picker on the statements
screen, and the switcher on PETs and LPETs, list everyone with their picture, label and two lines of the pen
portrait, and the bar over the statements screen, PETs, LPETs and a thematic analysis project's Coding shows the
picture before the name, said with its number as the rows say it, "P1 Wren", and the label after it, the label
giving way first in a narrow window. On GETs and
LGETs the Participants panel shows each participant's picture beside the name and the label under it, the pen
portrait in its tooltip. Trajectories shows the same picture and label, and its editor changes them for every
screen. Each change is a record in the project's History, and an agent sets them with `participant set`. Export as
REFI-QDA gives each participant's pen portrait as their case's description, and no picture goes into any export.

**The label and the pen portrait in the exports (11 November 2026, pbioexport).** Pen portrait, the last tick under
Export on PETs and on the print view, puts the participant's label, in italics, and their pen portrait under their
name at the head of the table of PETs, in the print view, the PDF and the Word document. Participants table, the last
tick on the GETs Export card, puts a first page before the GET table, the audit trail or all of it in one document:
a table of each participant in order, their number, pseudonym, label and pen portrait, as a write-up carries it, and
the part after it starts on the next page under its heading. In all of it in one document it follows the contents.
A thematic analysis project's theme table carries it too, in its PDF and its Word document. Both ticks are off on a
new install and kept as they are left. A participant with no label or pen portrait gets nothing under their name, and
a row with its cells empty in the table. The number is the one the folder gives, P2, or the participant's place in the
order where the folder has none. Participants table is not offered for the canvas, one GET's trail or a participant's
LPETs. No picture goes into any export, since a photograph of a real participant identifies them.

**Demographics (12 November 2026, demobuild).** Each project sets its own categories of what describes a
participant, in Project settings under Demographics, last in the sheet. A category is a List, one value each from
its values (Gender, Age range), or Free words, up to 12 each (Nationality, Occupation). Add category offers a
starting set, Gender (Female, Male, Non-binary), Age range (18 to 29, 30 to 39, 40 to 49, 50 to 59, 60 to 69, 70
and over, bands that never overlap), Nationality, First language and Occupation, each to take or leave, and New
category... for one of his own. Each value has a colour of its own from the participants' palette, so Female reads
the same colour on every row: a click on a value shows its colours, Rename..., Move to and Remove, and a list's
+ Add takes one more. A category's dots hold Rename..., List or Free words and Remove, its grip drags it to its
place (Alt and an arrow moves it one place), and a value drags along its category the same way. A value renamed is
renamed on everyone who has it. Removing a value or a category takes it off everyone who had it, after a card
saying who had what, the project file copied to `_Archive` first and the project's History keeping what went.
Move to puts a value, and everyone who has it, into another category, joining a value of the same words there. A
list turned to free words keeps every value, and free words turned to a list make the words in use its values.

A participant's values are set in their fields across their row (Edit participant profile), a line for each
category after the pen portrait: a list's values to click, the one chosen filled in its colour and the rest dashed,
a click on it again clearing it, and free words typed into Add, Enter or a comma ending each, the cross taking one
away. Everyone's values, Edit the table, opens a card of every participant's values at once, a row each and a
column each, for filling in a dozen participants together. The categories with Show as a pill ticked show their
values as pills on the project page's rows, on one line under the label, the last giving way to "+2" when the line
runs out, its tooltip naming them, and in the pickers after the label, under the name in the GETs' Participants
panel, and on Trajectories. The bars over a participant's screens name them in their tooltips.

Trajectories' own tags from before became each participant's values in a Tags category of free words the first
time the project page listed the project, each word keeping the colour Trajectories gave it, both files copied to
`_Archive` first. Trajectories shows the pills of the categories shown in place of its tags, and its editor's Tags
are the Tags category's. Sort them with Move to, Female into Gender and 40 to 49 into Age range.

On the GETs Export card, under Participants table, One row each puts a column for each category ticked after the
label, with the pen portrait on a line of its own under each row, and In sum keeps the table as it was and adds a
short table of each category's values counted, "Female (2), Male (1)", as a write-up reports a sample, a thematic
analysis project's first choice. A tick for each category says which go, those shown as pills ticked until he
changes one, and both are kept for the project. The PETs' Pen portrait puts the same categories' words on a line
under the label. Export as REFI-QDA carries each category as a variable and each participant's values on their
case, and bringing a REFI-QDA project in turns its variables into categories under the import card's Demographics
tick, a value on a case going to the participant the case becomes and a value on a document to the participant
whose interview it is. Demographics can identify someone in a small study: nothing leaves the project unless
ticked, In sum gives the counts without a row tying a pseudonym to an age, the starting set offers age bands and
never an age, and a value holding a name from the project's list of names to replace is refused.

**Rename (16 October).** A pseudonym given once sometimes changes, so Rename..., in a participant's fields (Edit participant profile in the dots) after the greyed
name, gives the participant a new one (a tester's ask, Adam's word). Its card
holds the name now, a field for the new name, one unticked row, Rename the folder too, and under them
the list of what will change, drawn before anything is written and drawn again as the name is typed
and the row ticked. The list stands under the words What will change, one plain thing that changes
on each line, and names no file the app keeps for itself (16 October, later, and 17 October after the
screenshot check, where a line led with the workbook and did not read): the participant's name on
the passages of each sheet it stands on, "Ada's name on 54 passages of the "Initial" sheet and 30 of
the "2d" sheet", each sheet named as the bar names it since 17 October, later, with the workbook it is in
after it only where two carry the name, "Ada's name on 54 passages of the "Initial" sheet, in the
transcript in Source", then "The participant's PETs boards", "The
project's GETs" when the GETs hold the participant, the project's own file, "The project's order of its
participants" when his order of the rows names the participant and "The project's note of the new name,
since the folder keeps its own name" while the folder keeps its name, and Idiograph's own list of
recent participants. Ticked, the list adds the folder and each workbook named after the participant, "The
folder P1 - Ada becomes P1 - Bea" and "The annotated workbook takes the new name and keeps its
progress and PETs boards", in words and never by a file's new name (17 October), and the project's note of the
new name leaves the list, since the folder then carries the name and the note is never written. Each
state lists exactly what its Rename writes. The line under it says "A copy of each file is kept
first.", as the app's backups go, the participant's `_Archive/` for its own files and the project's for the
GETs file and the project file, each named `(pre-rename <date-time>)`. Rename, filled, changes them
all, and Cancel and Esc change nothing. The card's kicker, Participant, stands in the soft ink, as
every card's kicker does since 17 October, later, where it stood in the crux orange, which design.md
keeps for a crux, a quote and the filled button, so Rename alone is orange and its refusal amber. Afterwards the renamed row stands in the middle of the
window, clear of the line at the foot that says the rename, "P1 Ada is now P1 Bea.", on a phone too.
Rename is refused in one line in the card, with nothing changed, when no name is typed, when it is
the name the participant has, when it is not one capitalised word, as New project's pseudonyms are, when it
is the interviewer's name in Settings or another participant's name in the project, when Excel has a
workbook of the participant open, "P1 Ada - EN & ES.xlsx is open in Excel. Close it in Excel first, then
try again.", when a folder or a file the move lands on is there already, and when a file cannot be
written, which puts back everything written before it. While a refusal shows, the list of what will
change goes with its words, since nothing will, and both come back as the name is typed again (17
October). The line "A copy of each file is kept first." goes and comes with them, since a refused rename keeps
no copy (17 October, later). Rename stays ready to press, as a dialog's button does, so after closing the
workbook in Excel a second press renames. The interviewer's passages and name are never
touched, nor are the backups in `_Archive/`, nor the transcripts in `Source/` as they were dropped.
Exports already written are left as they are. Afterwards the row, the PETs and GETs boards, the
bar of Experiential statements, the participant picker and Add transcripts show the new name with no restart, and a
trim's or an assignment's copy is found in the folder it moved to. With the folder kept, the
project's file keeps the new name by the folder's, `names`, which every screen reads, and the files
keep their names, as Files shows them. The demo's names are fixed, so its rows have no Rename, and a
workbook sitting in the root itself has none either.

Since 11 November (renamefix) Rename carries the participant through every file of the project that names
them. The list adds "The project's LGETs" when the LGETs hold the participant, "The Trajectories board" when
they are on it, and "The project's list of names to replace" when it has an entry for them or writes their
name, which then writes the new one. Everything they had on the LGETs and on Trajectories stays theirs: their
LPETs' cards and where each stands, their trajectory and their place in it, their label, tags, note and
picture, and the LPETs hidden there. Their PETs boards at every timepoint take the new name. Ticked, a
workbook that takes the new name keeps its LPETs and its PETs boards at every timepoint, and their own
picture on Trajectories, named after them, takes the new name too: "Their picture on the Trajectories board
takes the new name". Since 11 November (pbiobuild) their picture, label and pen portrait go with them,
"Their picture, label and pen portrait in the project", and ticked their own picture's file takes the new name,
"Their picture in the project's pictures folder takes the new name". The list of names to replace keeps no copy in `_Archive/`, since it holds real names
and the app copies it nowhere. Rename is refused too when a file it would change is there and cannot be
read, "idiograph-trajectories.json could not be read, so nothing was changed.", and when the folder would
move while Working together is on, since the team knows each participant by their folder.

The list finds the annotated workbook of each participant and its raw source, nothing else: a workbook
under a project's root with a Name, a Timestamp and a Transcript column. Columns are found by their
headers, so another study's CSV layout (`Speaker | Time | Experiential statements | Text |
Exploratory notes`) can be added later without touching the rest. Anything under `_Archive` or
`Working`, anything deeper than a participant's own `Source/`, and every backup copy wherever it sits stay
out. A backup is a workbook whose name ends in a bracketed note starting `pre-` or `complete`, such
as `(pre-trim)`, which covers the app's own copies and the coordinator's.

**His order.** The rows stand in the order he is working through them, the more settled at the top
and the ones still to begin further down, and he sets it by dragging a row by the handle at its
left, six small dots, the row taking its place among the others as it passes each one's middle. The
handle takes the focus as any button does, and Alt + Up and Alt + Down move its row one place, the
drag for the keyboard, the handle keeping the focus and a screen reader told the row's new place.
Either way the order is saved at once in the project's file as `order`, a list of the participants' labels,
every other key of the file kept. A participant the list does not name, a participant's folder new since, goes
after the ones it names, in participant order: P2 before P10, then a folder with no P-number by its name,
then a workbook sitting in the root itself. A label in `order` with no participant behind it is passed
over, and a project with no `order` shows participant order. The demo's rows have no handle, and their
order, Juno, Rowan, Mabel, is fixed.

The counts come from the workbook, read once, and the progress file beside it, the statements' mark
from the progress file and the PETs' from the themes file, and the server keeps each until its file
changes, so the screen lands at once. A file that cannot be read shows no mark. Home is
fetched afresh every time it shows, the back arrow included, and the back arrow saves a field typed
into and not saved on the way, as any move does. Showing it reads the themes file's head, where the
Current board's mark sits, and writes nothing. A page in front of a server that
has not been restarted draws one section of its root, a row for each participant from the old rows,
without the counts, and every participant still opens.

A raw source workbook with three columns, marked "create annotated workbook" under Files and taken
by Start on a participant not started, opens the create card: it builds
`P<n> <Pseudonym> - EN & ES.xlsx` in the participant's folder with the headers, widths and formatting of the
reference workbook, a finished case, which is the format the app writes and exports in, and it never writes
into a `Source/` folder. Its card names the source by its participant
and its file, or by the file alone where the file's name already holds the participant's, "Ivy -
interview.xlsx" where it read "Ivy · Ivy - interview.xlsx" (17 October, later), as the make a workbook card
does, and asks only for the new file's name. A workbook Excel has open is refused, with a
line saying to close it in Excel first.

A transcript in another shape is offered from the participant's own `Source/` with "make a workbook", under
Files and through Start on a participant with no raw source: a VTT
or SRT file, plain text, a Word file, or a CSV or Excel file whose columns go by other names. Its card, in the
create card's style, shows the first eight passages as the app reads them, the speaker, the timecode
and the words, and the speakers found, with the interviewer chosen from them, preset to the
interviewer in Settings when a speaker's name or its first word matches and otherwise to the
speaker with the most question marks, and always his to change. A Word table, a CSV or an Excel
file shows every column it has, each with a chooser at its head: Speaker, Time, Transcript,
Exploratory notes, Experiential statements, Quote or Leave out. Each is guessed from the column's heading,
or from what it holds when there is none, and a change reads the file again. A column headed Notes,
Comments, Thoughts, Memo, Reflections, Reflexive notes or Analyst notes is guessed as Exploratory notes. One column takes each
role and one must be Transcript. Two columns given the same role, the card says so in one line and
Make waits. The preview below then shows the first eight passages as they will land, a column for
each role chosen, in the order Speaker, Time, Transcript, Exploratory notes, Experiential statements,
the notes beside the words they are about, so a glance tells whether the columns were found right.
On a phone the preview scrolls sideways inside its own box. Under it the card counts the passages,
says how many come with notes, and names any column left out. New project's rows read a dropped file
the same way. Make writes the columns beside the file as `<file name>.xlsx`, or
`<file name> (converted).xlsx` for an Excel file, never over a file already there, with the
interviewer's passages under the name Settings gives him so they read as context, which the card says
under the choice when the names differ, and goes straight on to the create card above. The file is
not offered again once its workbook stands beside it. In a VTT or SRT file a speaker is named by a
`<v Name>` tag, as Teams writes it, or a leading `Name:`, as Zoom does, and the cues of one speaker
in a row make one passage at the first cue's time. A file that names nobody keeps each cue as a row
under Speaker. In plain text a line that opens with `Name:` starts a passage, the lines after it carry
it on, and a time at its head, `[00:01:23]`, `00:01:23` or `1:23`, is the passage's time. Without
times the player stays quiet, as it does for any workbook without them. A file is read as UTF-8,
with or without a byte order mark, or else as Windows-1252, and one the app can make nothing of
says so in one line and nothing is written. A `.docx` is read a paragraph a line, as plain text is,
unless it is a table of transcript and exploratory notes, as the IPA book lays one out. Then each row
is a passage, and the notes beside it come in as that passage's exploratory notes, a line of the cell
a note, just as if typed on the Experiential statements screen. Notes on the interviewer's passages go
to his Interviewer notes. A heading row finds the columns, Speaker, Time, Transcript, Notes,
Exploratory notes, Comments, Experiential statements and the like, in any order. With no heading the
column with the speakers' words is the transcript, a column of times the time, a column of a few
names the speaker, and the fullest of the rest the notes. A third column with no heading the card
can place is left out until he chooses a role for it. Words outside the table are left out, and the
card says so. A row that opens with `Name:` names its speaker, a row with none carries on the speaker
before it, and a time at a row's head is its time. A row is never split, and a row with notes but no
words adds them to the passage before it. A spreadsheet's notes and statements columns come in the
same way, by their headings or by his choice.

**Quotes from a column (9 November 2026).** A column headed Quote, Quotes or Key quotes is guessed as
Quote, and any column can be set to it. Its cell holds a quote a line, and each line goes with the
statement on the same line of that row's statements cell: the first quote with the first statement, the
second with the second. A cell with more quote lines than statements keeps the extra ones, and the
passage waits under Quotes to pair. A cell with fewer leaves the last statements with no quote. A quote
that is a run of words in the passage is marked there as any quote is. One that is not word for word is
still kept as its statement's quote, unmarked in the words, so nothing is lost. Under the preview the
card says how many passages come with quotes. Add transcripts and New project read an Excel file of two
sheets or more at its first sheet with anything in it, with a Sheet chooser on its row to read another.

**Work done elsewhere (20 October).** A researcher may bring an old project, or want only PETs and
GETs, with the transcript marked up to any degree. A statements column lands each statement on its
passage, several in a cell a line each, so the participant opens ready for PETs, with or without notes.
Under the preview the card lists every speaker with a chooser each, Interviewer, Participant or Other
speaker, the interviewer guessed as before and every other speaker a Participant, his to change. One
transcript is always one participant. Two participants, a couple interviewed together, are one participant with
one set of PETs, each passage under its speaker's name. Another speaker, someone heard off camera,
stays in the participant, a column headed Other speaker marking the turns: a step from passage to passage
passes them as it passes the interviewer's, and a click opens one for a note or a statement if he
wants. Two interviewers, or no participant, the card says so in one line and Make waits. Beside the
column choosers, Time codes shows the format the Time column's times were found in, "As found,
1:02:03", with a chooser to set it by hand, each format named by an example of it: 1:02:03, 02:03,
1:02:03.5, 62.5 seconds, and "1:02:03:12, frames" with Frames a second beside it, 25 unless he says.
Times are read with one or two figures for the hours or the minutes, in brackets or not, with a
fraction after a full stop or a comma as SRT and VTT write them, and seconds as a number. A format
set by hand reads only that format, 1:02:03 and 1:02:03.5 reading each other. The preview shows each
passage's time as it will land, a time never broken across two lines, and a time the format cannot
read stands struck through in it, with a line under the preview naming it, "The time 0:0x:12 on
passage 2 cannot be read as 1:02:03, so it comes in without a time." On a phone the preview's
columns stack, each passage's name and time over its words, its notes and statements under them,
each with its heading. Recording, at the
foot, offers the recordings beside the file and in the participant's Source folder, Choose for one elsewhere
on a Mac, and None. Make copies the one chosen into the participant's folder where the player finds the sheet's,
`Source/Transcript/Source/`, named by the participant's pseudonym and timepoint, `Wren T2.m4a`, or
`Wren.m4a` in a project of one timepoint, never by the file's own name, which may carry a real name
(9 November 2026). A REFI-QDA project's recordings are named the same way. With Offset in seconds, plus or minus, 0 unless he says, for a recording a little different from the one the times were taken on.
The time codes stay as they are, and playback moves by the offset, later for plus and earlier for minus.
The offset is kept beside the recording as `offset.json`, so it holds across a restart. Under the
player, the Offset button beside the recording's name, "Offset +1.5 s" or "Offset −1.5 s" once one
is set, opens a card to change it, Seconds, plus or minus, and Save. On a phone the recording's name
and the Offset button take a line of their own under the player's bar, the name whole where it fits
and cut at its end where it does not, the whole name under the pointer. The PETs screen's player and the GETs trail add it too.
`template/Transcript template.xlsx`, beside the app, is the three columns with three invented rows,
for a transcript typed or pasted in by hand.

**The days.** With Work in rounds ticked (see Rounds), in the head of Home, top right
beside the wordmark, stand eight weeks of small squares, under the wordmark on a narrow screen, a column a week with Monday at the top and the
newest week on the right, each day tinted by the rounds closed on it across every
participant of every project, in four steps of the accent at rising strength: none, one, two, and three or
more. Today is outlined in the ink, in the crux orange until 17 October, later, a day still to come
this week is left blank, and each square's
tooltip gives its figure, "Thu 1 Oct: 3 rounds". One line in the small type sits under them, "4
days running. Target met 9 of the last 14 days.", the days in a row the daily target was met and
how many of the last fourteen met it, today counted once its target is met, as the round card's
streak counts it. The line is left out while the eight weeks hold no round. The tally is the one the
target counts, kept in each participant's progress file, and `/api/days` sums it across every participant of
every project and writes nothing. A page in front of a server that has not been restarted gets no answer
from it and draws nothing there. With Work in rounds off, as on a new install, the head holds no squares
and no line, and the page asks the server nothing for them (15 October).

**The marks.** Idiograph's mark is an orange dot between two square brackets, the participant's
experience held where the researcher's hand enters a quotation, and the wordmark at the head of its
Home is that mark with the name beside it in the mark's square stroke. Sift and Trace each have a
mark of their own in the same square line and a wordmark drawn the same way, and each app a colour of
its own, Sift a plum, Idiograph a deep blue and Trace a sea green, the three of one weight, each about 7 to 1 against the page in both
appearances, and each told from the others with any of the three common kinds of colour blindness
(15 October, later). An app's mark stands on every title bar of the app between the arrow back and
the project's name, 7 pixels from the name at every width, the name after it cut short with an ellipsis
where the bar runs out of room, Experiential statements, PETs and GETs carrying Idiograph's, and in
Settings the category chosen takes its rule in the app's colour. In a title bar and in Settings the
mark is drawn again for its small size, 18 or 16 pixels, every line on a whole pixel, so it reads as
sharp as the words beside it. The three colours carry one weight, each within a tenth of 7 to 1
against the page in both appearances, where Trace's stood lighter in one and darker in the other
(15 October, later). An app's colour is only
ever its mark's and its Settings rule's, never a decision. The browser tab shows the mark on its paper tile,
dark when the system is, and the Mac and Windows icons are the same mark, drawn for 16 pixels at the
smallest sizes so it stays crisp.

**The bars since 26 October 2026.** Adam chose option C of the bars' drawings, and every screen's head now reads the
same way, in Idiograph, Sift and Trace. At the top left stands the app's lockup, its mark and its name, and a
click on it goes Home. The Preview Edition stamp stays on Home and in About. After the lockup come the stages as
tabs, Experiential statements, PETs and GETs, or with timepoints ES, PETs, LPETs, LGETs and Trajectories, every
tab drawn alike. At the right stand the screen's own tools, Export on PETs, View and Guidance on Experiential
statements, then a rule, then Search, Feedback and Settings, Settings at the far right. Each tool keeps its word
where the bar has room, and where it runs short the words go first and then Experiential statements becomes ES.
The back arrow has gone. Under the bar, the research question's band starts with where you are: the
project's name, and on a participant's stages the participant's chooser, and on a timepoint's PETs or statements the
timepoint's. The name opens the project's menu and the choosers open their menus as the one in the tab did. The chooser shows the participant's name alone, Wren
for P1 - Wren, on every stage, LPETs included. On PETs, LPETs, GETs and LGETs the toolbar under the band starts
with the left sidebar's button, Statements, Participants or Timepoints, then the board and Auto-saved, the
tools, and ends with Inspector, whether the tools are docked there or floating on the canvas. Canvas and
Table stand on the toolbar directly after Auto-saved (Adam, 26 October: it is not a status bar thing), there in the
Table view too, so the way back to the canvas is always in reach, and T still switches. The status bar holds the
counts and its tools alone. Where it runs short, as at 1280
with the sidebar open and every count ticked, the tools' words give way first, Fit all, Minimap, Quotes and
Shortcuts standing as icons with their words in their tooltips, so the counts always say the whole sentence there,
"18 ES: 17 in PETs, 0 stacked, 0 set aside, 1 not placed | 3 PETs" on the demo's Mabel (Adam, 26 October).
Since the same day (Adam's option B) Align and Spread stand under the toolbar's three dots, after Auto-arrange:
the dots open a menu of two sections, Align with Left, Centre and Right, Top, Middle and Bottom, and Spread with
Across and Down, each with its icon and its word, doing to the selection what its button did and faint as the
buttons were, with nothing or one card selected, and Spread's two until three. So at 1280 Sticky note, Group,
Auto-arrange, Undo and Redo keep their words. Where the toolbar runs short Select all loses its word first, then
every tool shows its icon alone with its word in its tooltip. On Experiential
statements the sheet moved to the status bar before the place, and the round, the clock and Mark complete
after the counts. Trajectories' bar gained Search and Feedback. Sift's steps are tabs on its bar, with the
screening's or the review's name in the path and the review's question after it. Trace's one bar holds the
lockup, which is Home, the project's name and its tools. Keyboard shortcuts are unchanged. Since the same day the
app's window is never narrower than 720 pixels (Adam, 26 October 2026: 360 is dropped). At 720 Idiograph's bar
keeps its one row, the tabs in their short names beside the lockup, the tools as icons, and the toolbar stands
on two lines, the sidebars' buttons, the board, Auto-saved and Canvas and Table over the tools.
Sift's bar, whose steps have long names, takes two rows at 760 and below, the steps on a row of their own.

**The band since 6 November 2026.** Adam chose option D, after a tester found the lockup and the path's Home doing
the same thing. On every project screen the lockup at the bar's left is the way Home, and the band under the bar
has no Home. It reads, on one row: the project's name with a small chevron, then the participant's chooser, with
the timepoint's chooser after it in a project of timepoints, then the rule, Research question and the question. On
the screens that are not one participant's, GETs, LGETs, Trajectories and the Code list, it reads the project's name
and its chevron, then the question. The project's name looks and works as the participant's chooser does: a press
opens a menu under it, the arrow keys move through it, and Esc shuts it. It is no longer a way to the project's
page, since everything that page does can be done from inside the project. A long name stops at 22em with an
ellipsis, the chevron still there and the whole name in its tooltip. Its menu is the one the project's card has
on Home, the same items in the same words: Share a copy…, Export as REFI-QDA…, Show in Finder (Show in Explorer on Windows, Show in Files on
Linux, and in Idiograph's own window alone), Project settings, Project history and Remove from Idiograph…. A demo's has Project
settings alone, as its card does. Remove from Idiograph asks first, in the same card as on Home, then leaves the
screen as Home does, saving what is typed, takes the project off Idiograph's list, its folder and files left as
they are unless the card's tick moved the folder to the Bin, and ends on Home without it.

**Sift's and Trace's project menus.** A Sift or Trace project's card on Home has a "…" at its top right, as an
Idiograph card has, and in its band, or on Trace's bar, its name has the same chevron and opens the same menu
(6 November 2026). It holds what applies to these apps: Show in Finder (Show in Explorer on Windows, Show in Files on Linux, in
the app's own window alone), Project settings, which opens Settings on Projects with this project in front, where its name,
question and the rest are kept, and Remove from Sift… or Remove from Trace…, which asks first and, from inside,
leaves the screen and ends on Home. A project whose folder has gone has Remove alone. Sift and Trace keep no
History of a project and make no shared copy, so neither is there. The name no longer goes from a record back to
the table, which Esc and Back still do.

**The tabs keep their place.** The tab in front is in bold, and every tab is always as wide as its name in bold, so
switching stage moves none of them (6 November 2026). The boards', Trajectories' and the code list's bars start
their tabs where the statements screen's does. Sift's steps do the same.

**Auto-saved under the board's name.** On PETs, LPETs, GETs and LGETs the save state stands under the board's name
in smaller words, so the pair takes no more width than the name and Canvas and Table stand closer (6 November 2026).

**The statements screen's toolbar.** Under the band of Experiential statements runs a toolbar in line with the
boards' (6 November 2026): its grip at the left, then Find and replace, which opens the Find and replace card as
`Cmd + Shift + F` does, Previous passage and Next passage, as `Cmd + J` and `Cmd + K`, and at its right end Undo and
Redo, the screen's own, as `Cmd + Z` and `Shift + Cmd + Z`, a field's own undo while its typing is the newer.
Each is an icon and its word, the words giving way where the row runs short, the key in its tooltip. Dragged by
its grip it floats over the columns as the boards' toolbar floats over the canvas, a column on the card's paper,
the row under the band gone, and dragged back under the band it docks again, a dashed slot showing where. Where it
stands is kept on this computer. The small Replace in the transcript link in Search's card stays.

**One title bar.** Every bar in the app works the same way (12 October), its parts in one order on
every screen (16 October, after a tester found Appearance on some screens and not others). Each tool
on it is its icon and its word: View, Guidance, Search, Shortcuts, Feedback and Settings on Experiential
statements, Participants at the left end of the bar on GETs, then Sticky note, Group, Undo, Export on PETs alone,
Search, Shortcuts, Feedback and Settings, and Inspector at the right end on PETs and GETs, Export, Second
screener, PDF, Search, Shortcuts, Feedback and Settings in Sift, PRISMA flow on the line under it since 12
October, Search, Feedback and Settings on Search strategy, Search, Shortcuts, Feedback and Settings in Trace, and
Search, Feedback and Settings at the head of Home. Each tool shows its word where the bar has the
room, from 761 pixels of window, and where the bar runs short the icons stand alone, each named on hover (since 26 October, where
the words showed from 1280 pixels).
From the keyboard every tool on a bar, its tabs and its switchers take the app's one focus ring, the
orange wash every button takes, and so does every tick and every field of one line, where a tool given the
focus back from its menu, View after Esc among them, and a tick drew the browser's own blue ring and a field
such as Rename's New name showed none (17 October, later). A card's close in its corner takes the
same ring, where the guidance's close drew the blue (18 October). Since 8 November every card, Settings and
Shortcuts among them, keeps the keyboard inside it while it is open: opened from the keyboard its first field
takes the focus, or Done, `Tab` and `Shift + Tab` go round inside it, and when it closes the focus goes back to
what opened it. Since 12 November a click outside a card closes it as `Esc` does, but a card with words you have typed
and not yet saved, or one still at work, stays open. A screen reader hears each card as a dialog named by its title. View, Export, the boards and the
participants on PETs, and a participant's menu on a project's page, take the arrows: opened from the keyboard
the first item has the focus, `Up` and `Down` move, `Home` and `End` go to the first and the last, `Enter`
chooses and `Esc` closes back to the button. `Tab` leaves a participant's handle on a project's page, where it
stayed put, and `Alt` and an arrow still move the row. On Coding, `Tab` from the notes goes on to each
extract's Add a code. The line at the foot and the statements screen's Saved are said by a screen reader (on
Linux the app's window says the line at the foot to Orca itself), and
each screen has a heading for one. On Linux, Orca 46 keeps its one-letter navigation keys while you write in a
field, so it takes most letters as its own: press `Orca + Z` to turn those keys off while you write and again to turn
them back on. A Tab to the statement's quote or to Columns with Orca on no longer stops the window (9 November 2026). The app's own words use
straight quotation marks and apostrophes throughout, "Initial" sheet among them, a participant's words and
the printed quotes keeping their own (17 October, later). The
lockup stands at the left of every bar and goes Home (since 26 October, in place of the way back's arrow), and Idiograph's tabs on its bar name every screen of Idiograph (see Idiograph's
tabs). The
tools keep one order on every bar: the screen's own first, what it alone does, then what
writes or sends, then the rest, and last the tools every bar ends with, Search where the screen has
one, Shortcuts where it has keys, Feedback and Settings. Search took Find's place on 17 October, and
came to Sift's, Search strategy's and Trace's bars and Home on 18 October (see Search). A sidebar's button stands at its own side,
over the sidebar it opens: Participants at the left end of the GETs bar and Inspector at the right end of
the PETs and GETs bars, each the standard panel icon with its own side filled. Every button with a
key names it in its tooltip, "Group (G)", "Search (Cmd + F)", with Ctrl in place of
Cmd on Windows and Linux, and the shortcuts card stays. Since 17 October every key on the statements
screen is named the same way, in its hints, the quote's empty field, its lines at the foot and its
shortcuts card, Cmd on a Mac and Ctrl elsewhere, Option or Alt, and Home and End for a line's ends
off a Mac, so "Ctrl + Enter saves" never stands beside "Hold Cmd" and the card names one key where it
said "Cmd / Ctrl". Sift's shortcuts card and Trace's name their keys the same way since 17 October, later.
Every key on a button stands in the faint ink and a key beside a decision's word in the word's own colour,
where until then each stood at a little over half its button's word and
read under 4.5 to 1 (17 October, later). The time on Back to where I was stands in the faint ink with them since the same
day, where it stood in the crux orange, which means a crux, a quote and the filled button alone. The `?` of Shortcuts stands in the icons' 15 pixel box at the weight of their lines
on every bar (17 October), where at the bar's own small size its thin strokes read fainter than the
icons beside it. Appearance, the light, dark or system choice,
left every bar for Settings, General the same day (see Light, dark or the system). To make room for the
words on Experiential statements, the line to today's target leaves its bar below 1440 pixels, and
below 1280 pixels its first tab, Experiential statements, reads ES (see Idiograph's tabs). At 1280 pixels a name of 30 letters stays whole
on every bar, except where a bar holds its most: Experiential statements marked complete with passages
still undecided, and Sift with Second screener on, where the name ends in an ellipsis and shows whole
on hover.

**Keys in capitals (17 October, later).** Every letter key stands in its capital, as keyboards and the
Mac's and Windows' menus print it, on every shortcuts card, in every tooltip, "Group (G)", and in every
line, "Select the words inside the passage first, then press Q.", where until then Experiential statements
and PETs wrote theirs in lowercase beside Sift's and Trace's capitals. The key is pressed as before,
without Shift. Since 18 October Experiential statements takes its letter keys with Caps Lock on too, as
PETs, Sift and Trace always did, where until then `Q` and the rest did nothing with it on.

**Idiograph's tabs.** Each of Idiograph's three bars carries a fixed tab per stage, after Idiograph's mark
and the project's name: Experiential statements, PETs and GETs, in the book's order, steps 2 to 5 for one
participant, Step 6 for each participant in turn and Step 7 across the participants (Smith, Flowers and
Larkin, 2022, ch. 5). With two or more timepoints the bar is drawn for five, Experiential statements, PETs,
LPETs, LGETs and Trajectories, and a tab shows only once its screen exists. Since 21 October all five
do, LGETs standing where GETs would, and with five below 1600 pixels the first reads ES and the tools
show their icons alone, so each bar stays on one row at 1280. A tab is never closed or doubled: File, New Window gives two side by side. The
tab in front stands in the page's paper on the bar's lower edge and holds the participant picker, the
participant's name and a small chevron, which lists the project's participants, the one in front ticked,
each opening on their statements, with Open in a new window beside each. On PETs the picker lists them with
Open beside this one and Open as table, and GETs, the project's, holds none. The timepoint, where a project
has two or more, stands just after the tabs.

A tab opens its screen for this participant, the passage in front saved first on Experiential statements
and the canvas saved first on PETs and GETs. On a project's GETs opened from its page, Experiential
statements and PETs open the participant you opened last in that project, named in their tooltips, "PETs
for Mabel", and the first participant until you have opened one. On LGETs they open that participant at the
timepoint whose PETs you opened last. On GETs opened from a participant's PETs they stay with that
participant. Where
the way back goes to the same screen the tab is the way back, so Experiential statements reached from PETs
comes back on the passage he left, and PETs reached from a statement's card comes back on the board as he
left it. Otherwise the screen opens afresh and its way back returns to the one he left. There is no arrow on the bars
since 26 October: the lockup goes Home, and Back returns to where the screen was opened from. `P` on Experiential statements opens PETs.

The tabs read at 15 pixels, and below 1280 pixels Experiential statements reads ES, its whole name in its
tooltip. So the tabs fit 1280, the tools show their icons alone below 1440 pixels, their words in their
tooltips. At 760 pixels and below the bar stands on three rows: the lockup and the tools, then the tabs on a row of their own, scrolling sideways under a fade when five stand there,
then the sheet or the timepoint and the place, or the board. The keyboard reaches every tab with Tab, Left
and Right move along them, and Home and End go to the first and last. Until 20 October the stages were
small steps of words after the participant's name, and a tester had found the way from statements to PETs
to GETs too hard to see before those came on 18 October.

**Rounds.** Rounds are a pace of his own, not a step of IPA, so they are a setting, Work in rounds
under Experiential statements in Settings, off on a new install, and a settings file without
it reads off (15 October, `work_in_rounds` in `config.json`). With it off nothing about rounds shows
anywhere: no round count or its short bar in the top bar, no round clock, no round markers across the
transcript, no line to today's target or streak, no round card in mid-sheet and no confetti for a
round, and no days on Home. The card still comes at a sheet's end and at the participant's end,
without round figures, target or streak (see Round complete), and the quiet control that marks the
phase complete still comes once every passage is decided (see Complete). The rounds are still cut and
each still closes with the server as its last passage is decided, quietly, so the daily tally is true
on the day he ticks it. With it ticked, everything below holds as it did. Each sheet is cut into
rounds of transcript time, default 10 minutes, at passage boundaries so no passage is split. A round never spans two sheets, so the last round of a sheet can be
short. Rounds belong to their sheet: each sheet has its own set, numbered from 1, and the end of a
sheet is a natural place for a break, even in a participant with several. Every round number on screen is
the sheet's. Underneath, each round keeps a number unique across the participant, sheet by sheet, which is
what the progress file, the daily tally and `/api/round-complete` are keyed by, so a progress file
written before this reads without change. The demo's Initial sheet, 22 transcript-minutes and 39
participant passages, comes out as 3 rounds.

**Round markers.** With Work in rounds ticked, a thin rule runs across the transcript column before
the first row of every round on the sheet, round 1 at the top of the column, so the sheet shows where one round ends and
the next begins: above the line is round 3, below it round 4. At its left, in the margin's small
capitals, a label names the round by its number on the sheet, "Round 4", with its state under the
name where a passage carries its timecode. A round closed reads done, with the small tick, its rule in
the faint rule colour. The round holding the passage in front of him reads now, its words and its rule
in the ink of the current passage's rule, orange until 17 October. A round not reached yet reads to do, faint,
in the faint ink at full strength since 17 October, later, as the interviewer's name in the margin is, told
apart by its lighter weight, where a fading took both under 4.5 to 1. A round closed
that still holds the current passage reads done. The states follow every move and every round close
in place, so the column is never redrawn for them and the sheet does not jump. A click on a marker
goes to the round's first undecided participant passage, or to its first participant passage when every
passage in it is decided, the way a click on a speaker's name goes to a passage, and its tooltip says
which: "Round 4, 12 passages, 30:02 to 39:55. Go to its first open passage.", the passages counted being
participant passages and the times those of the round's first and last rows. A marker is never a
passage: the keys never land on it, it is never the current passage and it is never counted. Below 1000px, where the margin lies
along the top of each passage, the name, the state and the rule sit on one line. A sheet with one
round shows one marker, and a page in front of a server that sends no rounds shows none.

**The count.** On every step on that decides a passage, Next after a save, a save with nothing in it,
Skip, and a blank passage passed with `Cmd + K`, the arrow or a click further on, the new place in the
round flashes over the middle of the transcript column, "8 / 20" in the numeral face and the ink, where
it stood in the crux orange until 17 October, later, the numbers alone with no box around them: they grow out of a blur as they fade in, keep growing a little, and
grow on into a blur as they fade out, 850ms in all. With Work in rounds off the place is the
passage's on its sheet, as the top bar has it, "8 / 120", Halfway at the sheet's midpoint and Last
one on its last passage, and only the move that ends a sheet or the participant raises none. At the round's midpoint passage, the first place at
or past half its participant passages, it reads Halfway, and on its last passage Last one. In the same
instant the place in the top bar, "passage 8 of 20 in this round", brightens on its numeral, from the
faint ink up to the ink, where until 17 October, later, it ticked in the crux orange, so the eye
learns where the number lives. It counts the passages of the round, never statements. A
click back, `Cmd + J`, a marker's click, the sheet switcher and undo raise nothing, and neither does
the move that closes a round, because the round card and the confetti have that moment. A new
flash replaces one still showing. It never sits over the fields and never takes the pointer or the
focus, and under reduced motion nothing shows at all.

**Experiential statements (the statements screen).** The top bar names the part after the participant name,
Experiential statements in the place where the bar in PETs says PETs, then a thin rule and the sheet.
The speaker of the passage in front of him and its place (15 October) stand at the left of the status bar
under the player since 21 October, where until then they stood in the top bar after the sheet (see The
status bar on the statements screen). With Work in rounds off
the place is the passage's among the sheet's participant passages, "Juno, passage 8 of 120", and in a
participant of more than one sheet its tooltip carries the participant figure, "Juno, passage 8 of 120 on this
sheet, 128 of 300 in the participant". With it ticked it is the place in the round, "Juno, passage 8 of 20 in
this round", with the round's short bar, "round 2 of 4", the round clock and the line to today's target. Since
17 October the screen is the book's three columns (see The three columns), experiential statements,
the transcript and exploratory notes side by side under their headings, each of her passages a row
across the three, with the speaker and the timecode hanging in the left margin of every passage's
words and the player at the foot of the three. The passage being worked on carries its statements as a
card in its row of the statements column and its notes as the notes field in its row of the notes
column, where until then the fields stood in a panel at the right for that passage alone. The
guidance slides in over the right of the screen from Guidance on the bar (see Experiential statement
guidance), where until 16 October it stood in a column of its own. The passage being worked on
sits large and at full contrast, the rest of the sheet sits smaller and dimmed around it, unless the
view draws every passage at one size, and
every passage carries its quotes marked in its words and, once decided, its bar at the edge of
its words (see Quotes in the passage and Done marks). The three columns keep the whole height of
the screen and scroll as one, the card and its row growing with the statements written. Every move
re-centres them on the current passage, never so far that its speaker and time go out of sight: a
passage taller than the column stands with its name and time just under the column's faded head,
below the title bar and the research question at every width, their height measured as they stand,
where at 360 the notes' field under the words had taken the name and time up under the question (17
October). Scrolling them by hand moves nothing else and leaves the cursor where it was. Adam's own
passages are context and never a stop. Scroll the passage out of sight and a "Back to where I was" button appears
with its timecode on it, in a strip of its own at the foot of the columns, which gives up that strip
while the button shows, so it never covers a line at any width (16 October), which `Esc` does too from anywhere on the page,
leaving whatever is in the fields alone. The wheel takes the columns as far from the passage as you like, either way,
and over a long passage's card it scrolls the card and then the columns. A click on a passage, `Cmd + J` and `Cmd + K` move at any
time and any passage can be revisited.

**The status bar on the statements screen (21 October, Adam's drawings).** Along the window's foot, under
the player, runs a status bar, as the PETs and GETs boards have one, and the player keeps its size above
it. At its left stands the place, "Juno, passage 7 of 39" (with Work in rounds ticked, the place in the
round), and then the participant's statements counted, "41 statements", the passage being worked on
counted as its fields hold it. Since 30 October the count holds still as you move from passage to passage, where it
went up or down by the statements of the passage left and the one opened, and it changes only when a statement is
added, removed or emptied, a statement counted as you type it, before it is saved. It counts every statement in the
workbook, one on an interviewer's turn too, as the PETs board's status bar and the agents' `statements` count them.
At its right stand Minimap, Quotes and Shortcuts, each an icon and its word.
Minimap shows or hides the map as `M` does, pressed in while the map shows, and goes with the map set to
Off in View. Quotes is pressed in on a new install, each statement's quote shown whole. Pressed out, every
quote's words are hidden, with no first line and no arrow, only its Quote label and chevron left, so the
statements stand clear on their own (Adam, 21 October: until then Quotes off folded each quote to its first
line). Each quote also folds and opens on its own, whatever Quotes says (21 October, for long quotes set
several to a statement): a set quote's Quote label carries a small chevron, down while the quote shows
whole and right while it is folded or hidden, and a press on the label folds or opens that quote alone.
Folded alone, with Quotes on, a quote keeps its first line, ending in an ellipsis, and a press on that
line opens it. Opened alone, with Quotes off, it shows whole. A quote of several pieces folds to one line
holding them all. A press on Quotes puts every quote back to what it says. An empty quote is never folded
or hidden, so its line and its arrow stay in reach. Quotes is kept in the settings, so a
reload or a restart keeps it. Shortcuts opens the shortcuts as `?` does. The place and Shortcuts stood in
the top bar until 21 October. On a phone, 360px wide, the place drops the speaker's name, "passage 7 of 39",
the count and the recording's name beside the player go, and Minimap, Quotes and Shortcuts keep their icons
alone, each named in its tooltip.

**The three columns (17 October).** Smith, Flowers and Larkin (2022, *Interpretative Phenomenological
Analysis: Theory, Method and Research*, 2nd edn, Box 5.4, Step 3) lay the transcript out in three
columns, experiential statements, the transcript and exploratory notes, the notes typed "into a column
that runs alongside the transcript" (Chapter 5, step 2), and a tester asked for the notes beside the
transcript, so the statements screen stands in those three columns, Adam's decision of 17 October,
where until then the statements stood in a panel at the right for the passage in front of him alone,
and the passages not in front of him showed none. Each column has its heading over it, a grip before
its name, and the order is his: the book's, statements, transcript, notes, on a new install, and any of
the six by dragging a heading's grip to another place, a bar in the ink marking where it goes, or by `Alt`
and the left or right arrow with a grip in focus, and Back to the book's order, in the menu of Columns at
the right of the headings, puts the book's back. Until 18 October that menu listed the six orders, the
book's first, and Settings did too (see Show, hide or stack the columns). Columns says its word alone at
every width, the columns shown in its tooltip, where until 18 October it said the order beside its word
only where the last heading left it the room, which happened at 800px alone, and where a heading's longest
word would not stand whole beside the word, as at 801px, it keeps its chevron alone. Its menu opens under
it at the right, and where it would leave a strip of the last column showing beside it, a sliver of the
notes field among it, it takes that column's whole width. The order is kept in `config.json` as
`statements_columns`. A settings file from before, which kept the
notes right or left of the transcript or under the statements, reads the order nearest the screen it
drew, transcript, notes, statements for right, notes, transcript, statements for left, and transcript,
statements, notes for under, and the old key leaves the file on the next save. In every order the
margin with the speaker, the timecode and the done bar stands at the left of each passage's words, in
the transcript's column wherever that column stands.

Each of her passages shows its statements read-only in the statements column beside its words, each
numbered as in the card, in the reading face, and a click on one goes to that passage with the caret
in that statement, the way a click on its quote's mark goes, so the statements and the quotes
marked in the words keep the same numbers. A statement still to write shows its quote in the faint
ink, so every number keeps its place. The passage being worked on has its statements editable in its own
cell, a card a size larger, each pair numbered beside its statement field, its word count and nudges
under it, then its Quote label with Remove at its right, then its quote field (see Pairs), and
at its foot Add another, AI suggest while the AI features are on, and the one filled button (see The
buttons). The card is made for one statement as a rule, sometimes two and rarely three, with room for
six or seven, and it and its row grow with them, never a box that scrolls on its own. While a card of
several pairs runs past the column's foot, its foot keeps to the column's foot, so Next stays in reach
as he writes, and the row takes no wash while the pointer is in the card. The foot then ends the card
there, with a hairline and the paper under it, so nothing of the card shows below Next, and the fields
above it fade into it, so none is cut through its letters at its edge (18 October). A field grows with
its words, and an empty one with its prompt, so a prompt of two lines reads whole. The notes stand in
their column beside each passage, the current passage's the notes field itself. It starts about five
lines tall and grows with its words as the card does, never a box that scrolls on its own, so a note
longer than the passage beside it takes the room it needs and the row grows with it, where until 18
October it started at two lines and a long note felt cramped. It saves as it always has, with Next, `Cmd + Enter` or any move, `Tab` reaching it after the last quote, and the
other passages' read-only in the faint ink with the field's own padding, so their words sit where the
field's would, a click on them going to that passage with the caret in its notes. The interviewer's
passages carry neither statements nor notes, and an interviewer note on one stands in the notes column
beside it (see Interviewer notes).

The three stand side by side down to 801px wide, each column narrowing to its own least width, the
statements 210 pixels, the transcript 300 and the notes 160: at 1280 the statements and the notes about
320 pixels each and the transcript about 530, its words about 420, and at 801 the statements at their
210 and the transcript and the notes sharing the rest. From 800px down to a phone's width the notes go
under each passage's words in the transcript's column, behind a hairline so a faint note never reads as
the speaker's words, and their heading goes with their column, while the statements keep a column of
their own. At 600px and below, a phone or a narrow window at Text size Large, each passage stacks,
its name and time, its words, then its statements and its notes in the columns' order, and the
headings go. The minimap keeps its corner,
and the guidance's sheet slides over the columns as before.

**The column edges (20 October).** On a wide screen the three columns stopped growing at about 1,480
pixels and left the rest of the window empty either side (a tester's letterbox at 2560), so every column edge
can be dragged, Adam's choice from a drawing: the outer edge of the first column and of the last, and the
edges between them. Since 6 November the two edges between columns show at rest, a faint rule down the
columns with a small handle on it, a pill of two upright bars at the middle of the columns' height, which
stays in view as the passages scroll under it, after Adam found the edge between Transcript and Exploratory
notes invisible, with nothing to say it could be dragged but a slow hover (option C of three drawn for him).
Each is 12 pixels wide to take the pointer. The two outer edges, the margins, show nothing at rest and are 8
pixels wide. Over any edge the pointer turns to the resize cursor, the rule darkens and thickens, and over
the two between columns the handle fills in the soft ink with its bars in the paper, so the handle itself
says it is under the pointer. A drag moves that edge alone, the columns either side taking up the
room and the transcript the rest, and with the widths dragged the transcript's words run the width of their
column. `Tab` reaches each edge and the left and right arrows move it, a little at a time, more with
`Shift`. A double click on an edge puts that edge alone back where the screen opens. The widths are kept
for each size of screen, so a laptop and a wide screen each keep their own, and a window narrower than the
widths were dragged on gives up its margins first, then the side columns, the transcript keeping its 300
pixels. Reset widths, at the foot of Columns' menu under Widths and in Settings (see View), puts every edge
back for this screen, and since 21 October every column back alone (see Stack by dragging a heading), and
is faint while they all stand where the screen opens and nothing is stacked. A screen never dragged
opens as it always has, with the columns sharing the width as the statements 2, the transcript 3 and the notes 1,
whatever their order (6 November, from the widths Adam kept himself, about a third, a half and a sixth, where
it opened 3, 5 and 3), each held to its least width, so under about 1,090 pixels the notes stand at their least,
160 pixels, and the other two share the rest as 2 to 3. Stacked, the statements and notes stand beside the
transcript in the same 2 to 3, and up to 800px the statements and the transcript do. Widths dragged before
stay as they were, and Reset widths puts every edge back where the screen now opens. In a narrow notes column
the heading takes two lines, and Columns keeps its chevron alone where its word would not stand beside the
heading's longest word, its tooltip saying Columns and the columns shown and a screen reader hearing
Columns. At 800px and below the edges give way to the narrow layout above, and the
transcript alone keeps its reading measure, with no edge to drag.

**Show, hide or stack the columns (18 October).** Working in his own order, Adam wanted to hide the
exploratory notes, or the experiential statements, or both, the transcript always shown, and to have the
notes under the statements in one column beside the transcript, and he chose four layouts and one menu
from a drawing. Columns' menu holds three parts. Under Show, a tick for Experiential statements and one
for Exploratory notes, each from its whole row: unticked, that column and its heading go and the others
share its room, and ticked again it comes back where it stood in the order. Hidden is never deleted:
what was written stays in the workbook and shows again with its tick, and the card and the notes field
keep the current passage's words out of sight, so `Cmd + Enter` still saves and moves on. With the
statements hidden the caret goes into the notes, and with both hidden the transcript stands alone at a
reading measure in the middle of the screen, its grip gone with nothing to change places with. Under
Statements and notes, Side by side, the columns as above, or Stacked, notes under statements: the
transcript one column, its passages' words alone, and beside it, on the statements' side, a column of two
halves, the current passage's statements above, its card still the place to write them with Next at its
foot, and its notes below, each half scrolling on its own if it must, a divider between them starting at
half. The divider moves by a drag, by the up and down arrows with it in focus, Home and End taking it to
either end, and a double click puts it back at half, and its place is kept. Dragging the statements'
heading or the transcript's to the other side moves the stacked column there, as `Alt` and an arrow do.
With a column hidden, Stacked has nothing to stack, so its two rows are faint and not offered, the choice
kept for when both are shown. Under Order, Back to the book's order, which closes the menu, and since 20
October under Widths, Reset widths (see The column edges). Since 21 October Back to the book's order puts
the statements back above the notes in a stack too, and Stacked's row says "Stacked, statements under notes"
while the notes stand above. Opened from
the keyboard, the menu's first tick takes the focus, `Tab` keeps to the menu, `Space` ticks, the arrows
choose between Side by side and Stacked, and `Esc` closes it. Narrower windows follow the rules above for
whatever is shown, the notes under the words up to 800px, Stacked among them, and each passage stacked at
a phone's width, and a hidden column stays hidden at every width. An interviewer note opens under his
words while the notes are hidden or stacked. Each choice is kept in `config.json` beside the order,
`columns_hidden`, `columns_stacked` and `stack_split`, and a settings file with none of them reads as the
three columns side by side. Settings' View holds the same ticks and choices (see View).

**Stack by dragging a heading (21 October).** From Adam's backlog: drag a column's heading by its grip and
let it go over the other column's lower half, and the two stack in one column, the one dragged below,
over its upper half and it goes above. While the heading is over a half, a box in the ink stands round that
column, the half it would take in a faint tint that leaves its words as readable as the rest, and a line in the
ink where the two would meet, in the gap between two statements nearest the middle, never through words.
Over a gap between columns the bar marks the place as before. The statements and the
notes are the two that stack, the transcript keeping its own column. The stack stands where the column it
was dropped on stood, the lower column's heading and grip over its half, and the divider between them
moves and is kept as above, its place the upper half's share. Each half scrolls on its own, and while more
of it lies below or above its edge it fades there, as the transcript does, the card fading out just over
Next with Next itself whole. Drag the lower heading back out to a gap
between columns and it stands alone there again, or over the upper half and the two change places. The
upper heading moves the whole stack, as `Alt` and an arrow do from either grip. For the keyboard, and for
anyone who would rather not drag, a click on a heading's grip, `Enter` or `Space` with it in focus, or a
right-click on the heading opens the heading's menu: Stack under Exploratory notes, or Stack under
Experiential statements, while the two stand side by side, and Stand alone while they are stacked. Reset
widths puts every column back alone as well as every edge, the statements above for the next stack and
the divider at half, and it is offered while a stack stands. At 800px and below the screen stands as
before, with no drop on a half and nothing in the heading's menu. The column above is kept in
`config.json` as `stack_top`, beside `columns_stacked`.

**View.** Two things about the statements screen are a matter of taste, so each is his to choose
and neither is hidden in Settings (16 October, after a tester's feedback). View, the first of the top
bar's tools, an icon of a page in two columns and its word, opens a small menu under it: a tick,
Larger current passage, and since the evening of 16 October the minimap, since 17 October, later a
choice of Auto, On and Off under its name (see The minimap). Until 17 October its first three rows
chose where the notes stood, right or left of the transcript or under the statements, and the three
columns and their order under Columns took their place. Each row ticks from anywhere on it, each change
shows at once and is kept, and the menu stays open on it, so the views can be tried one after
another. `Esc` closes it, and so does a click anywhere else. The same choices stand in Settings,
under Experiential statements, under a small heading, View, Larger current passage first, then
since 18 October Show and Statements and notes as Columns has them, where until then the columns' order
stood first as Columns, a list of the six, and the two always agree. They are kept in `config.json` as
`statements_columns`, `larger_passage` and `minimap`, `auto`, `on` or `off`, and a settings file
without them reads the defaults, the book's order, the current passage larger and the minimap on Auto.
The columns shown and the stacking are kept beside them, every column shown side by side when absent (see
Show, hide or stack the columns). Since 20 October Column widths follows, its Reset widths putting the
column edges back for this screen at once (see The column edges).

With Larger current passage ticked, as on a new install, the passage being worked on is drawn large
and at full contrast, its name in the margin and the rule beside its words in the full ink, never the
crux orange, which in the transcript marks a quote alone
(17 October). Unticked, every passage is drawn at one size, the passage being worked on at
full contrast on a band of the sunk paper with a fine rule round it, never the crux orange, which
means a crux, so the column no longer grows and shrinks as the current passage moves down it.

**The minimap (16 October).** A tester lost his place in a long transcript and asked for a wider
scrollbar or a minimap, and Adam chose the minimap, a part of the screen he chooses himself, never a
setting buried in Settings. It is a card at the bottom right of the transcript column, where until 17
October it was a strip down the column's full height, which took too much of the screen for a quick
look (Adam's word, 17 October), and since the evening of 17 October it is drawn to Adam's own drawing,
where for a few hours it stood in short columns side by side. The card is one size, about 135 by 300
pixels, whatever the interview's length, and what it holds is scaled to fit it, like a measuring jug.
The transcript stands in it as one narrow column, as if its words were wrapped narrow: each of her
passages is a solid block in a mid grey as tall as its words, and where a passage would come out under
about 4.5 pixels it is joined with its neighbours into one block, so a short interview shows every
passage and three hours a few passages to a block. Past an hour the column is drawn finer, the least
block and the gaps between growing evenly smaller to about 2.5 and 1.6 pixels at three hours, so three
hours stands in more and smaller blocks than an hour, as Adam's drawing has it, where until 18 October
three hours looked like an hour, 31 blocks against 30. The interviewer's passages are a thin pale mark, about
two fifths of the column's width, where they fall between blocks. A track 4 pixels wide runs down the
column's left: the green of saved stands beside each passage done, at its place, a skipped one counting
as done, and nothing beside one not done, the track's outline alone, with no light green anywhere. The
part of the transcript in view is a box drawn in a solid line of the ink 2 pixels thick, near white in
dark, never under about 12 pixels tall, and the column outside it is dimmed, its blocks fainter, a little
less in dark, so the part on screen stands out clear and shows at once where he is at an hour and at
three hours (18 October, Adam's choice from four looks drawn for him, one's solid line with another's
dimming, where since 17 October, later, it was a light wash of the ink with no edge that he could not
see, at its least a faint sliver of 6 pixels, and at first a thin edge in the soft ink). The line holds
3 to 1 or more against the card, the blocks and the dimmed blocks in both themes and stands on the card
clear of the green, the blocks in view keep their grey, the dimmed ones stay in sight, and under the
pointer a light wash fills the box. The time stands at the column's right in
the faint ink, like a jug's dashes, each at the place its minute falls between the timecodes either
side: labelled every five minutes in an interview
under half an hour, every fifteen up to ninety minutes and every thirty beyond, with short dashes and no
label at the fifteens between, a label reading 00:00 and past an hour running on in minutes, 90:00 and
180:00, never hours. Nothing else stands on it, no quote's mark, no round's rule and no mark for
the passage being worked on: the box shows where he is. The card holds the map alone. Its button is
Minimap on the status bar since 21 October (see The status bar on the statements screen), where until
then it stood outside the card in the corner, a small card of its own on the card's bottom edge, and at
first inside the card beside the last label. Each block and the green reach 3 to 1 or more
on the card in both themes, and the time's labels 4.5 to 1. A click anywhere on the card brings that
place to the middle of the column, a drag on the box scrolls it, a click and a drag together carry on
from the place clicked, and the wheel over the card scrolls the transcript as it does over the words.
With the pointer on a passage a small tip gives its speaker and its timecode. Only the column moves:
the passage being worked on stays as it was, the caret stays in the fields, and Back to where I was shows
as it does after any scroll by hand, to the card's left on one bottom edge with it, the card keeping
its place, where at first it rose by 44 pixels and moved under the pointer in the middle of a drag,
and then stood 4 pixels higher than Back to where I was (17 October, later). The box follows the column as
it glides to a new passage, and the card is drawn again as he works, so a statement saved or a view
changed shows in it at once. It works in every order of the three columns and with Larger current
passage on or off, since each passage's place on the card is tied to where it stands in the column. The
column keeps its own scrollbar, the card standing clear of it, and its foot keeps room under the last
passage, so that passage scrolls clear of the card.

Minimap in View is a choice of three, Auto, On and Off, and so is Minimap under View in Settings, Auto on
a new install and for a settings file from before, where the old tick's on reads as Auto and its off as
Off. In Auto the card appears as he scrolls the transcript, by the wheel, the scrollbar or the keys, or
moves to another passage, stays while the pointer is on it or a drag lasts, and fades out about two
seconds after, leaving its button alone in the corner, the box over the part in view fading with the
map (18 October, where the box went first). On keeps it there, and Off leaves nothing in
the corner. The same choice rules the map on the PETs and GETs boards since 18 October (see The minimap
under PETs). In Auto and On the button, "Minimap (M)" in its tooltip, and `M` anywhere outside a field,
as the shortcuts card says, show the card until the next passage, or while it shows hide it until then.
The words he is writing and the passage being worked on never stand under the card: while the current
passage's words, its exploratory notes, a passage open for correction or a field in focus would stand
under it, it gives way to its button, and under the button too the button goes as well, at every width,
each coming back as soon as they are clear, where at 1100px and below the button stayed over the last
line of his passage (17 October, later). The passage being worked on stands in the middle of the column, so the card
gives way only when he scrolls it into the corner or a passage is very long, and never while the
pointer is on it or a drag is under way. At 1100px of window and below, where until 17 October the
sheet and the fields stacked, the card would cover much of the last column, so it gives way to its button there, as the strip gave
way below 620px, and a press on the button or `M` opens it over the column, as a press does while it has
given way at a desk width. An opening of his shows the card over whatever stands in the corner as he
opens it, and lasts until what he is working on comes under it: once the passage being worked on, its
notes or a field in focus reaches the corner after the corner stood clear, once he clicks into a field
under the card, or once his pointer leaves the card or he scrolls the words while they stand under it,
the card closes to its button at 1100px and below and gives way as at any time at a wider window (17
October, later, where an opening lasted for the whole passage and at 1024 wide covered the notes he was
writing). A move to another passage ends an opening too. Where an opening of his stands over the
transcript's words, as at 360px, the column's words fade out under the card across its full width, from
just above the card to the column's foot, so the card's edges never cut a line, unless a field he is
writing in stands there, which never fades (18 October, where the card crossed the lines beside it).
At 1100px and below the button alone does the same where it stands over a passage's words, as at 360px,
so it never covers a word (18 October, later). Where the column has no room for Back to
where I was beside the open card, as at 360px, the column's words fade out in a strip at its head and Back
to where I was stands over it at the card's right edge, so it never cuts through a line and the words never
move, where it stood squeezed to two lines into the words and then over a line above the card.

**Narrow windows.** This is not a phone app, but down to 400px nothing overlaps and nothing scrolls
sideways. Since 21 October the place and Shortcuts stand on the status bar under the player, which keeps
them at every width (see The status bar on the statements screen), and what follows about the place giving
way in the top bar is its history. The top bar keeps to one line and gives way in order. The participant name truncates with an
ellipsis at any width, with the whole name in its tooltip. Below 1440px the line to today's target goes
and the tools stand as their icons alone, each named in its tooltip, and below 1280px the first tab,
Experiential statements, reads ES (see Idiograph's tabs). At 760px and below the bar takes its three rows,
the tabs on the middle one (see Idiograph's tabs). With Work in rounds ticked
the speaker's name and the round's short bar go below 1440px too, each saying what the bar says beside
it, the participant name and the round's counts, so at 1280px a name of 30 letters stands whole with
Guidance and Search on the bar, where a name of 25 letters lost its last letters (17 October, later,
where they went at 940px and 760px). Below 940px the round clock and its
reset go. Until 3 October 2026 the bar said Statements,
which went at 760px with the short bar, and the clock went at 900px. Experiential statements is
twice that width, and kept to those steps it pushed the cog off the bar from about 1000px down,
while just above 900px the bar ran past the window even with the short word. The place keeps "passage" and its numbers whole at every width, and
gives way in order, the speaker's name first, then the sheet's label (16 October). With Work in rounds
ticked the place is longer, so the speaker's name goes below 1440px, "passage 9 of 16 in this round",
below 1440px "in this round" and "round 4 of 5" give way to "passage 9 of 16 in round 4", and below
620px "in round 4" goes to the place's tooltip, so the bar reads "passage 9 of 16", the word passage
kept, where until 16 October, later, the sheet's label and the word passage went instead. With it off
the speaker's name goes below 620px, "passage 9 of 39", and with it on or off the sheet's label goes
below 760px (540px until 18 October). A participant of more than one sheet keeps the switch's chevron where its label
was, which opens the same list. The speaker's name and the round's count are said whole in the
place's tooltip, "Juno, passage 9 of 16 in this round, round 4 of 5". A participant marked complete with passages undecided stands its mark before
the place, so there the place takes its short form at every width. Below 620px the separators go, and
the band stacks its label over the question, the three columns keeping the rest of the screen's height at
every width since 17 October, so the page itself never scrolls, and a drag selecting words in the
transcript never takes the question with them (17 October, later). Every card stops at the window less its gutters, a card's
buttons wrap rather than run off it, and the row's menu stays inside its row, its entries wrapping
below 620px. Below 480px the bar's spacing tightens, and the cards and the shortcuts table take less
room. In a participant of two sheets the sheet switch is as wide as the sheet it shows, so the bar fits a phone
360px wide. Below 480px a participant marked complete keeps its tick without the word, said in full in its
tooltip, so the participant name keeps its letters at 360px, "Juno …" beside "passage 7 of 39" with
Guidance on the bar since 16 October, "Juno - E…" before it
since Appearance left the bar ("Juno…" while View and Appearance both stood there), and a few
beside the demo tag (16 October). Settings' categories become a row of tabs over the content on a phone (see Settings). A participant marked complete
gives way in the same steps (see Complete). The bug for Send feedback, there once the build carries the collector's address (see Send feedback), sits just before the cog at every width, as it does on the PETs and GETs bars, so it stands in one place throughout. View stands first of the tools, Guidance after it (16 October), then the magnifier, Search's since 17 October (see Search), and the shortcuts, PETs having gone from among them to the tabs (see Idiograph's tabs), so Settings stands last (see One title bar), and below 480px View is the one that takes the tools to the right edge (16 October). The rest of the bar gives way before the tabs do, so they keep their words and the participant's name its letters: below 1440px "Statements complete" reads "Complete", the tab naming the screen, and the round's words take their short form, so a name of 30 letters stays whole at 1280px, below 760px the shortcuts go, as Sift's and Trace's do at that width, `?` still opening them, with the sheet's label, and below 480px View goes, its choices kept under Experiential statements in Settings, and Guidance takes the tools to the right edge. Measured on 18 October, before the tabs, on the demo's invented participants, an unfinished participant with rounds on, the fullest the bar gets, keeps all of its name or all but its last letters from 1600px down to 480px, and below that its first letters and the ellipsis, "Jun…" at 360px, the bar's sides 8px below 480px and its tools 16px wide below 400px, and a finished participant keeps more, a name of 30 letters whole at 1280px. The icons at the right of the bar
stand 4px apart where the bar's other items stand 8px (12px until 13 October), 3px apart and 24px wide below 620px, and
2px apart and 18px wide below 480px, which is what gives the magnifier its room: each icon takes
30px of the bar, 27 below 620px and 20 below 480px, which the participant name gives up, so just above
940, 620 and 480px the name keeps a letter or two, as it did before the magnifier. The bug stands among the icons at the right and slims with them.

**Sheets.** A participant with more than one sheet makes the sheet name in the top bar a switcher: the same
words, "Initial" sheet, with a small chevron after them, and the workbook's sheets listed in order.
Choosing one goes to the first undecided participant passage on that sheet, or to its first passage when
every one is decided, the way any move goes: the column is redrawn, the player cued and a field
typed into saved on the way. `Ctrl + Cmd + Up` and `Ctrl + Cmd + Down` go to the sheet before and the
sheet after the same way (`Ctrl + Alt` and the arrow on Windows and Linux), the same modifiers as the
seek because `Cmd + Shift` and a bracket are the browser's own tab keys, and the shortcuts card lists
them under Moving about with `Cmd + J` and `Cmd + K`. With Work in rounds ticked, rounds are numbered sheet by sheet, so
"round 2 of 4" in the top bar is the second of the four rounds on the sheet in front of him, the
sheet's name already beside it, and its tooltip carries the participant figure, "round 6 of 9 in the
participant". The round bar is the round the passage is in, and the participant line counts every sheet.
Passed passages are worked out sheet by sheet, so working 2d before Initial passes nothing on Initial.
A workbook with one sheet keeps the plain label, with no chevron.

**Entry.** One statement a field, each with its quote under it (see Pairs). `Cmd + Enter` does
what the filled button at the card's foot says, Skip or Next (see The buttons), so every passage he goes on from is decided and the count of
unvisited passages stays honest. A blank passage he moves past with `Cmd + K`, an arrow key or a click,
without pressing Skip or Next, is passed: moving past it is a decision not to code it. A passage
counts as passed once a passage further on its own sheet is decided, or once the last passage saved sits further on that sheet. Passed is worked out every time
the participant is read and never written, so moving between passages writes nothing, and it counts exactly
as a passage saved empty counts, in a round, in the bars and in the numbers. The notes stand open on
every passage in their own column (see The three columns), where until 17 October they could be shut
under their heading in the panel, a dot beside it saying whether they held anything.
`Tab` goes through the fields in the order they sit in, each statement and its quote, pair by
pair, then the notes, with `Shift + Tab` going back, each pair's bin after its quote since 18 October
and the fields of a hidden column passed over. The line in the first statement's empty field
is a craft prompt, a fresh one on every passage.

**Pairs.** The first quote belongs to the first statement and the second to the second, so each
statement is a field of its own with its Quote field under it, a pair, where the screen once
copied Excel's habit of one box of statements and one of quotes. A passage opens with its pairs, one
empty pair on a passage with none. Add another, at the card's foot under the last pair, adds an empty
pair and puts the caret in its statement. Each pair is numbered beside its statement, 1, 2 and on, as
the passage's statements are numbered in the column, numbered again as pairs come and go, where from
14 to 17 October each opened with a heading, Experiential statement 1, and its statement keeps that
name for a screen reader. Remove is a small bin with no word at the top right of each pair, level
with its statement's first line, the statement field ending short of it, in the soft ink and red under
the pointer or in focus, its tooltip and its name for a screen reader Remove this statement (18 October,
Adam's drawing, where until then a red-edged Remove with its word stood at the right of the Quote
label, too near the fields and too loud for an act this rare, so the Quote label stands alone on its
line). It takes away the whole pair, the statement and its quote, one step of undo, and a passage
always keeps one pair. `Tab` reaches it after its pair's quote, and `Enter` presses it.
While the pointer or the keyboard's focus is on the bin, a red line round the pair shows what goes (14 October).
`Enter` never breaks a line in a pair: in a statement it goes to
its quote, and in a quote to the next statement, or under the last pair it adds another.
The pair being worked on is the one whose statement or quote last had the focus, else the last
pair. The same words may be the quote of two pairs. A quote with no statement is kept, written
after the pairs that have one, until it has its statement. The workbook keeps its two columns: the
statements stay in theirs and the quotes in theirs, one a statement in the same order, so once a
passage has a quote its quotes cell holds exactly one entry per statement, "(no quote)" for a
statement with none. Idiograph reads "(no quote)" as empty everywhere, keeping its place, and a cell
that has it from Excel reads the same. A passage with no quote at all keeps its cell empty.

**A passage changed since the page was loaded (18 October, the words of 19 October).** A save carries
the passage as the page last loaded it. When something else has saved that passage since, another
window, an agent working through the command line or the MCP server, or anything else that writes the
workbook, nothing is saved, the page stays on the passage with what was typed still in the fields, and a
line at the head of the card says the passage has changed since this page was loaded, with Reload and
Overwrite. Reload loads the passage as it now is into the fields and keeps what was typed under the line,
in plain text that can be copied from, with Put my words back to bring it into the fields again.
Overwrite saves what was typed over the change. Until 18 October the later save replaced the earlier
one without a word.

**A resize while typing (18 October).** Narrowing or widening the window keeps the field holding the
caret where it stood in the column, else the passage being worked on, so neither scrolls out of view.

**A drag takes whole words (18 and 19 October).** A drag over a passage's words selects whole words as
it goes, as a word processor's drag does, so the highlight is the words a quote, an assignment or
anything else takes, and none holds part of a word. Punctuation touching a word goes with it, an
ellipsis, a comma, a semicolon or a full stop at its end, and quote marks or brackets round it.

**The buttons.** At the foot of the current passage's card sit the operations on the passage in front
of him, each with a small drawn line icon: Add another at the left, AI suggest beside it while the AI
features are on, and at the right one filled button in the crux orange, which reads in both themes and
says what it will do. With every field empty it reads
Skip, with the skip icon: the passage is recorded as read in the progress file and not one cell of the
workbook is touched. With words in any of them it reads Next, with the tick: the fields
are written to the workbook, the passage is recorded as done, and the next passage comes up, so Next
is the one button that saves and moves on. The word
changes as he types, with nothing redrawn, because both words sit in the button and one of them
shows. A passage that had words in the workbook and has had them all deleted reads Next, because the
empty fields have to be written over them, which Skip never does. `Cmd + Enter` does what the button
says, the key in its tooltip. A click on a passage, `Cmd + J` and `Cmd + K` move between passages from
anywhere, and the shortcuts card lists the keys under Moving about. Previous stood at the left of the
row and Quote before the filled button until 17 October, when the three columns came: a click on a
passage moves, or a scroll and a click, and a quote comes from the toolbar by the selected words
(see The toolbar by the selection). Until 3 October 2026 Previous passage
and Next passage sat in a row under the player, and Skip and Next were two buttons beside Flag for
later. Highlight stood before Quote until 16 October, and New statement after it for that morning.

**The word count.** Under each statement its count sits, "8 words", and its nudges under that, so
neither has to say which statement it means. A statement past fifteen words takes its whole count
into a badge, "17 words", reversed out, the paper colour on the amber, which reads at a glance in
both themes. Nothing is said about a short one, and the words are counted the way the length nudge
counts them, so the number and the nudge never disagree.

**Quotes, one key (16 October).** Select words in the passage and press `Q`, or Quote on the
toolbar beside them, as Quote under the fields did until 17 October: they go verbatim, in inverted commas, into the quote of the pair being worked on while
it has none, and otherwise into a new pair under the last, as Add another puts one, with the words
as its quote. Either way the caret lands in that pair's statement, so the statement is written
next, in his own words for the passage. A quote is changed by clearing it, then `Q`, so `Q` never
writes over one. The line at the foot says "Quote added, verbatim." `Cmd + Z` takes it back in
one step: an empty quote filled is empty again, "(no quote)" back where it stood, and a pair
it added goes, while a statement written in that pair since stays where it is with its quote
emptied, so an undo never takes his words. `Cmd + Shift + Z` puts it back. Until 16 October `Q`
put the words into the pair being worked on in place of any quote there, and a second key, `S`,
made the new pair (see A new statement from the selection). A PET's
picks follow the quote as they do when the quote is edited by hand. A quote can be made of
more than one piece of the same passage. Select the first piece, then hold Cmd and select the next: each piece
gets a light mark in the passage and the assembled quote shows as one line under it, the pieces sorted
into transcript order and joined with an ellipsis where they are not next to each other. Overlapping
pieces, and pieces with nothing but a space between them, become one. `Q` commits the whole thing.
A plain selection starts again, and so does a save or a move to another passage. Quotes already in
other pairs are left as they are.

**A quote across her passages (30 October).** One quote can take in the same participant's passages
just before or after the one being worked on, when nothing but the interviewer's words stand between,
as the thesis rule has it: adjacent passages combine into one block quote with a range of timecodes when
their order is kept. It is still one quote, never two. Select the first piece in the passage being
worked on, then hold Cmd and select words in her next passage, or the one before: the piece is marked
there as the first is, and the candidate under the passage takes it in, the pieces in transcript order
with an ellipsis at every gap. The interviewer's words between are never in it. `Q` puts it in as any
quote. Cmd and words in the interviewer's turn says "A quote holds the participant's words, never the
interviewer's.", in another speaker's passage "A quote holds one speaker's words, and these are another
speaker's.", and in a passage further off "A quote can take in only the passage just before or just
after, with nothing but the interviewer between." Each passage takes in more of hers the same way, one
after another, so no passage of hers is skipped. The quote stays with its statement, in its own row of
the workbook, so the statement keeps its place and every board its card. Its words are marked in each
passage they come from, in the statement's colour, and a click on a mark there brings its statement
forward. Everywhere the statement is named with where it is, the PETs and GETs boards' cards and
quotes, the Table view, the print view, its PDF and the Word document, it carries the range, "Initial,
25:51–26:50", from the first passage's timecode to the last's, and a quote inside one passage keeps its
one time. A correction, a trim or a find and replace under a piece is followed as it is for a quote of one
passage: Replace all changes the quote's words with the passage's, and a change the quote does not take
leaves it unmarked until it reads as the passages do again.

**The arrow by the quote (21 October).** Some people select the words first and then write the statement
(a tester, through Adam). Beside each statement's Quote box stands a small arrow, lit in the crux orange
whenever words are selected in the passage being worked on, or pieces are held with Cmd. A press makes the
selection that statement's quote, as `Q` and Quote by the selection do: verbatim, in inverted commas, into
that statement's quote while it has none, and otherwise into a new pair under the last, so a quote is never
written over. The caret lands in that pair's statement, the line at the foot says "Quote added, verbatim.",
`Cmd + Z` takes it back, and Next saves it to the workbook as it saves any quote. With nothing selected the
arrow is faint and a press says "Select the words inside the passage first, then press the arrow." The
empty Quote box says "Select in the passage, then press Q or the arrow. Hold Cmd to add another piece."
(Ctrl off a Mac), where until 21 October it named `Q` alone.

**Each statement level with its quote (21 October).** Each statement is a box of its own, numbered, and
the card's foot, Add another and Next, ends the last box. In a long passage each box sits beside the top of
its own quote: once a statement's quote is set, by `Q`, the arrow or Quote by the selection, its box moves
level with the quote's first line. Two quotes close together stack their boxes in order, the second under
the first, never over it. A statement with no quote yet stays where it is, at the passage's top for the
first and under the one before for the rest, and does not follow a selection: its box moves only once its
quote is set. A box never moves while he types, and the boxes are placed again when the passage opens, when
a quote is undone or redone, and when the columns or the window change size. Where the statements stand
under the words, as on a phone or with the notes stacked under the statements, the boxes keep their order
under the passage as before.

**The card in reach beside a long passage (30 October).** Where a passage is too long for the column to show
it with its card, as at Text size Large in a small window, the card stays in view as the column scrolls: beside
the words it keeps between the column's head and foot, level with its quote where that is in view, and where it
stands under the words it keeps to the column's foot and the words pass behind it. A card taller than that
scrolls inside itself, with Add another and Next at its foot. A passage that fits the column is as before.

Words selected in another of her passages on the screen, then `Q` or Quote, go to that passage
first, the way a click on it goes, the passage being worked on saved on the way, and then go into
its pairs as above. A selection in one of the interviewer's passages, or across two passages, gets
the line about selecting first, as it always did. With an interviewer note open, `Q` keeps the note
first, as a click on Quote always kept it, so the quote never goes into a pair out of sight, where
until 16 October the key left the note open and filled the pair hidden behind it.

A drag across passages selects their words alone. The names, timecodes and
row menus in the margin and the exploratory notes beside the words stay out of it, where until 18
October the drag took them in the browser's own blue.

The assembled line is labelled **Quote candidate**, with the key that commits it beside the label,
because until it was labelled it read as something the app had already done. Nothing is written
until `Q`. A plain click in the column that leaves nothing selected clears the pieces and the
candidate with them, and `Esc` does the same, before it goes back to the passage or closes a panel.

**The toolbar by the selection (16 October).** A tester found too much hidden behind keys and
right-click, and pressed `C` with the caret in a statement, so it typed a c. Words selected in one of
her passages now bring a small toolbar beside them, in the menus' paper: Quote, which does what
`Q` and Quote do, and Give to another speaker, which offers what `C` and the right-click's Assign
entries offer, each key in its tooltip, "Quote (Q)", and on the shortcuts card. Until 17 October
each also showed its key on its face, and a line beside the quote candidate's label said "q adds it
to quotes", so with the selection `Q` was explained four times at once. The candidate keeps its
label, and Quote under the fields kept its word, its key in its tooltip, until it went on 17 October,
when Quote here became the one button for a quote. It stands above the selection's
first line, or under its last where the column has no room above, inside the column, so it never
covers the words, and it follows them as the column scrolls. It is never wider than the column, and
at 360 its two buttons stand on one line since their keys left their faces, where at first it ran
past the column's right edge and then wrapped onto two lines. Where it meets
the minimap's card it stands over the card. Where the notes stand beside the words it
keeps to the words' side of them, in the transcript's column since 17 October with the statements
and the notes in theirs, its buttons one above the other if it must, and it stands 6
pixels clear of the highest and the lowest of the words selected, at every width and in
both themes, where at 1280 it once sat on the first line and the notes' edge (16 October, later). It
stands clear of the passage's speaker line too, the name and time over the words at a phone's width
and in the margin at a desk width: where the two would meet above the selection it goes over that
line, and where there is no room there, under the selection, where at 360 it covered the name (17
October, later). Its far edge never cuts a line of words through its letters: where it would clip a line
by a few pixels it steps clear of it, still clear of the words selected, where it would cut the letters
themselves it grows over that line whole, its buttons in its middle, and where only the room under the
letters is clipped it stays as it is, where until 18 October it could cover half a line
above the selection. It fades in where it stands, where it rose from below over the line under it. Selecting words moves the keyboard to the transcript, out of any
field the caret was in, so `Q` and `C` act at once. `Esc` takes the toolbar away with the selection
and the pieces under it, and so does a click anywhere else. A selection in one of the interviewer's
passages brings no toolbar, and `C` and the right-click work there as they always did. The keys stay
for those who use them.

**A new statement from the selection (16 October).** For that morning `S`, or New statement beside
Quote, made the quote of a statement still to write from the selection, filling the pair being
worked on while it had neither a statement nor a quote and else adding a pair under the last,
the caret in its statement. The same afternoon it went into `Q` and Quote (see Quotes, one key),
which fill a pair's empty quote whatever its statement holds, so `S`, the button and its line
on the shortcuts card are gone. The quote-first way of working stays one act, the statement his own
words for the passage, and the passage the unit. A pair made this way is saved like any other, and
one left without its statement is kept as a quote with no statement until it has one (see
Pairs).

**Quotes in the passage (16 October).** A tester lost track in long passages of the words he
had already drawn on, so every statement's quote is marked where it stands in its passage, the
crux orange's wash and a fine rule in it under words that keep their passage's ink, the one orange in
the text since Highlight went the same day. In a passage set in the faint ink, every one but the current,
its words take the soft ink so they read on the wash, where in the dark appearance they stood faint
(17 October, later). Where a quote wraps, its wash and rule stop at its last
word on the line, where until that evening they ran on over the space at the edge, and its words were
orange. A quote put together from pieces with an ellipsis is marked piece by piece, each
piece where it stands. A word of his own in square brackets, "my rational [mind] tells me", is his
clarifying insert and not the passage's, so it is never looked for and the words either side of it are
marked where they stand (20 October). The passage being worked on is marked from the fields as they stand, so a
quote shows the moment `Q` puts it in or it is typed, and every other passage from its pairs as
saved. Each piece is found after the one before it, any run of spaces reading as one, participant set
aside, and curly and straight inverted commas and apostrophes matching each other. A quote any piece
of which the passage no longer holds, its text corrected since, goes unmarked and nothing else
changes. A mark's tooltip names its statement, "Experiential statement 2", or both when two pairs
hold the same words, "Experiential statements 1 and 3". A plain click on a mark brings its statement
forward: on the passage being worked on the caret goes to that pair's statement, and on another
passage the move goes there first, as a click on its row does, and then the caret goes to the pair.
Since 21 October the statement's box also scrolls into sight in the statements column when it stood
out of it, by no more than it takes, so with many long quotes to a passage a click on the words finds
the statement that quotes them. A drag across marked words still selects them for a new quote and
opens nothing. Words two quotes share open the first statement by number. A quote under the pointer or holding the caret lights its marks in the passage, a stronger wash
and a firmer rule. The marks read in light and dark, on the current passage and the dimmed ones,
in every order of the three columns and the larger current passage on or off. The shortcuts
card lists it under Mouse, "Click a quote", "Shows its statement", which read "Its statement" that
morning.

**A colour per statement (18 October).** Each statement's quotes take its own colour in the
passage, so the parts of a passage each statement draws on show at a glance. Statement 1 keeps the crux
orange's wash and rule, and statements 2 to 6 take the participants' colours of the GETs board in its
order, Blue, Plum, Brown, Indigo and Teal, a seventh starting again at the orange. This screen holds one
participant, so here the colours mark her statements, and on the boards and every other screen they
mark a participant as before. Olive is left out, since it reads as the orange to a colour blind eye.
Each wash is a bright tint of its colour, as light as the orange's, so it reads as that colour and
the words on it as well as on the orange's. On the card each statement's number
stands in a dot of its colour and its quote has a stripe of that colour at its left, and the
numbers beside every other passage stand in their dots too. The colour follows the statement's place
in the list, so removing or moving one recolours the rest at once. Words two statements share keep the
first one's wash and take a rule for each, the first's where it always stands and the second's under
it, and words three share show the first two's rules, the tooltip naming all three. Each rule reads at
3 to 1 or more on the paper, and the words on each wash read at least as well as on the orange's in
the same appearance.

**Done marks (16 October).** Each of her passages he has worked carries a thin bar at the edge of
its words, in the margin where the current passage's rule stands, in the green of saved and never
the crux orange: full where the passage has at least one statement, fainter where he skipped it,
and none while it is undecided or only passed. A passage he jumped over on the way further, passed,
carries no bar, so jumping ahead to passage 30 leaves passages 1 to 29 bare, and nothing reads as
done up to here (Adam's word, 16 October). Each passage says its own state, so work done in any
order shows as it is. The bar runs the whole height of the row, so passages next to each other
join, and the interviewer's passages between two of hers carry it on at the fainter of the two, so
a stretch of worked passages reads as one. The current passage's rule stands over its bar, solid,
the orange taken toward the paper, so the green never shows through it as brown. The full bar is
the green at its whole strength and the fainter one at about half, where in light the first read
grey (16 October, later), and the minimap's track takes the green at its whole strength for both. Where the
margin lies along the top, below 1000px, the bar stands at the row's left edge, the words 12 pixels
clear of it, since at the right edge it read as the column's scrollbar, the current passage's as
well, and with Larger current passage off its band keeps its hairline above, below and at the left,
so nothing of it stands in the scrollbar's lane at 360. The counts and the rounds are as they were:
a passage passes the way it always has, once a passage further on its sheet is decided, and counts
as decided there, with no bar.

**The recording.** The player sits at the foot of the sheet's column and takes its whole width,
built from the app's own parts: a play button at 48px, the elapsed time, a scrub bar that fills
what is left, the total, and the file name faint on the right. The track holds a floor of 120px, so
a long file name ellipsises rather than thinning the bar out. With no recording nothing shows at the
foot (17 October), and a click on a timecode or `Space` says "No recording found for" the sheet as a
line at the foot, where until then the player stood as that line alone on every participant without one,
taking the width and wrapping on a phone (15 October, later). The player follows the passage, so every
move cues it to that passage's timecode, carrying on from the new place if it was playing and staying
put if it was paused. Under the pointer the play button and the track go to the ink, as any control
does, where until 17 October, later, they went to the crux orange.

An arrow icon with a small 5 stands either side of the play button (8 November): the one on the
left goes five seconds back and the one on the right five seconds forward, from wherever the clock
sits. They do what `Ctrl + Cmd + Left` and `Ctrl + Cmd + Right` do, and neither runs past the start or
the end of the recording. Their tooltips name those keys. Like the play button they are not in the Tab
order, so the cursor stays where it is in a field.

Clicking a timecode in the margin plays from there. Clicking the same one again pauses, and a click
after that carries on from where it stopped rather than going back to the timecode, because a pause
is a place he chose. Another timecode jumps there and keeps playing. Any other cue, and a drag on
the scrub bar, end that toggle. A double-click on a timecode corrects it (see Correcting a
timecode): its first click has played from there, and its second leaves the player alone rather
than pausing it.

Outside a field, `Space` plays or pauses from wherever the clock sits. `Ctrl + Cmd + Left` and
`Ctrl + Cmd + Right` (or the two arrow buttons beside play) jump five seconds either way and work inside the fields too (`Ctrl + Alt` and
the arrow on Windows and Linux). The chord is the app's own because `Cmd` and an arrow belong to the
text on a Mac, the line ends and with `Shift` the selection out to them, and one chord must mean one
thing wherever the caret is. Both move the playhead mark and the elapsed time at once. The file is found at
`<case>/Source/<Sheet>/Source/`: the one called
`P<n>-<Sheet>`, or the largest `.m4a` that is not a per-speaker track. Timecodes are the recording's
own clock, with no offset. A missing file, or one iCloud has evicted, is one quiet line where the
controls would be and nothing else changes.

**The playhead.** The passage the recording is in, playing or paused, has its timecode in bold in the
accent rather than the crux orange, with a small play triangle before it. It draws no line of its own
beside the words, where the passage being worked on has its rule. While the timecode is open for
correction it has no triangle. (28 October, Adam's choice of three drawn. Until then a quiet rule in
the accent stood just before the words, 2 pixels from the rule of the passage being worked on, and the
two read as a double line. It had stood there since 18 October, and before that at the row's outer
edge, 100 pixels from the words, where it read as a stray rule between the columns.) The span runs
from a passage's own timecode to the next one, the interviewer's passages included. The column glides
to keep the marked passage in sight, though it leaves the column alone while a selection or a drag on
the scrub bar is under way, and the passage being worked on never moves with it. Any cue moves the
mark to the cued row, playing or paused, so the mark and the clock never say different things. Pausing
leaves it where it stopped.

**A click on a row.** A plain click anywhere on a row acts, the margin and the text alike. On one
of her passages it goes to that passage, the way the speaker label always did, so the recording cues
there and carries on if it was playing. On one of Adam's the passage being worked on does not change:
the recording cues to that row, jumping there and playing on if it was playing, and the playhead
mark moves to it at once. The timecode keeps playing from there, and the small control beside it
opens the row's menu. A click that selected or extended text, a click that travelled far enough to be a drag,
and a click with Cmd, Ctrl, Shift or Alt held all pass through untouched, because the text has to
stay free to select for a quote, built from one piece or several. A plain click on a quote's
mark brings its statement forward (see Quotes in the passage). A faint wash on the row
under the cursor, the sunk paper of a row under the pointer since 17 October, later, on which its
timecode and its ⋯ read as well as on the page, and a pointer over the margin, say the row is a target.

**Interviewer notes.** Her passages take the statements, quotes and notes, and his own interventions
are worth a note too: one that moved her on, a poor one, a place where the next question belonged.
A plain click on one of Adam's passages cues the recording and marks the row as before, and puts one
field in the notes column beside it, headed Interviewer note with the row's timecode beside it and holding
the note the workbook has for that row (17 October, where until then it stood in the panel in place of
the pairs and the notes, which hid them). The current passage keeps its card and its notes as they
stand, and the note closes on any move to one of her passages: a click on one, `Cmd + J`, `Cmd + K`, a
sheet switch or the next stop. The passage being worked on does not change while the note is open, and
the bars, the clock and the progress strip stand as they were. The line in the empty field is a
craft prompt, a fresh one on every open, "What did this intervention do?", "What might have served
them better here?", "A question, or a lead?" or "Where were they going before this?". While the note
shows, the filled button reads Next, with the tick, as on her passages, and it and `Cmd + Enter` do the
same: the note is kept and its field goes. A click anywhere but the field, its row and the player keeps
it too, and so does any move, the way a field typed into is saved on the way. `Esc` closes it
with nothing written. A note the workbook refuses comes back in the field the next
time that row is clicked. A row with a note carries a small pen in its margin, on the timecode's
line, so the notes can be seen down the column, and the pen goes when the note is cleared.

The note goes to `/api/interviewer-note` and into the workbook's Interviewer notes column (see
[docs/internals.md](internals.md), How the workbook is written), and nowhere else. It is never a stop, never counted and never nudged, and
it is in none of the CSV, the PET draft, the themes file, the prompts or anything sent to a model. Nothing in the progress file changes, so the rounds, the row states and
the passed passages are as they were. The route refuses a workbook Excel has open with the passage
screen's line, and a row whose speaker is not the interviewer named in Settings with "Interviewer
notes belong to the interviewer's passages." An empty note clears the cell, and a note that has not
changed writes nothing. A page in front of a server that has not been restarted finds no note on
any row, and a click on his passage cues the recording as before.

**The row's menu.** A right-click anywhere on a row, the margin or the text, opens one menu, in the
menus' paper, and the small control in the margin, three dots on the timecode's line, opens the same
one. The control stands in view on every row in the faint ink since 16 October, where until then it
showed only with the row under the cursor and a tester found the menu by chance. Its entries come in groups with a thin rule between them.
The assignments come first (see Assigning words to another speaker), where Unhighlight stood before
them until 16 October. Then Edit
text, which is what a double-click on the text does, and Edit timecode, which is what a
double-click on the timecode does. Then the two cuts, "Cut this passage and 73 before" and "Cut this
passage and 3 after", each with its rows and timecodes in small type under it, "74 rows, 00:44 to
17:09" (see Trimming the ends). Esc closes the menu, and so does a click anywhere else. Shift with a
right-click keeps the browser's own menu, and a right-click inside the passage editor or the timecode
box is the box's own.

**Highlights (gone 16 October).** Until 16 October a phrase selected in the passage and `H`, or
Highlight under the fields, became an orange run (theme 9, tint 0) in the Transcript cell, the crux
the annotation pipeline and the guides name. Adam's decision on a tester's feedback took Highlight
away and gave its place to the quotes, which are the marks in the text now (see Quotes in
the passage), so nothing on the screen makes a highlight, and `H`, the button, its line on the
shortcuts card, the Unhighlight control and its entry in the row's menu are gone. Highlights already
in a workbook stay in the file exactly as they are, never rewritten and never stripped by a save,
and the app draws them as plain words. A correction and a replace still find them again by phrase
and keep them where their words survive, naming one dropped (see Editing a passage), the find
still counts the occurrences inside one, since a replace there drops it from the file, a trim's card
still names a row that carries one, and a split or a merge keeps them on their characters. No export,
print or prompt ever carried them, and none does now. `/api/crux`, which wrote them, stays on the
server for a page from before, with `add` and `remove` as it always took them, and nothing on the
page calls it.

**Editing a passage.** The transcript carries slips, inverted commas missing from a stretch of
internal speech among them. `E` opens the passage being worked on, a double-click on the text opens
any passage, the interviewer's as well as hers, and so does Edit text in the row's menu. The box holds
the plain text of the cell with every run flattened, grows as it is typed into, and carries the
hint and two small buttons: `Cmd + Enter` saves, `Esc` cancels with nothing written. The box is
about the text alone, and its save sends only the text. The timecode is corrected in the margin
(see Correcting a timecode). One passage is open at a time, opening another cancels the first, and a
move to another passage cancels it too. A double-click no longer feeds the quote builder, so the word
the browser picks out goes to the editor rather than into a quote.

While the box is open it holds the caret. A click inside it places the caret and does nothing else:
the column does not navigate, does not re-centre and is not redrawn, and a drag inside the box is
the box's own rather than a piece of a quote. Until this was so, a click in the box bubbled to the
column's whole-row handler, which read it as a click on the row it sits in and put the caret back
in the statement field, so the box could be opened on the passage being worked on and never typed
into.

Saving goes to `/api/edit-turn`, which writes the text into that row's Transcript cell and nothing
else. The cell keeps its font, its alignment and its number format, and never gains a fill. The
orange runs are found again by phrase: a run whose phrase still occurs keeps its highlight at the
first occurrence in the new text and in the font it already carried, and one whose phrase has gone
is dropped and named on screen as `Workbook highlight dropped: "..."`, where until 16 October it said
Highlight, the name of a tool gone that day. What lies between the marks comes
back as the cell's body text, because the text has been rewritten and there is no character to
carry a run on. Text that has not changed writes nothing, an empty passage is refused, and the header
row is never edited. A changed timecode is written into the timestamp cell in the representation
the cell already holds, a `datetime.time` in every workbook so far, and one that cannot be read is
refused with a line and nothing written. The old and the new text both go into the progress file
under `edits`, beside the trim record, with the old and the new timecode beside them when that
changed too, so a participant rebuilt from its raw source can be reconciled with what was corrected
here. The source CSV the participant was built from is not touched. The statement fields, the pace clock,
the speaker and the playhead are all left where they were.

**Find and replace.** A slip the transcription made the same way many times, a "so" that wants a
comma after it, is put right once for the whole workbook. `Cmd + Shift + F` on the statements screen
(`Ctrl + Shift + F` on Windows and Linux), from the fields as well, or Replace in the transcript under
a This participant search (see Search), opens one card, Find and replace, in the trim card's style but standing at
the top right with no veil, so the sheet stays in sight under it. It stands under the research question,
as the guidance sheet does, so the question reads whole while it is open, where at 1280 its top hid the
question's end (17 October, later). Below 1100px, where until 17 October the sheet and
the fields stacked, it stands at the foot of the window over the columns, and the line the app says
things in rises above it. Below 700px it takes the window's whole width there, so no strip of the
fields under it shows their labels cut beside it (17 October, later). It carries Find, Replace with, two ticks, Whole word, ticked, and Match
participant, not ticked, a count line, Previous and Next, Cancel, Replace and Replace all. Each box is in the ink since 17 October, where it stood in the browser's own blue, as Settings' are. A passage open for
correction is cancelled as the card opens, and words selected on one line of the column start the
find. Esc closes it and takes the washes with it.

The match is literal, never a pattern. With Whole word ticked an occurrence may not run into a
letter or a digit at an end that is one itself, so "so" never touches "also" or "sofa" and does find
"so," and, with Match case not ticked, "So". With Match case not ticked each replacement takes the
participant of what it replaces, so "So" at the head of a sentence becomes "So,", "SO" becomes "SO," and
"so" is written as Replace with is typed. With it ticked the replacement is written as typed. The find runs
over the Transcript column, every row of every sheet, the interviewer's passages included. As Find is
typed the page counts over the text it already holds, a breath after the last key, and the line
reads "14 on Initial, 3 on 2d" with "17 on 2 sheets" in the small type beside it, "No occurrences",
or nothing while Find is empty. Occurrences that sit in a highlight the workbook holds are counted
after a dot, "2 inside workbook highlights", because a replace there drops the highlight, where until
16 October it said "inside highlights", naming a tool gone that day. Since 26 October Replace all changes
the words in the statements, the quotes, the exploratory notes and the interviewer's notes as well, so
the line then reads "8 in all: 3 in the transcript, 5 in your analysis" (singular where it is one, "1 in
the transcript"), and Replace all's number counts them with the transcript's.

Every occurrence on the sheet on screen carries a yellow wash, never the orange of a quote and
never written anywhere, and the one in focus a stronger one with an edge, the column taken to it
the way the playhead takes it. In dark the stronger wash is two fifths of the yellow since 17 October,
where at half its words read under 4.5 to 1, and the words under every wash stand in the ink, so one
found in the interviewer's fainter passage reads as well as any. The focus starts at the first occurrence at or after the passage being
worked on. Next and Previous, and Enter and `Shift + Enter` in Find, walk them in transcript order,
round from the last to the first, and one on another sheet is reached through the sheet switcher's
own path, which lands on that sheet's first undecided passage, with the caret back in the card. The
focus only ever sits on the sheet on screen, so Replace never touches words out of sight.

Replace, and Enter in Replace with, replaces the occurrence in focus and moves the focus on past
the words it put in, never round to the top. Replace all reads "Replace all 17", the number in front
of him as he presses it, and stands disabled while there is nothing to replace. Both go to
`/api/replace`, which counts again by the same rules. It refuses a workbook Excel has open with the
statements screen's line and an empty Find, does nothing when Replace with reads as Find, and for Replace
names the occurrence by its place among the row's matches, refused with a line when the passage no
longer reads as the page holds it. It never touches the header row. It loads the workbook once,
writes each changed cell through the write a correction takes, so the cell keeps its font, its
alignment and its number format, gains no fill and has its highlights found again by phrase, and
saves once. Replace all changes the words wherever a passage holds them (26 October): the transcript,
each statement, each quote, the exploratory notes and the interviewer's note, a statement, a quote or
a note at a time, so a name taken out of the transcript goes from the quote that copied it and the
statement and the note that named it too. A "(no quote)" keeps its place, and a statement the replace
would leave empty keeps its words. Every PETs board of the participant, and every copy of them, the GETs',
and in a project of timepoints the participant's LPETs and the LGETs (since 30 October), takes the new words
with the workbook, so no card shows as changed for it and the participant stays in. Replace, the one occurrence in
focus, changes that occurrence in the transcript alone. The page redraws the rows that changed and nothing else,
counts again and says what it did, "17 replaced, 14 on Initial and 3 on 2d. Cmd + Z puts them
back.", each highlight dropped named after it with its sheet and timecode, `Initial 03:55, highlight
dropped: "..."`. Every row changed goes into the progress file under `edits` as a correction does,
its old and its new text, all of one press under one `batch` id, with `find`, `replace`, the
occurrences replaced and, for a row that lost a highlight, where it sat, and the old and new words of
each statement, quote or note cell it changed. Cmd + Z puts all of it back, the boards and every copy
with it. The source CSV is not touched, and the nudges, the pace clock, the speaker and the
playhead are left where they were. The fields of the passage being worked on show its new words, and
words typed there since the last save stay, the save then saying the passage has changed, as it says
for a change from another window. An AI agent runs the same replace (see the guide for agents). A page in front of a server that has not been restarted says "Restart the server to
finish this update." and changes nothing.

**Quotes to pair.** A passage saved before the pairs pairs by order: the first quote with the first
statement. A statement past the last quote shows an empty quote, and a quote past the last statement
shows as a pair with an empty statement. Nothing in the workbook changes until he edits that passage.
Under Find and replace, Quotes to pair lists every passage with at least one quote whose count of
quotes differs from its statements', each a line with its sheet when the participant has more than one, its
timecode and its counts, "03:55 3 statements, 1 quote", that opens its passage. Saving the passage writes it
paired, so it leaves the list. The list stands only while it holds a passage.

**Correcting a timecode.** A single click on a timecode plays from it, and the same timecode again
pauses, as before. A double-click opens a small box in the margin in its place, prefilled the way
the project writes its timecodes (see Timecodes, in Project settings), with the text selected, and Edit
timecode in the row's menu opens the same box. `Enter` saves, `Esc` cancels, and so does a click
anywhere else. The first click of the double-click has already cued and started the player at
that timecode, and the player is left as that click left it: the second click neither pauses it
nor cues it again. Saving goes to `/api/edit-turn` with the row's text unchanged and the new
timecode, which the server writes as above, and one it cannot read is refused with its line while
the box stays open. The row's timecode, the cue point a click on it or a move to the passage takes,
and the playhead mark all change at once, with no reload, and the player is not touched. `Cmd + Z`
puts the old timecode back: the undo entry for an edit carries the old and the new timecode beside
the text.

**Assigning words to another speaker.** A passage sometimes carries words the other speaker said: a
short question of Adam's in the middle of her answer, transcribed as hers, which used to mean
splitting the row by hand in Excel. Select the words in any passage, his or hers, and press `C`, or
right-click them and choose from the row's menu: they become a passage of their own with the speaker
they belong to, and the rows
either side keep the original speaker, so one row becomes three, hers, his, hers. Words at the very
start or end of a passage make two rows, not three. The
selection widens to whole words, never half of one, and must sit inside one passage: a selection
across two passages, or one with no words in it, is refused with a line. A selection goes straight
through, because it is precise and undoable.

With nothing selected, `C` assigns the whole passage, and that shows a small card first, in the
style of the trim confirm: one line naming exactly what will merge ("Adam 00:46 and Adam 01:21
become one passage, with Juno 00:51 between them assigned to Adam", on the demo), what the rows carry
across, statements, quotes and notes, and Enter to go or Esc to cancel.

The speakers of a sheet are its distinct names, in the order they first appear, and there is no
limit on how many, so a focus group of six works the same way as an interview of two. On a sheet
of two speakers `C` assigns to the other one at once. On a sheet of three or more it opens the
row's menu with the assignments alone, and Esc cancels it. The assignments list one entry for
every speaker but the passage's own, "Assign to Adam" for the words selected and "Assign this passage to
Adam" always, and never quote the words, because a selection can be a long passage. The last
entry, Assign to someone else, asks for a name in a small box: a new speaker is fine, and becomes
one more name like the others. A name already on the sheet is taken as it is spelled there. In the
right-click menu they come first, above Edit text, Edit
timecode and the two cuts (see The row's menu).
`C` works outside the fields and outside the passage editor, like `Q`, and selecting words in one
of her passages takes the keyboard out of a field, so `C` acts at once, and Give to another speaker
in the toolbar by the selection does what `C` does (see The toolbar by the selection). The interviewer named
in `config.json` stays the one speaker who is never a stop.

A row that lands beside a passage of the same speaker merges with it: after an assignment a row
joins its previous and next neighbours only when they carry the name it was just given, and
otherwise stays a row of its own. So a whole passage given to Adam between two of his joins them into
one, and the sheet never reads Adam, Adam, Adam. At the first or last row of a sheet it merges with
the one neighbour it has. Words at the start of her passage that are his join his passage before it the
same way.

The cut falls at the edges of the widened selection, with the spaces there trimmed and no
character invented. The orange runs travel with their characters, so a highlight through the cut
is cut there and stays on the words it was on, and every other attribute of its font survives. A
merge joins the texts with a single space, in sheet order, and keeps every run. The first row keeps
its own timecode. Each new row takes an estimate from where the cut falls: the seconds from this
passage's timecode to the next passage's, whoever speaks it, shared out by character offset, rounded to
the second, never before this passage and never past the next. The last passage of a sheet is taken to
run 0.4 seconds a word. The estimate is written the way the neighbouring cells hold a timecode,
and a double-click on the timecode corrects it.

The statements, quotes and notes of a split passage stay with the first row that keeps the
original speaker: the row before the cut, or the row after it when the selection starts the passage.
The rows made for the other speaker start empty. A merge appends the merged rows' statements, key
quotes and notes line by line in sheet order, each row's quotes kept with its own statements,
"(no quote)" holding the place of a statement with none, and takes the furthest state any of them had got to. Nothing written is ever dropped.

Rows are inserted or deleted in place, through the trim's own path: the header row is never
touched, widths, freeze panes and zoom are kept, custom row heights move with their rows and a
new row gets its share of the height of the row it was cut from, and no cell gains a fill. The
cells of a new row take the style of the row they were cut from. The workbook is copied to
`_Archive/<stem> (pre-assign <date-time>).xlsx` before any row moves, a copy of its own for every
assignment. `/api/rows` carries it, with `op` of `assign`, `preview` for the card and `restore`
for the undo, and a page in front of a server that has not been restarted says "Restart the server
to finish this update" and does nothing else. The participant then reloads in place the way it does after
a trim, on the passage he was on, the first row that kept the original speaker when that was the
passage assigned from, with the player untouched and the playhead marked again.

The progress file moves with the rows, row states, edit records and the last passage saved all
through the one re-key the trim uses, and the assignment goes in under `assignments`, beside
`edits` and `trims`: the sheet and the row, the kind (`assign`, or `merge` when rows became one),
the offsets, the two speakers, the text of the rows before and after, the backup and the time. That
is what reconciles the workbook with a participant rebuilt from its raw source later. The themes file moves
with the rows in the same request, every board and every revision, so a merged passage's cards stand
on the one row after the cards of the passage it joined, the way its statements stand in the cell, and
the undo puts them back on their own row, in their PETs.

**Undo.** `Cmd + Z` reverses what the app itself did, several levels deep and newest first: a key
quote taken with `Q`, an empty quote filled emptied again and a pair it added going with it, a
pair taken away with its Remove,
put back where it stood, a passage corrected in place with
`E`, which goes back through the same endpoint and re-keys the highlights again, a timecode
corrected in the margin, the same entry carrying the old and the new timecode, words assigned to
another speaker with `C`, a split or a merge reversed as one step, and a trim cut at either end. An assignment is undone on the server from its own archive copy:
the rows it made go, the rows it replaced come back cell for cell, values, rich text, styles and
heights, and the progress file is re-keyed back and the record marked undone. A statement, key
quote or note written since into a row the assignment made is appended to the restored passage,
never dropped. Redo applies the assignment again from the offsets it recorded. A trim is undone
the same way from its own archive copy, and redone with a fresh cut (see Trimming the ends).
An interviewer note kept is one entry with its row and the old and the new text: `Cmd + Z` writes
the old text back through the same route and opens the note on that row again, and `Cmd + Shift + Z`
writes the new.
A replace, of one occurrence or of all of them, is one entry with its batch id, its passage the first
row it changed on the sheet on screen: `Cmd + Z` writes every row's old text back through
`/api/replace-undo`, puts a highlight it dropped back on the words it covered and marks the records
`undone`, and `Cmd + Shift + Z` applies it again from the same records. Either is refused whole when
a row it changed reads otherwise now.
`Cmd + Shift + Z` puts it back. Every entry knows its passage, so undoing one that belongs somewhere
else goes to that passage first and then reverses it there. The reversal reaches the workbook and the
progress file as well as the screen, because a quote already saved is saved again without it. Past
sixty steps the oldest goes, where from 14 October a quote `Q` replaced was held on the stack while
its passage was open, and since 16 October `Q` replaces none. Undoing a quote leaves its
pieces selected in the passage, so a second `Q` takes the same quote again. Its line says so, "The
quote is out, and the pieces are still selected." or for a pair `Q` added "The statement is out,
and the pieces are still selected.", and a pair put back with Remove's undo says "The statement is
back.", where until 16 October they said pair and marked, and marked now means a quote shown in
its passage. Typing in the fields keeps the
browser's own undo: while the field you are in took a keystroke more recently than anything on the
app's stack, `Cmd + Z` belongs to the field. The stack is in memory for the open workbook and goes
when another one opens.

**Light, dark or the system.** Appearance, as the Mac names it, is a setting under Settings, General,
three radio rows, Light, Dark and Same as this computer, each ticking from its whole row and applied
the moment it is ticked, with no Save (16 October). Until then a button on most bars cycled the three
states with a glyph for each, and Search strategy and Trace carried it while Experiential statements,
PETs and GETs did not, so it left every bar (see One title bar). Same as this computer is what a
fresh browser starts in: it follows the appearance set in macOS and changes with it, no reload.
Light and Dark hold whatever the machine is doing. The choice is kept in this browser under its old
name and values, `system`, `light` or `dark`, and a choice stored before this, of two states, is
still honoured. Sift's PRISMA flow, which draws its own colours, draws again on a change. In both appearances the small grey type, a timecode, a count or a line of fine
print, stands out from its paper at 4.5 to 1 or more, and a card that could not do what was asked
says why in the amber of a warning, never the orange of a crux (15 October). The orange of a crux
and the amber of a warning read at 4.5 to 1 or more as words too, the orange a shade deeper in
light, and in dark the orange is Excel's own, so the bar beside a chosen row never reads as Maybe's
amber.

**Trimming the ends.** Every recording opens with consent talk and closes with scheduling and
goodbyes. Those passages are transcribed and are not data. The row's menu, from a right-click anywhere
on a row or from the small control in its margin, ends with the two cuts, "Cut this passage and 3
before" and "Cut this passage and 11 after", each with the number of rows and the timecodes they cover
under it. The passage the cut is made at is always one of the rows cut, which "Cut this and everything
before", as the entry read until 30 September 2026, left him to find out. Choosing one goes
straight to one card, **Trim the transcript**, which carries what decides and nothing more: the
line naming the cut, "Cut 4 rows: this passage and the 3 before it, 00:00 to 01:35." or "Cut 12 rows:
this passage and the 11 after it, 13:12 to 14:09.", with "this passage and the one before it" for two rows
and "this passage only" for one, a line when any of those rows carries a statement, a note, a quote
or a workbook highlight, an orange run of the workbook's own, named as Find and replace names it since 17 October,
later, where the line said a highlight. Enter cuts, Esc cancels. With both ends offered the card takes the room to
hold its three buttons on one row wherever the window has it. `T` opens the same card on the passage being worked on with both ends offered, the cut toward
the nearer end of the sheet on the filled button and the other end beside it, each button saying
its cut the short way, "Cut this passage and 3 before". The workbook is
copied to `_Archive/<stem> (pre-trim <date-time>).xlsx` before a row goes. Whole rows are cut on one sheet,
so the sheet stays in sequence, the header row is never touched, and the orange runs, widths, freeze
pane and zoom of the surviving rows come through unchanged. The progress file is moved onto the rows
that survived, edit records and all, through the same re-key an assignment uses, and the
trim is written into it as a record. The themes file moves with them in the same request, every board
and every revision, and a card on a row that was cut goes under its board's `cut` list with the
trim's id, its PET, its discard and the picks on its row, which the trim's undo puts back where
they were. An edit record on a row that was cut stays in the file, marked
`cut`. A field typed into and not saved is saved first. The participant then reloads in place, so a cut at
the front can renumber the rounds, on the passage he was on wherever it has moved to, or on the nearest
passage left when it went with the cut, and the line under it reads "4 rows cut. Cmd + Z puts them back."

A trim is one step of undo, in order with the rest of the stack, rather than a clear of it.
`/api/trim` answers with its record: an id, the sheet, the direction, the first and the last row
cut, the count, the backup and `undone` false, beside the boundary timecode and the first words the
record always kept. `Cmd + Z` hands the id to `/api/rows` with `op` of `untrim`: rows open at the
place of the cut and take the cut rows back from the backup, values, rich text, styles and heights,
the way an assignment is put back, and the rows that survived only move, so a statement, quote
or note written on them since stays where it was written. The header row is never touched and no
cell gains a fill. The progress file is moved back with the inverse of the trim's re-key: the row
states, the edit records no longer marked `cut`, and the last
passage saved where it was before the cut when nothing has been saved since. The record stays, marked
`undone`. The participant reloads in place, on the passage he cut from when he has not moved since, and
otherwise on the passage he is on. Two cuts from the top come back newest first, and an older trim on a
sheet is refused while a later one on it stands. So is an undo whose rows beside the cut no longer
read as the backup reads them there, because the sheet has been changed some other way, and nothing
is written. The trim's re-key never moved an assignment record, which stays in the numbering it was
made in, the numbering its own undo reads, and the stack takes a later trim back before it reaches
an earlier assignment. `Cmd + Shift + Z` cuts again with a fresh call on the same sheet, row and
direction, which makes a backup of its own. A page in front of a server that has not been restarted
gets no id back from a trim, and `Cmd + Z` then says "Restart the server to finish this update" and
does nothing else.

**Round complete.** With Work in rounds ticked, a round is done once every participant passage in it is decided: saved with a
statement, saved empty, skipped or passed. It closes by itself. A save of its last passage closes it at
once. A round closes once, so the card shows once for it: a save on the last passage of a round already
recorded moves on as any save does, with no card, whether or not the participant is marked complete. Every move, a save or a skip included, closes each round below the passage it lands on that is
done and not yet recorded, so a round whose last passage was passed closes as soon as a passage in the
next one is decided. Opening a participant closes every such round quietly, with no card, which is what
closed the rounds finished before a passed passage counted. Each goes to `/api/round-complete` once,
oldest first, and the server records it only when it finds the round done too, so a page working
from stale numbers cannot add to the tally. A round closed on open counts toward today's tally even
when its passages were read on an earlier day, because today is when the count was taken.

Confetti, one line, and the numbers: rounds done, rounds left, and the time left at the measured
pace, for the round just left, or for the last of several closed at once. The confetti comes in
three levels, each running longer and throwing more than the one before: six cannons at the left
and right edges, at a quarter, a half and three quarters of the window's height, spray inward and
upward a beat apart from the bottom up, for about three and a half seconds when a round closes,
about five when the round closed finishes a sheet, and about seven, with two more cannons at the
top corners firing down, when it finishes the participant. A level fired while one runs replaces it,
nothing is drawn over the card, so its words stay clear, and nothing at all under reduced motion.
Its pieces take the app's own tints, the crux orange among them, in the appearance on screen.
The target line under them is one sentence, "1 more round today meets the target.", or the target
met and the streak.
The pace is minutes of clock time per completed round, taken from the gaps between saves with
anything over five minutes counted as a break rather than work, and with the seconds the window
spent hidden or out of focus taken off the gap before that test. Nothing is shown before the first
round is finished. The daily target is 2 rounds by default, with a streak across days, and "2 rounds
to today's target" in the top bar, in a window 1440 pixels wide or wider, counts rounds closed today, however they closed. Nothing anywhere
counts statements: zero on a passage is often right.

Until a round has been timed, the pace figure is a sentence in the small type, "measured after the
next round", rather than a number in the numeral face. Rounds closed on open carry no time, which is
what leaves a participant in that state. When the round closed is the last one in the participant, the card is the
participant-complete card: the round's own kicker, the title "Participant complete.", the rounds done and left with
no pace beside them, the line "Every passage of this participant is decided." ahead of the target sentence,
and Take a break beside Back to the participant list in place of a Next round there is not, with Mark complete
after them as the filled button. Enter presses it. The phase is then marked (see Complete), the
button goes, the card reads "Experiential statements marked complete, 3 Oct 2026." with a small tick,
and Back to the participant list becomes the filled button. A participant already marked shows that line and no
button, and a page in front of a server that has not been restarted shows no button at all.

In a participant with more than one sheet the card counts the sheet the round closed on. Rounds done and
Left on this sheet are that sheet's, the time left at his pace is the time left on it, and the
kicker names the round by its number on the sheet. When other sheets remain, one small line sits
under the figures, "Then the 2d sheet, 5 rounds.", the next sheet in workbook order with rounds left
on it and the rounds left there. When the round closed finishes its sheet and the participant is not
finished, the card is the sheet-done card instead, with the second level of confetti: the kicker
"Initial sheet done", the title "The 2d sheet is next.", the figures Rounds on this
sheet, Sheets left and the time left at his pace on the rest of the participant, the target sentence as on
any round, and Take a break beside Next sheet, the filled button, which goes to the next sheet's first
undecided passage the way the switcher does. Enter presses Next sheet and Esc is Take a break. The card never speaks of stopping, which is his
call: Take a break closes it and says the next round or sheet is there when he is ready. The round
that finishes the last sheet shows the participant-complete card as above. The summary the server sends
carries `sheetRounds`, every sheet's rounds, rounds done and left and minutes left at the pace, with
`sheetsDone` and `sheetsLeft` for the participant, and every round carries `on_sheet`, its place on its
sheet. A participant with one sheet reads exactly as it did in every number and every line, and a page in
front of a server that has not been restarted finds none of these and draws the card as it always
did.

With Work in rounds off a round closes the same way, quietly, with no card and no confetti, and the
count still flashes on the move that closes it. The card comes only for the round that ends its sheet
or the participant, with the same confetti and Celebrations governing it. The sheet-done card keeps its
kicker, "Initial sheet done", and its title, "The 2d sheet is next.", with two figures,
Passages on this sheet and Sheets left, no target line, and Take a break beside Next sheet. The
participant-complete card reads "Every passage decided" over "Participant complete.", with two figures, Passages
decided and Sheets, no target line, and Take a break and Back to the participant list with Mark complete as
the filled button until the phase is marked, as above (15 October). Take a break on the participant-complete
card says "A break at the end of the participant."

**Today's haul.** Take a break, on the round card, the sheet-done card and the participant-complete card,
closes the card and, where it stood, shows one quiet line in the card's style for about four seconds
before it fades, "Today: 3 rounds, 47 passages, 1 h 12 min.": the rounds closed today in the participant, the
participant passages in them and the time measured on them, the seconds the pace counts. A click or a
key takes it away at once and does what it always does. The figures come with the summary,
`todayRounds` with `todayTurns` and `todaySeconds` beside it, a round counting on the day it closed,
as the tally counts it. A figure the server does not send, as one that has not been restarted does
not, is left out of the line, "Today: 3 rounds.", and so is a time under half a minute. With Work in rounds off the rounds are left out, "Today: 47
passages, 1 h 12 min.". The line at the foot that says the next round is there when he is ready stays
as it was. Under reduced motion the
haul shows and goes without the fade, and with Celebrations off it never shows (see Celebrations).

**The two bars.** The thin line under the top bar is the whole participant, with Work in rounds on or off: participant passages decided,
saved, skipped or passed, over all the participant passages in it, so it moves on every Next, every
Skip and every passage passed. Beside "passage 9 of 16 in this round" in the top bar, which is the place of the
passage in front of him, a short bar of the same thin line, 40px long, is the passages decided in that
round over the passages in it, shown only with Work in rounds ticked. Both are drawn in the green of a
decided passage's bar at the edge of its words, since they count decided passages, and never in the
crux orange, which on this screen marks a crux and a quote alone (16 October, later). Each carries its numbers in a tooltip: "80 of 108 passages decided", the
bar's own word since 16 October, where it said done, and "9 of 16 done in this round". The round after them, "round 2 of 4", is the sheet's (see Sheets), and in
a participant with more than one sheet its tooltip carries the participant figure, "round 6 of 9 in the participant".
The thin line stays the whole participant, "2 rounds to today's target" stays rounds however they fall
across the sheets, and the pace stays minutes per round. The summary the server sends carries
`turnsDone`, `turnsTotal` and, for every round, its decided and total passages and whether it is
recorded, beside every key it always carried, and a page in front of a server that has not been
restarted counts from the states instead.
Once every participant passage is decided, and once the phase is marked complete, the bars give way
as Complete says.

**The round clock.** With Work in rounds ticked, the clock in the top bar is the time he has spent on
the round in front of him. Each round keeps its own count of the time at this screen while the passage in front of him is
in it. The seconds the window spends hidden or out of focus are left out, so it stands still within
a second of his leaving and goes on when he comes back. Moving into a round shows that round's
count, 00:00 the first time, and going back to an earlier round resumes its count where it was, so
a step back to check a passage never wipes the round he is on. Its tooltip names the round: "Time on
round 4 so far, the time away left out." A small circular arrow beside it, Reset the clock in its
tooltip, sets the current round's count back to zero and touches no other. It has no key. Opening a
participant clears every count. The pace keeps its own count of the time away, which
starts again at every save, so the pace and the round card's figures are as they were.
Nothing about the clock is saved anywhere, so a reload starts it again.

**Complete.** IPA is iterative and a statement can always be revised, but working through the
transcript to write the statements is a phase, and it ends. This mark is that phase's, the
statements', and the PETs phase has a mark of its own (see The Current board). Whenever every participant passage in the
participant is decided and the participant is not marked, the round text in the top bar, "passage 8 of 8 in this
round" with the short bar and "round 5 of 5", gives way to one quiet control, "Every passage decided ·
Mark complete", the words the participant-complete card's kicker uses (16 October), underlined like Reset demo, with the numbers in its tooltip. That is how a participant finished
before this came in is marked on its next open, and the participant-complete card offers the same (see
Round complete). Pressed from the bar, it fires the third level of confetti once, the level the
participant-complete card opens with. Marked, the bar shows "Statements complete" with a small tick in the
app's green and the date, "3 Oct 2026", in place of the round counts and the short bar. The thin
line under the bar goes, its 2px kept in the paper so the band keeps its place, and "2 rounds to
today's target" goes, while the round clock stays. The tooltip carries the time it was marked
and the numbers, "39 of 39 passages decided · round 3 of 3", decided as the line under the bar says
it (16 October), and with Work in rounds off the place,
"Juno, passage 39 of 39", gives way the same way and the tooltip carries "39 of 39 passages decided"
alone. A click on it opens a small card in the trim
card's style, Statements complete at its head: "Marked complete on 3 Oct 2026 at 14:05.", one line, "Statements can still be revised.
Reopen puts the counts back.", and Reopen, the filled button, beside Cancel. Enter reopens, Esc
cancels. Reopen clears the record, the line under the bar and the target come back, and with every
passage still decided the control stands where the mark stood.

Passages stay editable while it is marked. Next and Skip work as they always do, and a round already
recorded is not recorded again, so a save on the last passage of a recorded round moves on with no
card, as it does in a participant not marked (see Round complete). A passage that becomes undecided while it is marked, which an untrim
can bring back, leaves the mark where it is and brings the counts back beside it, the round text,
the short bar and the line under the bar, with the mark reading "Complete · 2 passages undecided", so
nothing is hidden. At narrower widths the mark gives way with the rest of the bar: "Statements
complete" becomes "Complete" below 1440px and the date goes below 620px, and a mark with
passages undecided reads "Complete · 2 undecided" below 1140px, keeps its tick alone below 940px, and
below 760px stands beside the counts with no rule between. Beside the mark the place takes its short
form at every width, "passage 9 of 16 in round 4" with no speaker's name (16 October).

The record is `complete` in the progress file beside the workbook, `{"at": "<iso time>"}`, and
absent until he marks it, so a progress file written before this reads as not complete.
`/api/complete` takes `{"workbook": ..., "op": "mark" | "reopen"}` and writes that key and nothing
else: the progress file is read as it sits, the one key is set or taken away, and it goes back in
the shape the app always writes it in, so every other byte stays as it was. It never touches the
workbook. Marking a participant already marked keeps the first time, reopening one that is not marked
writes nothing, and a progress file that cannot be read is refused rather than written over. The
summary the server sends carries `complete`, the time or null, and the rows and the workbooks
under Files carry it too. A page in front of a server that has not been restarted finds no `complete` and draws the
bar as it always did, and a page from before this sends nothing new. PETs says nothing about this
mark, and keeps a mark of its own in the themes file. Reset demo puts it back as each demo participant
ships: each of the three pristine progress files carries its mark, since the demo is a finished project.

**Settings.** One card, about 760px wide and never wider than the window less its gutters, the same from
Home and from every screen, with its categories down the left and the chosen one on the right. Each
app's Settings holds its own categories, and the chosen one takes its rule in the app's colour. Idiograph's
are General, Language and formats, Experiential statements, PETs and AI features (since 5 November a project's own settings are in Project settings, see Project settings).
Sift's are General, Language and formats, Databases, Projects, Zotero and AI features (see Sift's manual), and
Trace's General, Language and formats, Projects and AI features (see Trace's manual). General and Language and
formats are the same in all three. General: Appearance, Light, Dark and Same as this
computer, applied as each is ticked (see Light, dark or the system), then in Idiograph's own window Text
size (see Text size), then Celebrations, Updates and Closing. Language and formats: see Language and formats. Appearance is kept in the app's own settings as well as in the browser, so Sift's and Trace's
first start take it from Idiograph's.

Experiential statements holds what the statements screen uses: the interviewer, then Work in rounds, a
tick off on a new install, with the line "Work through the transcript in rounds of about 10 minutes of
talk, with a daily target and a streak, to keep a long interview at a steady pace." under it, and the
transcript minutes in a round and the rounds a day under it only while it is ticked, then under a small
heading, View, Larger current passage, the columns shown and how the statements and the notes stand,
side by side or stacked, the column widths, and Minimap, its Auto, On and Off, which rule the boards' map
too and which Save writes only when one has moved since the card opened, so a choice made in the menu
since is never put back (see View), then Nudges, the nudges on a statement as it is typed, each one a
tick box with a small circled i after its label, the length nudge's "word count past the statement length"
using the open project's number (see Statement length), and with AI features on, under AI, the Experiential
statements prompt and its test bench. PETs holds what the PETs screen alone uses: one line of small type
saying the on-screen guidance is `themes_guidance.md` beside the app, then under View the Status bar
tick, and with AI features on, under AI, its own model for the suggested titles, Same as Experiential
statements unless another is chosen, and the key when only this screen needs it. AI features comes last (see AI features). Since 5 November 2026 Settings holds the app's own settings alone, the
same on Home and inside a project: GETs' rules, a project's name, question and the rest are in that project's
Project settings (see Project settings), and the exports are the boards' Export menus'.

Every key in `config.json` stays where it was, the nudges under `nudges`, and the PETs screen's model is
`pets_provider` and `pets_model`. The most PETs a New AI board proposed, under `themes` as `cap`, went with
New AI board on 11 November 2026, and a file that holds it keeps it unread. Each screen's own settings open
the card on its own category: the Settings on Home on General, the statements screen's cog on
Experiential statements, the PETs and GETs screens' cogs on PETs, Sift's cog on its
Projects and the searches' Settings on Databases, and Trace's cog on its Projects. A line that names a choice made in Settings names its category, "as
chosen in Settings, General". The category chosen holds while the card is open, and the next open goes
to the screen's own category again, so nothing about it is kept in the browser. Below about 700px the list becomes a row of tabs over the content, and
Experiential statements says Statements with its whole name in its tooltip, the row wrapping on a phone,
and each field narrows with its row and stops short of the scrollbar, so none loses its right edge. Below
480px each label stands over its field. Save at the foot saves every category, and writes a project's
file only when its name, its question or its tick has changed. Over a demo participant, Projects shows the demo's own values read-only, under a line saying the demo's
project is fixed. A page in front of a server that has not been restarted since this came in shows
"Restart the server to finish this update." in place of what the server has not got yet, and the rest of
the card, Save included, works as before. Opening the page reads the settings and writes nothing to
`config.json`, and starting the app writes nothing to it either, unless a setting it needs is missing,
and then only that setting (see `docs/internals.md`, Settings file).

**AI features (experimental).** Each app's last category in Settings (21 October). It opens with a short
paragraph on why these features are not advised, each app's own, in plain type with a rule under it: guidance
on AI in research is changing, AI makes mistakes, what you ask about goes to the provider you choose, and the
advice is to keep them off unless you are researching AI. Then one large slide switch, AI features, Off or
On, turns every AI feature of the app on or off. A new install starts with it off, and a settings file that
has it keeps its value. Turning it on first shows a small card over Settings, AI features (experimental),
with a fuller warning in each app's own terms: not recommended for most analysis, learning to do it by hand
matters if you are new to it, AI makes mistakes and can sound surer than it is, what you ask about leaves
your computer for the provider you choose, and you may need to acknowledge its use when you publish. Its two
buttons are Back to safety (keep off), the default, which Enter and Esc both press, and I understand the
risks, turn on, plainer beside it. Save keeps it, as `ai_suggest`. While it is on, in this order: Provider, a line saying where
the passages go, the Address for a provider that has one, API key with Check key beside it, Model (Deployment for
Azure OpenAI), then a switch for each of that app's AI features, ticked until you untick it. Check key
asks the provider which models the key can use: "This key works." and the Model list filled with them, or
"This key was not accepted." and the list left as it was. An accepted key typed in the field is stored, each provider's its own and
the three apps sharing it, and with the field empty Check key checks the stored one. A refused key says who
refused it and why, in the amber, "Mistral refused the key (HTTP 401)." Idiograph's features are Suggested statements for a passage, Suggested
titles for a PET and Suggested titles for a GET. Sift's is AI proposals in
screening, and Trace's AI passages for each claim. A feature unticked shows none of its controls and asks
no model, and the server refuses its calls. Off, no screen shows an AI control, tab, menu entry,
shortcut, tooltip or line: no AI suggest or AI suggest PET titles, no
`N` row in the shortcuts, no AI sentence at the foot of Guidance and no statement's short id, and the
server refuses every call to a model. Settings then shows the switch, its line and Using your own AI agents (below) and nothing else about
the AI, neither the provider, the model, the key, the prompt and the bench, nor the PETs model,
nor Sift's AI proposals, nor in Project settings the agents' tick, their guide and Add Idiograph to Claude
Desktop, and it asks the server nothing about them. The record of what an AI made stays whatever the
switch: "with AI" after the name of a board an agent made, the reason an agent gave under a card, and History. At the end of the
page, whether the switch is on or off, Using your own AI agents says you can work with your projects through
AI agents you already use, such as Claude Code, OpenAI's Codex or Google's Gemini CLI, through the app's command line and MCP server, and gives a
box of words to paste into the agent, with Copy: where this copy of the app keeps its command line, its MCP
server and its guide for agents, and to run every change as a dry run first and show you the result before
it writes. The paths are this install's own, the Mac app's, the Windows app's or a copy run from source. On, every
feature shows as before.

**An agent waits for your yes** (27 October). When an agent asks to delete a board, put an old revision over
one, replace words across every participant, cut passages off a transcript, take a statement off the boards,
rename a participant's folder or send the whole project, nothing happens yet. The line in the top right, where
a change made in a conversation shows, says so: "Claude Code is waiting for your yes: delete Board 2 of
Juno." It shows on the statements screen, on PETs and on GETs, and with two or more waiting it says how many.
Review opens a card with the agent's name, the question, what the agent says you asked, "Claude Code says
you asked: ...", in its words, and what it would do. Those are the agent's words, not yours: the card shows them
on one line, with no hidden characters, no quotation marks and no working links, and cuts them short past 300
characters, as it does a replace's find and put words. Approve does it, and History names the agent, approved in the app. Decline does nothing but add a line
to the board's History, and the agent is told when it asks. Either way the line then says what happened,
with its cross to close it. Esc closes the card and the action still waits. If the board changed since the
agent asked, the card says so and shows what it would do now.

With more than one waiting (1 November), Review opens one card listing them all under what the agent says you asked, a row
each with what it would do, the agent and when it asked. Every row is ticked as the card opens, but for one
that changed since the agent asked, which says whose, "Mabel's boards changed since Claude Code asked." Details opens a row's own card under it. Untick a row to
leave it waiting, or use Tick all and Untick all at the head. Decline and Approve name how many are ticked,
Approve 10, and answer them in order. The card then says how many were done, 9 of 10 approved and done, with
a line for each, and why any was not done. The ones you did not tick still wait. Review the 2 waiting opens
the card again for those, and Done closes it, the line in the corner saying how many still wait. Your own
answers never count as a change: ten deletes on one participant go through together. Only a change made
since the agent asked by something else, another window or another command, leaves one waiting.

While Approve or Decline answers a list (11 November), the card gives up its rows and buttons for one line, Approving 4 of 13
or Declining 4 of 13, and a bar that fills as each one finishes. Nothing on the card can be changed until the last
is done, and Esc does nothing meanwhile. The actions go one at a time, in the order shown. If one cannot be done, the
card then says which were done, that one with its reason, and that the rest still wait for your yes. One action
approved from its own card says Approving... under what it would do only when it takes longer than half a second.

On Home, a project with actions waiting says so on its card, in orange, "13 actions are waiting for your yes", and
nothing shows for a project with none. Press the line and the project opens on its first participant's PETs screen,
with the card for the waiting actions open. Home counts them each time it is shown.

Under Using your own AI agents, **Dangerously
skip permissions** is off on a new install. Ticking it asks first, I understand the risks, turn on, or Back
to safety. On, agents no longer wait, and History says the agent did it without asking. It shows whether AI
features is on or off, as Using your own AI agents does.

**The agent log.** Under Dangerously skip permissions, the Agent log line says how many entries it holds
from the last 7 days, "12 entries in the last 7 days", with Open, or "Nothing in the last 7 days." Each time
Idiograph refuses an agent, through its command line or its tools, an entry is kept: a project that does not
allow AI agents, a command it does not have, one only you do in the app, one given the wrong way, one refused
inside a project, and an action you declined. Turning Dangerously skip permissions on or off is an entry too.
Open shows them in a card over Settings, newest first, a line each: what was asked and in which project, why
it was refused and when. Details opens the agent, the project, the command, the refusal and what the agent
says you asked, with Copy. A project that does not allow AI agents is never named, only counted. The same
refusal again within a minute adds to the one entry. The log keeps the last 7 days and drops what is older
by itself, so it never needs tidying and nothing clears it. It is kept in the app's own folder beside its
settings, never in a project, so it never goes with a copy you send or a note you send us. It never keeps what
an agent handed in, only the command's flag names. Agents read it, never change it.

Sift and Trace each keep an agent log of their own, the same way, under Settings, AI features, Using your own
AI agents: each time that app refuses an agent, the review or the project by its folder's name, never a record,
a claim or anything the agent handed in. Each is kept beside that app's own settings, never in a review's or a
project's folder, and one app's log never shows another's.

**Restart and Quit.** A short section at the foot of Settings, at the left of Save, carries Restart
Idiograph and Quit Idiograph, so neither waits for a double-click on the app. Each saves what is
pending first, the passage's fields, an interviewer note and the canvas's last save, as a move does.
Restart shows Restarting. The server waits for any write in hand, answers, closes its port and
starts again in the same process with the same arguments, so the pid file a launcher keeps still
names it, and the page reloads itself once the server answers again. Windows cannot run a program
again in the same process, so there the server starts anew as a process of its own, in run.bat's
window from source and through its launcher in the Windows app. It comes back to the screen it
was on, the same participant and passage, PETs or GETs on the same board, and to Home only when that
participant or board is gone. Quit says "Idiograph is
closed." with how to open it again, by the way it was started: from Applications for the Mac app,
the Start menu for the Windows app, Idiograph.app in the app's folder, or run.command, run.sh or run.bat. The restart line, "Restart the
server to finish this update.", carries the same Restart wherever it shows, since a page newer than
its server is when a restart is needed. A server from before them has no such route, so the line
stays as it was, with no button, and the foot of Settings shows it in place of the two. Both
answer the server's own page alone, never a page served from anywhere else. With the tick under
Closing on, the server also quits by itself a few minutes after its last tab closes (see Closing).

**Text size.** In Idiograph's own window, under General in Settings before Celebrations, Text size has
three rows, Small, Medium and Large, and the one you tick applies at once to every window. It is the same
as View's Bigger Text, Smaller Text and Actual Size, and the two keep in step: Medium is the actual size.
A size the keys have left between the three, 110% for one step up, ticks none of the rows and the heading
says it, "Text size: 110%". Picking a row sets it again. The window keeps it for the next time. When the keys
or View's items change the size, a line at the foot of the window says it for a few seconds, "Text size 110%",
and again at each step. Picking a row in Settings does not say it, since you see it there. In a browser's tab
the browser's own zoom does this, so the rows and the line do not show (20 October, 30 October).

**Language and formats.** A page of Settings of its own, after General (28 October 2026), the same in all three
apps: Language, then Dates, Times of day and Numbers. Each starts on Same as this computer, with what this
computer gives beside it, and each choice is written as an example of itself: Dates 28 Oct 2026, Oct 28, 2026 or
2026-10-28, Times of day 14:05 or 2:05 pm, Numbers 1,234.5, 1.234,5, 1 234,5 or 1’234.5. The one you tick applies
at once: the page loads again and comes back where you were, Settings still open on this page. The order of a
date is the setting's, the month's name the language's. Every date, time of day and number the app shows follows
them, a board's History, Mark complete's day and time, Updates' last check, Sift's
dates, counts and kappa, Search's count, and so do a print view's date and the interviewer notes file's Exported
on. The end card's time left and the break's line say a length of time one way, 45 min, 1 h or 1 h 25 min, where
the end card said 85 min and 1 h 30 before. Under Language, "Help translate Idiograph into your
language." opens a page on translating the app, which the app carries.

**Language.** Language has three rows: Same as this computer,
with the language the app reads in on this computer beside it, then English (UK) and English (US). The one you
tick applies at once: the page loads again in that language and comes back where you were, Settings still open.
English (US) changes only what American English writes otherwise, colour as color, centre as center, ticked
as checked, dates as October 28, 2026 while Dates is Same as this computer on an American one, and the window's menus are the same in both (28 October 2026). In Trace it writes judgement as judgment (1 November 2026). The
Shortcuts card's X reads Set the selection aside in both, the words of the boards' sidebar, where until 28
October it read Bin the selection.

**Celebrations.** Under General in Settings, after Appearance, a small heading, Celebrations, carries a
switch for each of Idiograph's screens, Experiential statements, PETs and GETs (20 October), all three on
by default. Each stands for its own screen's confetti and counts: on Experiential statements the
confetti, the count after each passage and today's haul on a break, on PETs the statements left and the
confetti when the last is placed or the PETs are marked complete, and on GETs the PETs left and their
confetti. Unticked, a switch turns off its own screen's and leaves the others. A settings file from
before the three, with its one Celebrations switch, reads as all three as that switch said. Sift and
Trace keep the one switch. The line under the switches names what is celebrated, with Work in rounds off
"Confetti at the end of a sheet or a participant and when a board's last card is placed, the count after
each passage and the cards left on a board." and with it ticked the same line starting "Confetti at the
end of a round, a sheet or a participant", following the tick as it stands in the card.
Sound, off by default, plays a soft tick on every step on that decides a passage, a short two-note
chime when a round closes and a longer one when a sheet or the participant is done. The chime goes with the
confetti, so the last statement placed on the PETs screen brings the longer one, and the PETs count
itself is silent. Sound plays only with a Celebrations switch on, and its tick greys while all three
are off. Ticking it plays the tick once, so its loudness is known. The sounds are made in the page with
the Web Audio API, quiet and with no audio file, the tick under 200ms, and reduced motion leaves
them alone. Save writes them to `config.json`, as `celebration_screens`, `celebrations` (on while any
screen's is) and `sound`, and a page in front of
a server that has not been restarted, which knows neither, reads Celebrations as on and Sound as
off. The days in Home's head are a record rather than a flourish, and stay whatever the tick says.

**Updates.** In Idiograph's own window, on a Mac, Windows or Linux, a small heading, Updates,
stands under General before Closing (18 October), and a copy run from source in a browser shows nothing
of it. Its first row is the version you have, "Idiograph 0.9.1", with What's new beside it, which opens
that version's notes. Then two ticks, Check for updates and Download updates without asking, which
waits on the first, and the line "Once a day Idiograph asks GitHub for a newer version. GitHub sees your
internet address and version number, never your work." With it on, Idiograph checks
a few seconds after it opens and once a day while it is open. Check now asks at once, whatever the ticks
say, with the last check's time beside it, as "Last checked today at 14:05", and a line under it says
what the check found: that this is the newest version, that a newer one is available, its download under
way, or that it is ready. A check or a download that fails says why in one amber line: that GitHub could
not be reached, that its answer could not be read, that the update could not be downloaded, "Idiograph
could not confirm the update is genuine, so it was not installed.", or that Idiograph could not put it
in place. Each update is
signed when it is made, and Idiograph keeps one only when its signature holds against the key built into
every copy, so nothing but an update its author made is ever installed. Save keeps the two ticks, each
only once it has moved.

The first time Idiograph opens, Home asks once, at its head, "Check for updates?", with the
line about what checking sends under it and two buttons, Check and Don't check. The answer is the tick
under Updates, and the question never comes again. With Download updates without asking off, a newer
version is offered at the head of Home, "Idiograph 0.9.2 is available.", with Download and
Later, and while it downloads the line says how far it has got. Once it is ready the line says
"Idiograph 0.9.2 is ready. Relaunch to use it.", with Relaunch now and Later, and Settings shows Relaunch
now too. Relaunch now saves what is typed first, as Restart Idiograph does, says "Relaunching
Idiograph.", then installs the update and opens the new version where you were, on Windows with a small
progress bar while it installs. Should what you typed not save, it says "Your last change could not be
saved, so Idiograph did not relaunch.", and should the relaunch itself fail, "Idiograph did not relaunch.
Quit it and open it again." Later hides the line
until Idiograph next opens, and the update installs as Idiograph quits, so the next time it opens it is
the new version.

**What's new.** The first time a new version opens, a line at the foot says "Updated to Idiograph
0.9.2." with What's new and a close mark, once. While it shows Home leaves room for it at its
foot, so its last line, Add transcripts on a project's page, scrolls clear above it, where until 18
October that line stayed partly under it at 360px. What's new opens a sheet of the notes of every version
since the one you had before, newest first (29 October 2026), so going from 0.9.10 straight to 0.9.13 shows
0.9.13 and then 0.9.12, each under its own number and date with a plain line for each part, Sift, Idiograph
and Trace. The versions scroll inside the sheet, with Done always at its foot. Under the last, Earlier
versions adds every older version below, newest first. The sheet opens again from Settings, General, What's
new beside the version, and from Help, What's New in Idiograph on a Mac and What's New on Windows, with the
version you have first and Earlier versions under it. While an update is waiting to install, What's new in
Settings shows that update's own notes first, then the version you have. The notes come with the app, so they
open with no internet. Sift and Trace show their own.

**The Preview Edition (21 October).** While Idiograph is in preview its lockup carries a stamp, PREVIEW EDITION in
the crux orange, tilted a little, under the end of the name, as the launch video shows it. The mark and the name
stay as they are. The stamp stands on Home's head, where the lockup is a little larger than before, at the top of
About Idiograph, which opens on the lockup in place of its name, and beside the mark on every title bar, small,
where it and the mark are one button that goes Home. On a phone's width the bars drop the stamp and keep the mark.
Sift and Trace carry no stamp. When the preview ends the stamp goes from every place at once. Right under the
lockup on Home, so the stamp and what it means stand together (22 October), a quiet panel says what the preview means: an early proof of concept, not fully tested or reviewed, not for
anything important, your data could be damaged or lost so keep copies, not yet a replacement for the software
you use day to day, and tell Adam what you think with the bug button or by email, and, since the preview is
private, "Please keep it to yourself for now: don't share it or post about it." (29 October). A small warning sign
in the crux orange stands at the start of its first line. It goes with the stamp.

**The mark coming in (22 October).** When Idiograph opens on Home, the mark at its head comes in, in one
movement: the two square brackets turn round each other and land while the dot drops and bounces into place,
the two coming to rest together, and the name fades in as the brackets turn. Then PREVIEW EDITION is stamped
on. It takes under two seconds, once each time the app opens, and Home can be used while it plays. With
reduced motion turned on in your computer's settings the mark simply stands still.

Since 23 October that is one of seven ways the mark comes in, a different one each time the app opens: every one
plays once before any plays again, and never the same one twice running. In Pong the brackets are paddles in a quick
rally, moving only up and down, the dot a ball as in the first video games, with angled shots and last moment saves. In Pinball they are flippers: the dot rolls down the left one nearly to its end, which flips it up to three faint bumpers
above them, and on back and forth, each hit lighting a run of neighbouring letters of the name. In the anagram the name arrives as GO RAPID HI, stays that way for a moment, and the brackets sort it, lifting and carrying letters into place. In Football
they kick the dot to each other, one heading it on the way, in the kiss the dot holds them together until it pops out, and in the race all three
hurry to their places: the right bracket sprints in from beyond the window's right edge, the left close behind, both running on
over the tops of the letters, and the left overtakes the right just before the finish. The dot comes third, a ball
thrown hard from beyond the window's edge that bounces off the G and the right bracket's top arm, losing pace at
each, and drops quickly into the middle. Since 23 October the spin's brackets come
in from further out as solid things, fading in as they come, their arms turning away from you and back as they
circle each other and come down onto the page. Each ends on the mark as it always stands, then the stamp, within
four seconds, the anagram five and a half.

**About Idiograph.** A card with the app's name, the version you have, its author, Adam Knowles, the
licence and the acknowledgements. A copy built from the code between releases names its build after the version,
"Version 0.9.23, build e45b1af", and a note from Send feedback carries it too. The licence's line says "© 2026. Free and open source under the GNU AGPL v3,
with no warranty. github.com/Pharkie/idiograph", and GNU AGPL v3
opens the licence's full text, which comes with the app, in a window of its own, and the address opens
the code's home on GitHub in your browser (21 October). Sift's and Trace's About cards say the same with their own
names. The acknowledgements: thanks to Curt Strangward for his article on IPA in ATLAS.ti, with its
reference, and for testing early builds of Idiograph on Windows, and the line "Adam Knowles made Idiograph
working with Claude Opus 5.5, an AI model by Anthropic, in Claude Code." It opens from About Idiograph at the foot of Settings, in a browser
tab or the window, from the Idiograph menu on a Mac and from Help on Windows (20 October). Its links out
of the app open in your browser. Done or Esc closes it, and Settings is still there when it was opened from there.

**Support Idiograph.** "Other ways to help", after Ko-fi's button on Home, and Support Idiograph, beside About
Idiograph at the foot of Settings, open a card of short parts (28 October). Under its heading it says Idiograph is
in a private preview, to keep to yourself for now (29 October). Cite it gives the citation with
the version you have in place of x.y.z, "Knowles, A. (2026). Idiograph (Version x.y.z) [Computer software].
https://idiograph.app", and Copy. Translate it is the line under Language, Send feedback opens Send feedback,
Contribute code says the code is open to change and build on, and links to it on GitHub, Fund
it says what the app costs Adam, in pounds, with Ko-fi's button, and Thanks says who can be named in the
Acknowledgements. Sift's and Trace's cards say the same with their own names. After your first Word export of PETs, the note it leaves says
once, under a thin rule, "Idiograph is free. If it helps your work, there are ways to support it.", the link
opening the card. It never shows again.

**Closing.** Last under General in Settings, a small heading, Closing, carries one tick, "Quit
Idiograph a few minutes after its last tab closes", on for a new install (16 October). Idiograph is
a small server on your computer and its tab is a window onto it, so closing the tab alone used to
leave it running until Quit. With the tick on, it quits by itself about five minutes after its last
tab closes, the way Quit does, every write finished. Something still running holds it, a Sift search
run, a Zotero sync, an AI request, a save or a backup, or a Restart, and the five minutes start
again once it ends. A tab left open in the background keeps it running, and so does an AI agent
working through the running app. Opening Idiograph again starts it at once. A tab that comes back to
it after it has quit, as one the browser put to sleep can, says "Idiograph is closed." with how to
open it again. Off, it runs until Quit. Save writes the tick to `config.json` as `quit_when_closed`,
and it holds at once, with no restart.

**Databases.** Sift's own category in its Settings, after General and whatever AI features says,
holds your own list of the databases Sift searches (see Sift's manual, Search strategy),
empty on a new install. Add takes one of the databases Sift knows, Scopus, Web of Science, PsycInfo,
CINAHL, PubMed, Europe PMC, OpenAlex, Embase, ProQuest Dissertations & Theses and Google Scholar, or
Other with its name, and each row keeps its place in the order you added it. PsycInfo and CINAHL
carry their platform, EBSCO, Ovid or ProQuest, EBSCO unless you choose another, since each writes
its own string. Scopus, Web of Science, PubMed, Europe PMC and OpenAlex choose By API or By export,
and the rest go By export. A row By API shows its key fields: Scopus's API key and its optional
institution token, Web of Science Starter's API key, OpenAlex's and PubMed's optional keys, which
raise their limits, and none for Europe PMC. A key field never shows the key, only Saved or Not set,
in the faint ink since 17 October, where the browser's own grey read under 4.5 to 1, as Folder did on New
project and Name on Set columns.
Save beside it puts the key in the macOS keychain as the Anthropic key is kept, under
`ELSEVIER_API_KEY`, `ELSEVIER_INSTTOKEN`, `CLARIVATE_API_KEY`, `OPENALEX_API_KEY` or `NCBI_API_KEY`,
so a key already there shows as Saved at once, and off a Mac in the `.env` file. Remove deletes it,
and Check sends a search for one record with the key and says in one line whether the database took
it. Remove at the end of a row takes the database out of the list. Save at the foot writes the list
to `config.json` under `databases`, never a key. On Search strategy, each database's cog, on its row
under Searches, opens the same platform, By API or By export and keys under its name, and Add
database adds to the same list, each written at once.

**A Sift project's own parts.** In Sift's Projects category, which Sift's cog opens, a row of the Sift
projects' names, when there are several, each name for its project's newest screening, the screening
open on Sift's screen first. Under it stand the project chosen's own parts: PDFs, Find open-access PDFs with your email for
Unpaywall, whatever the AI switch says, and with the switch on its AI proposals and the bench (see
Sift). Sift's own settings card is gone, so every setting of Sift is here.

**Zotero.** Sift's category before AI features, whatever AI features says, since a sync calls no model: Library, your
own or a group's, which asks for the group's id, and the key. Your own library is the one the key
belongs to, so no user id is asked for. To make a key, sign in at zotero.org and open
Settings, Security, Applications, then Create new private key, with Allow library access and
Allow write access ticked, and for a group library read and write access to that group. The key goes in through Settings
alone: its Save puts it in the macOS keychain under `ZOTERO_API_KEY`, as every key is kept, and off a
Mac in the `.env` file, and the field shows only Saved or Not set. Remove deletes it. As soon as the
key is saved, and whenever the library or the group's id changes, Sift asks Zotero for the key's own
record and the library's name and says in one line whether the key works, "The key works with the
library of" and your Zotero name, or what stands in the way, in the amber when Zotero refuses the key or
a Save or Remove fails, as every line in Settings that says something failed is since 17 October, later,
where it stood in the small print's grey. Save at the foot writes the library and
the group's id to `config.json` under `zotero`, never the key.

**The PETs model.** Under AI in the PETs category, Model offers Same as Experiential statements
first, the default, then every Anthropic model the Experiential statements select offers, then the
local models when Ollama answers, then the models of the other provider chosen for Experiential statements,
each with its provider's name, "mistral-large-latest, Mistral", each labelled as it is there. A line of small type under it names
the model the PETs screen uses now, "Uses Haiku 4.5, the Experiential statements model." or "Uses
Opus 5.5.", and follows both selects as they change. AI suggest PET titles and AI suggest GET titles
ask it. The test bench stays on the
Experiential statements model. With Local under Experiential statements and an Anthropic model for
PETs, the key row stands under the PETs model instead, the same field and the same keychain item.

**Send feedback.** For a tester to send Adam a quick note, a bug or an idea, with no email. A small
bug, a quiet line icon with no sparkles since it is not the AI's, sits at the right of every top bar, just before the cog, Send feedback in its tooltip, so it stands in one place on the Experiential statements, PETs and GETs bars, and since 16 October on Sift's, Search strategy's and Trace's and at the head of Home beside Settings, where until then the statements, PETs and GETs bars alone had it (see One title bar).
A press opens one card in the trim card's style, Send feedback: a box of a few lines, "A bug, an idea,
a shortcut you missed", a line under it, "Your name or email, if you want a reply", which can stay
empty, one line of small type, "Sent with the app's version, your system and the name of this screen.
Nothing from your participant goes.", and Send beside Cancel. Esc cancels, `Cmd + Enter` sends and so does Enter in the reply line,
and Send is greyed while the box is empty or holds only spaces, and comes on with the first character, so
`Cmd + Enter` with nothing written does nothing either. While the note travels the button says Sending. A note sent
closes the card and the line at the foot says "Sent, thank you.", and a failure says why in one line
in the card, the words still in the box. The words stay in the box while the app is open, so a card
closed by mistake loses nothing, and only a note sent clears it. A long note scrolls up and down in the box and
never sideways, at any zoom, where in the Mac window at a zoom above 100% the empty box drew a sideways bar until
29 October. The note goes only when Send is
pressed, and exactly this travels with it: the words, the reply line as typed, the app's version
(`VERSION` in `server.py`, 0.9.1 for now), the system in plain words with Python's name for it,
"macOS 26.5, darwin", the browser's user agent string, one short word for the screen
it came from, and the time. The word is `home` on the first screen, `project` on a project's page,
`statements`, `pets`, `gets`, `sift` for Sift's Screening, `searches` for its Search strategy, or
`trace`, from a fixed list the server and the collector both keep, and any other word goes as none,
never the page's own text (16 October, where until then only `statements` and `pets` were kept).
Settings has no bug of its own, since it opens as a card over a screen. The app adds nothing else to what he types. Never a participant, a file name, a
path, a participant's words, the key or the settings, and never a screenshot, the clipboard or
anything else from the page. The page posts
`{"text", "contact", "screen", "agent"}` to `POST /api/feedback`, which refuses a GET, and the server
adds the rest and posts the JSON on to the collector through `urllib`, as the AI calls go, with a
15-second wait. It answers with the row's id, or with one line: an empty note is refused, a note over
8 KB is too long to send in one go, a collector out of reach says "The note could not be sent. Check the
connection and try again.", and one that answers anything but 2xx says "The note could not be sent just
now (HTTP 503). Try again later." with its status in brackets, never the collector's own answer (17
October, later). The collector
is Adam's own, a Cloudflare Worker on the free tier writing each note as a row of a D1 table, which he
reads with `notes.sh` (see `feedback-worker/README.md`). Its address is `FEEDBACK_URL` in `server.py`,
the Worker's `workers.dev` address with `/v1/feedback` after it, and `feedback_url` in `config.json`
stands in for it on one machine, an http or https address alone. With neither, the bug is hidden on every bar and the
route answers "Feedback is not set up in this build." `/api/cases`, `/api/open` and `/api/themes`
carry `feedback`, true when there is an address, and a page in front of a server from before this
finds none and keeps the bug hidden.

**Export.** The PETs board's Export menu, Markdown and CSV, or an agent's `participant export`, writes every statement in the participant to
`<case>/Working/<stem> - All Experiential Statements.csv`, in the format of the reference CSV: a
byte order mark, `Interview,Timestamp,Experiential statement,Proposed PET (blank for you)`,
timestamps as HH:MM:SS, then a last column, `Quote`, each statement's own quote without the
marks the workbook keeps round it, empty when it has none (`Key quote` until 22 October). The PET column is empty for a participant with no
themes file. A participant with one has the column filled from the board current on its PETs screen:
each statement carries the labels over its card, top-most first and joined with ` / `, "PET" or
"PET / Sub-theme", `Set aside` for a card set aside (`Discarded` until 19 October, `Binned` until 20 October), and nothing for a card not placed. Its rows
then go PET by PET in canvas order: each PET's statements in the order the canvas
reads them, top to bottom and left to right along a row, a sub-theme's where its frame's top sits
among the PET's cards, then those not placed and last the discarded, both in transcript order. A participant
with no themes file keeps transcript order throughout. The PETs board's Export menu, Markdown and CSV,
writes that board's markdown draft and the same CSV (see PETs, Export), the canvas saved first. Settings'
Export pane, with its Export all statements to CSV and Export the PET draft, went on 5 November 2026, and an
agent writes the CSV alone with `participant export`.

Under Markdown and CSV in that menu a tick, Include interviewer notes (in Settings' Export pane until 5
November 2026), off until ticked and remembered in the browser under `idiograph-export-notes`, makes it also write
`<case>/Working/<stem> - Interviewer notes.md`: a heading with the participant name, one line with the date
of the export, then the notes in transcript order, sheet by sheet, the sheet name as a heading only
in a workbook of more than one sheet, each note under its timecode as HH:MM:SS with one blank line
between notes. The line on screen then says "40 statements and 3 interviewer notes written" and
names the notes file with the other two, and a participant with no notes writes no file and says so. The CSV
stays statements alone in the reference format, and the PET draft is as it was.

## PETs

The IPA step after the statements: a participant's experiential statements grouped into personal
experiential themes on a canvas, which Miro and Freeform did until now, tried as named boards
side by side, each with its history, with the quotes that carry each PET picked in the sidebar beside the canvas and the
grouping exported as a PET draft.

**Opening it.** Each annotated participant's row has a PETs half, and its workbook under Files a quiet PETs, a
workbook open in Excel included, and the Experiential statements bar carries the PETs tab (see Idiograph's
tabs), which `P` outside a field opens too. From the statements screen a field typed into and not saved is saved first and the recording stops.
Back, the browser's Back, a mouse's back button and Cmd + [ on a Mac (Alt + Left
Arrow on Windows), returns to where the screen was opened from, on Experiential statements, PETs and GETs alike:
the participant list, fetched afresh, Experiential statements on the passage he was on, or the GETs it was
opened from (the arrow at the left of the bar went on 26 October). Forward, the mouse's forward button
or Cmd + ] (Alt + Right Arrow), opens again the screen you came back from, the passage opened from the same
card, or does nothing where that is not possible (19 October, Adam's mouse button on a passage he had opened
from a PETs card). What you were typing is saved on the way. The shortcuts card (?) lists
Back and Forward under Moving about, and on PETs and GETs under General, each key as the machine names it.
A project's page is a screen of its own in that history too (20 October): Back from it, a mouse's back
button among the ways, returns to Home, and Forward opens the project again. In Idiograph's own window on
a Mac the mouse's two buttons work as they do in Safari. Home is one click from every screen: Idiograph's
mark at the left of the statements, PETs and GETs bars is a Home button, and so are View, Home and Cmd +
Shift + H (Alt + Home on Windows). What you were typing is saved on the way, and a canvas that cannot be
saved keeps you where you are. The top bar reads, left to right, Idiograph's lockup, which is the Home button, the tabs, Experiential statements or ES, PETs in front, and GETs (see Idiograph's tabs), then on the right Export, Search, the bug for Send feedback once it is set up and Settings (see One title bar). Under it the band holds the project's name, with the demo tag on the
demo, and the participant by its pseudonym with a small chevron (see Another participant's PETs), and the toolbar under the band the sidebar's button, the board switcher and its save state, "Board 1 ·
Auto-saved", the Canvas and Table switch, the tools, and at its right end Inspector, the sidebar's button (6 November, see The band since 6 November 2026). Inspector is the standard panel icon in the rail toggle's style, a frame with its right part filled, pressed in while the sidebar is open (see The sidebar). Until 19 October the counts, Sticky note, Group, Undo and the shortcuts stood on the bar too, and at exactly 1280 it took two rows. They went to the status bar and the palette (see The status bar and the palette), and the bar stands on one row at 1280 and wider. Under the bar runs the band the statements screen carries, Research
question and the whole question in the serif, the same band from the same project file, and the canvas
takes its height off its own through the same `--band` measure. With no question set it says so and
points at Project settings, as the statements screen's does. `/api/themes` carries `project` as
`/api/open` does, and a server from before it sends none, so the band says there is no question yet.

**Statements left.** An act that takes statements out of Not placed, into a PET or a sub-theme or
onto the pile, raises the count of those left over the middle of the canvas, "4 left", in the ink since 17 October,
later, where it stood in the crux orange, the passage
screen's count (see The count) in the same face and the same 850ms. When the last statement not placed
goes, the third level of confetti fires, the participant-complete card's, and one line stands in the
count's place, "Every statement placed.". The counts before and after the act decide it, so an act
that leaves Not placed as it was raises nothing, and an undo or a redo that brings a statement back
raises nothing either. On the GETs board the count is of the study's PETs and sub-themes in no GET, one with no card on the board counted as well, and one whose every card is in the bin not, so "Every PET placed." stands only when it is so, and an act that only bins raises nothing (20 October: Select all and the bin raised it, and so did going back and forward). Nothing is written, since it is the page alone. It takes no pointer and no
focus, under reduced motion it never shows, and Celebrations in Settings silences all of it.

**The bar at narrow widths.** The bar keeps to one line and gives way in order, as the statements screen's
does. The participant name truncates with an ellipsis at any width, with the whole name in its tooltip, and
so does the board's, though both only once the counts have stepped down, each keeping its first
letter and the ellipsis so neither is ever cut through a letter (17 October). At any width where the
participant's or the project's name or the board's would still be cut once the counts have gone, the bar
takes two rows: the way back, the tabs and the tools stay on the first, with the counts beside them again where they fit, and the mark, the names and the board
move to a row of their own under them, so on a phone 360 wide "Juno", "Living with a dog" and the
board's name read whole at their usual size (17 October, later), and so does a long name on a desk.
Wherever everything fits, the bar keeps one row, on PETs and GETs alike. Where it runs a little short, before it takes two rows, the save state keeps its mark alone and then Experiential statements reads ES, so the board, its save state and the Canvas and Table switch stay on the one row after the tabs, at 1280 and wider even with long names (23 October). On the second row, where it is needed, the switch stands inside the bar. A name too long even for the
second row ends there with its ellipsis, the whole name in its tooltip. The way back is a
place and no tool, so on PETs and on GETs alike it never takes a tool's box, at rest or under the
pointer, its arrow going to the ink under the pointer (17 October). Nothing in the bar is
the AI's, so the switch makes no difference to it. Below 900px the save state keeps its mark alone,
with the words in its tooltip, below 740px the counts go, and since 18 October no word stands beside the
way back to go below 560px, as the words Experiential statements did until then, the arrow saying where it
goes in its tooltip at every width. At the statements screen's
620px step the gaps close up, the rule before the board staying on PETs and GETs so "GETs" never runs into
the board's name as one phrase (17 October, later), and at its 480px step the buttons slim. The tabs keep
their words at every width, Experiential statements reading ES below 1280px, and at 760px and below they
take a row of their own (see Idiograph's tabs). The icons at the right of the bar stand as the statements screen's
do, 4px apart where the bar's other items stand 12px, 3px apart below 620px and 2px apart below
480px, the bug for Send feedback among them. Measured on 5 October 2026 on Rowan's participant opened
from Experiential statements, the bug and the Current board's ribbon counted, the bar needs 896px at
its fullest, 833 with the save state's mark alone, 577 without the counts and the GETs link of the time, which
went together below 740px, 537 once the gaps close up, 400 without the words on the way back and 335
with the buttons slimmed. The ribbon takes 16px of each, and the bug 30, 29 once the gaps close up
and 22 once the buttons slim. So the save state's step sits 4px above the 896, just above 740px the
counts still show a little over half of themselves, and just above every step both names keep their
whole width. Down to 400px nothing overlaps and nothing scrolls sideways. Until 5 October 2026 the
bar also carried the Inspector's button, Board's button and the shortcuts at its right, 60px more,
and its widths stand where they stood. On 16 October Group, Undo and the shortcuts came to the bar, and
measured again on Rowan's participant opened from the participant list, with its longer workbook name, it needs
879px at its fullest, 813 with the save state's mark alone, 546 without the counts, 506 once the gaps
close up and 398 with the buttons slimmed, so the widths stay where they were. Measured again on 18 October with the steps of the time and Sticky note on the
bar and no word beside the way back, on Rowan's participant opened from Experiential statements, it needs 975px at
its fullest, 836 with the save state's mark alone, 673 without the counts, 652 once the gaps close up and
522 with the buttons slimmed, so it kept one row down to about 670px and took its two rows below it, the
steps on the first with the way back and the tools. Since 20 October the tabs take that place, and at 760px
and below the bar stands on the three rows of Idiograph's tabs. Below 480px Sticky note,
the first tool since 18 October where Group was, takes them all to the right edge, the participant's name and the board's give way in full to
their ellipses, where their small share of the shrinking left the bar 50px past a phone 360 wide, and
the save state shows a failure alone, so the names keep a few letters at 360.

**Another participant's PETs.** The participant picker in the PETs tab is a switcher, in the board switcher's style: the
name, a small chevron, and a click opens a menu under it with every participant of the project
that has a themes file, listed by pseudonym, the participant on the screen ticked. Under each
name sits the board it opens on, its Current board with the ribbon when it has one and else the board
last open, and at its right Open as table (see Print). A click on another participant saves anything still to
save and opens that participant's PETs at once, on that board, with the way back going to the participant list, so
two participants' boards are a click apart and never a trip through the participant list and the statements screen. Opening
one writes nothing in its themes file, and the file names the board as the one last open only once he
changes something there. The demo is a project of its own and lists its three participants, Juno, Rowan and
Mabel, each whether it has a themes file or not. Esc closes the menu,
and so does a click anywhere else. The list is asked for each time the menu opens, through
`/api/themes-cases`, and a page in front of a server from before it says "Restart the server to finish
this update." in the menu. Each other participant also carries Open beside this one, over Open as table,
which splits the canvas and puts that participant's board beside this one, read-only (see Open beside this
one, under GETs).

**Cards.** One card per experiential statement: every line of column C, on every sheet, keyed by
sheet, row and line, `Initial:12:0`. A card is 200px wide and carries the statement in the serif
and the row's timecode under it in the code face, the way the project writes its timecodes, as the
player's clock does. A long statement stops at four lines, with the whole of it in the card's
tooltip. A card from a sheet after the first carries that sheet's name, small. A double-click on a
card opens its statement for editing on the card, as a double-click on a PET's title opens the title,
and so does a double-click on its statement in the Inspector (see Editing a statement). Go to the
passage in its right-click menu opens its passage on Experiential statements (see From a statement to
its passage). Since 20 October a first open puts nothing on the canvas: every statement waits in the
sidebar's Not placed in interview order (see The sidebar). Put all on the board, or New board, all on the
canvas, lays them in a compact pile in the middle of the canvas, the margin between neighbours, which
until then was every first open.

**The canvas.** Miro's model, which he knows. The wheel zooms about the pointer, from 15% to 250%,
and so does a pinch. A sideways wheel, the thumb wheel of a mouse such as the MX Master or a
trackpad's sideways swipe, pans left and right, and so does the wheel with Shift held, and the wheel
with Alt held pans up and down. Space held with a drag pans, and so does a drag with the middle button. A
plain drag on empty canvas draws a lasso and selects every card and label whose middle falls inside
it. A click selects one card or label, and a click on empty canvas clears the selection, as Esc
does. Shift or Cmd adds, Ctrl on Windows and Linux: with a click it adds one card or label to the
selection or takes it away, and with a drag it draws another lasso over what is selected already,
inside a PET's frame too, so statements scattered across the canvas, or inside a PET, can be
picked and then grouped with `G` or taken out with Backspace. A drag on a selected card moves the
whole selection, and a drag on a card not selected selects it alone first.

`H` is the hand: a plain drag anywhere pans, the cursor a hand, and `H` again, `V` or Esc gives the
pointer back. Two small controls at the bottom right, the pointer and the hand, say which is on and
switch between them. Beside them is the zoom: minus, the level, which goes back to 100% when
clicked, plus, and Fit all, which brings everything into view and never closer than 100%. Since 20 October Fit all leaves room for the palette, which floats over the canvas, so no card or frame is left under it, at 360 as at 1280. Each takes the side it costs least: the palette a strip down the left, and the bin a strip down the left or, on a phone, off the foot. Going to a theme, a card or a close pair does the same. The canvas opens fitted, and below 620px the words Fit all go. A board too big to show whole even at the least zoom, 15%, shows its top left there (30 October), where its middle could be blank canvas. The line at the foot stands just over the zoom bar and the bin wherever it would cover them, as on a phone, where until 18 October it hid the zoom bar. The shortcuts button, `?`, sat at the end of the zoom bar, where Figma and Miro keep help, from 5 to 16 October, and stands on the top bar now, as on every bar.

**The status bar and the palette (19 October, Adam's choice A).** Along the canvas's foot runs a status bar, as Excel's and Photoshop's do. Its left holds the board's counts in plain words, each number in the mono face, a count of nothing said too so the counts hold their place. Since 26 October (Adam's wording C) the total comes first and where they are after it, then the PETs: "46 ES: 25 in PETs, 5 stacked, 2 set aside, 14 not placed | 3 PETs", with "3 in no PET" among them when cards lie loose on the canvas. The 25 in PETs count each card once, a stack's top among them, and the statements stacked under a top are counted apart, so the parts add up to the total. On the GETs, LGETs and LPETs boards a card is a PET or a sub-PET, so the count is of cards: "11 cards: 7 in GETs, 1 set aside, 3 not placed | 2 GETs". While anything is selected the count of it follows the PETs, "1 ES selected", "2 cards selected" on GETs, or "3 selected" when PETs or notes are among it. Until 26 October the counts stood apart with no total, "3 PETs", "25 in PETs", "14 not placed", "2 set aside" and "5 stacked". A right click on the bar opens a tick for each, PETs, In PETs, Stacked, Binned and Not placed, in the order the bar says them, and what he ticks is kept at once. A statement stacked under a top counts as stacked, and its top stands for it in the rest. With a count unticked that holds anything, the total goes, "ES: 25 in PETs, 14 not placed", since the parts shown no longer reach it. Its right holds the pointer and the hand, the zoom, Fit all, the minimap's button, Quotes on cards, Close pairs on the PETs board, Notes on cards on the GETs board, and Shortcuts. Since 20 October (from a tester's feedback) the minimap's button reads Minimap beside its icon, Quotes on cards Quotes and Notes on cards Notes, and each gives way to its icon alone where the bar runs short, as Fit all and Shortcuts do, and with the status bar off. It is on by default and turns off from Settings, Idiograph, PETs, View, Status bar, and in Idiograph's own window from View, Status Bar, kept across a restart. Off, the counts go and the tools float at the bottom right as the zoom bar did before, Shortcuts as `?` at its end. Where the bar runs short it gives way in the order Adam set on 26 October, the counts last: first the tools' words, each tool keeping its icon and its word in its tooltip, then a count beyond the total and its parts, such as how many are selected or the close pairs, then the spacing closes up, then the tools go, the pointer and the hand, the minimap's button and Shortcuts, then the zoom's minus and plus, then Quotes, Notes and Close pairs. Only then do the counts go, the PETs first, so at 1280 the bar always says the whole sentence, and at 720, the app's smallest window, the total and its parts still show. In a canvas narrower still the total goes with every part but In PETs and Not placed, "ES: 25 in PETs, 14 not placed", so it never stands over parts that do not reach it, and then In PETs, so no count or button is ever cut off. The bin and the map stand above it, and in the Table view it keeps its counts alone.

**Quotes on cards (19 October, from a tester's reflection on IPA in ATLAS.ti, Adam's way A).** A button of two inverted commas among the status bar's tools, after the minimap's, "Quotes on cards" in its tooltip, shows each statement card's own quote under its statement, inside the card, in italic behind a short orange rule, on the PETs and the GETs boards alike. It is pressed in while the quotes show, off on a new install, and kept across a restart, and with the status bar off it floats with the other tools. A quote runs to three lines at most and the whole of it is in its tooltip. A quote in pieces shows them in order, joined by the ellipsis it was saved with, and a card with no quote shows nothing more. A click on the quote selects the card and shows the quote whole beside it, on its right or left, or under or over it, wherever it covers least of the cards around and otherwise on the side with more room, under Quote and its timecode, with a play button on the PETs board when the sheet has a recording, and Show in passage, which opens the passage as Go to the passage in the card's menu does, Back returning to the board. A double-click on the quote shows it whole as a click does, and edits nothing. Esc, a click anywhere else or the wheel puts it away. The taller cards take their room as a stack shown open does: what stands below a quote in its column moves down as far, and turning the quotes off puts everything back where it stood. That room is a view, so the file keeps where everything stands with the quotes off, and a card let go below a quote stays where it was let go. Since 23 October (from a tester's report) a card moves with the quotes shown only when he moves it or when a move of his sends it clear, and then as far as it would with the quotes off: a card moved a little moves alone, a label that grows sends clear just what it reaches, and turning the quotes off and on again leaves every place in the file as it was. The room for the quotes and for an open stack is made again once the type has loaded, so an open stack keeps its height. Since 30 October (Adam's report: a sub-PET under two side by side kept a large gap under them, and dragging it up pushed them up the board instead) what stands below two or more that grew, a sub-PET under two sub-PETs whose cards both show their quotes, or one with a stack shown open, moves down as far as the one that needs most, never by both together, so it shows as close under them as the board has it, and a drag up brings it to rest a margin under the lower of them with nothing else moving.

**Quotes in three ways, Off, Short and Full (30 October, Adam: "full quotes on each card without having to click anything additional").** Quotes on cards has three ways. Off shows no quote. Short is the quote as above, three lines at most, its whole in its tooltip and a click away. Full shows each quote whole on its card, every piece, with no ellipsis but the ones it was saved with. Each click on Quotes takes the next way, Off, Short, Full and back to Off, its tooltip saying which, "Quotes: off", "Quotes: short" or "Quotes: full". It is pressed in for Short and Full, and after its word a small mark of two lines says Short and one of four lines Full, the room for the mark kept at Off so the tools beside it never move under the pointer. A right click on it, or a press held, opens a menu headed Quotes on cards with Off, Short and Full, the one in use ticked, a choice kept at once and the menu left open as Close pairs' menu is, Esc or a click elsewhere putting it away. The way is kept across a restart, Off on a new install, and a version from before reads Full as Short. At Full a click on a quote is a click on its card, which it selects, and a double-click edits its statement as one on its words does, since there is nothing more to show beside it. Its play button stays in the Inspector, and Go to the passage in the card's menu. The canvas makes room for the whole quotes as it does for short ones: what stands below a quote in its PET or sub-PET moves down, the frames grow, nothing overlaps, the minimap and Fit all take the taller board, and Short or Off puts everything back where it stood. On the GETs board a PET unfolded in place shows its statements' quotes whole at Full too. Quotes has no key. Since the same day Esc puts away the status bar's counts menu and Close pairs' gap menu too, which until then only a click elsewhere did.

**Notes on cards (20 October, from a tester's feedback).** On the GETs board, a button of a page with lines, after Quotes, reading Notes, "Exploratory notes on cards" in its tooltip, shows under each statement card's quote the exploratory notes of its passage, upright in the sans face behind a faint rule, three lines at most with the whole in its tooltip. Several notes on one passage are joined by a dot. It is pressed in while the notes show, off on a new install and kept across a restart, as the quotes are, and the cards' room is measured with the quote and the notes together. It is not on the PETs board, where the passage is one step away, Go to the passage in a card's menu.

**Close pairs (20 October, after supervision, Adam's way B and way 1).** His rule: statements from the same passage of the same sheet stack under the best one unless they say radically different things. A button of two linked cards among the status bar's tools, after Quotes on cards, "Close pairs" in its tooltip, draws a thin dashed amber line between the two cards of every close pair on the PETs board: two statements in the same group, or in the same PET when it has no groups, from the same sheet within a minute of each other by their passages' times. On a sheet with no times a row counts as half a minute, so a minute is two rows. A small dot marks where the line meets each card. When one card stands over the other it is a short straight line from the upper card's foot into the lower card's top. The line keeps to the gaps between the cards and runs under them, so it never crosses a card's words, and it never meets the ⋯ at a selected card's top right corner: where its way passes that corner it stops short of it and starts again beyond, a dot there cut back with it. It is quiet at rest and strong while either card is under the pointer or selected, and its tooltip says how far apart the two are, "12 s apart", "1 row apart", or "Same passage" for two statements of one row. A card close to two others has a line to each, and selecting it, or pointing at it, strengthens both, by design, as it belongs to both pairs, and a card stacked under another is in no pair, so a pair is gone once stacked. The button is pressed in while the lines show, off on a new install and kept across a restart. A right click on it, or a press held, opens a menu of the gap: 15 seconds, 30 seconds, 1 minute, 2 minutes or 5 minutes, kept at once, and under it the pairs marked Not the same, each with Show again. While the lines show, the status bar's counts end with "5 close pairs" and ‹ and ›, which step through the pairs, "2 of 5 close pairs", each step selecting both cards and gliding the canvas to bring them into view. A click on the count steps too. Where the bar runs short it reads "5 close", and in a bar shorter still the ‹ and › and the zoom's minus and plus give way, a click on the count still stepping. A click on a line, or on a dot, opens a small menu headed by the gap: Stack under 12:04 and Stack under 12:16, each stacking the other of the two under the one it names, as a drop on its middle does, one step of undo. Then Not the same, which takes the line off that pair for good, kept with the board and one step of undo, and Inspect both, which selects the two and opens the Inspector on them, one under the other with its time and its quote, Stack the later under the earlier and Not the same under them. Two statements that share a time, or have none, are named by their first words. In the Table view each row of a close pair carries a link mark with the gap, "12 s apart", whose click opens the same menu, Stack the other under this one or Stack this one under the other. Never on the GETs board.

A palette floats at the canvas's left edge, as Photoshop's tools do: Sticky note and Group, then under a rule Undo and Redo, icons alone, each named in its tooltip with its key, "Group (G)", "Redo (Shift + Cmd + Z)". Its grip of six dots at its top drags it anywhere on the canvas, and letting go settles it against the nearer side edge at the height it was let go, a place kept across a restart. While cards are dragged it goes faint, and a drop over it lands on the board under it. The Table view keeps it with Group, Undo and Redo (see Canvas and Table).

**The toolbar (21 October, Adam's choices of 20 October, from a tester, who missed the floating palette and found many things only shortcuts).** The palette now stands docked by default as a toolbar under the research question, on PETs and on GETs, each tool with its icon and its word: Sticky note, Group and Select all, then Auto-arrange, then Align, Left, Centre and Right, Top, Middle and Bottom, then Spread, Across and Down, and at the right end Undo and Redo. Align's six are faint until two or more cards are selected, and Spread's two until three or more. A grip of six dots at its left end pulls it off: drag it, and it floats on the canvas as the palette did, the same tools with the same words in a column, so it reads as one toolbar in two places. Dragged back by its grip, a dashed slot across the top of the canvas shows where it docks, and letting go there docks it. Docked or floating, and where it floats, is kept on this computer for every board, across a restart. On a narrower window it gives way a step at a time and never cuts a word: Select all keeps its icon alone first, then Align and Spread theirs, then every tool its icon alone, and at a phone's width Align and Spread go under a button of three dots, which opens the same eight in a menu. Since 26 October the docked toolbar always keeps Align and Spread under its three dots, as two sections of its menu, and the floating one keeps them in its column while the canvas is tall enough. The Table view keeps Group, Select all, Undo and Redo.

**Align and Spread (21 October).** With cards selected, Align moves them to the edge or the centre of the outermost of them, left, centre or right, top, middle or bottom, the cards not selected staying where they were. Cards that would then overlap move on along the line, in the order they stood, just far enough to keep the margin between them. Spread keeps the first and the last where they stand and spaces those between evenly, across or down, and where they need more room than the two give them the last moves on. A label selected moves with all it holds. Each is one step of undo. The same eight stand under Align in the right-click menu of a selection of two or more, opening beside it as the pointer comes to Align.

**Descriptions (21 October, Adam's idea and his ruling on the drawings).** A PET, a sub-PET and a GET can carry a description as well as its title: the title stays the short version to scan, and the description, longer, sits under it as a secondary heading, smaller and lighter, so the step from the statements up to the theme can be read. A sub-PET's is smaller again than its PET's. On the board the title's card runs wider to show it whole, as wide as what its PET or sub-PET holds and never wider than its frame, so a PET's runs across its own frame and a sub-PET's across the sub-PET's (31 October, Adam: he would rather it were wider than deeper). Where what it holds is narrow, a single column of statements, the card keeps the width it always had. The title wraps at the same width. A description too long even for that takes up to six lines, the rest of it in the title's tooltip and the Inspector, where until 31 October it took two. What stands near a card that grew is moved clear of it, as it is when a title takes a line more. A title with no description runs as before. To write one, double-click the title, or choose Add description in its right-click menu: under the title's box a second box opens, "Description" in grey while it is empty. The boxes open over the title where it stands, its words where they were, and nothing on the board moves while they are open or when they close. Enter keeps the title and the description and closes the boxes in one press, from either box, Tab or Shift + Enter goes from the title to the description and Shift + Tab back, Esc leaves them as they were, and a box left empty is no description at all. Once a label has one, its menu reads Edit description and Remove description, which takes it off in one step that Undo brings back. The same words are in the Inspector, in a box under the title in its head, and written in either place they are the same. There is no limit on its length. It is a field of its own, apart from the label's note. On the GETs board a GET takes one the same way, and a PET's card there shows its PET's description under its title. The Table view shows each description whole under its title inside the heading's band, in the serif and never in capitals, and the print view and the Word document show it under its title too, while Descriptions is ticked. That tick sits under Export with the others, beside Board note on the print view and on the GETs print card, and it is on on a new install and kept as he leaves it. A board with no descriptions looks, saves and prints as before. Since 22 October a description stays through every other change to the board, a rename, a reorder or a move on the canvas, an AI revise, a write by an agent, a revision restored or a PET copied to another board: until then any save from the canvas took every description off.

**The minimap (18 October).** A small map of the whole board stands above the zoom bar at the
canvas's bottom right, Miro's and tldraw's way, as the transcript's minimap stands at the bottom right
of the statements screen (Adam's choice, 17 October). It is a card as wide as the zoom bar and 160
pixels high, and it draws the board fitted to every card on it: each card a small rectangle in the
tint of the PET it stands in, a card in a sub-theme in its PET's own, a card in no PET in the faint
ink, each sticky note on its own paper, and every PET's and sub-theme's frame an outline in its tint. A
discarded card is left out, as the canvas leaves it, and a board of a few cards fills the map's width
as a big one does, where until 18 October it sat small in the middle, never drawn at more than a fifth
of its size. The part of the canvas in view is a box clear inside a solid line of the ink, near white in
dark, with the rest of the map dimmed, as the transcript's minimap draws it, where until 18 October it
was a light wash of the ink with a quiet edge. Where the view reaches past the map the box keeps its
size and the map's edge cuts it, where until 18 October it shrank to the part inside the map. Where it
would reach past the map on every side, as after Fit all, the map draws the view's box whole with the
board inside it as the canvas shows it, where until 18 October the whole map was washed over with no
edge to say where the view was.
A click on the map glides the view there, the place clicked coming to the middle of the canvas, a drag
on the box pans the canvas, a click and a drag together carry on from the place clicked, and the wheel
over the map zooms and pans the canvas as it does anywhere on it. The map is drawn again at most once a
frame, its box on every pan and zoom and the rest as cards move. While a drag lasts it keeps the scale it
had when the drag began and moves only the marks of what moved, what is dragged, what makes way and the
frames that reach out to it, and on the drop it is drawn whole and fitted to the board again (18 October,
where until then it wrote every mark of the board again on every frame of a drag).

The transcript's one setting rules it, Minimap's Auto, On or Off, in View on the statements screen and
under View in Settings, Idiograph, Experiential statements. In Auto the map appears as he pans or zooms, by
the wheel, a drag, the zoom bar or Fit all, and as a board opens, stays while the pointer is on it or a
drag on it lasts, and fades out about two seconds after. On keeps it there, and Off leaves no map and
no button. In Auto and On its button at the end of the zoom bar, the map the transcript's button
carries, "Minimap (M)" in its tooltip, and `M` show the map until pressed again, or while it shows hide
it, in Auto until the next pan or zoom and with On until pressed again. While the map shows the button
is pressed in, on the sunk paper inside a firm edge as the pointer and the hand show the one in use, where
until 18 October only its ink darkened and it read as not pressed. Whatever the button or `M` said
goes when the screen is opened again or the setting changes. Below 768px of window the map and its
button go, as tldraw's does below a tablet's width. The export's line opens over
the map, and below about 900px, where a sidebar lies over the canvas and stops above the zoom
bar, the map gives way while the sidebar is open, where at first its foot showed in a strip under the
sidebar's.

The shortcuts card, `?` or Shortcuts on the top bar, has two groups, headed Experiential statements and
PETs and GETs, with the moving about, the audio and the mouse as small headings under Experiential
statements, and the mouse and trackpad under PETs and GETs. Each row is a key, a key combination or a
mouse act that is not obvious, with a phrase of two to six words in the small sans, on one line where the
card has room and wrapping where it runs short, its key whole beside it, "g ·
Group the selection", "Option / Alt + wheel · Pan up and down". Until 17 October, later, a phrase never
wrapped, and Sift's longer ones ran out of its card. A feature with no key of its own has
no row, and neither has a plain click or drag. Since 5 October 2026 (item 190) the card carries the
mouse acts too: the wheel and the pinch, the sideways wheel, Shift and Alt with the wheel, the middle
button, the double-clicks on a card, a label and the canvas, and the right-click, on the statements screen
the timecode's click and double-click, the text's double-click and the row's menu. Over this screen
it shows the PETs and GETs group alone, with the general row that still applies there, `?` itself,
and not one of the transcript's, a double-click on a card editing its statement (30 October, where from
16 October it read "Go to its passage"), and over GETs it says a statement's passage or another card's
Inspector, as it does there (16 October). Over
Experiential statements it shows both.

**Motion.** Weight you can see, in the register of the Finder and the iOS home screen, and nothing
bouncy or slow. A card or a PET picked up lifts, four per cent and a deep shadow over 120 ms, and
while it is dragged it leans into the way it travels, up to six degrees at full speed, and stands
up again when the pointer stops. A PET dragged by its label or its frame carries its cards with
it, every card leaning the same way as the label, so the whole PET tilts as one body, and the
cards trail the label by 140 ms. A card dragged on its own leans the same way, and so does one dragged
out of the PETs board's sidebar or the GETs Participants panel (21 October): it lifts as it leaves its row,
sways with the pointer, and lands as a card dropped on the canvas does, where it was let go. Several rows
dragged together come as a card each, laid out as they will land, leaning as one. While it is dragged it
leans a step each frame with the pointer and eases only as it stands up, and the trail is worked out each
frame too, where until 18 October each was a transition WebKit, the engine of the Mac window, began again on
every move of every card, which held a drag there to 30 frames a second on the demo's board and 8 on a
crowded one. On the drop it lands
over 220 ms with a visible overshoot, coming down to its own size and standing up from its lean as
it lands, so a drop has settled inside 250 ms. A card or a PET pushed clear by the margin slides to
its new spot over 240 ms rather than jumping, and so do the cards an Auto-arrange gathers, and one
that makes way for a drag slides aside over about 160 ms (see Nothing overlaps). All of it rides on CSS
transforms, nothing in it waits on the layout or delays a save, and with reduced motion set in the
system all of it is off. A drag takes one step a frame, the pointer's latest place, however many moves
the system sends in that frame, and the board's map moves only the marks that moved while it lasts (see
The minimap).

**Nothing overlaps.** Every card, every label and every frame has a margin round it that nothing
else comes to rest inside, one constant, a twentieth of a card's width, 10px on a 200px card,
`MARGIN` in `themes.py` and `TH_MARGIN` in the page. It is the space in the first pile, round a drop,
a nudge, a card put back, a new card, the AI's layout and an arrange. The law holds between
neighbours. On the canvas the neighbours are the cards in no PET and the PETs, each PET by its
frame, so a PET's frame keeps the margin clear of every other PET's frame and of every card in no
PET, and the margin between two frames is the same one. Inside a PET the neighbours are its own
cards and its sub-themes, each sub-theme by its frame, so a sub-theme's frame keeps the margin clear
of the PET's own cards and of the frames of the sub-themes beside it, and the same holds inside a
sub-theme. A label stands inside its own frame, so a label and what it holds never count against
each other, and nothing inside a frame counts against what lies outside it, since the frame stands
for all of it there. A card in no PET is never inside a frame without belonging to it: let go in a
PET's body it comes into that PET (19 October), and one a push leaves inside a frame joins that PET. A sticky note is a neighbour as a
card is, on the canvas while it is in no PET and inside the PET it sits in otherwise, whose frame
runs round it, and a note in no PET left inside a frame comes into that PET the same way (see
Sticky notes).

Whatever is dragged, a card, a sticky note, a selection, a PET with all it holds or a sub-theme, no PET
or sub-theme moves out of its way (31 October, design A, Adam's choice after the drag audit, where a PET
he aimed at ran from the pointer). Only what is inside the PET, sub-theme or group whose body is under
the pointer makes room, and only where a drop would land in it: its own cards and notes, each that comes inside the
margin of what is dragged, a card or a note by its box, a selection by each member's and a PET or a
sub-theme by its frame, sliding clear by the least distance over about 160 ms, never onto a sub-theme
of it or its title, and pushing a third as a frame that grows does (below). The sub-themes in it hold
still, and every title on the board stays where it stood, so a title never runs from the pointer. What
makes room follows the drag live, worked out each frame from where everything stood when the drag
began, so one the drag moves away from slides back to its own spot. On the open canvas nothing makes
room. What is dragged lands exactly where it is let go, what made room stays where it went, and the
drop then settles the rest: a frame that grows, the frame of a PET a member was dragged out of among
them, sends clear what it reaches, which slides there over 240 ms, so nothing overlaps. The whole drag,
what was dragged, all that made room and all the drop sent clear, is one step of undo, and Esc during
it puts everything back. A drop on a title strip takes what is dragged one level under that title (see
PETs): while the pointer is over it that PET's frame is outlined in its tint and nothing moves, and the
drop makes room for it. Let go in a body, what is dragged goes into the PET, sub-theme or group under the pointer at
the line shown, keeping its level: statements and notes into the innermost one (statements since 19
October), a sub-theme into the PET, a group into the sub-theme, and a PET into none (31 October). While
the pointer is in such a body that one is outlined in its tint and its title tinted, it stays where it
is, its own cards make room, and what is dragged shows it is leaving its own. A member let go on the
open canvas, or in its own PET, stays a member without Alt (see PETs), and each frame that holds it
reaches out to it, pushing nothing until the drop. With reduced motion set, what makes room moves
without the slide. A PET, a sub-theme or a group dragged up to its neighbours in its own place, the
last sub-theme of a PET to the ones above it, stops a margin from them and lands there, and none of
them moves (26 October): while it meets them only by a little it rests at that small, even gap, and
pulled further over one it lies over it until the drop settles the two. The line that shows where a drop comes in a theme's order shows only when the drop changes that
order or brings something in. A frame that grows, because a card joined its PET, a
card inside it was moved to its edge, its label was renamed longer or took a note's mark or a pick's
(a pick's since 17 October, later, when a quote picked could take a title onto a line more and over the
card above it), a
sub-theme was made or moved inside it, or it was arranged, stays where it is, and a neighbour it
comes near shifts clear by the least distance, a card on its own and a PET or a sub-theme as one
block with all it holds. A neighbour pushed into a third pushes that one too, for eight passes at
most, and then it stops. A PET's frame follows whatever moved inside it and sends its own
neighbours clear the same way. All of it is inside the one step of undo of the act that caused it. A
statement edited on the canvas that takes a line more settles the same way, its card clear of what it
comes to rest on and its frame sending its neighbours clear (17 October, later). A board laid out where
its words or its type stood another size, a line re-read on open or a PET retitled in its participant and
taken in on GETs that takes a line more, a board from another computer, an agent or a hand, makes room
once the page has measured it, on opening and once the type has loaded: a card or a note resting on a
PET's or a GET's frame, its title among it, goes to the nearest free spot clear of it, and of two frames
the second goes, as a drop there settles, so a title never stands over a card. Nothing is written until
the next act (17 October, later). Since 31 October two cards or notes too near each other make room the
same way, on opening, on taking a change made in a conversation and on a reload, at Quotes Off, Short or
Full: the one that reads first stays where it is and the other moves clear, as when a card is dropped
there, pushing on what it then meets, so a card an agent gives longer words no longer stands over the card
under it until it is dragged. An agent's own changes make the same room before they are saved, with the server's
sizes: what a change moved, made or made taller stays, and what it comes near moves clear by the least
distance, after every `board apply`, after `turn write`, after Find and replace and on the other boards an
edit on the canvas reaches.
A card put back from the pile, and a new line read since the board was made, take the nearest free
spot to the middle, clear of every frame. Sizes are measured on the page, and estimated on the
server for a layout made before the page has drawn: the first pile, a new line, an AI proposal and
a copy. The server's estimates come from the widths of the page's own type, each a little over the
page's and within a margin of it, so a layout the server makes needs no shift when the page draws
it. A note's estimate still makes room for the square it was before it fitted its words, so it runs
wider than the page draws it, and a layout the server makes still needs no shift. A label's estimate is
its title and its marks alone since 17 October, later, where it made room for the count it carried
before the badge, a line more for a title that filled its line, so Rowan's and Mabel's boards in the
demo were laid out again from their source. A revision on view is read-only and shifts nothing. A board saved before this keeps the spacing
it had until something there is moved.

**PETs.** Select cards and press `G`: a label stands above them with a box for its title, Enter
keeps what is typed, Esc keeps the title it had, and a title left blank is Untitled. Group on the bar
does the same (16 October). The cards then
belong to that label. Membership is stored, never read off where a card sits. A label sits above
what it holds, its left edge on theirs, and follows them as they move, and carries its title alone.
Its count is a small badge sitting on its frame's bottom edge at the left corner: the number of its
statements at any depth, 0 when it holds none, in the small sans and not bold, in the PET's tint as
its text and its outline, its corners rounded as the frame's are. Its figures take the PET's own tint a third
of the way to the ink, so they read in both themes, where a sub-theme's lighter step and the paler tints read
faint, and its outline keeps the step (17 October, later). On a card inside a PET or a GET the timecode and
the count of statements stand in the soft ink, which reads on every tint's wash in dark (17 October, later). Half of it lies in the frame's
padding and half in the margin beyond, so it never covers a card, and it never takes a click. A
badge that would lie over a sub-theme's at the same corner steps right past it, and a label with
nothing in it draws no frame and so no badge. The label's tooltip and the Inspector keep the full
words, "3 statements", on a PET over sub-themes "2 sub-themes · 7 statements", and on a sub-theme or a
group over groups "2 groups · 7 statements", the labels it holds itself and the statements at any
depth. Every
PET draws its frame, a faint rounded rectangle in its tint round its label and its members, which
follows them wherever they go, and a frame that grows into a neighbour stays where it is and sends
the neighbour clear by the least distance (see Nothing overlaps). Its cards take its tint, a wash and a rule down the left edge. The
tints never repeat: PETs take eight in turn, each its own, a PET keeping the one its
number gives it while no PET before it holds that one, and a PET past the eight is a neutral
grey rather than a tint already in use. A sub-theme takes its PET's tint a step lighter, and a group a
step lighter again. None of
them is the crux orange.

Drop a card on a PET's title strip, its label, and it joins that PET, and the same on a sub-theme's
or a group's strip at any depth: what is dragged goes one level under the title it is let go on, a
sub-theme into that PET and a PET too, which becomes its sub-theme. While the pointer is over a strip a
drop would merge into, the strip lights in its tint and reads "Merge into" and its title, its frame is
outlined in its tint, and the drop makes what is dragged a member there. No title moves while a drag
lasts (31 October), so the strip stays under the pointer, and the place where a strip stood before it
moved aside, which took the drop from 19 October, is gone. In a body a line in the tint of the PET,
sub-theme or group it goes into shows where it comes in the order that one reads in (see Higher is
better), standing in the gap beside the statement it comes before or after, or lying across the gap
between two rows. Statements and notes let go in a body move into the innermost PET, sub-theme or
group the pointer is in, at that line, at every depth (19 October, Adam on the shots, where one let go
in another PET's body went back into its own), and since 31 October a sub-theme let go in a PET's body
goes into that PET, and a group into the sub-theme it is let go in, keeping its level, while a PET let go
in another's body only moves. On the open canvas each stays in what holds it. Undo is as it was. Drag a label and everything it holds moves with it,
and a drag that starts on the empty space inside a PET's frame, off its cards and its label, does
the same, while a click there selects the PET as a click on its label does. Double-click a label
to rename it: the box keeps the title's width and wraps as the title does, as tall as its words, so a
long title is edited whole. Enter keeps it and Esc leaves it as it was. Leaving a PET is an act of its own: a member dragged anywhere stays a member, and
its frame stretches to follow it live, during the drag and not only on the drop, so a card taken
far shows its frame reaching out to it, and a sub-theme dragged inside its PET stretches that
PET's frame the same way. A frame so stretched pushes nothing while the drag lasts, and the drop sends
clear what it reaches (see Nothing overlaps). A card or a sub-theme leaves its PET five ways: Backspace or Delete
on it selected, or Take out of PET in the Inspector or in its right-click menu, Take out of sub-theme
when a sub-theme holds it, which leave it where it stands without the tint, a drop with Alt held (Option on a Mac), which takes it out and leaves it
where it lands, a drop on another PET's title strip or in its body, which moves it to that PET, and, for a card,
a drop on the sidebar. While Alt is held during a drag the frame lets go of what is dragged and it loses
its tint, so the leaving shows before the drop. Alt joins nothing (31 October): with it held no title,
body or card's middle takes what is dragged, a card, a sub-theme or a PET, which leaves the PET it was
in and lands where it is let go, and no strip says Merge into. Until then a card let go with Alt on
another PET's strip joined it. Each is one step of undo, and the drop settles clear what it lands
beside or over (see Nothing overlaps).

While a card in a PET, or a sub-theme, is dragged, a small tip follows it a little below and to
the right of the pointer, in the small type on a quiet chip: "Hold ⌥ to remove from PET" on a Mac
and "Hold Alt to remove from PET" elsewhere, by the platform. With Alt held it reads "Release to
remove from PET". When what holds the dragged card or sub-theme is a sub-theme, it says sub-theme in
the place of PET, "Hold ⌥ to remove from sub-theme", and group when a group holds it. It never shows for a card in no PET or for a PET dragged by its own label, it goes the
moment the drag ends, and nothing about it is saved.

A right-click on a card or a label, or inside a frame for its label, opens a small menu in the
style of the statements screen's row menu, for that one item: Take out of PET when it is in one, or Take out of
sub-theme or Take out of group by what holds it, then on a label Auto-arrange, Rename and Note (see PET notes), then Set aside on a card, X at its right, and Delete this
label on a label. Esc puts it away, and so does a click anywhere else. The same menu opens from "⋯",
a small round button on a selected card's top right corner, clear of its words, as a selected sticky
note carries its cross, and on a label at its top right corner, beyond its cross, showing with the label's
other small controls, so nothing there is reached by the right-click alone (16 October). On a label it stood in
the title's line until 17 October, later, and took a long title's room there, so a GET's title wrapped onto a
line more than its board leaves it. The entries that take
something away, Delete this label and Delete note, are red with a bin, as every
Remove and Delete is. Take out of PET, of GET, of sub-theme or of group (Remove from PET until 20 October,
when a tester read its bin as binning the card) is a move: since 20 October the card goes back to the sidebar's Not placed, `Backspace` at its right, beside
where it stood, and the entry carries an arrow out of a frame in the ink.

**Group and Ungroup (20 October, from a tester's feedback).** A right-click on a card offers Group, which
does what G does with what is selected, the card alone when it was not selected, and Ungroup when the
cards selected are the whole of one PET, GET, sub-theme or group and nothing else, which deletes its label
and keeps the cards where they stand, as Delete this label does. Each is one step of undo.

**Auto-arrange.** The small grid beside the cross on a label, and the entries in the Inspector and in its
menu, all read Auto-arrange and tidy the PET's cards under its label in a compact block, rows about as wide as the
square root of what is in it, the margin between them, keeping the order they read in now, top to
bottom with ties broken left to right. Each sub-theme is arranged inside its own frame first and
then set in the block as one piece where it read. The label stays where it stands, and so does the
PET, and a neighbour its new frame comes near shifts clear by the least distance, as it does for
any frame that grows. It is one step of undo.

Since 21 October Auto-arrange has three ways, each with its icon: Grid, the block above, Column, one card
above another in the order they read down the PET, which carries its hierarchy, each sub-theme kept whole
as a block in its place and arranged the same way inside, and Row, all side by side. On the toolbar a click
on Auto-arrange repeats the last way, its icon on the button, and its small arrow opens the three, the last
one ticked, a choice running at once and kept for the button on this computer. The toolbar's Auto-arrange
tidies each PET or label selected, or the one a selected card is in, and with nothing selected every PET on
the board, in one step of undo. The control on a label and its menu entries take the last way too.

**Higher is better.** Inside a PET, higher means a better example or better quotes, so the canvas is
read top to bottom and left to right along a row, statements whose tops sit within half a card's height
counting as one row. The PET draft, the print view, the Word document and the CSV list a PET's
statements in that order, and put a sub-theme where its frame's top sits among the cards (see
Export, Word document and Print).

Select labels, or labels and cards, and `G` makes a label over them: the same object one layer up,
which is how sub-themes are drawn. A label at the top of the canvas is a PET, a label inside a PET a
sub-theme, and a label inside a sub-theme a group, with groups inside groups as deep as he likes, and
the Inspector, the counts, the menus and the exports name each so. A board from before groups had a
name reads the same way, with nothing lost. A PET or a sub-theme dragged nests in another on that
one's title strip, which reads "Merge into" and its title while the pointer is over it, "Merge into
Mornings", and the drop makes it a sub-theme of a PET, or a group inside a sub-theme or a group, at any
depth. A sub-theme let go in another PET's body goes into that PET as its sub-theme, keeping its level,
and a group into the sub-theme it is let go in, while a PET let go in another's body, or beside it, only
moves (31 October). Nothing it passes moves out of its way. The strip says it the moment the pointer is on it and goes the moment it leaves, at the drop, and
over the strip of the theme that holds all that is dragged already, where nothing would merge. Until 18
October a PET or a sub-theme nested wherever the pointer was more than the margin inside another's frame,
under a large Merge across that frame. A sub-theme stays in its PET
wherever it is dragged on the open canvas until Take out of PET in the Inspector takes it out. Cards that all sat under one label make a label inside
that one, in their place, so a sub-theme drawn out of a PET stays in it. A label never goes
inside a label it holds. Select a label and press Backspace or Delete, or use the small cross on it,
and the label goes: what it held stays on the canvas, in the label above it where the deleted one
stood, or standing free. Nothing else is lost. With cards and labels selected together, Backspace
does both in one step.

**The sidebar: Not placed and Set aside (20 October, Adam's way A).** The bin went on 20 October, after
A tester's feedback that PETs had two places for what is off the board, the Not placed pile and the bin, where
GETs keeps what it has not placed in its Participants panel. The PETs board now has a sidebar of its own at the
left of the canvas, as GETs has, its button, Statements, at the left end of the bar, the panel icon with
its left part filled, pressed in while it is open, with the count of statements waiting beside its name.
Its cross sits at its head, then a search over its statements, then two sections. **Not placed** holds the
participant's statements not on the board, in interview order, each with its time first, a sheet after
the first under its own name, and its count at the right of its head. A stack waits as one row at its
top's time, with "2 stacked" under it, and a statement whose line has gone from the workbook comes last,
under Missing from the workbook, with Remove. A statement an agent left out with a reason has it under it in
the small type, and so does one a New AI board left out before 11 November 2026. **Set aside**, pinned to the panel's foot and folded until he opens it, holds what the bin
held, each with Put back, which sends it to wait in Not placed, its count at the right of its head. Every
board from before opens with its binned cards under Set aside, and the file keeps them as it did.

The canvas holds only what is placed. A row of either section drags onto the canvas: let go in a PET's
body or on its title strip it goes into it, and let go on empty canvas it lies there loose, on the board
but in no PET yet, to be grouped, as slips lie on a table. Rows select as the Table view's do, a click, Shift
for a run and Cmd for one more, and the rows selected drag together, the first under the pointer with how
many on it, the rows left as faint outlines while they are in the air. Let go back over the sidebar, or
press Esc, and nothing changes. Put all on the board, under Not placed's head, puts every statement waiting
on the canvas as one pile in the middle of what is in view, his own way of starting ("chuck all on the
canvas"). A card dragged from the canvas onto Not placed waits there again, and onto Set aside is set aside.

Take out of PET in a card's menu and `Backspace` send a card back to Not placed, at its own time in the
order, the row lit for a moment and the list scrolled to it, and on a card loose on the canvas `Backspace`
and Back to Not placed in its menu do the same. `X` and Set aside in a card's menu set it aside, and Set
aside's head lights for a moment when it is folded. A stack's top taken out takes its stack with it.
Set aside is never emptied and nothing on this screen deletes a statement. The menu shows each entry's key at
its right, Backspace and X. On the status bar "5 not placed" and "1 set aside" open the sidebar on their
section, and "3 in no PET" counts the cards loose on the canvas, said only when there are any. Below about
900px the sidebar lies over the canvas, and at a phone's width it is a sheet over the board, its whole
width.

**A new board offers both starts.** The board menu's New holds New board, empty, every statement waiting
in the sidebar, and New board, all on the canvas, every statement on the canvas as a pile in the middle,
in no PET yet. A participant's first open starts empty.

**Select all.** `Cmd + A` (`Ctrl + A` on Windows) selects every statement on the canvas, or in the Table
view every statement it lists, and after a click on a row of the sidebar every row of that section. Select
all on the palette, under Group, does the same as the key on the canvas.

**Group, stack or set aside.** Most statements go into a PET, grouped with the ones they belong with. When a
participant says one point several ways close together in the transcript, stack the others under the
statement that says it best, which stands for them. Set aside is for a statement with a reason to go: it
does not answer the research question, it is badly evidenced, or it is irrelevant in some way. Setting one
aside is rare, so record why (Adam, 19 October), and it can always come back. The Guidance tab says the same.

**Stacks (19 October).** A stack is statements under a better one, the top, which stands for them in
the PETs table and the exports, while the others stay one click away for the audit trail. It is not a
PET and not Set aside. A top shows paper edges under it, one for each statement stacked under it, so a
stack of two shows one and a stack of five four, and past five four with a small plus on the corner where they
end (19 October, later), and its count on its foot, "3 stacked". Drag a statement onto the middle of another's card to
stack it under that card: the card shows an outline while the dragged one is over its middle, and the
card dropped onto is the top. A drop nearer a card's edge moves as any drop in a body does, and a title
strip still merges. Or select the statements and press `S`, and they stack under the highest of them,
since higher reads as better. The right-click menu on a card with others selected carries Stack the
selected statement under this one (or Stack the 3 selected under this one), which makes that card the
top. While a drag is over a card's middle, the tip about Option or Alt goes, since the drop stacks. A statement stacked leaves its PET, Not placed or
Set aside, and goes wherever its top goes after, into a PET, Not placed or Set aside. A top stacked under
another brings its own stack with it, so a stack is one level deep. Copy to board brings each top's
stack with it, and a board an agent makes keeping another's layout keeps that board's stacks.

The count on a top's foot, Show stack in its menu, or `S` with the top selected alone, opens the stack in
place: its statements stand under the top a little in, each a card as any is, a rule of its tint down
their left, and Stack again under the last. What stands below moves down to make room, the PET's frame
growing round them. Each card of an open stack opens its statement for editing on a double-click, shows its quote
in the Inspector, and has its own menu, Make this the top and Take out of the stack. Make this the top
puts it in the top's place, the old top first under it. Drag a card out of an open stack onto the board
and it lands where it is let go, out of the stack, as any card does. Take out of the stack leaves it
just below the stack, in the top's PET, never above its top, moved down past anything there. A stack
opened near the foot of the canvas glides up until its last card is clear of the zoom.
Stack again, the count, `S`, or Esc with nothing selected, stacks it again, and what moved down moves
back up. Opening a stack is a view: it changes nothing, has no step
of undo, and the board saves as if it were shut. Every stack, take out and Make this the top is one step
of undo. The PETs table, the Word document and the PET draft show the top alone unless Include stacked
statements is ticked under Export (see Print), and the statements CSV lists every statement, a stacked
one straight after its top with "Stacked under:" and its top's words in the Proposed PET column. The
counts on a label and a PET's badge count the tops alone.

**Sticky notes.** His notes to himself on the canvas, as Miro's post-its are: "not sure about this",
"merge with group 4", "think about splitting this one". A sticky note is never a statement and never
becomes one. A double-click on empty canvas puts one there, yellow, with the caret in its words, and so
does New sticky note, the one entry of the menu a right-click on empty canvas opens, in the row menu's
style, and since 18 October Sticky note on the PETs and GETs bars, which puts one of the canvas's own in
the middle of the canvas in view, clear of a sidebar lying over it, settling at the nearest place clear of
every PET and card as a card dropped there does. A double-click on the empty space inside a PET's frame puts one in that PET. Enter keeps the
words and leaves the box, Shift + Enter starts a new line, a click away keeps them too, and Esc on a
note with no words takes the note away. Making one and its first words are one step of undo, and a
double-click on a note opens its words again. A note fits its words: as wide as they run, 64px at the
least and 160px at the most, where they wrap and the note grows down, and as tall as its lines with no
square to fill and no inner scroll, so "Yeah this needs a look" makes a small slip. It fits them as he
types, and every measure of the spacing takes the size the page measures on it. A new note settles with
the room its words will take, the widest a note runs and three lines more than it has, so it never comes
to lie over a card as he types, and should his words outgrow that room it moves clear again, the note
alone, where until 18 October a new note made beside a card could grow over it until its words were kept.
A note there already whose words grow over a card as he types moves clear the same way, with room to
grow, where until 18 October it moved only once its words were kept. It has a slight paper shadow and no border, and comes in
four soft colours, yellow, pink, green and blue, tokens of their own beside the PETs' tints and none of
them a tint, which read in both themes, light and dark. The words are set in a handwriting
face from the system, Bradley Hand on a Mac, with Noteworthy, Segoe Print, Segoe Script and Comic Sans
MS after it, so nothing is downloaded and no font file ships, in a dark blue ink that reads on all four
colours, at about a card's size, and they zoom with everything else.

On the canvas a note behaves as a card does: it drags, keeps the margin, sends and is sent clear, falls
in a lasso, joins the selection with Shift or Cmd, and lifts, leans and lands, with reduced motion as
for a card. Dropped on a PET's title strip it comes into that PET and rides with it, the frame stretching
round it, and a drop with Alt held, Backspace with it selected, or Take out of PET in the Inspector or
in its menu takes it out again and leaves it on the board. With cards and notes selected together, `G`
groups the cards and the notes come along inside the new PET. A note is never a member, so it is never
counted: "3 statements" stays "3 statements" in the tooltip with a note inside, and the badge keeps its 3. Auto-arrange sets a PET's notes at the
end of its block, and a label deleted leaves its notes in the label above it or standing free, as it
leaves its cards.

A note selected alone carries its four colours in a small strip just under its bottom edge, its own
ringed, and one click there recolours it. The strip zooms with the canvas, sits clear of the cross on
the top corner, and goes while the note is dragged or its words are open, and when it is no longer
selected alone. A right-click on a note offers the four colours too, its own ticked, Take out of PET
when it is in one, and Delete note, and the Inspector has them as dots. A colour change from any of
the three is one step of undo. Delete note, or the small cross a selected note
carries on its corner, takes it off the board, and one step of undo brings it back where it was, in the
PET it was in. The sidebar is for statements alone: a note never goes there, and one dragged onto it goes
back where it was, as a label does. A note goes nowhere a statement goes, not into the counts, the PET
draft, the CSV's PET column, the print view, the outline the print view and the titles share, or
anything sent to a model, and a board an agent makes starts with none. The notes are the board's `notes` in the themes file (see Autosave and the file). A page in front
of a server from before them says "Restart the server to finish this update." on the double-click and
makes none.

**Undo.** On this screen `Cmd + Z` and `Cmd + Shift + Z` have a stack of their own, apart from the
statements screen's: a move, one step for each drag of a selection, ending where the drag settled, a label
made with its first title, a card joining a label or taken out of one, a rename, a PET's note
kept, an Auto-arrange, a label deleted, a card discarded, put back or removed, a quote picked or
unpicked, a sticky note made with its first words, its words changed, its colour changed or the note
deleted, and a statement edited in place, whose undo and redo write the workbook (see Editing a
statement). Undo on the bar takes back the last step as `Cmd + Z` does (16 October). Each board
keeps its own stack, so a switch to another board and back finds its steps where they were. The stacks are held in memory for the participant open here and
go when PETs opens on another participant. A step undone or redone is saved like any other
act. The board ops below are not steps on it: they change the file at once, and a delete asks
first. A restore, and a copy onto the board on screen, are one step each (see Copy to board and
History).

**Boards.** A grouping tried side by side with another is a board. The board's name in the top bar is a
switcher, in the sheet switcher's style: the name, a small chevron, and a click or `V` opens the menu
under it. The menu lists every board by name, the one on the canvas ticked and the Current board with
its mark after its name (see The Current board), each with its note under it, the one on the canvas too,
cut to two lines with the whole of it in its tooltip and in Edit the note. A click on another board
switches to it: the canvas saves anything still to save, the file records it as the board on the canvas,
`current`, and that is all a switch writes. The board comes on with its cards in view (30 October): the
view stays where it was when it shows any of that board's cards, as between a board and its duplicate,
so two boards laid out alike are compared in one place, else it goes back to where you left that board
since the participant was opened, else it fits the board as an opening does. Until then a switch kept
the view of the board you left, which could open the next one on blank canvas. The board that comes on
after Delete this board does the same. The entries come in two groups, each under a small kicker
in the style of the menu's BOARDS heading. Under the list comes the board on the canvas by name, "BOARD
1", with what it can do: Rename, Add a note, which reads Edit the note once the board has one,
Duplicate, Mark as current or Unmark current, Save a revision, and Delete this board last. Then a
hairline, and under NEW the entries that make a board. New board, empty, adds a board with no PETs, every
statement waiting in the sidebar, New board, all on the canvas, one with every statement on the canvas as
a pile in the middle (20 October, see The sidebar), and Duplicate a copy of the board on the canvas, groups, places, discards,
picks and sticky notes, the natural way to try another grouping. Either goes on the canvas at once with its name,
"Board 3" or "Board 1 copy", open in the menu to be typed over, Enter keeping it and Esc keeping the one
it had. Rename opens the same box on the board on the canvas, and a name another board has, whatever
its participant, is refused with a line in the menu. Add a note opens a box of a few lines in the place of the
note, for why the board exists. `Cmd + Enter`
or a click away keeps it, Esc leaves it as it was, and a duplicate starts with a note of its own, empty,
and a history of its own, empty. Save a revision opens a box for a name, which may stay empty, and Enter
or Save beside it keeps the revision, while Esc or a click away keeps none. Guidance and History
are no longer in the menu, since the sidebar's own tabs do that (see The sidebar). Delete this board
shows a card in the trim card's style, "Delete Mornings apart, with its 3 PETs and the 9 statements
placed in them.", with Enter to delete and Esc to cancel, and the board beside it, the one before when
there is one, takes the canvas. With one board left the entry is disabled and the server refuses it too.
Esc closes the menu, and so does a click anywhere else.

Names are just names. Every new board is "Board N", the next number free past the boards there are,
whether he made it or an AI agent did through the command line, and a name he
typed stays as he typed it. After the name of a board an agent made, in the board menu and in the participant
switcher under each participant, a small faint "with AI" follows, its tooltip naming the tool and its
source, the board on the canvas when it was made, "Claude Code in a conversation, from Board 2". The board
keeps its state hash as it was made, and his first save whose state differs from it adds "edited by
you since" to both the words and the tooltip, while a save that changes nothing leaves them as they
were. A name from before stays as it is, "AI board 3" among them. A board New AI board made before 11
November 2026 is an ordinary board now and carries no "with AI". A duplicate is his, and carries no
"with AI".

**The Current board.** One board can be marked as the one he is going with, the one to send a
supervisor, and on screen the word is Current. Mark as current, in the board menu, marks the board on
the canvas, and on the Current board the same entry reads Unmark current and takes the mark off. There
is one Current board at most, so marking another moves the mark. The menu shows a small ribbon after the
Current board's name with the word Current in the small type, and the switcher in the bar carries the
same ribbon beside the name while the board on the canvas is the Current one, "the Current board" in its
tooltip. The print view says "Current board" under the board's name (see Print). Deleting the Current
board takes the mark with it, unless one board is left, which then takes the mark as the only board
to go with, and with two or more left the mark goes nowhere and nothing is said. A duplicate never
carries it, and a file that has only ever had one board marks nothing by itself. The mark is set and
cleared through the board ops `choose` and `delete` and never by the autosave, and nothing on the
canvas changes with it. A page in front of a server from before it says "Restart the server to
finish this update." in the menu, and one from before the last board took the mark leaves it off. The
participant's card names the Current board on its PETs half, and its row under Files in its small type (see
Open a participant).

Grouping the statements into PETs is the participant's second phase, and the Current board is where it ends.
Mark PETs complete, the last entry of the board menu, after a hairline under NEW, marks the phase
complete on the Current board, the PETs in their final shape. It is there while a board is marked
Current, whichever board is on the canvas, and disabled with none, "Mark a board as current first" in
its tooltip. It records `complete` at the top of the themes file, `{"at": "<iso time>", "board": "v3",
"name": "Board 3"}`, through the board op `complete` and never by the autosave, and fires the third
level of confetti once, through the same call the participant-complete card makes. The menu then shows a small
tick in the app's green, PETs complete and the date, "4 Oct 2026", under the name of the board it was
marked on, and the same entry reads Reopen PETs, the time and the board in its tooltip, which takes the
record off through the board op `reopen`. The mark names the board it was marked on, so unmarking or
deleting the Current board leaves it as it stands, by the board's name now while the file holds it and
by the name it had when it was marked once it is gone. Marking PETs already marked keeps the first time.
Nothing about the mark locks anything, and every board stays his to change. The cards and the rows
under Files read it from the themes file (see Open a participant). The print view said it under its head until 31 October,
when Adam asked for the line to go.

**Copy to board.** A right-click on a label, or inside a frame for its label, carries Copy to
board…, which lists the other boards of the participant by name in the same menu, and a click on one
copies the PET there. A statement is on a board once, so nothing is duplicated: on that board
every statement under the PET, at any depth, leaves whatever PET holds it and comes out of the
Set aside if it was set aside there. A PET there that loses every statement goes, and so does a PET
above it left with none, and one that loses some keeps the rest. The PET arrives as a fresh one,
its title, its sub-themes in the same shape and its picks, laid out as a round blob, the way an AI
board lays a PET out, its statements in the order they read on the board it came from, and set
near the middle of that board's cards and four margins clear of every card, label and frame there,
the room the AI's layout leaves beside its pile, since a label as the page draws it can run a
little wider than the server's estimate, or to the right of them all when nothing nearer is clear. Before the copy the board it goes to keeps a
revision, "Before Mornings copied from Board 1", so it can go back to how it stood (see History).
The PET's sticky notes stay behind, since a note is his own word to himself on the board it was
written on, and the notes of the board it goes to stay as they were, a note whose PET the copy
empties standing free. The canvas stays as it is, and one line says "Mornings copied to Board 2". While a revision is on
view the menu offers the board it belongs to as well, first, "Copy to Board 1", which brings a
PET of the revision back into the board itself, its revision then named "Before Mornings copied
from Board 1 at 12:04": the canvas leaves the revision and shows the board with the PET in it,
and the copy is one step of undo there. With one board and no revision on view the entry is there
and does nothing. The server does the copy, so the file never holds half of one.

**The sidebar.** One sidebar at the right of the canvas holds what is about the selection and what
is about the board, as Figma keeps its properties on the right, one tab at a time, the tabs in this
order: Inspector (see The Inspector), about the card or the label selected, then Guidance (see
Guidance) and History, about the board as a whole, each of those two under the board's name and its
note. Its button, Inspector, at the right end of the top
bar over it, the standard panel icon, a frame with its right part filled, opens it on the tab left
showing and closes it again, "Show Inspector" or "Hide Inspector" in its tooltip with its key, `I`,
pressed in while it is open. Until 16 October it was named Sidebar and stood before the cog, its
tooltip "Show the sidebar" or "Hide the sidebar". A tab
at its head shows that tab. `I` outside a field opens it on the Inspector, and closes it again while
it shows the Inspector, and Inspect, the first entry in a card's and a label's right-click menu,
opens it on the Inspector for that one, on a revision on view too. Nothing at the edge of the canvas
opens it, so closed, the canvas runs edge to edge. A click on a card or a label selects it and never
opens or switches the sidebar, and nor does a lasso or a drag, so a selection made with History
showing leaves History showing. A double-click stays as it is, opening a card's statement for
editing and a label's title. Note in a label's right-click menu, `N` and an undo or a redo of a
PET's note open it on the Inspector. Esc and a click on empty canvas never close
it, a switch to another board keeps it open on the new board, and leaving the screen puts it away
until the next open. Whether it is open, and on which tab, is kept in the browser for each screen,
PETs and GETs apart, as the statements screen's guidance open or closed is, so a reload and the next open of the screen
bring it back as it was left. None of that is written to the themes file or to `config.json`. At a
desk width it takes a column of its own, 360px wide and the full height under the band, and the
canvas narrows for it. Below about 900px it lies over the canvas, stopping above the
zoom bar with its `?`, so both stay in reach with it open, and down to 400px it never scrolls
sideways. Its tabs share its width and keep to one line. Its buttons never take the focus, so `G`,
`X`, Backspace and `Cmd + Z` work on the canvas with it open. Until 5 October 2026 the Inspector and
a Board panel with the other tabs were two panels side by side, each with its own button in the bar,
its cross and a handle at the edge of the canvas.

**History.** Each board keeps its history, as a document in Google Sheets does: revisions of it,
each the board's cards, groups, discards, picks, sticky notes and the AI's reasons as the file holds
them. One is
made five ways. Save a revision, in the board menu and at the top of the History tab, keeps one by
hand, under the name typed in the box beside it or none. While he works, the page's timer asks for
one every fifteen minutes and the save writes it: the first save after a board comes on the canvas
keeps the board as it stood when it came on, and from then on, fifteen minutes on with an act
since, the next save keeps the board as it stood before it, under the time of that save. With no
act waiting the timer saves at once, so a pause in the work still keeps one. An automatic revision
is made only when the board differs from its last revision, by a stable hash of
the state. A restore keeps one first, and so does a copy onto the board, and so does an agent's change,
named "Before: " and his request. Every revision made by
hand, named or not, and every one made before a restore, a copy or an agent's change is kept, with
the last 48 automatic ones: a 49th takes the oldest automatic one away. A board deleted takes its
history with it.

A statement edited keeps one too (30 October, Adam: "Add a History line"), on every board that holds a
card of it, whichever screen the edit was made on: the card's box or the Inspector on PETs, a statement
reworded on the statements screen, or a statement's card on GETs, LGETs or LPETs. Each board keeps itself
as it stood before the edit, one line for the edit, named for the participant and the statement's words
before and after, `Juno's statement edited: "Lost at sea" to "Adrift at sea"`. A long statement shows
the words round the change, three words of what stayed on each side of it and an ellipsis for the rest,
each side cut at a word past sixty characters. The PETs boards are the participant's at the timepoint the
statement's sheet is at, and a GETs, LGETs or LPETs board has the line when it holds a card of the
statement, not for a PET's card alone. A save on the statements screen that rewords nothing leaves no line,
and a statement moved, added or removed there is not an edit of one. An undo of an edit is an edit back,
a line of its own. An AI agent's write keeps its own line, "Before: " and his request, on each board it
changes, and no second line for the same write. A Find and replace leaves none, since it keeps no board's
old words anywhere, its revisions included (see Find and replace).

The history sits in the sidebar's History tab (see The sidebar), under the board's name, with the
board's note under it in the small type when it has one, read-only there since Add a note in the
board menu edits it. A switch to another board keeps the tab open on the new board.

History lists the board's revisions newest first under the day they were made, Today, Yesterday or the
date, each with its time, its name, Automatic for one the timer made, nothing more for one kept by hand
with no name, and Restore. Each carries the time it was made, in the order they were made. Until 30
October 2026 an automatic revision took the time the board was last written, which an edit of a
statement did not change, so after an edit one could show between two of today's lines under a day
weeks back. On a board saved then, such a one shows at the time of the revision made before it, the
earliest it can have been made, so the list reads in order, and the board's next save keeps that time.
A click on one shows it on the canvas, dimmed and read-only, under a line at the top of the canvas,
"Viewing the revision of 12:04 · Restore · Back". Nothing on it moves: a drag
lets go, and a key or a control that changes a board, a tick, Put back, Rename, `G`, `X`, Backspace or
`Cmd + Z`, says in one line that the revision is read-only. The lasso, a click to select, the Inspector
and its player, the pile's list, the zoom and the right-click copy on a label all work. Back, or Esc,
puts the board back on the canvas as it was left. The autosave and the timer wait while a revision is on
view, and a board op or leaving the screen puts the board back first. Restore, on the
line or on a row, keeps the board as it stands as a revision named for the one restored,
"Before restoring 12:04", then makes the revision's state the board's. On the canvas it is one step of undo, and
one line says what was restored and what was kept.

The history lives in the themes file beside the workbook, under each board, each revision on a
line of its own. A revision of a hundred statements of about sixty characters, in a dozen PETs,
takes about 14 KB, so 48 automatic ones come to well under a megabyte. Statements much longer than
that, seventy-five characters and more on average, take a revision of a hundred past 15 KB.

**The Inspector.** The sidebar's first tab is the Inspector, about the selection. While it shows, it
follows the selection: the card or the label selected, and with several selected the one clicked
last. With nothing selected it has no head, since its tab already says Inspector, and under the tabs
it reads "Select a statement or a PET." in the small type. Esc clears the selection and leaves
it on that line, and so does a click on empty canvas. Its head names the thing, a PET by its title
in the PET's tint, with the whole of it in its tooltip, and a statement or a sticky note by its
kind, Statement or Sticky note, in the kicker's style the empty head's Inspector is set in, so a
statement shows once, whole, in the body under it, and the head keeps the card's own tooltip.
Another tab, or the sidebar closed, keeps a note being written there, as a click away does.

For a card the Inspector carries the statement, its timecode, and under Quote its own quote,
the one in its pair on the statements screen, with the row's timecode and a play button, or "No quote
for this statement." A double-click on the statement there opens it for editing in place, as a
double-click on its card does, and its tooltip says "Double-click to edit" (see Editing a statement).
From 16 to 30 October it was the one way in, while a double-click on the card opened its passage. For a sticky note it
carries the note's words in a box, Enter or a click away keeping them and Esc leaving them as they
were, its four colours as dots with the one it has ringed, and Take out of PET when it is in one (see
Sticky notes). A label's head says what it is, PET, Sub-theme or Group, over its count. A card in a
PET, and a sub-theme or a group, carry Take out of PET under the timecode or the count, Take out of
sub-theme or Take out of group by what holds it, with the title of what holds it beside it, which takes
it out and leaves it where it stands. For a label it carries the quote of every card under it,
each statement's own, at any depth, row by row in transcript order, each row under the statements of
the cards on it, so a row two cards share is listed once, with the label's picks among them. A label
over labels has the quotes of all of them.

The play button cues the recording of that sheet, the file the statements screen's player finds through
`/api/audio`, at the row's timecode and plays, in the accent while it plays, the playhead's, and in the ink
under the pointer, where until 17 October, later, both stood in the crux orange. The same button again pauses, a press after that carries
on from where it stopped, and another quote jumps there and plays. The Inspector's player is its own,
built from the statements screen's parts: the audio element as the engine, and at the Inspector's foot a play
button, the elapsed time, a scrub bar, the total and the file name. It is apart from the statements screen's
so a cue here never marks a passage there. Closing the sidebar, another tab, clearing the selection or leaving the screen pauses it.

**From a statement to its passage (16 October).** The hermeneutic circle runs from the part to the
whole and back, so a statement on the canvas leads to the passage it was drawn from (a tester's ask,
Adam's word). Go to the passage, after Inspect in a statement card's right-click menu, on the PETs
screen and wherever a statement's card stands on the GETs screen, opens Experiential statements at the
passage that statement belongs to,
the caret in that statement and its quote's marks lit in the passage when it has one, the
passage's start in view at every width: a passage taller than the column stands with its first line at
the column's head, and on a phone, where the fields stand under the column, the page stays on the
passage rather than on the field (17 October), its speaker and time below the title bar and the
research question under it, as tall as they stand, where at 360 the question's height was left out
and they stood under it (17 October, later). It stands there on a revision on view too, since it
changes nothing on the board. A double-click on a statement's card did the same from 16 to 30 October, on
the PETs screen and on the GETs screen, and since then it opens the statement for editing on the card, as
a title opens, on the GETs, LGETs and LPETs boards too (see Editing a statement). On the GETs
screen a double-click on a statement's row in the Participants panel does the same, its card on the board
or not, and the way back returns to the GETs board (see The Participants panel, under GETs). The canvas is
saved first. The way back then is the tab of the board's screen, PETs or GETs, or Back, and it returns to the board as it stood, the same board, the same place on the canvas and the
same selection, its undo kept. A window that changed size
while the passage was open, a phone turned or a window narrowed, finds the card he came from in the
middle of the canvas, at the same zoom. A label still renames on a double-click, a PET's, a
sub-theme's or a
group's, a click still selects, and a statement is edited in place by a double-click on its card or on it in the
Inspector (see Editing a statement). A statement whose passage is no longer in the transcript, its row gone or now the
interviewer's, says "This statement's passage is no longer in the transcript." and nothing changes,
the board, the screen and the recent list as they were. A participant opened from its row, or Home,
ends the way back to the board. The step on the statements bar for the board he came from is that way back too, on PETs, a timepoint's PETs, a
participant's LPETs, GETs and LGETs alike, where until 1 November the LGETs step and a later timepoint's PETs step
opened that board afresh.

**Editing a statement.** Now and then a statement needs a word changed while it is grouped. A
double-click on a statement card opens it for editing on the card, the way a double-click on a PET's or
a sub-PET's title opens the title (Adam, 30 October, for consistency): a box in the card's serif in the
place of its words, as wide as the card and as tall as the words, the whole statement in it and
selected, so a long statement that stops at four lines on the card opens whole. With the quotes on
cards showing, the quote stays under the box. It is the same on every statement card of the PETs board,
loose, in a PET or a sub-PET, a stack's top and each card of a stack shown open, and on a timepoint's
PETs. The timecode and the sheet's name are part of the card, so a double-click on them opens the box
too, and a double-click on the quote shows the quote whole as a click on it does. A double-click on the
statement in the Inspector opens the same box there, as wide as the Inspector. Until 16 October a
double-click on the card opened the box over the card, from then until 30 October it opened the
passage, which Go to the passage in the card's menu does now, and the Inspector was the one way in.
Since 30 October, later (Adam: "Edit there too"), it is the same on the GETs, LGETs and LPETs boards: a
double-click on a statement's card, or on the statement in the Inspector, opens the same box, and a
double-click on any other card there still opens the Inspector. A statement on those boards is a
participant's own, so keeping it writes that participant's workbook, the one the statements screen
reads, and every copy of the words follows at once: the participant's PETs boards, the GETs' copy of the
participant, which the Participants panel and every GETs board show, and in a project of timepoints the
participant's LPETs and the LGETs. The participant is not marked Changed since it came in for it. Until
then statements were never edited on those boards, and a double-click on the card opened its passage.
The box keeps the same keys, the same route and the same step of undo wherever it
opens, and the card and the Inspector both show the new words afterwards. Enter keeps it, Esc leaves it as it was, a click away keeps it as a
label's title does, and the text stays one line, so a line break typed or pasted becomes a space. An empty text is refused
with a line and the box stays open. A card marked missing has no line to write, so it cannot be edited,
and a revision on view says it is read-only. Keeping it is the one act on this screen that writes the
workbook. `/api/edit-statement`, with the workbook, `sheet`, `row`, `line`, `text` and `old`, what the
line read, replaces that one line of the row's experiential statements cell, split and joined as the
statements screen's save does, and keeps every other line, the cell's font, its alignment and its number
format, never with a fill. It goes through the lock guard the statements screen's save goes through, so a
workbook open in Excel is refused with the statements screen's line, and a line that no longer reads as `old`
is refused too. Nothing else in the workbook or the progress file changes. On success the server
answers with the new text, the page puts it on the card, in the Inspector and in the board's stored
text for that key, the save goes as usual, and nothing shows as changed. In the same request the server
gives the new words to every other board of the participant whose card for that line held the words it read
before, so no board marks the card changed for an edit made here. A board whose card held other words,
from a change made in Experiential statements or in Excel since it last saw the line, keeps them and
its changed mark, since that change is news there. The boards it carries the words to are those of the
timepoint the statement's sheet is at. It gives them as well to the GETs file's copy of the participant
and each GETs board's card of the statement, and in a project of timepoints to the participant's LPETs
file and the LGETs file, each the same way, so the participant stays in. A participant with a change
already waiting keeps its mark, to be brought in as ever. Revisions are left alone, and the progress file
is as it was. Since 30 October, later (Adam: "Add a History line"), every board that holds a card of the
statement, the participant's PETs boards and each GETs, LGETs and LPETs board with its card, keeps one line
in its History for the edit, the board as it stood before it, named for the participant and the words
before and after (see History). It is one step of undo:
undo writes the old text back through the same route, and redo the new, each a line of its own. A failed write is one line and
the card keeps its text. A page in front of a server from before the route says "Restart the server to
finish this update." on the double-click and changes nothing, and so does a GETs, LGETs or LPETs board in
front of a server from before 30 October, which would leave the GETs' copy behind.

**Picks.** On a label every quote carries a tick, to pick the one or two that carry the PET. A
PET's quotes to pick from are its statements' own, each the quote in its statement's pair. A quote
picked already stays picked and shown even when its statement sits under another PET, and is never
dropped by itself. A tick is an act like any other, saved with the board and one step of undo, and a label with picks
carries a small quote mark beside its count. The Inspector shows a label's picks again at its head,
under Picked quotes in the order they were picked, so the quotes that carry it are read first, and
the ticks stay with the statements below. Auto-arrange, Take out of PET and the note under them stand
clear of the last picked quote, where until 18 October Auto-arrange stood over its foot. A sub-theme has picks of its own, apart from the
PET it sits in. A pick is the quote's key, its sheet, its row and its place among the row's key
quotes, `Initial:12:0`, which is its statement's key too, and it belongs to its label only while a
card on that row is under it: a
card that leaves takes its row's picks with it, a label deleted takes its own, and undo puts them
back. A pick follows its quote's words: when a quote before it leaves the cell, or its row moves,
it takes the key of the quote with the same words on its row, or on a row with a card under its
label, and a pick whose words are nowhere there, reworded or gone, is dropped when the participant is read
and when the board is saved. The inverted commas round a quote are not its words, so a quote that
gains or loses them keeps its picks. A label takes as many picks as he ticks.

**PET notes.** A PET can carry a note, his own words on why it exists, what it holds and what it
answers. In the Inspector, for a label, under the count and Take out of PET and above the quotes, is a
box of a few lines in the board note's style, "Why this PET", "Why this sub-theme" on a sub-theme, or
"Why this group" on a group.
`Cmd + Enter` or a click away keeps what is typed, and Esc leaves the note as it was. A note kept is one
step of undo, like a rename, and undo and redo put the old text and the new back in the box, the sidebar open on the Inspector for that label. Note, after Rename in a label's right-click menu, opens the sidebar on the Inspector for that label with the box ready to type in. A sub-theme has a note of its
own, apart from the PET it sits in. A label with a note carries a small mark of three lines beside its
count, drawn as the picks mark is, and its tooltip carries the note after the count. The note travels
with the board: Duplicate copies it, Copy to board carries it with the PET and its sub-themes, a
revision holds it and Restore brings it back. While a revision is on view the note shows read-only, as
the rest does. With AI features on, AI suggest PET titles sends the note of the label it names, the
prompt saying in one line what a note is, and a label with no note sends its prompt as it did. The note is the group's `note` in the
themes file, kept stripped, and a group with none carries none, so a file from before the notes reads and
writes as it did. `/api/themes` carries `notes`, and a page in front of a server from before them says
"Restart the server to finish this update." in the place of the box, since that server would drop a note
on the save.

**Canvas and Table (19 October).** Adam's choice of 18 October, from a drawing: the PETs bar and the GETs
bar carry Canvas and Table after the board's name, two views of one board, always in step, the one showing
pressed in, and `T` switches between them, as their tooltips say. Each board keeps the view it was left in,
in the browser, across a restart. Table is the table of PETs the print view sets out (see Print), live: the
PETs in the order the canvas reads them, each lettered as the project labels them, its sub-themes and groups
under it, and each statement with where it is and its own quote, then Not placed. It is drawn from the
board on the page whenever the canvas changes, so it is never out of date, and the canvas stays laid out
under it. Every PET, sub-theme and statement row has a grip at its left: drag it to another place among what
sits beside it, or press Alt with the arrow up or down on its grip or its title, and the letters follow, 1d
put above 1c becoming 1c. The order is set as an agent's `order` sets it, each item moved into the place of
the one that read there before, so the canvas moves its cards to match. A statement dragged into another PET,
sub-theme or group goes there, at the line shown, as on the canvas, and one in Not placed goes into the PET
it is dragged into. A double-click on a PET's or a sub-theme's title, or a second click on the title of the
one label selected, opens it in a box in place, Enter keeps it and Esc leaves it. Each change is one step of the board's undo, `Cmd + Z` in the table as on the canvas, and is
saved as the canvas saves. The statements' own words are read-only here: they are written on the statements
screen, since the PETs are built from the statements. Print and Microsoft Word at its top right do what Export does. Its
heading is the participant, "P9 Wren", with Table of Personal Experiential Themes smaller under it and the
board's name beside that, as the print and the Word document head the table (20 October). A
revision on view is read-only in the table too. The zoom bar and the minimap leave the canvas's
corners while the table shows, and the palette stays, with Group, Undo and Redo, New sticky note being the
canvas's alone. The table takes its measure from the room it has, not the window, so beside the Inspector
or the Participants panel it lays out as it does in a narrow window: each statement on a line of its own with its
quote under it. Where it has room the table starts clear of the palette, and where it is narrow, as at a
phone's width or beside the Inspector in a small window, the palette lies flat in a row at the table's foot
right and floats over it, as it does over the canvas, so the table keeps its whole width. A Shift or Cmd
click, a right click or a double-click on a row selects no words in it, as on a card. On the GETs board the table is the GET table (see Table
under GETs), each GET with its grip to reorder the GETs, its title edited in place, and each participant's card
under it with a grip of its own to go under another GET, then the cards under none. A window of the Mac app,
or a tab, on the same participant sees a change made in another as it does today, by the line in the top right.

**Everything the canvas does, in the table (20 October).** Adam, 20 October: the table is self-sufficient,
so anything done on the canvas can be done in the table and the other way round. He chose the canvas's own
keys, palette and menus on the table's rows, so there is nothing new to learn either way. A click on a
statement's row selects it, Cmd with a click adds one or takes it away, Shift with a click selects the run of
rows between the last one clicked and this one, and Esc or a click on the table's empty space clears the
selection. A PET's or a sub-theme's row is selected by a click on its title strip. The selection is the
board's own, so the canvas shows the same cards selected after `T`, and the status bar counts them, "2
ES selected", on the canvas as in the table. The canvas's keys work on the rows selected and mean what they
mean there. `G` puts a label over them with its title box open in its row, a sub-theme when they all sit in
one PET and a group when they all sit in one sub-theme, and the letters below it follow, 1a becoming 1b.
`G` with nothing selected makes a new empty PET at the end of the table with its title box open, and the
statements are then dragged into it. On the canvas `G` with nothing selected makes the empty PET in the
middle of what is in view. `Backspace` takes a statement out of its PET or sub-theme to Not placed, and on a
title deletes the label, keeping what it held. `X` sets aside, `S` stacks the statements selected under the one
that reads first in the table, `I` opens or closes the Inspector, which follows the row selected as it
follows a card, and `N` asks for names when AI features are on. A right click on a row, or the ⋯ at its
right end, opens its card's or its label's menu, the canvas's own, and a PET's or a sub-theme's menu also
has New group inside, which makes an empty sub-theme inside a PET or an empty group inside a sub-theme, its
title box open. Auto-arrange is left out of the table's menus, since the table is always in order. A
double-click on a statement's row opens its passage on Experiential statements, and the way back returns to
the table where it was scrolled to, the row still selected. A selected statement's grip drags every
statement selected, together, in the order they read, to the line shown. Rows dropped on a label's title
strip go into it, "Merge into" showing over the strip as on the canvas: statements join it at its end, and a
PET or a sub-theme goes inside it with all it holds. Rows dropped on Not placed go back there. A stack's
count beside its top, "2 stacked", shows the statements under it in the rows below, and a click on it again,
or `S` on the top, stacks them again, their menus holding Make this the top and Take out of the stack. The
table's foot lists Set aside, each with Put back, and then any statement missing from the workbook, with Remove,
as the sidebar does. Every one of these is one step of the board's undo, as on the canvas. On the GETs
board the same keys and menus work on the cards: `G` makes a GET from the cards selected, and with nothing
selected an empty GET, a card's menu has Take out of GET, and Place also under when One GET per PET is off,
and a right click on a participant's name in a GET's row opens the participant's menu, whose Add participant note puts the
note under that GET, in that participant's row. A GET's menu and a GET sub-theme's have New group inside too, on the
canvas as in the table, which makes an empty sub-theme inside the GET, or a group inside the sub-theme, its
title box open. A GET's sub-themes stand as rows of their own at the top of what the GET holds, each with
its title, how many participants it holds and its menu, and a card dropped on a sub-theme's title strip goes
inside it, the card's row under the GET then saying "in" and the sub-theme's title. A row of the Participants panel
dragged onto the GET table goes under the GET or the sub-theme it is let go on, or into Not placed when let go
over that list, as a drop on the canvas does: its card comes in, or the one there already moves, out of the
Set aside when it was there, one step of undo.

Since 11 November 2026 an AI agent can do what dragging a statement's row from the Participants panel does, on
GETs, LGETs and a participant's LPETs alike: it brings that one statement onto the board, into the GET or LPET you
name, or onto the canvas in none, never the rest of its PET's statements. It runs a dry run first and keeps the board
as it stood in its History, as its other changes do. A statement on the board already, another participant's on
their LPETs, or a GET or LPET the board has not got is refused, with nothing changed (see the guide for agents).

**Export.** Export in the top bar, the share glyph, a box with an arrow up out of it, drawn in the app's
line style, opens a small menu under it, in the row menu's paper, and since 1 November it follows the view (Adam: "I
always switch to the table view if I want to print or export the table"). In Table view it is headed The table:
Print (see Print), Save as PDF, Microsoft Word (see Word document) and Markdown and CSV, then under a rule the ticks,
Descriptions, Include not placed, Include statements set aside, Include stacked statements and Leave out the board's
name, and under a last rule PET labels. On the canvas it is headed The canvas: Print, Save as PDF and Save as an
image, with no ticks, since the canvas shows what it shows. Print opens the canvas on one landscape page in a tab of
its own, as Canvas on one page did (below). Save as PDF saves the canvas on one landscape page as a PDF beside the
workbook, named as the table's PDF with "canvas" after it, "P9 - Wren - Board 3 - PETs canvas.pdf", with no print
dialog. Save as an image saves a picture of the whole canvas, every card whole under the title, as a PNG beside
the workbook, "P9 - Wren - Board 3 - PETs canvas.png", at twice the screen's sharpness, so it stays sharp on a slide or
as a figure in a thesis. Both show the quotes on the cards as Quotes on cards shows them, a short quote, a label's
description or a reason cut with "…" where the canvas cuts it, and the close pairs' lines while Close pairs is on. Each
adds the date and time to its name when a file of that name is there already, and a line names the file once it is
written, with Show in Finder on a Mac. Since 9 November 2026 Idiograph makes every PDF and picture itself, in its own
two typefaces, so Save as PDF, Export as PDF and Save as an image are the same on a Mac, on Windows, on Linux and in a
browser's tab, and nothing else needs to be installed. When one cannot be made, the line at the foot says so in plain
words and nothing is saved. Print in the Linux window opens the print dialog on the page's own landscape A4, as on a
Mac. Esc or a
click anywhere else closes the menu. Since 31 October each entry is named for what it
gives (Adam: literal words), where they read Print table, PDF, Canvas, .md and CSV and For sending, and each
entry's and tick's tooltip says the rest: the table of PETs on landscape A4, opening the print dialog, the table of PETs
as a PDF on landscape A4, the print's own pages, saved beside the workbook, the canvas on one landscape page,
the Microsoft Word document of the table of PETs, a .docx, saved beside the workbook (Microsoft Word since 1 November,
where it read Word), the PET draft as Markdown and the statements
as CSV, and for each tick what it puts on the page. Save as PDF saves the table of PETs as a PDF
beside the workbook, where the Word document goes, named as the print view names it, "P9 - Wren - Board 3 -
PETs.pdf", or the participant alone with Leave out the board's name on, and with the date and time added when a file of that
name is there already, so none is written over. There is no print dialog: Idiograph sets the pages itself, the
same foot on every page, and a line names the file once it is written, with Show in Finder on a Mac. A save still to
go is written first. It is the same in a browser's tab. The canvas's Print (Canvas on one page until 1 November) opens the canvas itself in a tab of its own, every
PET, sub-theme, group, card and sticky note in its tint, under a title naming the participant and the board,
with none of the screen's controls. On screen a statement's card stops at four lines, and on paper every statement is
whole: the canvas's own layout runs on a copy with each card at its whole height, so a PET, sub-theme or group grows
round a longer card and what lies below moves down, nothing overlapping, in the screen's columns, nesting and order.
The canvas on screen keeps its four lines and does not move. It fits the whole canvas on one landscape page of the paper
the print dialog picks, so choose A3 there for a large board. PET labels is a choice of two, A B C or 1 2 3. Smith,
Flowers and Larkin letter the PETs in Box 5.6, A, B, C, and leave the sub-themes unnumbered. Idiograph
follows the book by default, and gives each sub-theme and group a reference after its PET's letter, A1
and A2 under A, A1.1 under A1, so any label can be named in a note or a supervision. Numbers are a
setting: 1 2 3 labels them "PET 1", "PET 1a" and "1a.1" in their place. A press saves `pet_labels` in
the project file at once, every other key kept, for every participant of the project, and the menu stays open
on it. The Word document, the print view and the PET draft all follow it, and Project settings,
shows the same choice for each project (see Projects). The demo keeps the book's letters, its pair
greyed. Markdown and CSV
writes the board on the canvas, after saving anything still to save. A line in the top right of the
canvas then names the two files it wrote the way the participant holds them, `Working/<file>`, never with the
participant's folder's own name, and on a Mac carries Show in Finder, which opens a Finder window on the markdown
draft. The line stays until its cross or Esc. The first file is a markdown PET grouping draft at
`<case>/Working/<stem> - PET draft (<board name>).md`, `Juno - PET draft (Board 1).md` on the demo, the
stem the statements CSV uses, with any character a file name cannot carry in the board's name made a
hyphen. Its PETs, sub-themes and groups carry the labels the print view and the Word document give
them, in the same order, so the three never disagree (see Print). It opens with a title line, the participant
by its pseudonym and the board's name, then a list of every PET, its sub-themes and their groups in
canvas order, top to bottom and left to right along a row, labels within a card's height of one another
counting as one row, "A. Home life (1 sub-theme · 7 statements)", a sub-theme one step in, "A1.
Mornings (1 group · 3 statements)", and a group a step further, "A1.1 Early light (2 statements)". Then
each PET under its letter and title as a heading, "A. Home life", a sub-theme a heading a level
down under its PET, "A1. Mornings", and a group a level further, "A1.1 Early light". A group inside
a group, "A1.1.1", is a heading a level further again, and anything deeper stays at that level, as the
Word document's headings do. Under a heading come the PET's note, or the sub-theme's or the group's, as a plain
paragraph when it has one, then its statements and the labels inside it in the print view's order, each statement a list item,
`- Statement (Initial, 02:10)`, and its own quote on the next line in single curly marks, ‘like this’, none for a
statement without one. No picked quotes are listed, as in the print view. The
board's note stays out, and the CSV carries no note at all. At the end come Not placed and Experiential statements set aside
with their counts, "Not placed (18)" and "Experiential statements set aside (3)", as the print view and the Word document head them (until 19 October the second read Discarded, and until 20 October Binned experiential statements), in transcript order, each only when it holds
anything, set out the same way. The second is the statements CSV with its Proposed
PET column filled from the same board and each statement's own quote last, its rows PET by PET in canvas order, a sub-theme's where its
frame's top sits among the PET's cards (see Export, under The loop). The workbook is only read, so a
workbook open in Excel exports as it was last saved. Settings offers the same export, Export the PET
draft, for the board last on the canvas of the participant open on the statements screen.

**Word document.** Microsoft Word, the fourth entry under Export, writes the board on the canvas as a
Word file in the shape of the table of Personal Experiential Themes that Smith, Flowers and Larkin
(2022) set out in Box 5.6, their table of PETs for Elisa, plainer than the print view, for when a
polished page reads as finished work. Anything still to save is saved first. It goes at the
participant's folder's root, beside the workbook, where his PETs Word files live, as `<P9 Wren> - PETs (<board
name>).docx`, `Juno - PETs (Board 1).docx` on the demo, the participant by its pseudonym and any character a
file name cannot carry in the board's name made a hyphen. It never writes over a file. When the name is
taken the date and time go in it, `Juno - PETs (Board 1, 6 Oct 14.20).docx`, and a count after them in
the rare case that one is taken too. With Leave out the board's name ticked under Export it goes by the participant alone,
`P9 - Wren.docx`, then `P9 - Wren (6 Oct 14.20).docx` when that is taken (see Print). The line in the top right of the canvas then names the file the
way the participant holds it, with Show in Finder on a Mac. The document opens with the participant, large,
under Heading 1, "P9 Wren", or the name alone when the participant has no number, "Juno", so Word's navigation
pane names the participant, and under it the table's name, "Table of Personal Experiential Themes", smaller,
in Word's Subtitle style (Adam, 20 October). Then the PETs in the order the canvas reads them, the order he
sets for the story they tell, each lettered in bold capitals under Heading 2 as Box 5.6 letters them,
"A. HOME LIFE", then B and C. The title keeps his casing in the text and Word's All caps shows it in
capitals, so a copy pasted elsewhere keeps his casing. A sub-theme sits under its PET in bold under
Heading 3, "A1. Mornings", then A2, and a group, a label inside a sub-theme, in bold italic under
Heading 4, "A1.1 Early light", then A1.2. A group inside a group, "A1.1.1", takes Heading 5, and
anything deeper, "A1.1.1.1", keeps Heading 5, the same style as the level above it. With 1 2 3 under
PET labels the same headings read "PET 1. HOME LIFE", "PET 1a. Mornings" and "1a.1 Early light" (see
Export). A label's note, when it has one,
follows its heading in italics. Under each heading come its statements in the order the canvas reads
them, a label inside it taking its place among the cards where its frame's top sits. Each statement is a paragraph
followed by its sheet and timecode, "(Initial, 12:04)", and on the next line its own quote in
single curly quotation marks, ‘like this’, set in a little, never doubled when the workbook keeps its
own marks. A statement with no quote of its own has no quote line, and "(no quote)" never shows. There
is no list of the PETs at the head, no list of picked quotes and no key, since each reference names its
sheet. Not placed and Experiential statements set aside come next under plain headings with their
counts, "Not placed (18)" and "Experiential statements set aside (3)", each only when it holds anything and only when its tick under Export is on,
Include not placed and Include statements set aside (see Print), their statements set out
the same way, and a
statement no longer in the workbook says so in its reference, "(Initial, 12:04, no longer in the
workbook)". The labels and the order are the print view's, taken from one place, and the PET draft
takes the same labels. The
styles are plain: Normal in Times New Roman at 11pt, Heading 1 to 5 under Word's own names, so the
navigation pane and a reference document take them, restyled to the book's look, and no colour, no
fill, no list and no table. The page is portrait A4 with margins of an inch, where the print view's
PDF is landscape (see Print). It opens in Word, Pages and LibreOffice. The workbook and the themes file
are only read. `themes_word.py` writes it, with the standard library alone.

**Print.** Print, the first entry under Export, and Print at the top right of the Table view (see
Canvas and Table), open the board on the canvas in a tab
of its own at `/themes/print?workbook=<path>&board=<id>`, the print dialog opening at once, a page the server renders from the board as
the themes file holds it, a save still to go written first. It is the PET document he sends his
supervisor, the table of Personal Experiential Themes that Smith, Flowers and Larkin (2022) set out in
Box 5.6, the Word document's content (see Word document) typeset in the app's faces, on landscape A4,
as the book's tables are set, where the Word document stays portrait A4.
Since 9 November 2026 the print view is set in two typefaces the app carries, Charis SIL for the text and
Nunito Sans for the headings' labels, where a statement was said and the foot, so it looks the same on a Mac,
on Windows and on Linux, and the PDF made from it is set in the same two (Adam, 9 November).
The page's small print, the board's name, the labels, a statement's reason and the foot line, and the
GETs print's counts and the audit trail's places with it, is in the app's own faint ink, 5.3 to 1 on the
white paper, where until then it read at 3.8 to 1 (17 October).
The head is one band across the top of the first page. The participant is its main heading, "P9 Wren", the
dash of the case key dropped, or the name alone when the participant has no number, with the table's name,
Table of Personal Experiential Themes, smaller beside it on the same line (Adam, 20 October: with three
tables printed, each opening on the same title, what told them apart was hard to see). To their right the
project and the research question, each after its small label, the labels in a column of their own so the
two lines start together, the question wrapping in its column (Adam, 31 October, so the head takes less of
the page). No rule runs under the head, as PET A's shaded band parts it from the table. The date and the
board are in the foot. The page no longer says the PETs are marked complete (Adam, 31 October), though the
mark itself shows everywhere else as before. The board's note stays out. Board note, a tick
beside Print, off until ticked, draws the page again with the note under the head, `note=1` in the
address, and is greyed on a board with no note. There is no list of the PETs at the head. Then the PETs
in the order the canvas reads them, each lettered "A.", "B." as the Word document letters it, or
"PET 1.", "PET 2." with 1 2 3 under PET labels, its
title in capitals, a pale band of its tint behind the title and a thin rule of the tint down its side,
then the PET's note in italics when it has one. A sub-theme sits under its PET in bold, "A1.
Mornings", and a group, a label inside a sub-theme, in bold italic, "A1.1 Early light", each set in a
little further and a little smaller with a hairline of the lighter tint beside it. A group inside a
group, "A1.1.1", takes the fifth step, and anything deeper stays at that step's size and indent, as the
Word document's headings stop at Heading 5. The headings and the notes run across the full width.
Under each heading come its statements in
the order the canvas reads them, higher first, a label inside it taking its place among the cards where its
frame's top sits, each a row of two columns, since one line across a landscape page is too
long to read. On the left the statement in the serif at 10pt followed by where it is, "(Initial, 12:04)",
small and quiet in the sans, and on the right, the wider of the two, its own quote in italics at 9pt in single curly quotation marks,
‘like this’, never doubled when the workbook keeps its own marks, the quotes lined up in one column
down the page. A statement with no quote of
its own leaves the right empty, and "(no quote)" never shows. The picked quotes are not listed, since every
statement carries its own. The PETs flow on from page to page, a row never splits, so a statement never
parts from its quote across a page, and a title, a PET's, a sub-PET's or a group's, is never left at
the foot of a page: it goes to the next page with its first row, and a PET's title with its first
sub-PET's title and that sub-PET's first row. Every other row flows on freely, so the pages fill.
Nothing spills onto a page of its own
after the last row. Since 31 October the type is a step smaller than on screen, set as a research
document to read at arm's length: the participant 18pt, a PET's title 11.5pt in capitals, a sub-PET's
10.5pt in bold, a statement 10pt, its quote 9pt and where it was said 7pt, with room between the PETs and
the rows. The page prints at that size, the same on a Mac, on Windows
and in the PDF an agent makes. At the end come Not placed and Experiential statements set aside with
their counts, "Not placed (18)" and "Experiential statements set aside (3)", where until 19 October the
second read Discarded, in transcript order, their statements in the same rows, a discard
with the reason an AI proposal gave under its statement, each only when it holds anything and only
when its tick is on. The two ticks, Include not placed and Include statements set aside (Include binned experiential statements until 20 October),
sit under Export on the PETs screen, under the four entries, and beside Board note on the page, where
a tick draws the page again with the part or without it. Both are off on a new install, so the table
and the Word document hold the PETs alone, and a tick changed in either place is kept in the settings
for the next export of any participant, the table and the Word document alike (18 October). A third beside
them, Include stacked statements, puts the statements stacked under a top beneath it, under a small
line, "Stacked under it (3)", each with its reference in the soft ink and no quote, inside the top's
row, so the page never parts them from it. It is off on a new install, so the top stands for its stack
alone, and it reaches the Word document and the PET draft too (19 October, see Stacks). A fourth tick
beside them, Leave out the board's name (For sending until 31 October), is for the copy he sends his supervisor (19 October). Before them all stands
Descriptions (21 October), on on a new install, which puts each PET's and sub-PET's description under its
title on the page and in the Word document, and leaves it out when unticked (see Descriptions). After them all
stands Pen portrait (11 November), off on a new install, which puts the participant's label and pen portrait under
their name (see The label and the pen portrait in the exports). With Leave
out the board's name on, the PDF
saves by the participant alone, "P9 - Wren.pdf", where it otherwise saves as "P9 - Wren - Board 3 -
PETs.pdf", the Word document the same, and the page carries no board's name and no Current board
at its top right, only the date, and "PETs marked complete" without the board it was marked on. It
is off on a new install, kept as he leaves it, and also sits on the GETs print card. A small line at the
foot of every page has three parts: at the left the participant with the board in brackets, the project
and the table, "P9 Wren (Board 3) · Living with a dog · Table of Personal Experiential Themes", the board
left out for sending, in the middle the name documents carry, Confidential and the date printed, "Ada
Lark · Confidential · 31 October 2026", and at the right the page, "Page 2 of 4". The name is Your name,
in Settings, Experiential statements, under the Interviewer name, and while Your name is empty the
Interviewer name stands in. Word's document carries the same name as its author. Until 31 October the foot
named the themes file. Since 1 November the middle part sits halfway between the end of the left part and the
start of the right, so a long left part never runs into it, and when the three would still come closer than
about 6 mm the project's name in the left part is shortened at a word with "…" until they fit. The participant, the board,
the table, the name, Confidential, the date and the page are never shortened. Since 31 October the page's head
no longer has the date, the board's name and Current board at its top right, and since 1 November it is a grid
of two by two: at the left the participant with the table's name under it, smaller, and at the right PROJECT and
the project level with the participant, and RESEARCH QUESTION and the question level with the table's name, the
labels in a column of their own so the two values line up, the question wrapping in its own column. The GETs
print has the same foot, the project with the board in brackets and the part printed at its left, and the same
head: since 1 November the document's name as its title where the table of PETs has the participant, "Table of
Group Experiential Themes", the audit trail's and the full set's their own, and PROJECT and RESEARCH QUESTION to
its right as on the table of PETs (Adam: "it should be consistent across the PETs and GETs tables"), no rule, and
no line saying the GETs are marked complete. The Mac's web view draws nothing in a
page's margin, so until 31 October the Mac's own print had no foot line. Since then the app's window draws
the foot itself on every page, from the page's own words, so the Mac's print and its PDF carry the same
foot as Windows's and the PDF an agent makes. Safari's own print, in a browser's tab, still has none. Since 19 October the page opens
with the print dialog, where Save as PDF is one step, since the table is read in the Table view, and Print
at its top right opens the dialog again. A board with no PETs prints its head, and the Not placed list with its tick on. The labels and the order come from
the one place the Word document takes them, so the two never disagree, and the PET draft takes the same
labels (see Export). The workbook and the themes file are only read and nothing is written anywhere. A
workbook outside the project folder is refused, and so is a board the file does not hold, each as a page of
one line in the print view's faces, "That board is no longer among the participant's PETs boards, so nothing was
printed.", where until 17 October, later, it stood in the system's font and named the themes file, on the
print view's page and centred as its pages are, where it stood at the window's left edge. `auto=0` in the address leaves the dialog shut, for a look at the page. `/api/themes` carries
`print`, where the view is, and a page in front of a server from before it says "Restart the server to
finish this update." and opens nothing. `themes_print.py` renders it.

The same view is a participant's table. Open as table, beside each participant in the participant picker (see Another
participant's PETs), opens that participant's Current board, or the board last open when none is marked, in a tab of
its own with `auto=0`, the dialog shut and nothing on it to change. Two tables or more then sit side by
side in separate tabs, to look for what resonates from one participant to another. The participant on the screen
offers it too, a save still to go written first, and nothing else is written by it.

**AI help.** With AI features on in Settings, and its PETs switch, the screen carries one more
control, AI suggest PET titles in a label's Inspector. It goes out through the PETs model set in
Settings under PETs, the Experiential statements one unless another is chosen there, with the same key
(see Settings, The PETs model), and carries the project's research question. Its prompt is its own,
in `themes_ai.py`. The IPA guidance it carries is one file, `pet_guidance.md` beside the app, written
from Smith, Flowers and Larkin (2022), Smith and Nizza (2022), Nigbur and Chatfield (2025) and the
project's own rules: section 1, what a PET is, with rules 5, 6, 8 and 11 of section 3, the title, its
register, negative and unresolved material as valid and recurrence as grounding. It is read afresh on
every call, and editing it changes what the AI is told, with no restart. A file with no rules under
its section 3 is one line, and nothing is asked. Nothing moves by itself: a title goes on only when he
picks it. Every control that calls an AI model carries the sparkles, AI suggest under the statement
field, AI suggest in the test bench in Settings and AI suggest PET titles in a label's Inspector, and
no other control does, Auto-arrange and the sidebar button included.

New AI board, AI review and AI revise went on 11 November 2026 (Adam): an agent of his own through MCP
does that work better (see Working with an AI agent). A board an AI made before then is an ordinary
board now, and a board's review rounds and revise thread from before, `review` and `revise`, stay in
the themes file as they were, read by nothing and never sent.

The cog at the right of the PETs bar opens the same Settings card the statements screen's does, on PETs,
its own category, with its own model under AI. Saving it shows at once, the switch and the model's name
in the Inspector's titles, and the band takes a question changed in Project settings. A change to the
rounds made from here, Work in rounds ticked or unticked among them, reopens the statements screen's
participant on the way back to it.

AI suggest PET titles, one label with the sparkles, sits in the Inspector for a label alone, a PET or a
sub-theme, and never for a card, since a title belongs to a group of statements. `N` outside a field
does the same, opening the sidebar on the Inspector when it is not showing, since the titles land there: on the label
selected, or the one the Inspector shows. With cards selected and no label, `N` asks nothing and says
in the canvas's line "Group the statements first (G), then ask for titles." A press saves the canvas,
then sends the label by its id and the board by its own, and the server builds the prompt from the
board and the workbook, not from a list the page sends. The system prompt carries, in this order, the
introduction, the research question, section 1 of the guidance file, what a PET is, read from the file
afresh on every call, a line on what an experiential statement is, the researcher's own words for what
a stretch of the transcript means for the participant with the participant's own phrasing kept in the
quotes beside it, then the task, three titles from different angles, each grounded in the
statements and their quotes and none repeating a label on the canvas, then rules 5, 6, 8 and 11, the
format line and the shape of the answer. A guidance file without section 1 sends one sentence on a
PET in its place. The user prompt sets the PET out: its title, or "no title yet", his note on it, then each statement in the order the canvas reads them,
with its sheet when the participant has more than one and its timecode, and under it its own quote in
inverted commas with its timecode, a picked quote marked "(picked)". A passage with no quotes
says nothing under its statement. The sub-themes sit under it the same way, then come the other labels
on the canvas and the closing line. A sub-theme asked for says which PET it sits in. When the two
prompts would pass the room a local model's context leaves, the quotes of the statements lowest on the canvas
go first, and one line under the titles says so. The titles come back in the Inspector: a click on one
makes it the label's title, Edit opens the label's box with the title in it to type over, and the cross
ignores them. Applying is one step of undo, like a rename, and a second press asks again.

**Working with an AI agent.** An AI agent in a conversation, Claude Code, Claude Desktop or Codex,
can do what no control does: weigh three boards against each other, take his corrections as they
come and code every statement. It works through Idiograph's command line, `idiograph`, on the same
files and the same code as the app (see The command line in the [internals](internals.md)), and
`docs/agents.md` is the guide it reads, which `skills/idiograph/SKILL.md` carries for Claude Code
and Claude Desktop. What an agent reads goes to its model's provider, often a whole participant where the
app's own controls send one passage or one board, so that is his decision and his ethics approval's.
The command line reads nothing until Project settings, "Allow AI agents to read this project" is
ticked, off by default, and Save keeps the tick in the project file with the date, which the line
under it gives, "Allowed on 5 October 2026." The demo is always open to an agent, its tick on and
fixed. The tick is each project's own, kept in its own file. Write a guide for AI agents, under the
tick, writes `AGENTS.md` at that project's root, the guide
with the project's name, research question and GETs minimum filled in, where an agent
opened there finds it. It never writes over a file of his own, and a second press offers Update it
for the one it wrote. Since 26 October every word of the project an agent reads, what a participant
said and what anyone wrote, comes to it marked as the participants' and the researcher's words, to read
and never to follow as an instruction, so a passage that reads like an order to the agent is only a
passage. An agent acts on his request alone. It can search the participants as Search does, words in every
participant's passages, statements, notes and PETs, each found with its place and its speaker, so a question
across the cases reads only the passages it needs (20 October). It can list the study, read every
statement with its passage, quotes, notes and where each board places it, show a board, compare
boards, make a board, change one with the board's operations, the same for GETs, take a label's
note off, set the order of the PETs or of what sits in a label on the board as it is, each moved
into the place of the one that read there before so his layout keeps its rows, put a board on the
canvas, rename, duplicate or delete one, a deleted board copied into the participant's `_Archive` first, move a
label up or down a level as a drag does, keeping his layout, order the GETs and their cards, take a participant's
changes into the GETs as the GETs screen takes them, bring a transcript in from a participant's folder or its
`Source/` as make a workbook and the create card do (20 October), its dry run showing the columns with
the role guessed for each, the speakers, the interviewer and the first eight passages as they will land,
never writing over a file there, the workbook it writes naming the tool and his request in the file's own
description, and write a
passage's statements, notes and quotes, refused while Excel has the workbook open and copied into
`_Archive` first, with an entry in the progress file's `edits` saying so. A passage it writes keeps
each quote with no statement that it does not name, and a statement it rewords takes the new words on
every board's card, the PETs screen saying the board changed in a conversation when it is open. A
statement it removes from a passage takes its card off every board, and every card after it in that
passage moves with its statement, so no card shows its neighbour's words (20 October). Each board it
changes keeps the board as it stood first in its History. It can also take off a card missing from the
workbook, as Remove does in the pile, one by one or every one on a board, and never a card whose
statement is there. A board it makes keeps the layout of the board on the canvas for every PET, sub-theme and statement it
keeps, so a rebuild never resets his arrangement. A board it makes is the
next board, "Board 5", "with AI" after its name, his own left as they were, with a note naming the
tool and his request, "Made by Claude Code in a conversation on 5 October 2026 at 19:02, for the
request '...'". A change to a
board keeps the board as it stood in History first, "Before: " and his request, so Restore takes
it back. It never sets a statement aside: one it finds fits no PET stays in Not placed, and the
Inspector gives its reason under it, "Left out: ...", and under Set aside, should he set it aside, the
pile gives it under its words. With AI features on, a statement's short id, `S12`, stands
small and faint after its timecode in the Inspector, the same id the agent names it by, so either
can name one in the conversation. The page notices what an agent writes. On a focus of the window and every thirty
seconds the PETs and GETs screens ask. A change made in another window of this Idiograph is his own
(20 October, for two-screen working) and comes onto the canvas by itself, his canvas saved first. A
change made outside the app, by an AI agent's command line or MCP or by hand on the file, shows a bright
orange card in the top right of the canvas, "Changes made elsewhere", with Update, which saves the
canvas first, then loads the board where he had it, and stays until he presses Update or its cross. A
board added outside says "Board 5 added in a conversation.", with Show it, which fits the new board to
the view. Nothing jumps before he asks. The server tells the two apart by the files it wrote itself:
each write of a themes file, a GETs file or a workbook notes the file's time, and a file whose time has
moved since was written by something else. The list of what it wrote is kept in the app's own state
across a restart, so a file left as the app last wrote it is still its own after one, and a file changed
while Idiograph was closed is said as from elsewhere. A save from a PETs canvas that has not shown the change yet is refused, the
canvas kept in the board's History as "The canvas when a conversation changed this board", so
neither his work nor the agent's is lost. A change from a conversation leaves every PET, sub-PET and
statement it was not asked about in the order it read, in the table and the PDF as on the canvas, and a
statement it moves into a PET or a sub-PET goes in last there. Room the canvas makes for a board whose
type takes more space than the agent allowed for never changes that order either. Since 19 October every save of a board carries the board as
the window last read it, so a save over a board changed since, in another window or, on the GETs
screen, by an agent, is refused with nothing written. A card in the top right of the canvas says "This
board has changed since this page was loaded, so nothing was saved. Your words are still here.", with
Reload, which puts the board as it now stands on the canvas, and Overwrite, which saves the canvas over
it. Until he chooses, nothing more is saved. Sift's search plan does the same for a plan saved in
another window, the card at the head of the screen saying "plan". An agent's change that carries the
version it read is refused the same way when the board changed after it read it. Experiential statements does the same for a passage an agent
wrote, "A passage was written in a conversation.", with Show it, which saves the passage in front of him
and opens the participant on that passage. One writer goes at a time: the app and the command line take the
same lock around every write. The command line and the MCP server are his own tools outside the app,
so they work whatever AI features says, the tick deciding which projects they read.

**Add Idiograph to Claude Desktop.** For a researcher who works in Claude Desktop or Cowork and
never opens a terminal, Idiograph's MCP server offers the command line's commands as tools, the same
work on the same code. In Project settings, after Write a guide for AI agents, Add Idiograph
to Claude Desktop opens a small card with the entry that runs the server on the project shown, its
root as `--root`, or `--demo` for the demo, `--demo ta` for the thematic analysis demo: from source the venv's python running
`mcp_server.py`, in the Mac app the app's own executable with `mcp` first, and in the Windows app
`Idiograph-console.exe` in the app's `server` folder with `mcp` first. Add writes it into
Claude Desktop's settings file, `~/Library/Application Support/Claude/claude_desktop_config.json`
on a Mac and `%APPDATA%\Claude\claude_desktop_config.json` on Windows, under `mcpServers` as
`idiograph`, every other entry kept and the file as it was copied beside it first, its name with
`.before-idiograph-` and the time after it. A file that is not valid JSON is refused in one line and
left as it is. The line under the card then ends "Restart Claude Desktop to use it." The same card
gives the entry to copy for any other client and the one line for Claude Code,
`claude mcp add --scope user idiograph --` and the same command, each with Copy. User scope lets
Claude Code find Idiograph in whatever folder it starts in, where `claude mcp add` alone keeps it to
the folder it was run in (20 October). A board or a passage written through the tools
names the client, "Made by Claude Desktop in a conversation", and the tick still holds: with it
off, every tool answers with the line that says where to tick it. Beside the tools the server offers a
prompt, Start working with Idiograph, and resources (19 October), so an agent that has never seen
Idiograph finds its way in from the server alone. The prompt is what a new agent takes first: what it
reads goes to its model's provider, he makes every decision, the project as it stands, a dry run before
every write and where the rest is. Claude Code shows it as a slash command, and Claude Desktop among its
prompts. The resources are the guide for agents, whole and section by section, the files' schemas, and
the project's `AGENTS.md` once Write a guide for AI agents has written it. With the tick off the prompt
and the project's `AGENTS.md` give the same line as the tools. An agent adds an exploratory note to a
passage and keeps the notes there, where before a write of notes took the place of them all.

`/api/themes-ai` carries the titles, `op` of `names`, the workbook, `version` and `group`, the label's
id, through the same `ai_route` as a suggestion, refuses with the switch off, and refuses any other op
as something the AI help does not do. It answers with up to three `names`, and `said` when quotes went
for room, and writes nothing. The page also sends `statements`, `label`, `note` and `others` beside the
id, the shape a server from before this reads, and a body with no `group`, from a page before it,
builds the prompt it always did from them, so neither side breaks the other. `/api/themes` carries
`ai`, whether the switch is on and which model answers, read from the settings and never the key,
`platform`, which says whether Show in Finder can be offered, `project`, for the band, and `config`,
the settings Settings opens with over this screen. `/api/settings` answers a save with `ai` beside
`config`, so the titles take a new model at once. A page in front of a server from before this reads
the switch from its own copy of the settings, and a press then says "Restart the server to finish this
update." and does nothing else.

**Guidance.** Guidance, the sidebar's tab after the Inspector, holds a short reminder to hand while grouping, as
the statements screen's guidance holds one for statements: how many PETs, how to group, how to title,
what to discard, what goes first inside a PET, and what to ask before finishing. The sidebar button opens the sidebar on it when it was the tab left showing.
Each group's heading is in the label face a step smaller, as the statements screen's guidance's section headings are, and each
line under it is in the serif at that guidance's size, a plain line with a small mark before it. A line in
inverted commas keeps them. The tab scrolls when the sidebar is shorter than the text, and at its foot one
line in the small type says where the text lives: "From themes_guidance.md beside the app. The AI reads
pet_guidance.md.", the second sentence only with AI features on. Nothing in the tab calls a model, so
nothing in it carries the sparkles.

The lines live in `themes_guidance.md` beside the app, in the format of `guidance.md`: an intro the
app never shows, then a `##` heading for each group with its lines under it, each starting with
`- `. One parser reads both files, `guidance_sections` in `server.py`, which keeps this file's
headings as written. `/api/themes` carries them as `guidance`, a list of `{"heading", "lines"}` in
the file's order, read afresh on every open of the screen, so an edit shows on the next reload with
no restart. A missing file is an empty list, and the tab then says there are no lines to show. A
page in front of a server from before the tab gets no `guidance`, and the tab says "Restart the
server to finish this update." The AI never reads this file. What the titles are told is
`pet_guidance.md` (see AI help), the fuller text this one is distilled from.

**Autosave and the file.** Every act writes the whole board on the canvas about 300 ms after the last
one, one save at a time. Beside the board's name the save state reads "Auto-saved" with a tick whenever
the canvas is what the file holds, from the moment the screen opens, so a fresh open says "Board 1 ·
Auto-saved", and "Saving" while a save runs. A save that fails leaves a line there saying why, in the
amber as every failure line is, where it stood in the crux orange until 17 October, later, as did the
boards menu's line when a board op cannot go ahead and an AI title's line, and the
way back then keeps the canvas open. Opening writes nothing: a participant with no file is offered its first
board, and the file is written on his first move or his first board op. It is
`<case>/Working/<stem>.themes.json`, beside the progress file and with the stem the progress file uses:

```
{"schema": 2, "case": "P8 - Wren", "workbook": "P8 Wren - EN & ES.xlsx",
 "created": "2026-10-01T22:10:04+01:00", "updated": "2026-10-01T22:31:40+01:00", "current": "v1",
 "chosen": "v1",
 "complete": {"at": "2026-10-04T16:20:11+01:00", "board": "v1", "name": "Board 1"},
 "boards": [{"id": "v1", "name": "Board 1", "note": "", "created": "...", "updated": "...",
             "cards": {"Initial:12:0": {"x": 40, "y": -120, "text": "..."}},
             "groups": [{"id": "g1", "label": "...", "members": ["Initial:12:0", "g2"],
                         "x": 40, "y": -160}],
             "discarded": ["Initial:30:1"],
             "picks": {"g1": ["Initial:12:0"]},
             "notes": [{"id": "n1", "text": "merge with Mornings?", "colour": "yellow",
                        "x": 260, "y": -120, "in": "g1"}],
             "quoted": {"Initial:12:0": "the words of the quote"},
             "history": [{"id": "r1", "at": "2026-10-01T22:15:02+01:00", "name": "", "auto": true,
                          "state": {"cards": {...}, "groups": [...], "discarded": [...], "picks": {...}}}]}]}
```

`case` is the participant by its pseudonym, for the cross-case step, and the second part of a folder name never
reaches it. A card keeps its place and the text it had when the board was made, and a group keeps its
id, its label, its note when it has one (see PET notes), its members, which are card keys or the ids of
other groups, and the place of its label. `picks` holds each label's picked quotes by quote key, and a
label with none is left out. `quoted` holds the words of each picked quote as the workbook read them at
the last save, which the server writes and the page never sends, and `cut` the cards a trim cut, a
record a trim under its id, kept until that trim is undone. `ai` holds why a statement was left out,
by an agent or by a New AI board before 11 November 2026, and a board with no reasons carries none.
`review` and `revise`, a board's AI review rounds and revise thread from before 11 November 2026, are
kept as the file holds them, read by nothing, and the page sends neither, so a save leaves the file's as
they were. `notes` is the
board's sticky notes (see Sticky notes), each its id, its words with their lines, its colour, yellow,
pink, green or blue, its place, and `in`, the id of the group it sits in, which `normalise` drops when
it names no group, so the note stands free. A note is never among a group's members. A board with none
carries none, so a file from before them reads and writes as it did and the schema stays 2, and a save
from a page that sends no `notes` leaves the file's as they were. A revision holds them, so its hash
takes a note's words, its colour and its place, Restore brings them back, Duplicate copies them, and
neither Copy to board nor a board an agent makes carries one. `/api/themes` carries them as `stickies`, since its
`notes` says a save keeps a PET's note. Whatever the
page sends, the server keeps a member in one group at most, takes a discarded card out of every group,
and keeps a pick only once, only for a label that is there and only of a row with a card under it.
`current` is the board on the canvas. `chosen`, beside it, is the Current board, the one he is going
with, and never takes the place of `current`: it is set and cleared only through the board op `choose`,
and through `delete`, which gives it to the last board left when the Current board goes, kept only
while it names a board the file holds, and a file with none marked carries none. `complete`,
after it, is the PETs marked complete (see The Current board), set by the board op `complete` and
taken off by `reopen` alone, and a file with no mark carries none. A save from
the canvas writes that board in place and keeps the name, the note and the history the file holds, which
change only through the board ops, so a save sent just before a rename can never put the old name back.
A save of a board the file does not hold is refused, so a page left open on a board deleted since cannot
bring it back, and with no file yet only the first board is taken. `history` is the board's revisions,
oldest first, each with its id, when it was made, its name, empty for one without, whether the timer
made it, and its `state`, the board's `cards`, `groups`, `discarded`, `picks`, `ai`, `quoted` and `cut`
as above, written on one line of its own so a long history stays readable. A board's id is `v1`, `v2`
and on, from when the boards were versions, and is never shown. Schema 1, until 2 October 2026, held the
boards under `versions`, named Version 1, Version 1 copy and AI proposal 1. Such a file is read as
schema 2 in memory, its names said the new way, Board 1, Board 1 copy and AI board 1, and the "from
Version 4" in an AI board's note too. Opening it writes nothing, and the next save writes schema 2. The
screen writes the workbook in one participant only, a statement edited in place (see Editing a statement), and
otherwise reads it read-only and without the lock guard, so a workbook open in Excel opens here as it
was last saved and nothing is said about it. A themes file that cannot be read
is refused with a line and never written over. The demo's themes file is gitignored, as its progress
file is.

`/api/themes`, with `{"workbook": ...}`, answers with the cards merged with the stored board, the key
quotes of every row that has any, the board's picks and `history`, its revisions newest first without
their states, with `board` it shows that board in place of the one last open and writes nothing, and `/api/themes-save`, with the workbook and the board as `version`, writes it, and with
`revision` of `auto` from the timer answers with the history when it kept a revision.
`/api/themes-versions` carries the board ops, with `op` of `new`, `duplicate`, `rename`, `note`,
`switch`, `delete`, `choose`, `complete` or `reopen`, `id` for the board, null with `choose` to clear
the mark and none with `complete` or `reopen`, and `name` or
`note` where they apply, and answers with the screen's state afterwards. The routes and the fields keep
the word they had when the boards were versions, and the answers keep `versions`, `version` and
`current`, with `chosen` beside them, the Current board's id or null, and `complete`, the PETs' mark or
null. `/api/themes-boards` carries the
rest, with `op` of `copy`, `revision`, `view` or `restore`, `id` for the board, `revision` for one of
its revisions, `group` and `to` for a copy and `name` for a revision. `view` writes nothing and answers
with the revision as the canvas draws it, and the others answer with the screen's state afterwards.
`/api/themes-export`, with the workbook and `version`, the board on the canvas when none is named, writes the
draft and the CSV and answers with both paths, and `shown`, the two as `Working/<file>`. With `op` of
`word` it writes the board's Word document at the participant's folder's root instead, never over a file there,
and answers with `word` and `shown`, the file's own name, and `dated`, true when the date went in it.
`/api/themes` carries `word`, and a page in front of a server from before it says to restart and writes
nothing. With `op` of
`reveal` it writes nothing and runs `open -R` on the file named, `file` as `shown` gives it, or on the
board's markdown draft, on a Mac alone, and refuses a file outside the participant's `Working/` folder or the
project folder, a Word document beside the workbook the one file outside `Working/` it shows. Every route refuses a workbook outside the project folder. A page in front of a server from before
them shows "Restart the server to finish this update." on the canvas, in the board menu, in the
Inspector where the quotes go, in the History tab, after a copy or after Export, and does nothing else.
Its autosave works as before and keeps no revisions.

**Re-reading on open.** Every open reads column C afresh, builds the cards again and lays the stored
board over them, words before index. Rows renumbered by a trim or an assignment never get this far,
because the themes file moves with the rows in the same request (see Trimming the ends). A stored card whose
key no longer carries the words it was made with looks for them first: it takes the key of a line
with the same words, the spacing aside and the case kept, that no other card has claimed, on its own
row first and then anywhere on its sheet. So a line inserted at the top of a cell, or taken out of
the middle of one, leaves every other card in its PET and its place with no mark, and so does a pair
removed on the statements screen or a pair whose place on its passage moved. The key changes
everywhere the board names it, its PETs, Set aside and the reasons for what was left out, and the file
takes the new keys on the next save, since opening writes nothing. A revision follows its words the
same way when it is shown and when it is restored, so a restore lands on the keys the workbook holds
now. Only then does the rule for a line apply. A stored card whose line reads differently at its key
is marked changed, a small mark on the card with what it read in its tooltip. The file keeps the
text the board was made with, the line as it reads now beside it, until he moves the card or acts
on it, and then the live line becomes the stored text. A stored card with no line is marked
missing: in a PET it stays in its place, faded, and in no PET the sidebar lists it last under Missing from
the workbook, with Remove to take it out of the board. A line no card claims gets a new card, waiting in
the sidebar's Not placed.
A pick follows its quote's words the same way (see Picks), and so do the CSV's Proposed PET column
and the print view.

## GETs

The step after PETs, across the study: every participant's PETs on one canvas, where the analyst looks
for what they share and where they part and groups them into group experiential themes. It is the
PETs canvas one layer up, the same code run in a GETs mode, so every act of that screen works here
as it does there.

**Opening it.** A wide card after the rows on each project's page, over them until 18 October, reads "GETs, across all participants", and
under it, in the small type, "3 of 6 participants in · Board 2", the participants the GETs file holds of the participants
of the study and the name of its Current board, "No Current board" when it has boards and none
Current, with "GETs complete" after them once marked. It opens the GETs of that project, from its
own root, and a project with no annotated participant has no card. The demo is a project of its own and
carries the same card after its rows. GETs is the third of Idiograph's tabs on each of its bars (see
Idiograph's tabs), which opens the GETs of the project the participant belongs to, the demo's for the demo, after
saving anything still to save. Back goes to where the screen was opened from, the participant list, Experiential statements
on the passage he was on, or that participant's PETs on the board it was on, and the tabs name each
screen of Idiograph on the bar. The GETs bar mirrors the PETs bar, Idiograph's lockup, then the tabs with GETs in front, and on the right Search, the bug for Send feedback and Settings, and under the band the toolbar with Participants at its left end and Inspector at its right end, each over the sidebar it opens (see One title bar and The bars since 26 October 2026), with the project's name in the band and no participant picker, since GETs is the project's, then the board switcher and
its save state and the Canvas and Table switch on the toolbar. There is no Export
button, since Export sits in the board menu (see Print). Until 19 October the counts stood on the bar too, "7 in GETs · 3 not placed", with "· 2 discarded" after them only when a card was in the bin, and after them Sticky note, Group, Undo and the shortcuts. They went to the status bar and the palette, as on PETs, where the counts read "3 GETs", "7 in GETs", "15 not placed" and "0 binned" (see The status bar and the palette).

**The bar at narrow widths.** The GETs bar gives way at the PETs bar's widths, and at 760px and below takes the three rows of Idiograph's tabs. Its project name is
longer than a participant's, so it truncates with the board's, until 19 October once the counts had gone. Measured again on 5 October 2026, the sidebar button in the place of the Inspector's, Board's and the shortcuts, on the demo's project as it is named now, "Living with a dog", its three participants
ordinary participants of a project folder, opened from the GETs card, it needs 773px at its fullest, 711 with the save state's mark alone, 481 without the counts, 441 once the gaps close up and 376 with the buttons slimmed, the bug counted, the word PETs on the way back adds 30, and on the demo itself
its tag adds 63, and 47 once the buttons slim. Measured again on 16 October with Participants at the left end and Group, Undo and the shortcuts on the bar, it needs 892px at its fullest, 826 with the save state's mark alone, 589 without the counts, 546 once the gaps close up and 435 with the buttons slimmed, and below 480px the names give way in full, as on the PETs bar. Below 480px Sticky note takes the buttons to the right edge, Group until 18 October, where until 16 October, with no Export, the Participants panel's button did. Down to 400px nothing overlaps and nothing scrolls sideways. Measured again on 18 October with the steps of the time and Sticky note, it needed 852px at its fullest, 789 with the save state's mark alone, 687 without the counts, 663 once the gaps close up and 529 with the buttons slimmed, and took its two rows where the PETs bar did. The tabs stay at every width (see Idiograph's tabs).

**What comes in.** The study is every participant's folder under the project's root with an annotated workbook, as the
participant list finds them, and for a folder holding two the one with a themes file, then the newest. A
participant goes by the pseudonym its themes file names. Opening writes nothing: each participant not yet in shows
as it would come in, its PETs and sub-themes in the pile, and the file takes every such participant on his first
act on the screen, a move, a label, a board op or a save from Settings. A participant with its PETs marked
complete comes from the board the mark names. Any other comes from its Current board, else the board
last open, and its cards carry "PETs not complete". A participant with no themes file reads "No PETs yet".
What comes in is a copy: each PET and sub-theme with its title, note, parent, sub-themes, statements
and picks, and every statement of the participant, placed, not placed or discarded, with its sheet, timecode,
words, quotes and exploratory notes, read from the workbook. Every sheet is pooled, the sheet
named on each line. The screen writes a participant's files only when a statement is edited on its card
(see Cards), and then through the PETs board's route.

**Cards.** A card is one participant's PET, sub-theme or statement, or a participant note. Over its words
it names its kind and pseudonym in the small sans, "PET · Juno", "Sub-theme · Juno", "Statement ·
Juno" or "Participant note · Juno". A PET's card counts its statements at any depth, and a
statement's carries its timecode and its sheet, with its PET and that PET's GET under its words,
"Mornings · Starting the day". The marks go at the foot: "PETs not complete" for a participant not yet
marked, and "No longer in Juno's PETs" for a PET his participant has dropped. Every card of a participant, a PET,
a sub-theme, a statement or a participant note, carries its participant's colour along its top edge and a
badge before its kicker, the participant's initial in a dot of that colour, "J", two letters where
two participants share one, "Ju" and "Ja" (see Colours). A PET's and a sub-theme's words are read-only
here. A statement's are not since 30 October (Adam: "Edit there too"): a double-click on a statement's card
opens it for editing on the card, as on PETs, and Enter writes it into the participant's own workbook,
the participant's PETs boards, the Participants panel and every GETs board's card taking the new words at
once and the participant staying in (see Editing a statement, under PETs). From 16 to 30 October that
double-click opened the statement's passage on Experiential statements, which Go to the passage in the
card's menu still does (see From a statement to its passage, under PETs). A double-click on any other card
opens the sidebar on the Inspector for it.

**A PET card unfolds in place (21 October, Adam's ruling of 20 October, from a tester's wish to see a PET's
statements on GETs).** A PET's or a sub-theme's count, "7 statements", carries a chevron, and a click on it,
or Unfold in the card's menu after Inspect, unfolds the card where it stands: under its foot, behind a
hairline, its own statements, then each of its sub-themes by its title with the statements under it, each
statement with its own quote and its timecode, its exploratory notes too when Notes is on, and a statement
stacked under another on its participant's board under its top, a step in, as on PETs. The chevron again,
or Fold in the menu, folds it. Nothing is placed: unfolding brings no card onto the board and changes
nothing in the GETs file, so it is no step of undo. What stands below the card moves down to make room as
it does for a quote, and back when it folds. The cards he leaves unfolded stay unfolded after a reload,
kept in the browser with the board's view, Canvas or Table, for each board of each project. Auto-arrange,
Arrange by participant and Fit all take an unfolded card at its whole height. The Table view and the print
are unchanged. A PET with no statement and no sub-theme, a statement's card and a participant note have no
chevron.

**The canvas.** As on the PETs screen: `G` puts a label over the selection, a label over cards is a
GET and a label over labels a sub-theme, and a GET takes the next of G1, G2. Boards, the Current
board, history, undo, Set aside, sticky notes, Auto-arrange and the Inspector stand as they do there,
through the GETs routes, and the sidebar holds the Inspector, Guidance and History (see Table and AI help). The
minimap stands above the zoom bar as it does there, each card in its participant's colour wherever it stands, and each GET's and
sub-theme's frame an outline in its tint (18 October). Every PET
and every sub-theme of a participant lands in the pile as a card of its own on first coming
in, in no GET, so a sub-theme can sit under one GET and its PET under another. A sub-theme's groups,
at any depth, ride inside its card with no card of their own: its count takes in their statements, its
Inspector lists them under Groups, and AI suggest GET titles sends their statements with the sub-theme's.
Take, New board and Add every sub-theme all work this way. New board lays
every participant's PETs and sub-themes in the pile afresh, in an order seeded from their keys. Add every
sub-theme, in the board menu after Save a revision, gives a board made before sub-themes came in as
cards a card for each sub-theme of the study it has none of, a card set aside counting as one, all
in one pile in the nearest free spot clear of every card, label, frame and sticky note there, as one
step of undo. With none to add it says "Every sub-theme has a card on this board already, so
nothing was added." Copy to board is the PETs screen's alone.

**Arrange by participant (19 October, from a tester's reflection on IPA in ATLAS.ti).** In the board menu
after Add every sub-theme, and on a right click on empty canvas after New sticky note. It sets every
PET and sub-theme card that is in no GET and not set aside out in a row for its participant, the
rows in the Participants panel's order, each PET in the participant's PET order with its sub-themes beside it, and
each PET after the first a little further off, so it starts a small group of its own. A sub-theme
whose PET is in a GET or set aside goes at the end of its row, so a row reads PET by PET, each
followed by its own sub-themes. The rows go
below everything that stays, at its left edge: the GETs he has made, with all they hold, a
statement's card, a participant note and a sticky note stay where they are. It is one step of undo.
With every PET and sub-theme in a GET or set aside it says "Every PET and sub-theme is in a GET or set
aside, so nothing was moved."

**The Participants panel.** A sidebar of its own at the left of the canvas, the source the GETs are made from, as Figma keeps its layers on the left and its properties on the right. Its button, Participants, stands at the left end of the bar over it, before the way back, the same panel icon with its left part filled, "Show Participants" or "Hide Participants" in its tooltip, as Inspector stands at the right end over the sidebar at the right (16 October), where until then it stood before the sidebar's button near the cog with "Show the Participants panel" in its tooltip, and its cross sits at its head. It is open unless he closed it, which the browser keeps. It lists every participant of the study in participant order, with the participant's marks under its name: "PETs not complete", "No PETs
yet", "Changed since it came in" and "Out of the study" with the reason, and the swatch of its colour
at its right before its menu (see Colours). A participant with no PETs says "No PETs yet" once, in that line,
folded or open, where until 17 October, later, a participant folded open said it a second time at the panel's
left edge. Since 16 October each participant folds open to a tree, as its
participant's board holds it (a tester's ask, Adam's word): each PET, then under it its own statements and
its sub-themes, each sub-theme with its statements under it, a statement in one of a sub-theme's own
groups under that sub-theme, as its card carries them, and last a row Not in a PET, holding every
statement in none, not placed or discarded on its participant's board. Each level folds on its own with the
chevron at its left, a PET's, a sub-theme's and Not in a PET's row counting the statements under it,
and each statement is marked placed, not placed or set aside. The folds are kept as the panel's open
state is, in the browser, for each project, so the tree is as he left it after a reload and when he
comes back from a passage. One search over all of it matches names, titles, notes, statements,
quotes and exploratory notes, shows what it finds with the rows that hold it, and opens those rows,
a participant's name found showing all of the participant and a PET's or a sub-theme's title all of it. A chevron
pressed during a search opens or shuts its row until the search changes. Any
row drags onto the canvas as a card, a PET, a sub-theme or a statement at any level, into the GET under the pointer when there is one, and a row
whose card is on the board already moves that card there, out of Set aside if it was there. A click
on a row selects its card and brings it into view. Each is one step of undo. A double-click on a
statement's row opens its passage on Experiential statements, as Go to the passage in its card's menu
does, its card on the board or not, and the way back returns to the GETs board as it stood (see From a
statement to its passage, under PETs). A participant's menu, the
three dots at its right, holds Add participant note and Open
beside (see Open beside this one). A statement stacked under another on its participant's board (see Stacks)
stands under its top in the panel, its top's row saying "3 stacked", which opens them a step in, each a
row to drag, where until 20 October it stood under Not in a PET. The Inspector of a PET's card lists them
under their top, "Stacked under it". Below about 900px the panel lies over the canvas, as the sidebar does, stopping above the zoom bar, and at a phone's width it takes the whole width, where until 16 October, later, it left a strip of cut-off cards beside it, the bin and the zoom bar in view below it and never under it (17 October). Its list scrolls from
right under the search field, and once it has scrolled its top edge fades over a line's height, so a
row passing under the field fades out and never stands cut in half, as the transcript's column fades,
while at rest its first row stands whole (17 October, later). A level folded open carries a thin guide line from under its chevron down to its last row.

Since 20 October the Participants panel has **Set aside** at its foot, as the PETs board's sidebar has, in place of the bin: folded until he opens it, its count at the right of its head, each card set aside with its participant's badge and Put back, which puts it back on the board in no GET. A card dragged from the canvas onto it is set aside, `X` and Set aside in a card's menu do the same, and a row of it drags back onto the canvas. The Participants panel itself was already GETs' Not placed, so it gains nothing else.

**Colours (16 October).** Each participant keeps a colour of its own on the GETs board, so whose PET a card
is, and which PETs, sub-themes and statements belong together, shows at a glance, the participants staying
visible inside the GETs as the book asks (Smith, Flowers and Larkin, 2022, ch. 5), a tester's ask and
Adam's word. The colours are the participants' palette, eight of them, Blue, Olive, Plum, Brown, Indigo,
Teal, Purple and Slate, lighter in dark, none of them the crux orange and none red, each apart from
the others and from Supports' green, the amber and the red under colour blindness too. A participant takes
its place in participant order round the palette, the first Blue, the second Olive and so on, the ninth Blue
again, and its badge, its initial or the two letters, tells two participants of one colour apart. Since 21
October there are 25 (see More colours), so the ninth is Moss. The swatch
on a participant's row in the Participants panel, its badge in its colour, opens the colour choice under it,
"Juno's colour", with Default, the participant's own place in participant order, then the eight, a whole row each
with the participant's badge in its colour, the one it has ticked. A choice is applied at once, the cards, the panel and
the Table view drawn again, and kept in the GETs file under `colours`, which every screen and the print
view read. Default takes his choice away. It is no step of undo, since it is no part of a board, and
it stands on every board of the project. The badge goes with the participant's name in the Table view, the
audit trail and the print view's GET table and trail, and the canvas printed under Export keeps the
cards as they are, their colours with them.

**More colours (21 October, Adam's choice of 20 October, as a tester's studies have about 20 participants).**
The palette holds 25 colours: the eight first, then Moss, Spruce, Violet, Aubergine, Pine, Denim, Khaki,
Mulberry, Fern, Periwinkle, Umber, Grape, Ocean, Amethyst, Jade, Navy and Fig, each lighter in dark. A new
participant takes its own place in participant order while no one has that colour, and otherwise the next
colour free after it, so no two participants share a colour while one of the 25 is free. The colour choice
shows Default and the eight, a colour another participant has faint with whose it is, "Mabel's", then More
colours, which opens the 25 beside the menu in a grid of five, the participant's own ringed and each colour
another participant has struck through, with "Another participant's" under them. A colour another
participant has cannot be chosen, and every card keeps its participant's badge, so colour is never the
only way to tell participants apart. Neighbours in the picker's order, each and the next and each and the
one under it in the grid, stand apart as seen and under protanopia, deuteranopia and tritanopia.

**Colours told apart (16 October, later).** In dark, Blue, Indigo, Purple and Slate had read as one
pale lilac on the cards' edges and in the colour choice, so the dark colours are spread in hue and
lightness: Blue a pale sky, Olive a bright yellow green, Plum a pale mauve, Brown an ochre, Indigo a
strong blue violet, Teal a deep teal, Purple a strong orchid and Slate a grey. Each pair stands apart
as the light ones do, as small marks and under colour blindness too. Default in the colour choice
names the colour it gives, "Default (Olive)", and each row carries the participant's badge in its colour,
as its cards will. The badge's letter stays readable at every size it is drawn: on a card it grows as
the canvas zooms out, up to the card's top edge, and below 54% the badge keeps its colour without
the letter, which could no longer be read. It is larger beside a name in the audit trail, the Table
tab and the print view, and the canvas printed under Export grows it as the canvas does. A GET's
title on the GETs board takes its dot and its underline in the ink, so a GET never reads as a
participant's colour, and so do the left edge of each card in it, the stripe of its head in the
Table view and the underline of its title in the audit trail (17 October), its frame and its cards
keeping its tint as their wash.

**Participant notes.** Add participant note puts a card of his words in the middle of what is in
view, the sidebar open on the Inspector for it, its box ready: what he knows of the participant beyond the
transcript. Enter or a click away keeps the words, Shift + Enter starts a new line and Esc leaves
them as they were, each change one step of undo. A note sits under any GET and never counts.

**The Inspector.** On a PET or a sub-theme, its note, its sub-themes, its statements and its picks.
On a statement, its sheet and timecode, its PET and that PET's GET, its own quote and its
exploratory notes. Under a GET, a PET's picks and a statement's quote carry the ticks of Key
quote for that GET (see Table). On a participant note, his words in a box. On a GET, its count, the
minimum when it is under it, Auto-arrange and Audit trail side by side on one row (see The audit trail), its note, "Why this
GET", and the participants of the study, a participant with nothing under it saying "Nothing under this
GET".

**The count and the minimum.** Each GET's badge reads "6 of 8": the participants with a PET, a sub-theme
or a statement of theirs anywhere under it, sub-themes included, over the participants in the study. A
participant note never counts, and a second card of a PET counts its participant once, as does a PET with
its own sub-theme beside it. A PET under one GET and its sub-theme under another count the participant once
under each. A sub-theme inside a
GET carries its own count with no mark. The minimum starts at Smith's (2011a) band, every participant
for three or fewer, three for four to eight and half, rounded up, beyond eight, and stays his to
change. A GET under it keeps its place and its cards, and its badge takes a dashed outline with
"Under the minimum of 3" in its tooltip, as the label's tooltip says too. Nothing is removed or
hidden.

**One GET per PET.** On by default: a PET or a sub-theme sits under one GET at most, as every card
does on the PETs screen. Off, a PET's or a sub-theme's card carries Place also under in its menu,
which lists the other GETs and sub-themes and puts a second card of it under the one chosen, each
card then naming the other, "Also under Deciding". A pulled statement or participant note sits under
any GET. A PET under no GET stays in Not placed, which the counts in the bar give.

A statement's card on the GETs board says under its words where it comes from, "PET: Being trusted by the hive · GET: Belonging", the PET it sits in on its participant's board and the GET that PET's card stands under, or the PET alone while that card is in no GET, "Not placed in its PETs" or "Set aside in its PETs" when it is in none. Until 20 October the line gave the PET's title alone, which read as a note of unknown source.

**Changed since it came in.** On each open, a participant whose workbook and themes file are both older
than the time it came in is unchanged without a read, and any other is read again and compared with
its copy. Since 20 October (Adam, from a tester's feedback: "just take the changes automatically") there is
no Take the changes. A change he made in the app, on the participant's PETs or its statements, in this window
or another, comes into the GETs by itself as the screen opens, or within thirty seconds while it is
open, with "Brought in the changes to Juno's PETs." at the foot of the canvas, as one step of the
board's undo. A change made outside the app shows "Changes made elsewhere" with Update in the top right
of the canvas, which brings it in the same way, and until then the participant is marked "Changed since it
came in" in the Participants panel. Bringing them in keeps a revision of each GET board, "Before Juno's changes came in", its line in History, keeps each PET's place
by its id, then by its title, brings a PET or a sub-theme new to the participant in, not placed, in the nearest
free spot, as it does a top-level PET with no card, and leaves a PET gone from the participant where it is
with "No longer in Juno's PETs" on its card, never moved or set aside by itself. A card that comes in taller,
its PET given a description or a title a line longer, makes room below it: what it would run over, in its GET
or among the cards in no GET, moves straight down just far enough to clear it, and what that meets moves on in
turn, so a column keeps its order and nothing moves sideways (22 October). A sub-theme the participant
had when it came in and the board never held stays off it, and Add every sub-theme brings it. A
participant marked complete since it came in comes in from its marked board the same way.

**Mark GETs complete.** At the foot of the board menu, as Mark PETs complete is. It is refused,
saying which participants, "GETs were not marked complete. Waiting on Juno (PETs not complete).", unless
every participant in the study is in from its marked board and unchanged, and nothing more. It records
the time and the board, the Current board when one is marked and else the one on the canvas, fires
the third level of confetti once, and the menu then names it on that board and reads Reopen GETs,
which takes it off. The head row says GETs complete beside its count.

**Table.** The Canvas and Table switch on the bar, or T, shows the GET table of the board on the canvas, drawn
afresh with every act (see Canvas and Table). The sidebar's own Table tab went on 19 October, the switch doing
its job, and a sidebar left on it opens on the Table view. Each GET comes in canvas order, its title in its tint with its count, "6 of
8", the dashed outline and "Under the minimum of 3" when it is under the minimum, as on the canvas,
then its note and Audit trail (see The audit trail). Under it comes a row for every participant of the
study, in participant order: the pseudonym with its participant's marks, then what of the participant sits under the GET
in the order the canvas reads it, higher first, its PETs, sub-themes, statements and participant notes,
each with its grip to go under another GET. A card inside a sub-theme of the GET names it, "in Early
starts". Then the row's quote, and his note for the row. A participant with nothing under the GET reads "Nothing under this GET" in one plain line in the soft
ink, and a participant with no PETs at all "No PETs, so nothing under this GET", with no mark beside
the name, where the screenshot check found "No PETs yet" in amber and the line under it (17 October,
later), and a participant note alone leaves it so, since a note never counts. The quote starts as the first
pick of the participant's highest PET there, and failing a pick, the first statement there with a
quote of its own. On a participant's card under a GET the Inspector carries Quote for that GET, a PET's picks first
and then its statements' quotes, or a statement's own, each with a tick, the row's quote ticked,
filled when he ticked it and lighter when it is the one the row starts with. A tick on another makes
it the row's quote, and a tick on the one he ticked takes his tick off. Note, under a row, opens
a box for his note, and a click on a note opens it again: Enter or a click away keeps it, Shift +
Enter starts a new line and Esc leaves it as it was. Each tick and each note is one step of undo, and
both are kept in the board's `rows` (see The file). Print sits at the head of the table (see Print).

**The audit trail.** Audit trail, in a GET's Inspector and under its title in the Table view, opens a
card over the screen for that GET, its title in its tint, its count and its note, after saving
anything still to save. Five columns, Transcript passage, Quote, Statement, PET and GET, joined by
thin lines in the GET's tint, with a block for every participant of the study in participant order, the pseudonym
at its head with its participant's marks, and "Nothing under this GET" in one plain line when nothing of it
counts there, "No PETs, so nothing under this GET" with no mark beside the name for a participant with
no PETs, as in the Table and on paper (17 October, later). Its kicker, Audit trail, is in the soft ink
as every card's kicker is, never the crux orange, which design.md keeps for a crux, a quote and
the filled button (17 October, later). Each item under the GET draws its own path from the GET at the right: a PET or a
sub-theme through its statements at any depth and their quotes to their passages, the statements of
one passage together in one box, a statement pulled onto the board through its quotes to its passage,
its line crossing the PET column, and a participant note standing alone in its block, marked "Not
from the transcript", its line dashed. The row's quote carries Quote, and a statement with
no quote goes straight to its passage. A passage shows its sheet and timecode and the sentence round
the quote, the quote's words in bold, read from the workbook opened read-only, or its opening words
when the quote is not found in it. Its passages stand at the trail's own size, where a claim's larger
type in Trace had taken them over, and a box's small print, its kind, its place and its sheet, is in
the soft ink, which keeps 4.5 to 1 on the box's wash in dark where the faint ink did not (17 October). On a participant with a recording a click on a passage plays it from the
passage's timecode, and a second click pauses it. The lines are drawn from each row, so they meet at
any width and on paper, and the card is readable down to 900px, the trail scrolling sideways below
that. Print in the card prints this GET's trail (see Print). Esc closes the card, and
the canvas hears no key while it is open. Nothing is written. The server draws the trail, through
`/api/gets-trail`.

**Open beside this one.** In the PETs participant picker each other participant carries Open beside this one,
over Open as table. The canvas splits: his participant on the left as it is, the other on the right on its
Current board, else the board last open, read-only as a revision on view is, under a line naming the
participant, the board and Read-only. Nothing on it moves: a drag pans it, the wheel zooms it, Fit all
brings all of it into view, and its cross puts the canvas back whole. On the GETs screen a participant's
menu in the Participants panel holds Open beside, which puts that participant's board beside the GET canvas the
same way, the board its PETs came in from. Below 900px the two stack, his canvas above. Opening a participant or leaving the screen closes it. Neither
writes anything.

**Print.** Export, in the board menu above Mark GETs complete, and Print at the head of the
Table view, Export named as it is on PETs, opens a small card under the word Export. What to print is a list of
four, each its name with a line under it in the soft ink saying what it gives, the whole row choosing it (31 October,
Adam: never a choice left unexplained): GET table, "Each GET with a row for every participant, what of theirs sits
under it, its key quote and your note", Audit trail, "Each GET traced for every participant, from the transcript
passage to the quote, the statement and the PET", All of it in one document, "A contents page, each participant's
table of PETs, the GET table and the audit trail", and Canvas on one page, "The GETs board laid out on one landscape
page". Until 31 October they were four short buttons, GET table, Audit trail, Full set and Canvas, with the rest in
their tooltips. Under each participant then offers two the same way, Every statement and quote, "Everything of theirs
under each GET, with its quote", and Their key quote only, "The one quote chosen for them under each GET", the
choice the book leaves to the analyst, where they read Full and Selected. Then Descriptions, Include participant notes,
unticked each time, its tick in the ink since 17 October, later, where it was the crux orange, and
Leave out the board's name (For sending until 31 October), the same tick as under Export on PETs and kept with it, which leaves the board's name
off the page, its PET tables and its title, so the PDF saves as "Study - GET table" (19 October), and last
Participants table (11 November), off on a new install and kept as it is left, which puts a table of the participants
on a first page (see The label and the pen portrait in the exports), shown for the GET table, the audit trail and all
of it in one document. Canvas on one page prints the canvas itself as Print under Export does on the PETs canvas (see
Export, under PETs), every card whole, on one landscape page under the project's name and the board's, Under each participant
gone while it is chosen. Print opens the print view in a tab of its own,
`/gets/print?root=<path>&board=<id>&what=table`, with `trail` or `all`, `detail=selected` and
`notes=1` when chosen, after saving anything still to save. Save as PDF, beside Print at the card's foot
since 31 October, saves the same page as a PDF at the project's root, where the PDF an agent makes goes
and named the same way, with no print dialog, and a line names it once it is written. It is there for the
GET table, the audit trail and all of it in one document, the contents, each participant's table of PETs, the GET
table and the trail, and in a browser's tab too. For a participant's LPETs it opens Print, where Save as PDF is. With Canvas on one page chosen, since 1 November, Save as PDF saves the canvas's page
as the PETs canvas's Save as PDF does, at the project's root, "Study - Board 2 - GETs canvas.pdf", a participant's
LPETs beside their workbook, and Save as an image beside it saves the canvas's picture as a PNG named the same way, a
participant note on either only with Include participant notes. It is landscape A4 with a 14mm margin in
the faces of the PETs print, and it opens for reading on screen, Print at its top right opening the dialog. The
head is the table of PETs' (31 October, and since 1 November in full): the document's name as its title,
"Table of Group Experiential Themes", "Audit trail" or "Group experiential themes", with PROJECT and RESEARCH
QUESTION to its right, no rule under it, the board and the date in the foot. Under it come the board's note
and, only when there is one, any participant not complete, with no PETs yet or changed since it came in.
Until 1 November the head also said the minimum, "Minimum 3 of 8 participants, Smith's (2011a) band", and what
the pages hold, "Every item" or "Quotes alone": Adam had them taken off, and the settings stay where they are set. The GET table sets out
each GET as the Table view does, in a bar of its tint with its count, the dashed outline and "Under the
minimum of 3" when it is under, its note, and a table of Participant, Under this GET, Quote and
Note, Their key quote only keeping Participant, Quote and Note. In the print view on a narrow screen the table
keeps room for its four columns and scrolls sideways in its own box under the GET's bar, and the bar puts
its count and Under the minimum under the title, where at 360 pixels the columns stood a word a line (17
October, later). A quote stands in single curly quotation marks, ‘like this’, in the GET table and
the trail as in the table of PETs, where the two set straight double ones (17 October, later). A participant not
complete, with no PETs yet or changed since it came in stands in the warning's amber in the header, the
table and the trail, as the Table view sets it, where it was an orange brown (17
October, later). The audit trail gives each GET a page of its
own and keeps a participant's block whole on a page. On paper each block with paths opens on the five
columns' heads, so every printed page carries them as a table's headings do, where they stood at each GET's
start alone, and the screen shows them once under the title (17 October, later). Its words wrap whole, never through a letter: a
column too narrow for its longest word takes the room it needs from the others, on paper and in the
card alike, and in the print view on a narrow screen the trail scrolls sideways in its own box under
the GET's title, where at 360 pixels the PET and GET columns broke their words letter by letter (17
October, later), its five columns keeping about 720 pixels together there as the table does, where they
squeezed to a word or two a line (17 October, later). The full set opens on a contents page, then
each participant's PET table as it came into the GETs, in the print view's table of PETs, labelled the project's
way, each statement a row with its own quote on the right, a sub-theme after its PET's own statements,
Their key quote only keeping a row for each PET's picks alone, then the GET table and the trail. Participant notes appear nowhere in any of it unless Include participant notes is ticked. The
transcript stays the XLSX. Every file is only read and nothing is written. A folder that is not the
project folder or the demo's, and a board or a GET the file does not hold, are each refused as a page of
one line, in the print views' own faces on their white paper since 17 October, later, where it stood in
the system's font, and `auto=0` leaves the dialog shut. Every print view says it is in British English,
as the app's pages do. From the audit trail's card it prints that GET's trail
alone. `gets_print.py` renders it.

**AI help.** With AI features on in Settings, and its GETs switch, the GETs screen carries the PETs screen's AI
titles one layer up, with the sparkles, through the PETs model and the same key: AI suggest GET titles
in the Inspector of a GET. It carries the project's research question and section 4 of `pet_guidance.md`,
what a GET is and its rules, from Smith, Flowers and Larkin (2022, ch. 5, Step 7), read afresh on every
call. Guidance, the sidebar's tab after the Inspector, shows that section and section 5, the questions a
reviewer asks of a GETs board, with "From pet_guidance.md beside the app, the GETs sections the AI reads
on this screen." at its foot. Each card goes by its participant's pseudonym, each PET with its note, its
sub-themes and their statements, by sheet, timecode and words. Participant notes, sticky notes and a row's
note never go to a model, and nothing on the screen writes a workbook or a themes file. New AI board, AI
review and AI revise went from GETs as from PETs on 11 November 2026, and a board one made is an ordinary
board now.

AI suggest GET titles sits in the Inspector of a GET or of a GET's sub-theme, and `N` asks it as on
PETs. It sends what sits under it across the participants, each PET and sub-theme by its title with its
statements, each participant named and one with nothing there said so, and its count against the minimum,
"It holds material from 2 of the 3 participants, and his minimum is 3.", with the other GETs' titles so
the three stay distinct, and rules 5 to 8 of section 4, recurrence, negative and incomplete
trajectories, the title in the participants' language, typically five to nine words, and no cause. A
click on one takes it, and Undo puts the old title back.

`/api/gets-ai` carries it, `op` of `names`, and refuses with the switch off, any other op, and on a thematic
analysis project's Themes board. A page in front of a server from before it shows the control from its own
copy of the settings, and a press says "Restart the server to finish this update."

**GETs' rules.** Project settings holds them under GETs (Settings' own category from 20 October until 5 November 2026, and the cog over this screen opens Settings on PETs since): One GET per PET,
the Minimum stepper with "Smith's band" beside it while he has not changed it, and the study, each
participant with a tick in the ink, off the crux orange since 17 October, later, as every tick is. A participant taken out asks one line of reason, a pilot for one, and Save refuses one
with no reason. A participant out of the study leaves the count and the band, and its cards stay where they
are. These live in the GETs file, since the demo's project file refuses a save.

**The file.** `idiograph-gets.json` at the project's root, beside `idiograph-project.json`, written to a
temporary file and moved over the old one as the themes file is, and the demo's is
`demo/idiograph-gets.json`, gitignored:

```
{"schema": 1, "created": "...", "updated": "...", "current": "b1", "chosen": "b1", "complete": null,
 "settings": {"minimum": null, "one_per_pet": true},
 "study": {"P8 - Wren": {"in": true}, "P9 - Ash": {"in": false, "reason": "a pilot"}},
 "colours": {"P8 - Wren": 5},
 "cases": {"P8 - Wren": {"workbook": "P8 Wren - EN & ES.xlsx", "board": "v3", "name": "Board 3",
     "complete": true, "came": "<iso>", "hash": "<state hash>", "state": "in",
     "pets": [{"id": "g1", "title": "...", "note": "...", "parent": null, "subs": ["g2"],
               "statements": ["Initial:12:0"], "picks": ["Initial:12:0"]}],
     "lines": {"Initial:12:0": {"sheet": "Initial", "row": 12, "time": "02:10", "seconds": 130,
               "text": "...", "quotes": ["..."], "notes": ["..."], "pet": "g1", "discarded": false}}}},
 "boards": [{"id": "b1", "name": "Board 1", "note": "", "cards": {"P8 - Wren/g1": {"x": 0, "y": 0},
     "P8 - Wren/es/Initial:12:0": {"x": 0, "y": 0, "text": "..."}, "P8 - Wren/pn/1": {"x": 0, "y": 0, "text": "..."}},
     "groups": [{"id": "G1", "label": "...", "members": ["P8 - Wren/g1"], "x": 0, "y": -40}],
     "discarded": [], "picks": {}, "notes": [], "rows": {}, "history": []}]}
```

A card's key names its participant and kind: a PET or a sub-theme by its group id, a second card of one
with `/2` after it, `es` a statement and `pn` a participant note. `hash` is the copy's hash as the
history hashes a revision, and `state` is `none` for a participant that came in with no PETs. `rows` holds
the GET table's rows by GET and then by participant, `{"G1": {"P8 - Wren": {"quote": "Initial:12:0", "note":
""}}}`, the quote he ticked by its sheet, row and place among the row's quotes, and his note
for the row. A row with neither is left out, and so is a GET no longer on the board, so a new GET
that takes a gone one's id starts with none. The page sends the rows with the board, and a page from
before them sends none, which keeps the rows the file holds. A board keeps `ai`, the reasons for what an
agent left out, and `review` and `revise` from before 11 November 2026, as a PETs board keeps them. A
`cap` under `settings` from before then, the most GETs a New AI board proposed, is read as nothing. `colours` holds
the colour he chose for a participant, by its label, its place in the participants' palette from 0, Blue, to 7,
Slate, and is missing until he chooses one, a participant not in it taking its place in participant order (see
Colours). Rename carries it to the participant's new label. A page in front of
a server from before GETs says "Restart the server to finish this update." on the canvas, in the board
menu and under GETs in Project settings, and changes nothing. A page in front of a server from before the
colours draws each participant in its place in participant order, and a choice says "Restart the server to finish
this update."

## Search

Search finds words across the app (17 October, and Sift, Trace and Home since 18 October).
In Idiograph it finds a passage, an interviewer note, a statement, a quote, an exploratory note, a PET,
a sub-theme, a PET's note, a sticky note, a board's note, a GET and its note, a note on a row of the GET
table, a participant note, a participant by its name and the research question. In Sift it finds a record by
its ID, its title, its abstract, its authors or its journal, a decision note, one of your fields, Notes,
Digest, Critique and the columns you added, an answer on the form of Extract and appraise, a key excerpt,
and the plan's search terms and exclusion reasons. In Trace it finds a claim, a reference and a claim
note. AI suggestions, the AI's passages and the text of PDFs are left out. `Cmd + F` (`Ctrl + F` on
Windows and Linux) opens it on every screen, Home, the statements screen, PETs, GETs, a
project's page, Sift's screening and its Search strategy and Trace, from the fields as well, and so
does Search on the bar, the magnifier in the place Find had on Idiograph's bars and before Shortcuts on
Sift's and Trace's. While a card stands over the screen the browser keeps its own find.

The card stands under the bar, the field first and Search in at its right, and while it is open a
wash of the paper lies over the rest of the screen under the bar, so nothing cut beside the card or
under it reads as part of it, as the guidance sheet's wash does (17 October, after the screenshot
check). A click anywhere in the wash closes the card and goes on to do what it does. On a project's
page the page comes up to the project's name and the card stands under it, so the name stays in sight,
and on Home the card stands under the lockup and the head's tools, the days under the wash,
so a phone's width keeps its room for the results. While more results wait below, the last one in
sight fades at the card's foot. Every word typed is found, in any order, case and accents aside, so
"walk dog" finds "the dog's walk" and "cafe" finds "café". Each word finds its other forms too, so
"sleep" finds "sleeps", "sleeping" and "slept", and "walked" finds "walk" and "walking", each under the
wash. Words in quotation marks are found together and just as typed, so "sleep" in quotation marks
finds sleep and never slept.

Beside Search in stand two ticks, Whole word and Match case, as Find and replace has them (6 November, after
"cat" found "catch"). Whole word is ticked when the app starts, as it is in Find and replace, and Match case is
not. With Whole word ticked each word is found only as a whole word, together with its other forms, so "cat"
finds "cat" and "cats" and never "catch" or "catalogue", and a phrase in quotation marks is found only where it
starts and ends on the edge of a word. A letter or a digit beside the word rules the place out, and a stop, a
comma or an apostrophe does not, so "cat" is found in "the cat's coat". Untick Whole word and a word typed is
found inside a longer one too, so "cat" finds "catch". With Match case ticked each word is found in the case
you typed it, so "Will" finds the name and never the verb, and accents are still set aside, so "Cafe" finds
"Café". A word's other forms keep your case, "sleep" finding "slept" and "sleeps" and never "Slept", and "Sleep"
finding "Slept", and a word of mixed case such as "McKee" is found as typed, with no other forms. The two work
together. The words under the wash follow the ticks, the results change at once when you tick one, and the ticks
stay as you leave them each time the card is opened again, on every screen, for as long as the app stays open,
as Find and replace's do.

Search in starts at This participant on the statements screen and on PETs, so a participant is taken in depth and on
its own before another meets it, as the book has it, and at This project on a project's page and on
GETs, where meeting across the participants is the step. On Sift's screens it starts at This Sift project, on
Trace's at This Trace project, and on Home at Everything, every project Home
lists, the demo among them. Everything is the last choice on every screen, and on Home,
where it is the only one, Search in does not show (18 October, later). This project reaches every
participant of the project, its GETs, its participants' names and its research question. This Sift project reaches
the screening its Screening step opens, or on the screening the run that is open, and the newest
version of its plan. This Trace project reaches each manuscript as Trace reads it, the references its
claims take and your notes on the claims, or with no manuscript yet its reference list, and a reference
two manuscripts share is found once. A scope widened goes back to the screen's own at the next opening.

At the card's left stand the kinds found under Kind, each with its count, and with This project the
participants and the sheets too, under Participant and Sheet. With Everything the kinds stand under their parts'
names, Sift, Idiograph and Trace, in the order a study does them, and the projects under Project. Ticking
one shows that kind, participant, sheet or project alone, ticking two shows either, and each ticks from its
whole row. Where the column is too short for them all, the last row in sight fades at its foot and the
column scrolls to the rest. Below 700px they stand over the results, the first heading and three whole
rows of ticks, and More under them shows the rest, Fewer the three rows again, and a row brought into
the box by Tab shows them all as More does. A heading whose rows are all behind More shows with them and
never over nothing, as Project stood at 360 (18 October, later). A row under the pointer takes a fainter ground than a ticked
one, so it never reads as ticked. At the right each result gives its kind in small capitals, its words
with every word typed under the find's yellow wash, a long passage cut round the first word found, and
where it is in small type, "Juno · Initial 03:55", "Board 1 · PET B", "GETs · Board 1", "R010 ·
Abstract", "Search strategy · Block 1 · Ponds" or "seed protocol.md · Background · Okafor, 2019", with
Everything the project's name first. The first 200 stand in the list, and "200 of 1,234" under them says
when there are more. A search that finds nothing says Nothing found.

Up and Down walk the results, the one in focus on the sunk paper with the orange bar at its left and
one under the pointer on a fainter ground, Enter opens the one in focus and a click opens any, from
whichever screen the search was made on, the screen in front left as its own way out leaves it. A
passage opens on the statements screen at that passage, and an interviewer's at the participant's
passage after it with his in view, his note open when the result was his note. A statement or a key
quote takes the caret in its pair, and an exploratory note in the notes. A PET, a sub-theme, a PET's
note or a sticky note opens PETs on its board with it selected in the middle of the canvas, a GET, its
note, a row's note or a participant note opens GETs the same way, and a participant or the research question
opens the project's page at the participant's row. Opened from PETs or GETs, the statements screen's Back
returns to the board, as Go to the passage on a card does.

A record opens on Sift's screen at its stage, Screen by title and abstract until it has Yes or Maybe
there and Screen by full text after, an answer on the form at Extract and appraise while the record is
one of its papers, and a decision note or a key excerpt at the stage it was made at. There the record
opens with the words found in view, the caret in the decision note or the field, or the key excerpt
under the find's yellow wash in the list under the note until the record is drawn again. A record the
table's filters leave out stands among the rows in the table's order until the filters next change, so
nothing of yours changes. A search term opens Search strategy with the caret at the start of the term's
line in its block, and an exclusion reason with the caret in its meaning, nothing selected, so a key
pressed after replaces no word. A claim, a reference or a claim note opens its row on Trace's screen, a
reference at the first claim that cites it, or its own row when nothing cites it, and a note with the
caret in it. Esc, a click outside the card or Search on the bar again closes it, and `Cmd + F` again
brings back the last words and their results.

Under a This participant search on the statements screen, Replace in the transcript closes the card and opens
Find and replace with the words typed (see Find and replace), which keeps `Cmd + Shift + F`.

A search reads the files and writes nothing. What it reads is held in memory against each file's time
and size, so the next search waits on no file, and nothing of it is kept on disk.

## Projects

A project is a root folder holding its participants' folders, and Idiograph holds as many as he adds, two
studies side by side, each with its participants, their Experiential statements and their PETs,
and its own GETs. The app names no study's folder anywhere: it remembers each root it is given.
`config.json` keeps them as `projects`, in the order they were added, each `{"root": "<path>"}`,
absolute or from the repo root, or the app's folder in a downloaded copy, a participant's folder in it written as a glob on its pseudonym. A
`config.json` from before the projects, with `root` alone, reads as one project with that root, and
is written in the new shape only when Settings saves.

**The project of a path.** Every request that reads or writes a file asks which project the path
belongs to, the project whose root holds it, and works on that project's root, its project file,
its GETs and its participants. A path under no project's root is refused, as a workbook outside the participant
root always was. The recent list, the squares, the PETs screen's switcher, which lists
the participants of its own project, Find and every route keep their meaning across projects.

**The project file.** A project has settings of its own, the research question first, because the
question is what an experiential statement answers. They live in one file at its root,
`idiograph-project.json`, beside the participants' folders:

```
{"name": "...", "research_question": "...", "updated": "2026-10-01T12:48:00+01:00",
 "agents": {"allowed": true, "at": "..."}, "order": ["P3 - Cal", "P1 - Ada"], "pet_labels": "numbers",
 "timepoints": [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"}]}
```

`updated` is the time of the last save of the name or the question, in ISO form with its offset,
`agents` the privacy tick (see AI agents), `order` his order of the rows (see His order) and
`pet_labels` how the exports label the PETs, missing and so the book's letters until he picks 1 2 3
(see Export, under PETs). `names` holds, by a participant's folder's label, never its second part, the new pseudonym Rename gave a participant
whose folder it kept, `{"P1 - Ada": "Bea"}`, and is missing until one is (see Rename). The
server reads the file afresh on every `/api/cases` and `/api/open` and sends it as `project`, with
the root as Settings shows it. With no file, the name is the root folder's own and the question is
empty. Settings saves it through `/api/project`, which writes the name, the question and the time,
keeps any other key the file carries, and refuses a root that is not there rather than making a
folder to hold it.

**The project's own History** (2 November 2026). A change to the project itself keeps a record of when it
was made, what it changed from what to what, and who made it: you in the app, or an AI agent by name with
the request you gave it, "approved in the app" or "without asking" where the agent's action waited for your
yes. Each save of the project's name, research question, PET labels, timecodes, timepoints or statement
length keeps one, as does each save of the GETs settings, a participant renamed, and a participant's
statements marked complete or reopened. A save that changes nothing keeps none. The records are in
`idiograph-history.json` at the project's root, and a shared copy never carries them. An agent reads them
with `project history`. Project history, on the project's menu on Home (3 November 2026), opens them on a
sheet: every change newest first under its day, each with its time, who made it, every line of what changed and
what the agent says you asked. All, In the app and By an agent over the list show all of them or one side's
alone. A long record reads on as you scroll, and Done shuts the sheet. A project with no change yet says "No
change yet.", and the demo's card has no Project history.

**Project settings.** Each project's own settings are on a sheet of its own, Project settings (5 November
2026, where until then they stood in Settings under Projects, with a row of every project's name over them).
It opens for one project: from Project settings beside the project's name and question on its page, from the
project card's menu on Home, from File, Project Settings… in Idiograph's own window (greyed on Home), and from
the band's link when the project has no question. The sheet's head names the project. It holds the project's
name, its research question, its Method, Interpretative Phenomenological Analysis or
Thematic analysis, shown and never changed (31 October 2026), PET labels, A B C or 1 2 3, the same
choice as under Export on the PETs screen and saved at once the same way, Timecodes, its root folder with
Remove from Idiograph beside it, then under Experiential statements its Statement length, under GETs its GETs
rules (see GETs), and with AI features on the privacy tick, Write a guide for AI agents and Add Idiograph to
Claude Desktop. A thematic analysis project's sheet has no PET labels, timepoints, statement length or GETs. A
long folder path, here and under Sift and Trace, runs onto the next line only after a slash, never inside a
folder's name, unless that one name is wider than the line. A demo's sheet is read-only. Save writes the name,
the question, the tick and GETs' rules when they changed, each to its own file, and PET labels, timecodes,
timepoints and the statement length save as they are changed. Open project is on Home.

**Working together.** At the foot of Project settings (8 November 2026), Working together has one tick, Work on
this project with others, off in every project until it is ticked, so someone working alone sees nothing else.
Ticked the first time, it makes this computer's keys and makes you the project's lead, under Settings' Your name,
or a name typed in the row that asks for it when Settings holds none. Then it shows Send through, Relay or Shared
folder, the folder with Choose beside it when Shared folder is picked, People, each with how many computers and
the lead marked, with Remove beside everyone but the lead, Invite and Add a computer of mine, Who works on each,
a participant's person picked from a list, the GETs board's with Hand over, and Send the recordings too. Each
change saves at once and goes into the project's History. Invite opens a card with a link and twelve words, each
with its copy button: send the link by email, or read the words out. It works once, for seven days. When the
other person has pasted either into Join, both cards show the same six digits under Check code. Read them to each
other on a call, then press They match, and they join, or They differ, and their answer is thrown away. Join
stands beside Invite while nobody else is on the project. Remove asks one line first, then the project's key
changes for everyone left, so the one removed gets nothing new, and what they already have stays on their
computer. Unticking it stops anything more being sent or taken in, and ticking it again picks the team up as it
was.

**The relay code** (9 November 2026). The relay makes a project only for a relay code, which whoever runs the relay
gives out. The first time the lead sends through the relay, Working together shows Relay code under Send through.
Type the code and press Connect: the project is made on the relay, and the row goes. The code is used that once and
kept nowhere. A wrong code, a code that cannot start any more projects, or no connection is said in one line, and
nothing changes. Invite waits until the project is on the relay. Someone who joins needs no code, and neither does
the shared folder.

Send through is the lead's choice alone, as who is on the team is. On a member's computer it shows the team's route and
nothing to pick, and a change asked of it is refused in a line with nothing changed. When the lead changes it, the
change goes to everyone in the signed list of people and each computer follows. Switching to the relay waits for
the relay code: the members stay on the old route until the project is made there.

**Who works on each participant.** Once someone has joined, each participant is worked on by the person picked
for them in Who works on each, and the GETs board by its own, the lead until someone else is picked. Only their
computer changes that participant's files. On a participant someone else works on, the project's page shows a
tag with their name, "Curt's", and every change is refused with a line such as "Mabel is Curt's. Comment or
suggest instead.". Your copy of their work updates by itself: about a minute after their last change it comes
in, and a screen you have open on it says it has changes made elsewhere. A participant of yours goes to the
others the same way, about a minute after your last change, and at once when you quit. Someone who joins gets
a copy of everything at once. Under the project's question, the project's page says what came in today, "Curt's
changes to Mabel came in at 16:42", and, when there is no connection, how many of your changes are waiting,
"3 waiting to send: no connection". They go when the connection is back. A participant you add, with Add
transcripts or an import, is yours to work on, and once it reaches the lead's computer Who works on each names
you for it.

Since 9 November the lead also has Make lead beside Remove on each other person's row. It asks one line first,
then that person is the lead and adds and removes people from then on, and the participants and the GETs board
stay with whoever works on them. Anyone on the project can use Add a computer of mine, for a second computer of
their own: the same card, the same six digits read off both screens, and the new computer can read the project at
once. When you are not the lead, it goes on the list of people the next time the lead's Idiograph opens the
project, and a line under People says so until then. When someone has two computers or more, each is listed under
their name, with Remove this computer beside every one but the computer you are on, for a laptop lost or sold:
the lead can remove anyone's, and you can remove your own. The project's key changes, so that computer gets
nothing new, and what it already has stays on it, as safe as its disk. Someone's only computer cannot be removed
this way: Remove takes the person. Someone removed sees one line in Working together saying nothing new comes to
their computer.

**Working together through a shared folder** (9 November 2026). Send through, Shared folder, sends everything
through a folder the team already shares, such as a OneDrive, Dropbox or network folder, in place of the relay.
Pick Shared folder, then Choose and pick the folder, on each person's computer: it may sit in a different place on
each. Idiograph makes a folder of its own inside it, named Idiograph and eight letters of the project's id, and each
computer writes only in its own part of that, so the sync app never makes a conflicted copy. Everything in it is
sealed, as it is on the relay: anyone else who can open the shared folder sees file names and sizes, never words.
Each computer looks in it every 15 seconds while the project is open, and again on waking from sleep. A message
everyone has read is deleted from it. The person joining picks the same shared folder before pasting the invite
into Join, and when the invite has not reached their computer yet they are told it may still be syncing. When the
folder is not there, because a drive is not connected or the sync app is not signed in, a line under it says so,
"This folder is not there. Check that its drive or sync app is connected, or choose it again." When a file in it
will not open yet, a line says to keep the folder on this computer: in OneDrive, Always keep on this device.

**A board sent by a teammate.** With Working together on, on the PETs screen of a participant someone else works
on, you can still make boards of your own: New board, Duplicate, and every change on the canvas work as they do on
any board. Your own boards are kept on your computer apart from theirs, marked Yours in the board menu after their
names, and stay as they are when a new version of the participant comes in. Their boards stay theirs: on one of
theirs, the board menu's Rename, Delete this board, Mark as current, Edit the note and Save a revision are greyed
out, and a change to it is refused. Mark PETs complete and Reopen PETs are greyed out on every board of theirs
and yours, since the mark is theirs. Send board, in the menu of one of your own boards, sends the board on the canvas
to them. On their computer it waits, with nothing added to the participant, and shows on the same line as the rest
of Curt's review, "Curt's review of Juno: 2 comments and a board.", or "Curt's review of Juno: a board." when he
sent it on its own. Review opens the card, where "Curt's board of Juno's PETs" says "It comes in as your next board,
beside Board 1.", with Decline and Add as next board. Add as next board adds it as that participant's next board,
never the one on the canvas, named "Curt's board, 9 Nov", its note saying when it was sent and how its statements
came, "Curt's board, sent 9 Nov: 63 statements as sent, 2 reworded since.", then Curt's own note. When the
participant has no board yet, Curt's becomes their only board, on the canvas, with no empty board beside it. Decline adds
nothing. Either way Curt's computer hears your answer. A board waiting stays waiting when the app is closed and
opened again. Each send, arrival and answer goes into the project's History, and the board's own History says who
sent it.

**Timecodes.** In Project settings, after PET labels, Timecodes says how the project writes a timecode,
each choice an hour and a quarter in: 75:12 folds the hours into the minutes, 1:15:12 writes them
once past the hour, and 01:15:12 always. A new project starts on 1:15:12. It belongs to the project,
not the computer, so whoever opens it sees its quotes cited one way: the transcript's margin, the
player, the boards, the print views, Word and the PET draft. A press saves it at once. The statements
CSV and the notes export keep 01:15:12, and the workbook's own Timestamp cell keeps its form. The
demo's are fixed.
The folder becomes a project after the others, shown at once, and is refused when it is a project
already, when it sits inside another project's root or holds one, or when it holds the app or its
demo. Cancel changes nothing. Remove from Idiograph asks first in a small card (see Remove from Idiograph,
below), then forgets the project, its folder and every file in it left as they are unless the card's tick moves
the folder to the Bin. Removed from over one of its own participants, the page saves what is typed and
opens on Home.

**No project yet.** With no project, as the Mac app ships, Projects holds New project, Open project and Open
a shared copy alone, and Demo projects under it stands open with the two demos' cards. Open project there takes a folder through the Mac's dialog,
or off a Mac a field for the folder's path, and the project added opens on its page.

**New project.** Under the project cards on Idiograph's Home, New project opens a card that makes a
project from a folder and its transcripts. Choose takes the folder through the Mac's dialog, or its
path is typed, and it is refused as Open project refuses one. Name and Research question take what a project file
there already says, and either can be left. The transcripts are dropped anywhere on the card or
picked with Choose files, in any shape make a workbook reads, and each is a row: its first passages,
its speakers each with a chooser, Interviewer, Participant or Other speaker, as on the import card
(since 20 October, in place of one Interviewer chooser), the participant's number, preset from the folder's next free
number, the pseudonym, always typed, and the interview's name, guessed from the file's name or
Interview. Files under one pseudonym are one participant with an interview each, as GRAVITY's Initial and
2d. Create project checks every row and refuses in one line naming what to fix, then writes each participant as
`P<n> - Pseudonym`: a copy of each file in `Source/<interview>/`, the original untouched, the raw
source `Source/P<n> Pseudonym - transcript.xlsx` with a sheet an interview, the interviewer's passages
under Settings' name, every participant's under the pseudonym, and another speaker's under Other
speaker, Other speaker 2 for a second, marked as the import card marks them, so no name from the
recording's labels reaches the workbook, and the annotated workbook,
before the folder joins the projects and its page opens. A failure takes away what it wrote. A
folder with a second part after the pseudonym, as GRAVITY's, still opens and shows by its pseudonym
alone, but New project and Add transcripts make none.

**Method** (31 October 2026, drawn for review and not yet released). Under Research question, Method is a choice of
two, IPA, chosen as the card opens, or Thematic analysis. It is the project's for good: Project settings shows it
and never changes it, and a folder whose project file names one already shows that one, fixed. A thematic analysis
project shows its screens in Braun and Clarke's words, Codes for Experiential statements, an extract for a quote,
Notes for exploratory notes, and Themes for GETs, its board the thematic map of every participant's codes, each
participant's codes waiting under Codes in the Participants panel. It has no PETs, no timepoints and no
trajectories, its project page's rows show the coding alone, its Coding screen has no nudges, and its board no
Mark complete. Its AI features are its own, and IPA's never show in it (see Thematic analysis's AI). Its board's Export (1 November 2026) prints, or saves as a PDF, the Theme table, the audit trail, all of
it in one document or the canvas, each in its words: the Table of themes, every code with its extract under each
theme, the trail in four columns, Transcript passage, Extract, Code and Theme, and the full set with no tables of
PETs. Its codes' CSV is "All Codes", with Code, Proposed theme and Extract as its headings, and every line the app
says in the project, a refusal or a line after an export, uses the same words. Search in it finds the codes and
the passages, and nothing that would open a PETs board, and names what it finds Codes, Extracts and Notes.

**The code list** (2 November 2026). In a thematic analysis project a code is a label that many extracts share,
and each extract is still one quote. On the Coding screen each extract of a passage is a box, numbered in the
passage after its last words, with its codes as chips under it. Add a code under the chips suggests the project's
codes as you type, each with how many extracts and participants it has, or offers New code with the words typed.
Enter or a click puts it on the extract. The x on a chip takes the code off, and the extract stays, with no code,
when it was its last. Add an extract, or Q, takes the words selected in the passage as a new extract. Each of
these is a step of undo.

Quick keys while coding (9 November 2026). With words selected in a passage, the toolbar beside them has In vivo
code beside Extract and Give to another speaker, and under them a second line with the five codes used last in the
project, the last one first, with a firmer edge. A click on one makes the words a new extract with that code. The
keys do the same: R puts the code used last on the words, 1 to 5 the code at that place on the second line, and V
makes an in vivo code, the selected words a new code's name, without the stop at their end, put on the new extract
at once. Q makes the extract with no code, as before. Words the passage holds as an extract already get the code on
that extract. The keys work only while words are selected and the caret is in no field, and never with Cmd or Ctrl,
so Cmd + R and Cmd + V are the window's own. The right-click menu on selected words lists the same, each key in a
column at its right: Extract, Extract with the last code, In vivo code with the words, then Recent codes, numbered 1
to 5. The shortcuts card has R, V and 1 to 5 in a thematic analysis project. Each is one step of undo. The codes used
last are kept with the project's code list, so they are there after a restart, a renamed code keeping its place.
An IPA project's statements screen has none of these.

Code list is a tab of its own between Coding and Themes. Every code is on the left, sorted by name, with its
Extracts and Participants, and Search the codes narrows it. The code open on the right shows its name, its counts,
its Description and its extracts by participant, each with its time and Go to the passage, which opens the
passage on the Coding screen. Rename makes the name a field in place. Merge into another code opens Merge two
codes, which says what the merge will do before it is done: every extract of the one goes to the other, an extract
that had both keeping one, and the merged code leaves the list. Delete this code is there only for a code with no
extracts. The row's menu, its three dots, holds the same three. New code beside the search adds a code ahead of
its first extract.

A rename and a merge change every participant's workbook and every board at once. Each file is checked first,
and if one is open in Excel nothing is changed. A copy of each file goes into an _Archive folder first. Undo and
Redo at the foot of the screen, or Cmd + Z and Shift + Cmd + Z, put the whole change back, or make it again,
while no file has changed since. A project made before the code list has its list made the first time it is
opened, a name typed the same way in any case being one code, and each board keeps a revision first.

On the Themes board a code is one card: Code · 9 extracts, its name, and under it each participant's letter with
how many of its extracts are theirs. Its extracts follow it wherever it goes. A code whose extracts sat in
different places on a board made before the list goes where most of them were, and the board's History names it.
A new code waits under its participants in the Participants panel until it is dragged onto the board.

The Themes board as the thematic map (2 November 2026). The panel at the board's left has two tabs, Codes and
Participants. Codes lists every code of the project once, by name, with its extracts and each participant's count:
Not placed first, the codes in no theme and those that have never been on the board, then In themes. A code set
aside is under Set aside at the panel's foot. Search the codes finds a code by its name or its description. A row
dragged onto the board brings the code's card, or moves it when it is there already. Participants is the panel as
it was, each participant's codes under their name. The status bar counts codes, "11 codes: 9 in themes, 0 set
aside, 2 not placed", from the code list, so a code that never reached the board counts as not placed, then the
themes and subthemes, "3 themes, 1 subtheme".

The Inspector on a code's card shows "Code · 5 extracts", its name, each participant's count, its Description,
the same field as on the Code list, and the theme it sits in. Take out of theme and Open in Code list sit under
it, then every extract by participant, each with its time and Go to the passage. A description typed here is kept
when the box loses the focus, as on the Code list, whose Undo takes it back. Under a theme each extract has a tick:
the one ticked is that participant's key extract for the theme, which the theme table's Their key extract only
shows. Until you tick one, the first of theirs in the theme is ticked faintly. A tick is a step of undo.

The Inspector on a theme shows its Definition, the theme's central idea, in the box that was its description, then
how many codes, extracts and participants it holds, Auto-arrange and Audit trail side by side on one row, its codes and subthemes in the
order of its frame, each participant's extracts counted from every code under it, and its Note.

**Thematic analysis's guidance** (3 November 2026). A thematic analysis project's Coding screen has its own
Guidance, from the bar's Guidance tool or `g`, as the IPA statements screen has: Coding guidance, eleven lines from
Braun and Clarke's reflexive thematic analysis, each with its Less this and More this behind the small arrow, and the
paragraph under them. An empty Add a code field says Add a code, the questions staying in the Guidance (Adam,
3 November). The rail has no personal examples, which are IPA statements. The Themes board's Guidance tab shows the
lines on themes, What a theme is, Generating themes, Developing and reviewing, Defining and naming, The thematic map
and Before you finish. They live in `ta_guidance.md` and `ta_themes_guidance.md` beside the app, in the formats
of `guidance.md` and `themes_guidance.md`, and an edit shows on the next load. An IPA project's guidance is as
it was.

**Thematic analysis's AI** (3 November 2026). With AI features on in Settings, a thematic analysis project has
one AI feature of its own, written from its guidance, and none of IPA's. On the Coding screen each extract has
AI suggest beside its Codes, under the Experiential statements switch. A press sends that passage, the
interviewer's passage before it, the extract, its codes and the project's code list, and the answer stands under
Add a code as AI suggestions: up to three of the project's codes that fit, each with its extracts and participants
counted, then up to two new codes as New code "...". A click on one puts it on the extract as Add a code would, one
step of undo, and nothing is written until you click. A code you take is an ordinary code with no mark that the AI
offered it. The x puts the list away, and the next passage starts with none. It uses the provider, key and
model the Experiential statements' AI suggest uses, and sends only the passage in question. The Themes board's
AI review went on 11 November 2026, and a board's review rounds from before stay in the GETs file, read by
nothing.

Compact on the status bar shows each code's card as its name alone, so one screen holds more of the board. The
cards stay where you put them. It is off on a new install and kept, as Extracts is. Press it again for the cards
as before.

The board's Table view lists each theme in the board's order with its definition, its note and Audit trail, then
its codes, each with its extracts and under it each extract with its participant, time and words, then its
subthemes the same way. Not placed at its foot lists the codes in no theme, those on the canvas first, which drag
into a theme, then those never on the board.

The theme table goes to Microsoft Word too (1 November 2026): Microsoft Word beside Print at the top of the board's
Table view, and on the Export card beside Save as PDF while Theme table is chosen. The document is portrait A4,
with the project's name at its head and "Table of themes" under it, then each theme in the board's order with its
description and note, its subthemes under it, and under each its codes, each with whose it is and where, "(Juno,
Initial, 00:14)", and its extract on the next line. With Their key extract only chosen, each theme holds every
participant's key extract alone. Descriptions, Include participant notes and Leave out the board's name apply as
they do to the PDF, and Participants table puts the participants table on its first page, under Participants, the
themes starting on the next. It is saved at the project's root, where the PDF goes, as "<project> - Board 1 - Theme
table.docx", never over a file there, and its author is the name in Settings, General, Your name.

On a desk's width the card's Folder and Name fields start at one left edge and run to its right, as
on Sift's and Trace's New project, where the folder's started further left (17 October, later).

**Add transcripts.** Under the rows on each project's page, quiet, Add transcripts opens the same
card with the project's name over it and no folder, name or question to set. A file under a new
pseudonym makes a participant at the next free number as Create project does, and one under the pseudonym
of a participant already there is a further interview of it, its row reading "A further interview of P1
Ada", its copy in `Source/<interview>/` and its sheet added at the end of the raw source and of the
annotated workbook, a copy of the workbook kept in the participant's `_Archive/` first and every sheet
already there unchanged.

**Names replaced as a transcript comes in** (8 November 2026). A project can keep a list of real names and
what each is written as, and every transcript that comes into the project has them replaced on its way in,
so no workbook holds a real name. Each row of New project and Add transcripts has a Real name beside its
Pseudonym: the name typed there, and its first word when it has two, is replaced by the pseudonym in that
participant's transcript, and joins the list. The row's preview shows the text as it will land, each
replacement tinted, with the name it replaced as its tooltip. The Names line under the row's fields says how
many were replaced, with Review, which lists every name found by its entry in the list, each with a tick:
untick one and it stays as it is written, as "Will" in "Will you tell me" should. A speaker's name is one row,
however many passages it heads. The participant's name in the file's own name and the interview's name are
replaced too, and Source keeps the replaced text, not the original.

Names are found as whole words, so "Ann" is never found in "Annabel" or "annual", and case is ignored
unless Match case is ticked for a name that is also a word. "Tilda's" becomes "Wren's". Initials such as
"T.M." are found with or without their dots and spaces, by their case. Several spellings of one name go in
one entry with commas between, and a misspelling is not guessed.

Names to replace, from the Names line or from Project settings, is the project's list: each name, what it is
replaced with, whose transcripts it is in (Everyone, or one participant, for a "Ruth" who is a sister in one
interview and a friend in another) and Match case. Add a name adds a row, and Add from a file reads a
two-column CSV or Excel key you keep already, the real name then the pseudonym. The list is saved as you
change it, in one file in the project's folder, `idiograph-names.json`, so it moves with the folder. It is
never in a workbook, the project's History or a copy you share.

Check transcripts already in finds the list's names in the transcripts the project holds, their passages,
speakers, notes, statements and quotes, and says how many and where. Review and replace lists every one
with its tick, and Replace writes the ones ticked, the PETs and GETs following the statements. Before it
writes, each participant's workbook and raw transcript as they were are kept in their `_Archive` folder,
named "(pre-names" and the date, so the real names are still there: keep that folder safe, or delete those
copies when you no longer need them. Share a copy never takes them, nor the list.

**Projects from ATLAS.ti, NVivo or MAXQDA.** Since 21 October a project exported from ATLAS.ti, NVivo
or MAXQDA as a REFI-QDA project, a `.qdpx` file, comes into a project as participants, from New
project's card or Add transcripts' (see The import card for a project below), or through an AI agent
(`idiograph qdpx`, see the agents' guide). Each text source, or a recording's transcript, is one participant's
interview, given its pseudonym, its number and its timepoint as a row of Add transcripts is, and
made as Add makes one: a copy of the `.qdpx` in `Source/<interview>/`, the raw source and the
workbook, a pseudonym already there joining that participant. The text is cut into passages as a
plain text file is, a `Name:` line starting a passage, or else a paragraph a passage. Then, by
default:

- each code on a passage is an experiential statement named by the code, its quotation there the
  quote. A code over several quotations in one passage is one statement whose quote holds them all
  in transcript order, with an ellipsis where they are not next to each other, as a quote built with
  Cmd held is. The same code in another passage is the statement once there too. Codes can come in
  as exploratory notes instead, or be left out.
- a comment on a quotation is an exploratory note on its passage, or an experiential statement whose
  quote is the quotation.
- a quotation with no code and no comment is a quote to pair, listed under Quotes to pair until its
  statement is written. It can be left out instead.
- a source's memos go to a text file in the participant's `Source/`, "Wren - memos.txt".
- a recording in the project is copied into the participant's `Source/` for the player, each passage
  timed from the recording's sync points.

On request, a PETs board "From ATLAS.ti" (or NVivo, or MAXQDA) is made on each participant's canvas,
a PET a code group holding the statements its codes made. From a file Idiograph wrote, in a project of timepoints, each
participant's LPETs and the LGETs come in as boards too (see Export as REFI-QDA). A quotation that runs past its passage's
end is cut there. What does not come in is said in one line: PDF documents and pictures, variables,
free memos, links and networks, sets beyond the PET draft, codes on the interviewer's passages. The
same lines go into each workbook's History in its progress file. The `.qdpx` itself is only read.

**The import card for a project from ATLAS.ti, NVivo or MAXQDA.** Since 21 October a `.qdpx` dropped
on New project's card or Add transcripts', or picked with Choose files, comes onto the card on its
own: the drop place goes, and another file dropped with it or after it is refused with "A project
from ATLAS.ti, NVivo or MAXQDA comes in on its own. Add other transcripts after it." The cross at its
right takes it off the card. Under its file's name, "A project from ATLAS.ti" (or NVivo, or MAXQDA),
each source that can come in is a row, ticked: its name and its passages, its first eight passages
as they will land, in the columns Speaker, Time, Transcript and, where any passage has them,
Exploratory notes, Experiential statements and Quote, its speakers each with the role's chooser,
and the fields P, Pseudonym, Interview and, in a project of two or more timepoints, Timepoint, as a
transcript's row has them. Untick a row and that source stays out. Under the rows, What comes in:

- Codes: As experiential statements (the default), As exploratory notes, or Leave out.
- Comments: As exploratory notes (the default) or As experiential statements.
- Quotations with no code or comment: As quotes to pair (the default), each a quote waiting for its
  statement under Quotes to pair, or Leave out.
- Memos, when a source has any: To the participant's Source folder (the default) or Leave out.
- Recordings, when a source has one: Copy for the player (the default) or Leave out.
- A draft PETs board from the code groups, when codes come in as statements and the project has
  code groups, unticked until ticked.

Each choice reads the file again, and the preview and the lines under the choosers, what comes in
and what is left out, change with it. A refusal stands under them once every ticked source has its
pseudonym. Create project, or Add, brings in the ticked sources, writing nothing until every one is
checked. The card sends the file to Idiograph once, which keeps a copy while the card is open, up to
256 MB. A larger project, a recording in it say, comes in through an agent.

**A project card's menu.** Since 21 October (Adam's Way A) each project's card on Home has its dots at
the top right, and their menu holds, in order, Share a copy…, Export as REFI-QDA… (since 8 November 2026), Show in Finder (Show in Explorer on
Windows), Project settings, Project history, then under a thin rule Remove from Idiograph…, in red with its bin. Show in
Finder opens the project's folder in the Finder, selected in the folder it sits in, and is there in
Idiograph's own window alone, since a browser's page cannot open a folder. Project settings opens
that project's own sheet, its research question, its statement length and the rest of what is the
project's (see Project settings). Remove from Idiograph asks in a small card, then takes the project off Home. A
shared copy's card, marked copy, is removed the same way.

**Remove from Idiograph** (10 November 2026). The card names the project above Remove from Idiograph, says "Its
folder and files stay as they are.", and has one tick, off to start, Move its folder to the Bin too. Ticked, the
line says its folder and every file in it go to the Bin. Remove takes the project off Idiograph's list, and with the
tick moves its folder to the Bin as well, where the Finder's Put Back brings it back. Cancel or Esc removes nothing.
It is the Recycle Bin on Windows and the Rubbish Bin on Linux, and nothing is ever deleted outright. Once it has
gone, the foot says so: "Removed Keeping bees. Its folder is in the Bin." The folder is never moved when it is not
the project's own: a whole drive, your home folder or its Desktop, Documents or Downloads, the whole of iCloud
Drive, OneDrive or another cloud drive, a folder holding the app's own files or settings, or one holding another
project. Nor while the project is open in another window, or being saved. Each is said at the foot, and the project
stays in the list. When the system will not move the folder, the foot says so, and the project stays too. Sift's
and Trace's Remove ask in the same card. The app keeps a line for each removal, and whether the folder went to the
Bin, in a record beside its settings, never in a project.
In Idiograph's own window every other line the app asks you to confirm is asked in the window's own message box,
with OK and Cancel.
The demo's card holds Project settings alone, read-only
there as ever, and a card whose folder is not there Remove from Idiograph alone. A run of one project
offers no Remove.

**Share a copy.** A project can go to someone else's Idiograph, a student's to a supervisor's, say,
as one file, opened there as a copy. Share a copy on the card's menu opens a small card first (23
October), the project's name above its title, with two choices. Whole project, chosen to start, sends
every participant, their PETs and the GETs, and the line under it says so. A project of two or more
timepoints says LGETs there, and a project with no PETs or GETs yet leaves them out of the line. The
file then holds the whole project folder as it is: every workbook, the project file, the boards, the
GETs, Source and History. Under it one tick, Audio recordings, with the size they add, decides whether
the recordings go too. It starts unticked, and a project with no recordings has no tick.

Choose participants shows a row for each participant, ticked to start. Each row's experiential
statements and notes always go, shown by a muted check. A PETs tick stands on the row of a participant
who has PETs, ticked to start, and an Audio recordings tick, with its size, on the row of one who has
recordings, unticked to start. A participant with neither has nothing in those places. Untick a
participant and their row shows dashes, nothing of theirs going. The GETs never go this way, since they
are made from every participant. So to send one participant blind to your PETs, choose participants,
leave only that participant ticked and untick their PETs. Share… is there once a participant is ticked.
Each tick turns on or off from anywhere on its row.

Under either choice a Boards row (26 October) offers Current board only or All boards, All boards
chosen to start. All boards sends every board as it is, with its History. Current board only sends
each participant's PETs, and with Whole project the GETs, with the board each is going with alone,
the Current board where one is marked, else the board on the canvas. That board's own PET draft and
table go with it, the other boards and the History stay behind, and the copy opens on that board. In
a timepoints project the same goes for the LPETs and LGETs. The row is there only when it would change
the file: when a participant going with their PETs, or with Whole project the GETs, has two or more
boards.

Share… opens the save panel, the file named `Keeping bees.idiograph`, the project's name with
`.idiograph` after it, and the panel's line saying "Idiograph doesn't track changes between copies yet."
The file is written straight from the project's folder, so a project with long recordings is shared as
quickly as a small one. In a browser Share… downloads it, and the same line stands under Share a copy
in the menu. Tab moves through the choices and ticks, Space turns one on or off, Enter presses Share…
and Esc closes the card with nothing sent. Nothing in the project changes, but for an id its project file takes the first time (see A copy coming back). The file holds the
participants' words and recordings, so share it the way the study's ethics allow.

**Open a shared copy.** Under Idiograph's cards, after Open project, Open a shared copy takes a
`.idiograph` file, the dialog's line "Choose the shared copy.", and then the folder to put the copy
in, its line "Choose the folder to put the copy in. A new folder, Keeping bees, is made inside it.",
through the window's own dialogs or, in a browser on a Mac, the Mac's. In a browser off a Mac the file
is chosen and the folder's path typed, with Open. The copy goes in a new folder there, the shared
project's own folder name, `Keeping bees`, or `Keeping bees copy` when that is taken, then `Keeping
bees copy 2`, never over a folder already there. It joins the projects and its page opens, a "copy"
tag beside its name there and on its card on Home, and a line says where the copy is. Its card's menu
is any project's. A file from a newer Idiograph is refused, "This project was sent from a newer
Idiograph. Update Idiograph, then open it again.", and a file that is no shared project, "That file is
not a project sent from Idiograph.", with nothing written. A run of one project, which hides Open
project, hides it too. Taking turns and working on one project at once are not part of it.

**Opening a shared copy from the Finder or Explorer** (6 November). Once Idiograph is installed, a
`.idiograph` file is Idiograph's own: the Finder and Explorer call it an "Idiograph shared copy" and
show it with Idiograph's icon. Double-click one, drop it on Idiograph's icon in the Dock, or choose
Open With and Idiograph, and it opens as Open a shared copy opens a file you choose, with no file
dialog: the folder for the copy is asked for, and a copy coming back to one of your projects shows its
card first. When Idiograph is closed it starts, then opens the file. When it is open, the file goes to
the window in front, which comes forward, and on Windows the file goes to the Idiograph already open,
never to a second one. On a participant's screen or a board, Idiograph goes to Home first as Home
does, saving what you typed, and if that save fails you stay where you are and nothing is opened.
With a card open, the file waits until you close it. Files opened together open one after another. A
file that is no shared project is refused in the same words as above. Sift and Trace never open a
shared copy. On Linux, with Idiograph installed from its .deb, the file manager shows a shared copy with
Idiograph's icon, and a double-click or Open With hands it to Idiograph the same way.

**A copy coming back** (26 October). When you send a copy to another analyst and they send it back,
it is still your project, so their boards can be added to yours. The first time you share a copy, the
project file takes an id of its own, the only change a send makes, and the copy remembers it, with how
each statement read when it was sent. Through Idiograph's command line or MCP tool, an AI agent can then
bring the copy's boards in at your word, with a dry run first: each comes in as your participant's next
board, named whose and when, "Curt's board, 30 Oct", never current and never in place of one of yours.
Its History says "Brought in from" and the file's name. Since 6 November a board arrives whole: every card
keeps its place on the other analyst's board. A card is matched by its words first, so a statement that moved
up its passage when you removed one before it is still found. Then by its place in the transcript: a
statement you reworded since you sent the copy is linked to yours and shows your wording now, marked changed,
with theirs as what it read. A statement you removed, or one the other analyst added, is placed in their
wording and marked as no longer in the workbook. Nothing else in the project changes. You can then make the board current,
keep it beside yours, compare it with yours, or delete it, a copy kept in `_Archive` as delete always
keeps one. A file that is no copy of the project is refused. When most of a board's statements are not in
your project, open the copy as a project of its own instead, and its name can say whose it is,
"Keeping bees, Curt's copy". A copy sent from 6 November on carries its sender's name, Your name in
Settings, when they have set one.

In the app (26 October, evening, the card rebuilt 6 November), Open a shared copy knows a copy coming
back. Once the file is read, before any folder is asked for, a card says so: "A copy of Keeping bees, sent
30 Oct.", then Name on the boards, filled in with the name the file carries, and under it what a board
comes in as, "Comes in as: Curt's R2 Initial Grouping, 30 Oct", then two choices. Add its boards to
Keeping bees, the one it starts on, says how many boards would come in, "11 new boards, not current" or
"A new board, not current", and under it each participant's name, "P2 Wren", over a tick for each of
their boards, by its own name in the copy, every one ticked to start, with All boards above them to
untick or tick them all. Once under a participant's boards a line says how their statements came, "37 of
these statements you have reworded since you sent the copy, and 5 you have removed. They keep their places
on these boards, in your current wording, and the removed ones in Curt's.", or "All 46 statements match
yours.". A board of yours that comes back as you sent it, its cards where they were when you sent the copy,
whatever you have done to your own board since, is left out: under the participant a line says "1 board is
your own as you sent it, so it is left out." (8 November 2026). The button counts the boards ticked, "Add 5 boards" or "Add 1 board". With no board ticked or no
name, it cannot be pressed, and a line beside it says what is missing: "Tick a board.", "Type a name." or
"Tick a board and type a name.". It brings the boards ticked in and opens the first participant's PETs
board with its board menu open, the new boards in the list under yours, not current, each note "Curt's
copy, sent 30 Oct: 80 statements as sent, 37 reworded since, 5 removed since.", a part left out when
its count is 0, and under it the note the other analyst wrote on the
board in the copy, word for word, when there is one. Open as its own project goes on as Open a shared copy always has, Open… asking for
the folder, the copy named "Keeping bees, Curt's copy". Cancel and Esc open nothing. A copy whose boards
are in already starts on Open as its own project, the first choice saying "Its boards are in Keeping
bees already.". A file that is no copy of one of your projects opens as it always has.

**Export as REFI-QDA** (8 November 2026). A project, or some of its participants, goes out as a REFI-QDA project,
a `.qdpx` file, which NVivo, ATLAS.ti, MAXQDA and QualCoder open, so a supervisor or a co-analyst can read the work
in the programme they use. Export as REFI-QDA… on the project's menu, on Home or from its name inside, opens a small
card with the project's name above its title: Whole project, ticked to start, or Choose participants, a tick for
each, and in a project with recordings an Audio recordings tick, off to start. Export… opens the save panel,
the file named after the project, "Keeping bees.qdpx", and a line says once it is saved. In a browser it downloads.
Nothing in the project changes. In the file each interview is a text, its passages as the transcript has them with
their speakers and times. In an IPA project each experiential statement is a code, applied to its quote, a statement
with no quote to its whole passage, and each participant's PETs, from the board the GETs take, hold their
statements in the board's order, each PET and sub-PET with its description, then Not placed and Set aside. Each
PET and each GET is also a set, ATLAS.ti's code group. In a thematic analysis project each code is one code, with
its description, on each of its extracts, and the themes hold the codes. Exploratory notes are notes on their
passage. With the recordings ticked, each interview with one is the recording with its transcript, linked by the
passages' times. Brought back into Idiograph with Import, PET draft ticked, the file gives the same passages with
their speakers and times, the statements in their order with their quotes, the exploratory notes and the
Interviewer notes, each participant's PETs on a new board in the same order, each sub-PET inside its PET, each
label's description and note, and the statements set aside back in the bin. The GETs come back as a new board on
the GETs canvas, each GET with its description and note holding the same PETs. A recording comes back with its
offset and the transcript's own times. In a project of timepoints each interview goes to the timepoint you give it
and each timepoint's PETs to that timepoint's board. In thematic analysis the code list comes back with each code's
description, and the themes as a new board on the Themes canvas, each sub-theme inside its theme. What does not
come back (9 November 2026): where each card lay, which the new boards lay out afresh, stacks, whose statements
come back side by side, the boards' names, history and other boards, a board marked complete, the quote ticked
for a PET or a GET table's row, and sticky notes and participant notes, which REFI-QDA has no place for.
In a project of timepoints each participant's LPETs go too (12 November 2026), from the board the LGETs take:
each LPET is a code under the participant's LPETs code, with its description and note, its sub-LPETs inside it,
and a set of every statement under it, its domain and the LPET table's states and key quotes notes on that set.
Each LGET is a set of its LPETs and their statements. Brought back into a project of timepoints, each
participant's LPETs come back on a new board of their LPETs canvas, each LPET with its description, note and
domain holding the same PETs of each timepoint and the same statements on cards of their own, each sub-LPET
inside its LPET, and the LGETs on a new board of the LGETs canvas, each with its description and note holding
the same LPETs. The LPET table's states and key quotes stay in their note, since the table keeps a key quote by
where it stands in the transcript, and so does the bold in a key quote. An LGET inside another comes back as
part of it, as a GET inside another does, and a second card of an LPET stays out. Brought into a project of one
timepoint, the PETs come in and the LPETs and LGETs are left out, and the lines say so.

**Sending some participants, or leaving kinds out** (23 October). Through Share a copy's ticks, the
command line and the MCP server, a send can hold only some participants and leave out what you choose, so another analyst can make PETs for one of your participants without
seeing yours. `idiograph project send --to ~/Desktop --participant Wren --blind` writes a file with
the project's name, research question and settings and Wren alone: her workbook with its transcript,
exploratory notes, experiential statements, quotes, Interviewer notes and other speakers,
and her progress, and nothing of your grouping, no boards or their history, no PETs, no PET drafts,
no PET tables in Word or PDF, no GETs. Opened as a copy, in any Idiograph from 0.9.4 on, Wren's
statements are all there and her PETs canvas is empty, ready to start. `--participant` given again
sends more participants. `--leave-out` names the kinds to leave out, `pets`, `gets` or `audio`, so
`--leave-out gets` sends the PETs without the GETs, and `--blind` leaves the PETs and the GETs out.
Recordings stay out of such a send unless `--with audio` asks for them, since a voice can name a
participant, and `_Archive` copies never go. Your working notes stay out too, any file in the
participant's Working folder that is not Idiograph's own, a grouping draft or a statements CSV say,
and any other file beside the workbook, unless `--with notes` asks for them, and so does the Source
folder, raw transcripts and exports, unless `--with source` asks for it, since the workbook holds the
transcript. Each participant's folder in the file is named as
Idiograph names the participant, `P1 - Wren`, never with a second part the folder on your disk
carries. With the PETs left out, the participant's History stays out too, since its requests can name a board or a PET, and in the copy it starts fresh, the statements' progress and completion kept. GETs hold every participant they were made from, so when some of those are not sent the
GETs stay out and the answer says so. `--dry-run` lists every file it would hold and every file it
leaves out, and nothing in the project changes. `--pets Wren` and `--audio Wren` send Wren's PETs or
recordings and nobody else's, so one participant can go with PETs and recordings and another with
the statements alone. `--leave-out audio` on its own sends the whole project, notes, Source and GETs
with it, without the recordings. `idiograph project send --list` says which participants have PETs
and recordings and how big the recordings are, how many boards each has and which is current, and
writes nothing. `--boards current` sends each participant's PETs, and the GETs, with the current board
alone, the one you are going with, and the PET drafts and tables of that board only, the History left
behind. `--boards all`, as before, sends every board.

**Timepoints.** A longitudinal study (Farr and Nizza 2019) interviews each participant more than once,
before the season, at midsummer and after the harvest, say. In Project settings, after PET labels,
Timepoints says how many times each participant was interviewed, 1 by default, set with its minus and
plus. With 1 nothing longitudinal shows anywhere and the app is as it always was. With two or more,
a row each holds its label, T1, T2, T3 to start, his to rename, and its description, Before the
season. The number saves at once, and a label or a description once it is left. Lowering the number
while a timepoint that would go holds an interview is refused under the rows, "T3 holds interviews
of Wren, so the timepoints stay at 3.", and nothing changes. The project file keeps them as
`timepoints`, only with two or more.

A participant is one workbook at every timepoint, never a workbook an interview. Each timepoint is a set of
the participant's sheets: an interview in two parts is two sheets of one timepoint, as it always was,
and an interview at T2 months later is new sheets at the end of the same workbook. With two or more
timepoints:

- each row on the project's page shows the participant's name over a cell a timepoint, its label in
  bold and its description, then where it stands: the passages decided of the passages there,
  Statements complete, or Not interviewed in a dashed cell that opens nothing. PETs follows them as
  before. A cell opens Experiential statements at that timepoint. On a phone the cells stack.
- New project's and Add transcripts' rows each have a Timepoint chooser. A row under a participant
  there already starts at the first timepoint they have no interview at.
- the import card has a Timepoint chooser, starting at the first timepoint the participant has no
  interview at. With a workbook there already the line under it says where the transcript goes,
  "It goes at the end of P2 Tansy - EN & ES.xlsx, as the sheet T3.", and Make adds the sheet there,
  a copy of the workbook kept in `_Archive/` first, and opens the participant at that timepoint.
  Without one, the create card makes the workbook with its sheets at the timepoint chosen.
- the statements screen's bar shows the timepoint where the sheet switch stood, T2 large and
  Midsummer smaller beside it, the description gone below 900 pixels. From 620 pixels down View and
  Feedback give way, so the participant's name keeps its first letters, "P1 W..." at 360. Its menu lists the
  participant's timepoints, each with where it stands, a timepoint not interviewed greyed, and under a
  timepoint of two or more sheets its sheets. Choosing one goes to its first undecided passage.
  Ctrl + Cmd + Up and Down still step through the sheets. The line under the bar, the passages decided,
  Mark complete and Statements complete are the timepoint's, so T1 can be complete while T2 is under
  way.
- each timepoint of a participant has its own PETs canvas (21 October), its statements those of that
  timepoint's sheets alone, with its own boards, its own Current board and its own PETs complete. PETs
  opens on the timepoint in front of you on Experiential statements, and the PETs bar shows that
  timepoint after the tabs, T2 large and Midsummer smaller beside it, its menu listing the participant's
  timepoints with where their statements stand, a timepoint not interviewed greyed. Choosing one saves
  the canvas and opens that timepoint's.
- the LPETs tab, between PETs and GETs, opens the participant's LPETs canvas, longitudinal PETs made
  from their PETs at each timepoint as GETs are made from every participant's. Each card is a PET or a
  sub-theme of one timepoint, "PET · T1" over its title, and a label over cards is an LPET. It can be
  started any time from whatever PETs exist, the Current board of each timepoint, else the board last
  open, and a change to a timepoint's PETs comes in as a participant's does on GETs. The sidebar at the
  left, Timepoints, lists each timepoint with its PETs and statements, one not interviewed saying so.
  A statement's time is cited with its timepoint, "T1, 35:55". The participant picker sits in the tab,
  as on PETs. A double-click on a statement's card edits it as on GETs (30 October), its timepoint's PETs
  boards, the LPETs' copy and the LGETs' copy taking the words at once. The AI's help is not on LPETs yet.
  Since 12 November an LPET's domain shows on its label as its pills, under its title and description, the
  same words in the same colours as on Trajectories. Add domain in the LPET's menu, Edit domain once it has
  one, opens Domain in its Inspector, above its note, where the domain is typed, two or more separated by
  commas. Enter or a click away keeps it, Esc leaves it as it was, and an empty box takes it off. It is kept
  on the LPET of the board on the canvas, so Trajectories shows it when that is the board the LGETs take.
  The canvas is saved first, and the change is not part of the canvas's undo. The LPET table's key quote
  shows his bold from Trajectories on the same words, in the table and in its print view and PDF.
- the LGETs tab, after LPETs, opens the project's LGETs (21 October), longitudinal group themes made
  from every participant's LPETs as GETs are made from their PETs, the same canvas and the same ways.
  Each card is an LPET, "LPET · Wren" over its title, in the participant's colour, and a label over cards
  is an LGET. Each participant comes in from the board their LPETs were marked complete on, else its
  Current board, else the board last open. A statement under an LPET keeps its timepoint, "T1, 35:55".
  A project of two or more timepoints has no GETs at a single timepoint, so LGETs stand in the GETs'
  place, on the bar, on the project's page ("LGETs, across all participants") and for an agent. Its file
  is `idiograph-lgets.json` at the project's root, and a GETs file the project had stays as it was. The
  AI's help is not on LGETs yet.
- the Trajectories tab, last, opens the Trajectories board, laid out as Adam's own page lays his study
  out (10 November 2026). Its title is the project's research question. The trajectories are the
  project's own, made and named on the board itself, never fixed by the app. Each is a band down the
  screen: a head in its colour with its icon, its title and its sentence, then the timepoints across,
  each with its description ("T1: Before the season"), then each participant placed in it, in his order.
  A participant shows their picture, name, own label ("The late starter") and tags, and each of their
  LPETs is a row: its title and its domain, then at each timepoint its key quote over its state.
  - New trajectory, at the end, adds a band whose title is typed at once. A title and a sentence are
    changed by typing over them. The swatch on a band's head opens its colour (Green, Amber, Red, Blue,
    Plum, Teal, Taupe, Orange or None) and its icon (Rising, Mixed, Falling, Level or None), with Done.
    The cross takes the trajectory away, its participants going back to Not placed with all that is
    kept on them.
  - A participant moves by dragging their cell onto a band, landing where they are dropped, by Move to
    in their cell's menu, or with the keys while their cell has the focus: Up and Down within their
    trajectory, Left and Right to the trajectory before or after, Backspace to Not placed.
  - A double-click on a participant's cell, or Edit in its menu, opens their editor in place. Change
    picture... takes an image file, cut square, made small and kept in the project folder
    (`pictures/` since 11 November, the participant's own, `trajectories/pictures/` before), and a picture
    replaced or removed goes to that folder's `_Archive`, never deleted. The picture and the label are the
    participant's own since 11 November (pbiobuild), so the project page, the pickers and the bars show the
    ones set here. A label and a picture this board kept before move into the participant's own the first time
    the project's page lists them or one is changed, a copy of both files kept in `_Archive/` first,
    `(pre-participants <date-time>)`, with one line in the project's History. Choose from the set picks one of the app's 24 drawn portraits. Remove takes the picture off,
    and with none the participant's initial shows in their colour. Then come their label, their tags
    (Add a tag, a tag's cross taking it off), a tag's colour, which is that word's colour on everyone who
    has it across the project, and LPETs shown, a tick for each LPET, all shown until he takes one off.
    Done closes it.
  - Each cell is that LPET's row of the LPET table at that timepoint, so the LPETs screen's table and
    Trajectories show the same. The state is the row's note, typed in place. The key quote is the quote
    the row ticks, and until he ticks one the first quote stands in, fainter. A click on the quote, or on
    No quote, opens the quotes it can take, in three parts. In this LPET holds the LPET's own quotes at
    that timepoint. Elsewhere in this interview holds the participant's other quotes from that interview,
    whose statements sit in another LPET or in none. From the transcript comes last. Choosing one ticks it there, and
    nothing else changes: no statement moves and the workbook is not written. Choose a passage... under From
    the transcript opens the participant's transcript under the row, at that timepoint's interview, with a
    button for each of their other interviews, a box that finds words in the turns, and each turn's words.
    Select words in a turn and press Take the words selected, or press Take the whole turn, and that passage
    is the key quote (whole words, from any of the interviews, 11 November 2026). A quote from elsewhere or
    from the transcript shows as the LPET's own do, with the timepoint before its time only when it comes
    from another interview. A ticked quote whose statement, or a passage whose words, are later gone gives
    way to the first quote again. Words chosen in a key quote go bold with
    Cmd+B (Ctrl+B on Windows and Linux), kept with the row, never in the transcript. A timepoint with no
    quote says No quote over the state. A quote shows in the screen's own quotation marks once, the
    marks its workbook keeps round it left off there and the workbook left as it is, and its bold stays
    on the same words.
  - An LPET's domain shows as a pill under its title. An LPET in two or more domains has them separated
    by commas, "Relationships, Psychological", and each shows as a pill of its own in its own colour,
    the same colour wherever that domain is used across the project. An LPET keeps its domain through
    every change to the LPETs board, made on the canvas or by an agent: a statement brought in, an LPET
    retitled, moved or merged. The LPETs screen shows the same pills on the LPET's label and sets the
    domain from the LPET's menu or its Inspector (12 November 2026).
  - The status bar along the foot counts the participants placed and not placed and the trajectories,
    and holds Quotes, which steps through off, short (three lines) and full, and Notes, each
    participant's note on why they stand there (the old Why box), off until he turns it on. Both are
    kept in Settings.
  - While Notes is on, the screen has a note of its own under the research question, for the whole
    board: a credit for the pictures, say. It is typed in place as a trajectory's sentence is, Enter
    keeping it and Shift+Enter a new line, and an empty one shows Note. It is kept in the trajectories
    file with the board (10 November 2026).
  - The board is kept in `idiograph-trajectories.json` at the project's root, written on the first
    change. A project whose LPETs' notes hold their states as paragraphs headed T1, T2, T3, as one made
    in Excel does, has them moved into the LPET table's rows by an agent (`states_from_notes`), each
    note left as it was.
- the statements CSV from the PETs board's Export menu holds every timepoint's statements, T1's first, each timepoint's in
  the order its own Current board gives and with its PETs, and a last column, Timepoint, its label.
- a timepoint is known by its place, never its label, so renaming T1 Spring moves nothing: its LPETs
  stay as they came in, never "changed since", and cite it as "Spring, 35:55".
- PETs and LPETs made in Excel before Idiograph come in through an agent (9 November 2026), with no
  screen of their own. A table of a timepoint's PETs, with the columns PET, Sub-theme, Experiential
  statements, Location and Quote, becomes a new board at that timepoint, named From Excel unless he names
  it, each row placed on the statement it matches: the same words, else a statement of the passage at its
  Location or with its quote worded nearly the same. The table is the later word, so where its wording
  differs the statement on that passage takes the table's words, as an edit kept in History, and a row
  with nothing close there can come in as a new statement with its quote. A Location may hold two times
  ("18:15 and 05:59", two lines, or split by a comma, a slash or "&"), and the row matches at any of them.
  A statement two rows give is
  placed once. Every other statement waits in Not placed, and his other boards are as they were. A table
  of LPETs, a row each with its title and a line under it, then a cell for each timepoint, becomes a new
  LPETs board: each LPET with that line as its description and the cells in its note, a paragraph for
  each timepoint headed T1, T2, T3. The PETs whose statements its cells quote are put under it as a
  proposal for him to keep or move on the canvas, and every other card waits in Not placed. The agent
  shows him every match first and brings nothing in until he says.

The bar under the question has a button at its left, Not placed, with the standard left-panel icon the boards' sidebar button has. It hides the Not placed band, at the head of the bands, and shows it again, Hide Not placed and Show Not placed in its tooltip. While it is hidden the button carries the number of participants not placed. The choice is kept for the screen in the browser. A participant still goes back to Not placed with Backspace (10 November 2026).

A project of one timepoint, and every project from before, has none of this: one PETs canvas a
participant, GETs and no LPETs, LGETs or Trajectories, its files as they always were.

**One project a run.** A server or a command started with `--root` at a folder is a run of that one
project, whatever `config.json` names. It opens on that project's page, reads and writes the
project file in that folder and nowhere else, keeps its recent list in memory, and adds and removes
no project. Restart in Settings keeps that list, its Sift and Trace projects among them, where until 17
October, later, the run came back with none. The file at a real
root is seeded by hand, and no test or smoke run writes it.

**The band.** Under the top bar and over the three columns, a band the full width carries the label
Research question and the whole question in the serif, on as many lines as it takes. The PETs
screen carries the same band over its canvas. It is just
there: nothing folds it and nothing about it is kept in the browser. The columns under it keep the
rest of the height: the page measures the band into `--band`, and their heights take it off. With no question set, the band reads "No research question yet. Set it in Project settings.", and
Project settings there opens the project's sheet.

**The demo's own.** The demo is a project of its own, with its file committed at
`demo/idiograph-project.json`: Living with a dog, the project of its three participants, asking how people
experience sharing a home with a dog, and what the dog comes to mean to them. Opening any demo participant
reads that file and never a project's, a save for the demo is refused, and Reset demo leaves it alone.

A page in front of a server from before the project finds no `project` in the answers. The band
then shows the no-question line, and Project settings says "Restart the server to finish this
update." in place of its fields.

## Working together: comments and review

With Working together on in Project settings, each participant has one owner, and a teammate can review a
participant he does not own. Nothing of this shows while Working together is off.

**Asking for a review.** On the project's page, a participant you own has Ask for review in its menu, after
Rename. Its card lists your teammates, each ticked by its whole row, and a box for a line to them, "A line for
Curt". Ask for review sends it at once, and the participant's row says "With Curt for review" until his review or
his board comes back.

**Commenting.** On a participant a teammate owns, each statement of the passage you are on has Comment under it.
For a passage, select its words and press Comment beside Quote. On PETs and GETs, Comment is in a PET's or a
GET's menu. Each opens a box, Your comment, with Cancel and Add to review. What you add stays on your computer
as a draft and shows under its passage as "You: ...". While any wait, the top right says "Review for Adam:
2 comments" with Send review, which sends them all to the participant's owner.

**A review that comes.** The owner sees a line at the top right, where an agent's held change shows, "Curt's
review of Juno: 2 comments." with Review. The review card says when it was sent, what you asked, and each
comment with what it is on, "Comment on a passage, 21:45", the words it is on and Curt's words. Reply opens a box
and sends your reply at once. Resolve marks the comment done, and Reopen brings it back. Done closes the card and
keeps every comment you left open as unresolved, still showing under its passage on both computers. The cross
closes the card and leaves the review waiting.

Every comment, reply and review is sealed on your computer before it goes, by the relay or the shared folder,
and one that cannot go for want of a connection goes by itself once there is one. A board a teammate sends shows
on the same line and card (A board sent by a teammate).

**Suggesting a wording or a title.** On a participant a teammate owns, Suggest a wording sits beside Comment under
each statement, and Suggest a title beside Comment in a PET's or a GET's menu. Each opens a small box with the
words as they are now, to change into yours, and Why (optional) for a line to the owner. Add to review keeps it as
a draft with your comments, and the top right counts it, "Review for Adam: 1 comment, 1 suggestion". Send review
sends them together. Nothing changes on the owner's computer until he answers. Under the passage, your wording
stays with "Sent to Adam.", then "Adam accepted it." or "Adam declined it.", with his reason when he gave one.

**Answering a suggestion.** On the review card each suggestion shows Now, what it reads now, and the teammate's
words, with his reason. Accept makes the change as if you had made it, History saying the teammate suggested it
and you accepted it. Decline asks Why (optional) and changes nothing. Either answer goes back to him. When the
statement or title has changed since he suggested it, the card says so with the words he saw, and Accept still
puts his words in place of what is there now. When the statement has gone since, the card says so and offers
Decline alone. A review with a suggestion still waiting stays on the line after Done until each is answered.

## Demo participant

A participant that ships with the app, for showing it to somebody or recording the screen without a
participant's words being on it, and two more beside it for the step across participants. The demo, Living
with a dog, is three invented interviews about sharing a home with a dog, with Juno, Rowan and Mabel.
Nobody real is in them. The participants, the dogs, the households and every word of the
transcripts were written for this and are a composite of nobody. Since 26 October the demo is a
finished project, a worked example of IPA from the first passage to the GETs (Adam, 24 October: "a
complete worked example as if the project was finished"). Juno, Mabel and Rowan each have a recording
(12 November 2026), Juno's about twenty-eight minutes, Rowan's and Mabel's shorter, about eleven and ten. Each
comes annotated: every passage
decided, with its experiential statements, each beside its own key quote, its exploratory note and a
highlight here and there, the rounds closed and Statements complete, and its PETs on Board 1, the
Current board, marked complete, three PETs with sub-PETs, a description under every title and a picked
quote on each PET. Juno's holds 36 statements in three PETs and nine sub-PETs, Rowan's 24 in three PETs
and seven sub-PETs, and Mabel's 18 in three PETs and two sub-PETs, one of hers not placed (the analysis redone
on 12 November 2026). The GETs board across the three, Board 1 of the demo's GETs, the Current board and marked
complete, holds five GETs, each with its description, from the PETs and sub-PETs of all three, the
sub-PETs whose PET carries them set aside, and the quote of each participant's row ticked in the GET
table. The three share a home come alive with the dog, the dog as a way back to people or round them,
being changed by the dog, holding on to the dog through what it costs, and the parting from the dog,
each in their own way. Rowan gave his dog up and has not settled what that was. The PETs tables and the GET table are the app's own, made from those boards, so Open as
table and the exports show a finished project's tables. Every participant's interviewer is named as the
transcript names them, Adam today.

The demo sits beside the app rather than under a project's root, in `demo/`: the transcripts in
`demo/source/` in the raw three-column shape, `Juno - interview.csv` and the two beside it, with
each participant's annotations in `<name> - annotations.json` and the GETs board's in `GETs.json`, each
participant's annotated workbook at `demo/<name>/<name> - EN & ES.xlsx`, built from its CSV by the app's
own create-from-source, its sidecars in `demo/<name>/Working/`, the GETs file at
`demo/idiograph-gets.json`, the copy Reset demo restores from in `demo/pristine/`, the GETs file with
it, and the project file, `demo/idiograph-project.json` (see Projects). That folder is the
one place outside every project's root the server will open, and only that folder: its parent
and every sibling are refused the way a live participant is refused to a server started with `--root` at a
scratch folder.

**Opening it.** The demo's card, the first under Demo projects on Idiograph's Home, carries the "IPA demo"
tag beside its name and its research question under it, and opens the demo's page as a project's card
does, the same tag beside the name at its head. The page holds a row for each participant, Juno, Rowan and
Mabel, in that order, which is fixed, so no row has a handle, the demo's GETs as the same wide card
after them, and Reset demo under them. Each has its two
halves, its lines and Files as any row has, and a small demo tag. Each opens the way any other
participant opens, and while one is open the tag stands beside the name in the top bar, so a recording of
the screen says on its face that these are not a participant's words. None ever enters the recent
list. On
the PETs screen the participant picker of any demo participant lists the three. Each plays its recording
in the player at the foot, as any participant with one does, and a click on a timecode plays that passage. Each
opens on its last passage. Rowan's and Mabel's last was decided with no statement, skipped as zero is a
fine answer for a passage, so its empty first statement under Statements complete on the bar is a
passage read and left blank. Juno's holds her own summary of living with a dog. Every passage of each
participant is decided.

**The highlights.** Each participant's go in through the same function the `H` key called until 16
October, so they are real runs in the transcript cell rather than anything the demo does differently,
and since then they stand in the file as any workbook's highlights do, drawn as plain words.

**Reset demo**, the quiet control under its rows, puts all three participants back from `demo/pristine/`
after a confirm that names every statement, note, quote and board written in them, quote where
it said quote until 16 October, each workbook, progress file and board as it ships, and the demo's GETs
file, `demo/idiograph-gets.json`, put back as it ships, and takes away the exports' `demo/Working/`, so
the same demonstration can be given twice. A workbook open in Excel refuses the reset before anything is
written. A copy of the demo folder added as a project lists its three participants once: its
`pristine/` folder is never read as a participant.

**Building it.** `make_demo.py --written`, or a plain run, builds the whole finished demo from its sources,
the recordings aside: for each participant the workbook through create-from-source, every passage through the
passage screen's own saves, each statement with its own key quote, a quote of pieces found piece by piece in its
passage and joined with an ellipsis as the passage screen joins them, the progress file with its rounds closed and
Statements complete, and the board laid out as an agent's board make lays one out, its descriptions and picks
added, then saved, marked current and
marked complete through the PETs screen's own functions, and then the GETs board across the three, laid
out the same way, its descriptions and ticked quotes added, saved, marked current and marked
complete through the GETs screen's own functions. The clock is held at the times the sources give,
every part of each workbook's zip is dated alike and the files the GETs read are dated alike while they
read them, so the same sources build the same files byte for byte. It writes `demo/pristine/` and the
live demo, and `--force` lets it replace live workbooks already there. The live sidecars and the live
GETs file are gitignored, and the server copies a missing one in from `demo/pristine/` when it starts,
so a clone opens the demo as it ships.

**The thematic analysis demo** (3 November 2026). A second demo, Living with a dog with the "Thematic
analysis demo" tag, is a thematic analysis project of the same three invented participants, built from the
same transcripts, so the two methods can be compared on the same words. Its passages are coded with one
shared code list of 22 codes, each with its description, several codes on some extracts, and notes on
passages where the coding needed one. Its Themes board, done in Braun and Clarke's reflexive way, holds four
themes, each with its definition and most with a note, two subthemes, and two codes not placed. It lives in
`demo/ta/`, a project of its own inside the demo's folder: its project file, the participants' folders, the
code list and the Themes board's file at its root, its pristine copy in `demo/ta/pristine/`, and its
sources in `demo/ta/source/`, each participant's coding in `<name> - coding.json` and the code list and
board in `Themes.json`, the transcripts being the IPA demo's own in `demo/source/`. `make_demo.py --written`
builds it after the IPA demo, and `make_demo.py --ta` builds it alone, the same way and the same bytes every
time. Its project is fixed as the IPA demo's is, Reset demo on its page puts its participants, code list and
board back as they ship, and the IPA demo never reads its participants as cases of its own. Agents open it
with `--demo ta` (see Agents).

**The recordings** (12 November 2026). Each participant's interview is spoken passage by passage in voices
made with Google's Gemini, four synthetic voices designed for the demo: the interviewer a calm man with a
southern English accent, Juno a Spanish woman long in England, Mabel a woman of seventy-three from Lancashire and
Rowan a quiet young man from Dublin. Juno's runs about twenty-eight minutes, Rowan's about eleven and a half and
Mabel's about ten and a half. Each transcript's timecodes are written from the measured passages with half a
second between them, so clicking a timecode lands on the words of that passage. They replace the macOS `say`
voices the demo had until then, which spoke Juno's alone.

The three recordings are committed in `packaging/recording/`, each named by the participant, the sheet and the
hash of the transcript it was made from, with their own licence beside them, `LICENSE-audio.md`: AI-generated
speech, to be copied and shared only unchanged and only as part of Idiograph or a version of it, and never used
to train or evaluate an AI model. The README's licence line says they are the one exception to the AGPL.

The demo's own copy of each, in `demo/<name>/Source/Initial/Source/`, is gitignored. The first time a
participant's player looks for it, the server copies it in from `packaging/recording/`, in a moment, and the
installed app ships all three in its demo. Nothing is spoken on your computer. A transcript edited since its
recording was made has none, since its timecodes no longer match the voices, and its player shows nothing, as
for any workbook without one. By hand, each recording put in place:

```
.venv/bin/python apps/idiograph/make_demo.py --audio-only
```

An edited passage is voiced again by `packaging/recording/voice_demo.py`, which speaks that passage alone, joins
the recording again and writes the timecodes, then builds the demo again (see Internals, The demo's
recordings).

## Experiential statement guidance

The guidance stands under one heading, Experiential statement guidance, in the label face a step
above the two section headings inside it. The first section, Holding the craft, carries eleven lines
distilled from Adam's own guide to experiential statements, in your words: what the experience was like,
with the participant's stance, rather than a bare event or a topic, your own interpretative words, the
phenomenon the research question asks about first, the research question rather than the interview, one
idea per statement, the words it needs and no more, a statement that stands alone, not every passage
needing one, the movement in it, their stance kept whole, never smoothed into gladness, and force. Under
them stands his framing, that 1 and 2 are about the experience and interpretation, 3 and 4 about
relevance, 5 to 8 about form, a matter of judgement, so a statement that breaks one may show the line is
wrong, and 9 to 11 about what a statement carries, 9 and 11 being project rules. A colon after the phenomenon is fine, and no nudge flags one.
Each line has a small arrow at its end that opens, in place, two short example statements on the demo's
topic in two columns, Less this and More this, showing what the line means in practice. One stands open
at a time, and the arrow is a button, so Enter opens it from the keyboard.
They live in `guidance.md`, one per line starting with `- `, so editing that file changes the guidance,
each line's examples indented under it as `- Less this:` and `- More this:`,
and the plain paragraph under the section's heading there is the framing, which can be reworded the same way.
The craft prompts, one of which the first statement's field shows on every passage, sit in the same file under
a Placeholders heading and are read the same way. Each section is taken by its heading, so the two
never mix. Those lines are written with `*` rather than `-`, which is what keeps them out of the
rail on a server started before that section existed.

Guidance on the bar, an open book and its word after View, opens it, and `G` does the same from
anywhere outside a field, "Guidance (G)" in its tooltip. It slides in from the right edge of the
screen under the bar and the research question, over the right of the screen, and takes no width from the three
columns, so they keep their widths at 1280 wide whether it is open or closed (16 October, Adam's
decision on a tester's feedback, who asked for the notes in a column beside the transcript, the IPA
book's layout, which the three columns of 17 October gave whole). Under reduced motion it shows
and goes with no slide. Its close button at its top right, Guidance again, `G`, `Esc` and a click
anywhere outside it close it, and a click outside goes on to do what it does. It is closed on a new
install, and open or closed is kept in the browser beside the theme, so a reload opens it the way it
was left. Until 16 October the guidance was a rail with a column of its own at the right of the
screen, open by default, whose arrow put it away to a slim tab at the screen's edge, and a rail put
away then reads as closed now, as does a rail left open, so it never opens over the fields by
itself.

Open, the sheet carries a card's firm edge at its left with a dialog's lift, so the fields under it
read as under it, where at 1280 the faint rule left no edge and the form beside it looked cut
mid-word, and below 520px wide it takes the whole width, as the Participants panel does on GETs, where at
360 a strip of cut words stood beside it (17 October). While it is open the keyboard is in it, never
in a field it covers: a reload with it open, a passage opened from a board and a move by `Cmd + J` or
`Cmd + K` put the keyboard on its close button, as Guidance does, or leave it where it is inside the
sheet, where until then a reload left the caret in a statement under it. Closing it hands the
keyboard to Guidance on the bar, and a click in a statement takes it there.

Above 1100px wide the open sheet lies over the last of the three columns whole, its left edge at the
column's, so the columns before it stand whole beside it, where that column is 300 pixels or more,
as at 1280 in the book's order, where the notes' column is about 320 (17 October, where until then
it lay over the fields' column, and before that its 340 pixels left a strip of the fields about 70
wide showing with their words cut). At every width it stands under the research question, which
stays whole above it. Where the last column is narrower, and at 1100px and below down to a phone's
width, it is 340 pixels wide, and the rest of the screen sits under a wash of the paper, so what
stands beside it reads as under it, and a click there still closes it and goes on to do what it
does. The guidance speaks of the participant as they, as do the craft
prompts in the statement's field, the exploratory notes' prompt and the interviewer note's prompts,
since a participant may be anyone: "Mark their stance", "What are they noticing, doing, feeling
here?", "What matters to them, how they say it, what it might mean." (17 October, later).

The second section, Three personal examples, holds three of Adam's own statements, redrawn on every
passage, from the two pools `config.json` names: `corpus`, a markdown file of statements under one
heading per source, less any source named in `corpus_exclude`, and `gravity_reference`, a finished
workbook whose statement column is the register anchor for this project. The tick box under them,
Examples from this project only, narrows them to the reference workbook alone. With neither file on
the machine, as in a shared copy, both draw on the statements the demo ships with in
`demo/pristine/`, and with no demo either the section is empty. No statement is written into the
code. The prompt's `{examples}` fills from the same source, six at a time from the reference set.

**AI suggestions, if you want them.** Off by default, switched on in settings. With them on, an AI
suggest button sits under the statements, where its answers appear. One press takes the button
away and puts the section in its place, under the heading AI suggestions: a line of key concepts,
then the candidate statements listed under it. Clicking a candidate fills the statement of the pair
being worked on when it is empty, and else adds a pair with it under the last. The X beside the heading closes the answer and brings the button back, and
a fresh press asks again and gets a fresh answer, the model being sampled each time. The next passage
draws the button again. Nothing it says reaches the workbook on its own, and the passage leaves the
page only when the button is pressed.

The suggestion runs in two passes. The first asks for up to ten drafts, more than will be kept, and
the second hands them back with the rules and keeps the strongest one to three. The prompt in
Settings is sent unchanged in both, because what each pass is asked for rides in the user message
rather than in the system prompt.

The call carries the prompt from settings, the project's research question, the statement rules,
six of your own statements from the GRAVITY set, and the current passage with the interviewer's passage
before it. When the passage's pairs already hold quotes, the button sends them too,
ten at most, and both passes ask for statements centred on them in the light of the whole passage, with
"with your quotes" beside the AI suggestions heading. It asks for strict JSON and
reads it defensively, so a bad answer is one line in the panel. An error from the API comes back as
one line in plain words with its status in brackets and nothing else, "Anthropic refused the key (HTTP
401).", "Anthropic asked for a break from requests (HTTP 429)." or "Anthropic did not answer (HTTP
529).", and from a local model "Ollama refused the request (HTTP 404)." (17 October, later, where it
said "The suggestion call answered 529."): no header and no body reaches the page. A refusal from the model is one
line too, and so is an answer cut off at its length limit. The same switch and key serve
the AI help in PETs (see PETs), which asks the Experiential statements model unless Settings gives
PETs one of its own.

Eight providers can answer (aipage, 8 November 2026), chosen under Provider in settings and stored as
`ai_provider` in `config.json`. Both passes go to the same one, through one function, `complete` in
`ai_suggest.py`. Under the list one line of small type says where the passages go, as each provider's own
published terms put it, the fact an ethics form asks for:

- Anthropic, with your key (`anthropic`, the default), over the Messages API: "Passages go to Anthropic. They are
  stored in the US and may be processed in other countries."
- Mistral, with your key (`mistral`), at its EU address, `api.eu.mistral.ai`: "Passages go to Mistral, in the EU."
- Google Gemini, with your key (`gemini`): "Passages go to Google. On Google's free tier they may be used to
  improve its models and read by its reviewers."
- OpenAI, with your key (`openai`): "Passages go to OpenAI, which may process them in any country."
- Azure OpenAI, your organisation's (`azure`), with its Address and its Deployment, typed in place of a Model
  list: "Passages go to your organisation's Azure. Where they are processed depends on how it was set up."
- Another service, by its address (`other`), a university's own or one such as OpenRouter, with its Address, the
  key it asks for and its Model list, or the model's name typed where it lists none: "Passages go to" and the
  address's host.
- Local, Ollama on this machine (`local`), and Local, LM Studio on this machine (`lmstudio`), each with its Address
  filled with the usual one, `http://127.0.0.1:11434` and `http://127.0.0.1:1234/v1`: "Passages stay on this
  machine.", or the host an address elsewhere names.

Every row but the provider's own is hidden, and choosing another shows its rows at once, asks for its key's state
and its list, and loses nothing typed for the one before. Mistral's, Gemini's, OpenAI's, Another service's and LM
Studio's Model lists are the service's own list, by the models' own names, with no price. An address must be
https, or http on this computer. With AI features off none of this shows and no list is asked.

For Anthropic, the Model dropdown lists the current models, Fable 5.1, Opus 5.5, Opus 5, Opus 4.8,
4.7 and 4.6, Sonnet 5.5, Sonnet 5 and 4.6, and Haiku 5.5 and 4.5, each by its name. The chosen model's price
per million input and output tokens stands on its own line under the list, "$2 in, $10 out, per million tokens"
for Sonnet 5.5, so neither the name nor the price is cut short. The PETs model list still names each model
with its price, "Sonnet 5.5 · $2 in, $10 out, per million tokens". With a key stored the list comes live from
`GET /v1/models`, cut to those models and kept in that order, so a model the account cannot call is
not offered. The live list is held for an hour, and saving or removing the key lets it go. With no key,
or when the live list does not answer, the table built into `ai_suggest.py` stands in, and a line
under the dropdown says which you are looking at, and why in the same plain words, "The built-in list,
because Anthropic refused the key (HTTP 401).", in the amber when the live list failed, and so does
the line beside Check key when the keychain or the key fails (17 October, later). The choice is `model` in `config.json`, Haiku 5.5
by default, at a fraction of a cent per passage. A dated id stored before, such as
`claude-haiku-4-5-20251001`, still works, shows as Haiku 4.5, and stays as it is when the plain id
is saved over it. No request carries `temperature`, `top_p`, `top_k` or a `thinking` field, and
none prefills the answer. The 5.x models think by default, so they get a higher token ceiling and a
longer wait, and the answer is read from the text blocks alone.

For Local, the dropdown lists the models Ollama has pulled, from `/api/tags` at `local_url`
(default `http://127.0.0.1:11434`), and the choice is `local_model`. A suggestion is one
`/api/chat` call per pass, not streamed and held to JSON. Nothing about the key applies, nothing
leaves the machine and nothing is charged. With Ollama not running, the Local option says so and
what to do: install it from ollama.com, pull a model, for example `ollama pull llama3.1:8b`, and it
appears in the list. Its Address is `local_url`.

**The key.** Settings carries a hidden field for the API key, a Check key button beside it (21 October,
in place of Save key), and a line saying whether one is stored and where, or what Check key found.
Enter in the field is Check key, which stores the key only when the provider accepts it. They show under every
provider that takes a key and stand aside under the two local ones, which need none. Saving puts it in the macOS
keychain as a generic password under the provider's own service name, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`,
`GEMINI_API_KEY`, `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, or `IDIOGRAPH_AI_KEY` and the host for Another service,
replacing whatever was there before, and Remove deletes the chosen provider's item alone. The key never lands in `config.json`, in `state.json` or in a log, and the verbose log prints
the path of a key request and never its body. It is read inside the server at the moment a
suggestion is asked for, and goes no further than that request. Saving passes the value to the `security` tool as an
argument, which makes it visible in the process list for the life of that call, milliseconds on a
single-user Mac. That is the trade for never writing it to a file, and it is accepted here. A
machine with no `security` tool falls back to `.env` in the app's folder at mode 0600, and the status
line says which of the two it found. A key already in `.env` is read first and is left to VS Code:
Remove does not touch that file.

**The prompt.** The whole system prompt is a template in `config.json` under `ai_prompt`, shown in a
box in settings with a Reset to default beside it. `{research_question}` becomes "The study asks:"
and the project's question, with a sentence saying every statement answers it, and goes with that
sentence when the project has none. A suggestion on the demo carries the demo's question, and one on
any other participant the root's. `{guidance}` becomes the lines of the rail and `{examples}` six of your
own statements, each as a bulleted block. Settings names the three under the box in one line,
"Placeholders: {research_question}, {guidance}, {examples}". A template with no `{guidance}` or no
`{research_question}` in it is sent as it stands, in case you want one without, which is how a
prompt saved before the placeholder existed still goes out. A template with no JSON in it takes the
shape instruction on the end, so the answer stays parseable whatever else you do to it.

**The test bench.** Under the prompt sits one passage of the demo participant: the participant's passage in a
box, and the interviewer's passage before it above the box, in the smaller faint type the sheet gives
an interviewer's passage. Both are read from `demo/source/Juno - interview.csv` when settings opens
and never from a project folder, so no participant's words are on it when the app is shown, and both
can be edited. Its label reads Test bench (invented sample data), and a line of small type under the
boxes says "A passage from Juno, the demo participant, which is fictional. Nothing from your own participants is
sent.", and stays as it is when the box is edited. Under them is the AI suggest button, the one
under the statements, in its look, its icon and its label, and it sends what that button sends: the passage, the passage before it, its
timecode, the speaker and the participant, built by the one function `suggestBody` in `distil.js`, with the
provider, the model, the prompt and the research question of the participant's own project as saved, the rest as they stand in the panel,
saved or not. The answer takes the button's place the way it does under the statements, the
key concepts and the candidates with the model and the seconds it took, and the X brings the button
back. Nothing it says is written anywhere, and Reset to default fetches the passage again. The
endpoint is `/api/suggest-sample`: asked with nothing it answers the sample, and asked with the
four fields it runs the suggestion. A page from before this sends the one box as `text`, a passage per
`Name:` line, and is still answered. `/api/models` sends Anthropic's list and Ollama's status, and while another
provider is chosen that provider's list alone.

As a statement is typed, nudges appear from the checks in `ipa_annotation_audit.py`: a statement
past the project's statement length, 15 words by default (no minimum), a The/She/Her/A lead, a quoted fragment, a semicolon, an em dash, an arrow, the
reads-as construction. Each can be switched off in Settings, under Experiential statements, where
they sit under the small heading Nudges. Until 3 October 2026 the screen called them flags.
Nothing blocks a save and nothing is scored. The length nudge has no minimum, because about a fifth of Adam's own statements run to
six words or fewer.

**Nudges explained.** Each tick under Nudges in Settings carries a small circled i after its label,
reached with Tab and read out with its words. On hover or on focus it says what the nudge catches,
gives an example made up for it, and says why it is there where the code gives a reason:

**Statement length.** In Project settings, under Experiential statements, Statement length is the words
past which the length nudge speaks and the count under a statement turns amber (5 November 2026, where
from 21 October it stood in the length nudge's own row in Settings). The nudge's row in Settings says "word
count past the statement length", and its tick turns the nudge on or off for every project, each using its
own number. It is the project's own (20 October, after a tester's statements of 28 words), 15 by default,
the band of the book's census, which the number's tooltip names. Type it or step it with the arrows, from 5 to 60, and it is saved in the project's file a moment after the last
change, written there only when it is not 15. The demo's is fixed.

*Word count past the statement length.* Catches a statement past the statement length in Project settings, 15 words unless it is changed. For example, "Walking the dog each morning
before work becomes the one part of the day she keeps for herself", at 18 words. In a census of
1,560 statements the median ran to 10 words, and 78% to between 7 and 15.

*Opens with The, She, Her or A.* Catches a statement that opens on its subject or an article, The,
She, Her, A and the like. For example, "She feels calmer once the dog is asleep". The corpus drops
the subject, as in "Calmer once the dog is asleep".

*A quoted fragment.* Catches inverted commas inside a statement. For example, "Feels 'properly at
home' with the dog around". In the corpus one statement in seven carries a quote, and then a single
crux word.

*A semicolon.* Catches a semicolon inside a statement. For example, "Missing the dog" and "dreading
the empty flat" joined by one.

*An em dash.* Catches an em dash, the long dash. For example, "Calm at home" and "restless on the
walk" joined by one. It is typical of AI writing, rare in speech and in most writing, and best
avoided.

*An arrow.* Catches an arrow, drawn as → or typed as ->, inside a statement. For example, "Fear
→ trust on the second walk".

*The reads-as construction.* Catches a verb of interpreting, reads, casts or recasts, with as a few
words after it. For example, "Reads the barking at the door as a warning", where "Hears a warning in
the barking at the door" says it with a plain verb.

A nudge says what it has to say and no longer quotes the statement back: the statement is just
above it. Each statement's nudges stand under it, so none opens with a line number, as "Line 2:" did
while the statements shared one field.
