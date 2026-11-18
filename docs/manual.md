# Idiograph manual

Idiograph is a writing surface for Interpretative Phenomenological Analysis (IPA) and reflexive thematic
analysis. It is free, open source and flexible. It runs on a Mac, Windows or Linux, and your files stay on your
computer. When you make a project, you choose its method: IPA, Longitudinal IPA or reflexive thematic
analysis (RTA). You cannot change the method afterwards.

In an IPA project, Idiograph covers step 3 of IPA and the steps after it. You go from transcript to
experiential statements to PETs to GETs, reducing the detail while keeping its complexity. There are three
screens. In Experiential statements you read a participant one passage at a time and give each passage its
experiential statements, with exploratory notes and quotes beside them. In PETs you group the participant's
statements into personal experiential themes on a canvas. In GETs you group every participant's PETs into
group experiential themes. Experiential statements writes straight into the same `EN & ES` workbook that
Excel opens. PETs keeps its boards in a file beside the workbook, and GETs keeps its own at the project's
root. Nothing else in the pipeline changes.

A thematic analysis project follows Braun and Clarke's reflexive thematic analysis. It has three screens.
In Coding you read a participant one passage at a time and give each extract its codes. Code list shows
every code with its extracts across the participants, and there you rename, describe or merge a code.
Themes is the thematic map of every participant's codes. A thematic analysis project has no PETs,
timepoints or trajectories. Its extracts and their codes go into the same workbook, and the code list goes
into a file at the project's root. A codebook approach, such as template or framework analysis, or coding
reliability with a second coder, is a different method.

How to install and start it is in the [README](../README.md), and how it works underneath in
[docs/internals.md](internals.md).

**Home and its screens (20 October).** Idiograph is the app for IPA and thematic analysis. Its Home holds
your projects of both kinds and the demos under Projects. An IPA project's screens are Experiential
statements, PETs and GETs. A thematic analysis project's screens are Coding, Code list and Themes. Home
opens with the app's wordmark and one line. The analysis no longer has a name of its own beside the app's.
Idiograph's own mark, the dot between brackets, stands on its bars. Its colour is a deep blue, and the mark
and Idiograph's tab in Settings use it. On 20 October Home said under its line "Free, open source,
flexible, your files stay on your computer." Open a participant, below, says what Home shows now.

**Participant, and Quote (20 October).** Every screen now says participant where it said case. This covers
the Participants panel on GETs, the participant list on a project's page, the participant picker, Back to
the participants, "Participant complete." on the card at the end of a transcript, and a This participant
search. A quote is what used to be a key quote. That word changed on the statements screen, on cards, in
the Inspector, in Search, on the status bar's Quotes on cards and in the prints. The command line and the
MCP tools keep their names, case, cases and key_quote, so nothing that reads them breaks. Since 22 October
three more places say Quote too: the column in a new participant's workbook, the statements CSV's last
column, and the lines that a new AI board on GETs wrote until 11 November 2026. A workbook made before then,
whose column says Key quotes, reads and saves as it always did, and Idiograph leaves its heading as it is.
Since 23 October an AI agent can rename that heading to Quote when you ask it to. It can do this for one
participant's workbook or for every one in the project, through Idiograph's own command line or MCP tool,
with a dry run first. Only the heading changes, and Idiograph first puts a copy of the workbook as it was
into the participant's `_Archive` folder. When a participant's changes come into the GETs, the board's
History keeps the revision before them as "Before Rowan's changes came in". The Offset card under the
player says "Your time codes are not changed." under its seconds (21 October).

Every save writes the whole workbook back. A cell the save does not change comes back as it was. Its
formatting stays: each run of a highlight, bold, italic, an underline, a strike, a colour, a size and a
font. Each space stays too, even a run or a cell of spaces alone, and so does each line break. This is the
same in the installed app as in a run from source (17 October).

**Passages and rounds.** A passage is one person's stretch of talk, one row of the transcript. The
interviewer's passages are context. The word comes from the IPA book. Smith, Flowers and Larkin (2022,
*Interpretative Phenomenological Analysis: Theory, Method and Research*, 2nd edn) speak of a passage of
the participant's account in Chapter 5, at the exploratory notes. They use "turn in the conversation" only
in passing, in Chapter 4's advice on transcription. So the app says passage where it said "turn" until 15
October. Rounds are ten minutes of transcript at a time, with a daily target, a streak and the time left.
They are a pace of the author's own and not a step of the method. So they are a setting, Work in rounds,
which each project has in the statements screen's View and which is off in a new project (see Rounds).

Every Remove or Delete button with words looks the same, including the ones on confirm cards. It has a red
outline with a small bin before its word, so you can recognise a button that takes something away wherever
it stands (12 October, later). The Remove on each pair of statement and key quote was one of these from 14
to 18 October. Then it became a bin alone at the pair's top right (see Pairs). The entries of the canvas's
menus that take something away look the same way: Delete this label and Delete note, and the board menu's
Delete this board. Each has its red word and bin, and is outlined only under the pointer, as a menu's
entries are (16 October). Take out of PET, called Remove from PET until 20 October, moves a card and deletes
nothing. So it carries an arrow out of a frame, in the ink.

**Every tick from its whole row.** You can tick every checkbox and radio in Idiograph from anywhere on its
row, its words as well as its box. The pointer changes over the row, and the row is shaded under it (13
October). If a row holds other controls too, such as a name box, Remove or a handle, you can tick it from
anywhere except those controls. Every radio is the app's own. It is a ring with nothing in it until you
choose it, and then it has a dot in its middle, in light and dark alike. Before, in dark, the browser's own
radio filled an unchosen one with grey, so it looked almost chosen (17 October, later). Every tick and
radio is in the ink. The crux orange is kept for a crux, a quote and the filled button. A card that keeps
each change as you make it ends with Done at its foot right. Done closes it, as the X at its top right does.
A card with its own Save or confirm never has Done.

**In a window of its own (17 October, not shipped yet).** Idiograph is becoming an app with a window of
its own and its icon in the Dock or the taskbar, in place of a browser tab. In the window, Print opens the
system's print panel, which includes Save as PDF. Each print view opens in a window of its own that prints
the same way. Saving a file opens the system's save panel with the file's name already in it. If the file
cannot be written there, the app says so. A link to another site opens in the browser. Opening Idiograph
while it is open brings its window forward. New Window, Cmd or Ctrl+N, opens another window on what the
front window shows: the same participant, board or project. So two windows can sit side by side, one on
each screen. Since 20 October Open in a new window opens a participant's statements or a board in a window
of its own, in the browser as well as the app. You find it beside each participant in the participant
switcher on PETs, including the one on the screen, and for a board in the board menu under the board's
name. So a transcript can stand on one screen and a board on another. Two windows keep each other up to
date without you pressing anything. When you save a passage's statements, notes or quotes in one window,
they show in the other a moment later, where they stand. Each statement that changed shows a brief wash of
the crux orange that fades. The other window keeps its place in the column and the passage being worked on.
A change on a board, such as a statement reworded on it, comes onto the same board in the other window by
itself (see Changes made elsewhere). A field holding words not yet saved waits until they are saved. One
window stays the default, with no floating panels. Closing the last window quits Idiograph, and Quit in
Settings closes its windows. Since 31 October, Quit and closing the last window finish Idiograph's work
first and then end it, with its windows put away. If the window ever closes without Quit, as in a crash,
the part behind it closes by itself within about fifteen seconds. Before, it waited five minutes. When you
run Idiograph from its folder with `server.py`, it keeps the browser tab as it was.

**The window's menus (17 October, later, not shipped yet).** On a Mac the menu bar is a Mac app's own.
The Idiograph menu holds About Idiograph (see About Idiograph, under Settings), Settings… on Cmd+comma,
Hide and Quit. File holds New Window, Open Recent, Project History, Project Settings… and Close Window.
Open Recent lists Home's projects, and each opens in a new window where its card opens. Project History
opens the History of the project open in the window, as Home's project menu does. It is grey on Home and in
the demos. Project Settings… opens that project's Project settings and is grey on Home. Edit holds Undo,
Redo, Cut, Copy, Paste and Select All. Undo and Redo take back a move on a board or the last words in a
field, whichever has the focus. Then come Find… (Cmd+F), which opens Search on any screen, and Find and
Replace… (Cmd+Shift+F). Find and Replace… opens Experiential statements' Find and replace card and is grey
on every other screen (6 November 2026). Then comes Spelling and Grammar. Check Spelling While Typing is on
there, so a misspelt word is underlined as in a browser. View holds Home, Cmd+Shift+H (Alt+Home on
Windows), which goes to Home from any screen. Then come Bigger Text, Smaller Text and Actual Size, Cmd
with +, - and 0. They zoom every window together, and Idiograph keeps the size for the next time, the same
as Text size in Settings (see Text size). A line at the foot of the window says the new size for a few
seconds, for example "Text size 110%". View also holds Reload, and on a Mac Enter Full Screen. Since 17
November 2026 the status bar is always on, so View has no item for it. In a print view or the manual these
items zoom that window alone. On a Mac, Cmd+S in a print view opens its print panel, where Save as PDF is.
Window holds the Mac's own items, including the tab items. Help holds the manual, What's New in Idiograph,
which shows the notes of the version you have (see Updates, under Settings), Keyboard Shortcuts and Send
Feedback. On Windows each window has a menu bar of File, Edit, View and Help with the same items and
Windows's keys, such as Ctrl+Y for Redo. Find and Find and Replace are in Edit on Ctrl+F and Ctrl+Shift+F,
Settings is in File with Exit at its foot, and About and What's New are in Help. The windows stay separate
windows. Linux has Windows's menus. There, Edit's Undo, Redo, Cut, Copy, Paste and Select All show no keys,
but Ctrl+Z, Ctrl+Y, Ctrl+X, Ctrl+C, Ctrl+V and Ctrl+A work in a field and on a board as they always do.
Every window opens whole on its screen. If the screen is smaller than the window, the window is made
smaller. A new window opens a step down and to the right of the last one, and its foot is never under the
taskbar or the Dock. Each window's name starts with the app and then says what is in it, as in
"Idiograph - Living with a dog - Juno - Experiential statements". That is the project, the participant if
the screen is one participant's, and the screen. Home is just Idiograph, and a project's page is Idiograph
and the project. So you can tell two participants in two windows apart in the Dock, the taskbar and
Alt+Tab. Choose beside a folder opens the system's own folder dialog on either system. The window opens at
the size and place it had when Idiograph quit. If it opens again within ten minutes, for example after an
update or a Restart, it opens on the same screen. Settings kept on the computer, such as the folds and the
filters, follow Idiograph whichever port it starts on. Closing a window saves what you typed first. If that
cannot be saved, the window asks before it closes. Printing keeps the date, the title and the page's address
off the paper. General's Closing tick speaks of tabs, so the window does not show it. If Idiograph stops
without being asked, the window says so once, over the page: "Idiograph stopped unexpectedly. What you saved
is kept. Close this window and open Idiograph again." If it does not start at all, a small notice says
"Idiograph could not start. What you saved is kept. Open Idiograph again." A file you drag onto the window
from Explorer or the Finder lands as it does in a browser.

## Installing it

On a Mac, download `Idiograph.dmg` and open it. It is for Apple Silicon Macs (M1 or later). A Mac with an
Intel processor keeps the version it has, which goes on working, but gets no newer one. The dmg's window
shows Idiograph at the left and Applications at the right with an arrow between them. Drag Idiograph onto
Applications and open it there. While the build is not signed, macOS says the first time that it cannot
check the app. Open it once with System Settings, Privacy and Security, Open Anyway. On Windows, download
`Idiograph-Setup.exe` and run it. The first time, Windows says that it protected your PC. Choose More info,
Run anyway, once. Setup installs Idiograph for you alone, with no administrator's password and no restart,
as its first page says. It puts Idiograph in the Start menu, and its last page offers a shortcut on the
desktop. A newer version installs over the one you have in the same way. Every project, participant and
setting stays where it was, even through an uninstall. The last page's tick, Open Idiograph, opens the app
as Setup closes. If you run Setup for the version you already have, it offers to install it again or
uninstall it. If you run one older than yours, it says "A newer version of Idiograph is installed. This
Setup is older." and asks what to do. Idiograph needs Microsoft's WebView2. If Windows lacks it, Setup
installs it first. If Setup could not download or install it, Setup says so plainly and asks you to run
Setup again. The uninstaller has one tick, Also clear the window's size, zoom, appearance and folded
sections. It clears only what the window remembers. Your participants, transcripts and projects stay
either way. On Linux, download `Idiograph-x86_64.AppImage`, make it executable and run it (Ubuntu 24.04
needs `libfuse2t64` for that). On Ubuntu, Debian or Mint you can instead install `Idiograph-amd64.deb`,
which does not update itself. Each download is the newest version, from Idiograph's page on GitHub,
github.com/Pharkie/idiograph. Once it is installed, Idiograph can update itself (see Updates, under
Settings).

**From 0.9.0.** Idiograph 0.9.0 opened in your browser. On a Mac, first quit it from Settings, Quit
Idiograph. Then drag the new Idiograph to Applications and choose Replace. On Windows, run the new
`Idiograph-Setup.exe`. It stops 0.9.0 and removes it before it puts the window in its place. Your
projects, participants and settings are there when it opens. On Windows, if you had added Idiograph to Claude
Desktop, choose Add Idiograph to Claude Desktop again in Project settings, because the program it
names has moved. On a Mac the entry that 0.9.0 wrote still works.

## The loop

**Open a participant.** Idiograph's Home opens with its wordmark and the Preview Edition stamp. Then comes
its line, "Software for Interpretative Phenomenological Analysis", and under it four short items in a row:
Free, Open source, No cloud and Flexible. Then comes the panel that says what the preview means. Since 13
November it stands after the line and its items. Before, it stood under the wordmark. When the row wraps,
Open source, No cloud and Flexible keep together, so no word is left alone on a line (22 October). At the
bottom right of Home, under everything else, stands a pale blue button, "Support me on Ko-fi", in Ko-fi's
own look. When Home is short, it stands at the window's foot (17 November). Its cup with a heart gives a
little wiggle every few seconds. The button opens Adam's Ko-fi page in your browser. The cup stays still
when your computer is set to reduce motion. The app draws the button itself, so nothing comes from Ko-fi
until you press it. The head stands on the same grid as the projects under it (5 November). The lockup is
at the top left. Above it is room at least the height of its mark (32 pixels for the Preview Edition's
lockup) below the top of the window's own title bar (6 November). The page keeps a margin of 32 pixels at
each side, whatever the width of the window. Search, Send feedback and Settings stand level with it at the
top right. They show their words as they do on a project's screens, and give them up in the same way when
the window is narrow. The preview's panel is as wide as the column allows, so it reads in four lines. Then
comes Projects, with a card for each project in the order you added them (see Projects). Its head folds the
section to the head alone and opens it again. This browser keeps the fold, so a reload keeps it. A card
shows the project's name in the serif and its research question under it, as Project settings has them.
Under those, in the small type, it shows the project's participants and how many have PETs, meaning a
board or PETs marked complete, as in "3 participants, 2 with PETs". Under that it shows the GETs: "GETs not
started", the group themes on the Current board, as in "GETs: 4 group themes", or "GETs complete" once you
mark them. The demo's card has no GETs line. Under each project's name, on a line of its own, the card shows
the project's type in the plain grey tag (17 November 2026). The tag is IPA, LIPA for longitudinal IPA or
RTA for reflexive thematic analysis, as the project's Method says (see New project). A demo's card has its
own coloured tag in its place. Each card's dots, at its top right, open its menu (see A project card's
menu). Under the cards stand New project, Open project and Open a shared copy (see Projects). Open project's
tooltip is "Open a project folder already on this computer". Open a shared copy's tooltip is "Open a copy of
a project someone has shared with you". Under Projects stands Demo projects. It is a section of its own,
apart from your projects, and holds the four demos. Living with a dog is tagged "IPA demo". A second Living
with a dog is tagged "RTA demo". It codes the same three invented participants in a thematic analysis
project, so you can compare the two methods on the same words. First year on an allotment is tagged "LIPA
demo" (13 November 2026). It has three other invented participants, Hollis, Nell and Arlo. Each was
interviewed before the season, at midsummer and after the harvest. The demo has their PETs at each
timepoint, their LPETs, the LGETs and Trajectories, and each interview's recording. Working from home is
tagged "RTA demo" too (17 November 2026). It is a thematic analysis project whose interviews were made for
reflexive thematic analysis. An invented researcher, Leah Marsh, asked six invented participants, Kemi,
Toby, Ros, Glen, Dev and Ffion, one shorter guide. The demo has its code list, its Themes board, her
reflexivity statement as the board's note, and each interview's recording. Demo projects starts folded to
its head. If you open it or fold it, Home keeps it that way, as Projects keeps its fold. On a Home with no
project of yours yet, it starts open until you open or fold it, so you can find the demos. Each demo's card
opens its page, and its menu holds Project settings, read-only. Everything in the demos was made with AI,
so each card says so on a line at its foot, "AI-generated demo". That line opens a note with the same title:
"Real interviews are confidential, so these demos are generated by AI." and "Please don't take this as an
example of what a finished study looks like." (the same on every demo, 17 November). Inside a demo the same
note opens from the Demo mark beside the project's name. Settings, the cog and its word at the head of
Home, opens Settings on General.

A card opens its project's page. At its head are the way back to Home, a round arrow, then the project's
name with its type tag beside it (IPA, LIPA or RTA), and then its question. Under them, a row of tiles at
the top holds the work across all participants (17 November 2026, Adam's option A). Since 18 October one
wide GETs card had stood after the rows. Each tile has its status line and opens its screen. An IPA project
has GETs, "3 of 3 participants in · Board 1 · GETs complete". A longitudinal project has LGETs and
Trajectories, "3 trajectories · 3 of 3 participants placed". A thematic analysis project has Code list,
"24 codes", and Themes. Then comes a row for each participant, the full width of the column, with
everything of one participant in their box, and Add transcripts under them. A project with no participant
yet, as New project leaves it, has Add transcripts where the participants will stand. From a participant,
from Experiential statements, PETs or GETs, Back, the mouse's back button or Cmd + [ lands on the project's
page. A reload keeps the screen you are on: Home, a project's page or a participant on its passage. A run
with `--root` opens straight on its one project's page. A participant is a participant's folder under the
project's root. A workbook sitting in the root itself is a row of its own, named by its stem. A row's title
is the participant by their P-number and pseudonym, "P8 Wren". A folder named `P<n> -
Pseudonym-Secondname` shows by its pseudonym alone. The second name reaches the page only inside the paths
the server needs to find the file, and the page never draws those.

Each row holds the participant, their tags and the three dots, then two halves side by side. Each half is a
button. On a phone, under 560px, the halves stack under the name, and nothing scrolls sideways.
Experiential statements opens the participant at the passage after the last one you were on. Under it, in
the small type, it says how many of the passages you have decided, as in "64 of 207 passages", with
"complete" after them once you mark the phase complete (see Complete). PETs opens the participant's PETs.
Under it, it says the Current board's name (see The Current board), as in "Mornings apart". Then it says
"PETs complete" once you mark that phase, and "in GETs" once the GETs file holds the participant. The app
reads the first two from the themes file. If a participant has boards but none of them is Current, it says
"No Current board" there. If they have no board at all, it says "No PETs yet". While Excel has the workbook
open, the row has the tag "open in Excel" and the Statements half is disabled. PETs still opens, because
that screen only reads the workbook. A participant with no annotated workbook reads "Not started" and has
one button, Start experiential statements. It opens the create card on the newest raw source. If there is
none, it opens the make a workbook card on the newest transcript in another shape (both below).

A participant's workbook is the one that their progress and PETs files name (13 November 2026). Sometimes
that workbook is gone from their folder, and copies that a sync app named stand in its place, such as `P2 Ada
- EN & ES 2.xlsx` and `P2 Ada - EN & ES 3.xlsx` as iCloud Drive names them, or another workbook does. Then
the row says so in place of its two halves. It names the missing workbook and the files it found. Idiograph
opens and writes none of them, and neither does an agent. It never guesses which copy is the right one.
Give the right file its own name back in the Finder, and the row is as it was. Every save writes into the
workbook itself and keeps the same file. So iCloud Drive sees a change to the file it knows and keeps no
separate copy.

A participant's workbook is their annotated one. If there are two in their folder, it is the one opened
last, or else the newest. The three dots after the name open a small menu. It holds Edit participant
profile and then Show files (see A participant's picture, label and pen portrait, which is also where Rename
lives). Show files lists every file of the participant under the row: the annotated workbooks, the raw
sources and the transcripts. Each is a row with its tag that does what it always did. The item then reads
Hide files, and it folds the list away. An annotated workbook's row opens the participant and has PETs
beside it. Its sheets and marks are in the small type: "Initial, 2d · Statements complete" once you mark
the statements, "PETs complete" once you mark the PETs, and "Participant complete" in their place once you
mark both. The date is in the tooltip, as in "Experiential statements marked complete, 3 Oct 2026" or "PETs
marked complete, 4 Oct 2026, on Board 3". Participant complete shows both. The Current board follows,
"Current: Mornings apart", with "The Current board is the one you are going with" in its tooltip. A raw
source's row is marked "create annotated workbook" and a transcript's "make a workbook". Each is in the
soft ink on its own border. Until 17 October, later, they stood in the crux orange.

**A participant's picture, label and pen portrait (11 November 2026, pbiobuild, layout A).** Each participant
in every project, IPA and thematic analysis alike, has a picture, a label of a few words and a pen portrait.
The pen portrait is a short paragraph to remind you who they were. These sit beside the number and
pseudonym that their folder gives them. Idiograph never keeps the real name here. A row shows the picture
before the name. It is one of the app's drawn portraits or your own file. If there is none, it shows the
participant's initial in their colour. The label is under the name, and the pen portrait's first two lines
run across the row under them. The tooltip shows the whole pen portrait. To edit them, double-click the
name, the label or the pen portrait, or choose Edit participant profile, first in the dots. The fields open
across the row. First comes the picture with Change picture..., Choose from the set and Remove. Then comes
the participant, greyed, with Rename... after it. Rename... shows on a participant in a folder of their own,
never in the demo, and opens the Rename card below. Then come Label and Pen portrait, each kept as you leave
it, and Done at the foot. Choose from the set opens the drawn portraits under the fields, with a tab for
each set. The set of the current picture opens first, and the others are a click or an arrow key away. A
row holds as many as the window holds. In a narrow window you scroll to the rest, and a half row shows that
there are more. Since 12 November (peeps and picsets) there are two sets. Both are in black and white, and
both are in the app, so nothing is fetched. Sketches has eighty heads and shoulders from Pablo Stanley's
Open Peeps drawings. Line drawings has forty by Zoish (Notionists). Each set has a range of ages, hair,
headscarves and turbans, beards and glasses. A picture chosen from the 24 before shows as its nearest Open
Peep until you choose another. Your own picture is cut square, made small and kept in the project folder's
`pictures/`. The one it replaces is moved to that folder's `_Archive` and never deleted. A label is up to
60 characters and a pen portrait up to 800. Line breaks in a pen portrait become spaces. If a label or pen
portrait holds a name from the project's list of names to replace, the app refuses it in one line, "The pen
portrait holds entry 3 from the project's list of names to replace, so nothing was changed.", and keeps
nothing. The demo's three participants have theirs, and you cannot change them. The participant picker on
the statements screen and the switcher on PETs and LPETs list everyone with their picture, label and two
lines of the pen portrait. The bar over the statements screen, PETs, LPETs and a thematic analysis project's
Coding shows the picture before the name. It says the name with its number, as the rows do, "P1 Wren", and
the label after it. In a narrow window the label gives way first. On GETs and LGETs the Participants panel
shows each participant's picture beside the name and the label under it, with the pen portrait in its
tooltip. Trajectories shows the same picture and label, and changes made in its editor show on every
screen. Each change is a record in the project's History, and an agent sets them with `participant set`.
Export as REFI-QDA gives each participant's pen portrait as their case's description. No picture goes into
any export.

**The label and the pen portrait in the exports (11 November 2026, pbioexport).** Pen portrait is the last
tick under Export on PETs and on the print view. It puts the participant's label, in italics, and their pen
portrait under their name at the head of the table of PETs, in the print view, the PDF and the Word
document. Participants table is the last tick on the GETs Export card. It puts a first page before the GET
table, the audit trail or all of it in one document. That page is a table of each participant in order,
with their number, pseudonym, label and pen portrait, as a write-up shows them. The part after it starts
on the next page under its heading. In all of it in one document, the table follows the contents. A
thematic analysis project's theme table has it too, in its PDF and its Word document. Both ticks are off on
a new install, and the app keeps them as you leave them. A participant with no label or pen portrait gets
nothing under their name, and a row with empty cells in the table. The number is the one the folder gives,
such as P2. Where the folder has none, it is the participant's place in the order. Participants table is not
offered for the canvas, one GET's trail or a participant's LPETs. No picture goes into any export, because a
photograph of a real participant identifies them.

**Demographics (12 November 2026, demobuild).** Each project sets its own categories that describe a
participant. You find them in Project settings under Demographics, last in the sheet. A category is either a
List, where each participant has one of its values (Gender, Age range), or Free words, up to 12 each
(Nationality, Occupation). Add category offers a starting set, which you can take or leave: Gender (Female,
Male, Non-binary), Age range (18 to 29, 30 to 39, 40 to 49, 50 to 59, 60 to 69, 70 and over, bands that
never overlap), Nationality, First language and Occupation. New category... makes one of your own. Each
value has its own colour from the participants' palette, so Female shows in the same colour on every row.
Click a value to see its colours, Rename..., Move to and Remove. A list's + Add adds one more value. A
category's dots hold Rename..., List or Free words and Remove. Drag a category to its place by its grip, or
move it one place with Alt and an arrow. You drag a value along its category in the same way. When you
rename a value, it is renamed on everyone who has it. When you remove a value or a category, a card first
says who had what. Then the app copies the project file to `_Archive`, takes the value or category off
everyone who had it, and keeps what went in the project's History. Move to puts a value, and everyone who
has it, into another category. If that category has a value with the same words, the two join. When you
turn a list into free words, every value is kept. When you turn free words into a list, the words in use
become its values.

You set a participant's values in their fields across their row (Edit participant profile). After the pen
portrait there is a line for each category. For a list you click a value. The chosen one is filled in its
colour and the rest are dashed, and clicking it again clears it. For free words you type into Add, and
Enter or a comma ends each one. The cross takes one away. Everyone's values, Edit the table, opens a card
with every participant's values at once, a row for each participant and a column for each category, so you
can fill in a dozen participants together. If a category has Show as a pill ticked, its values show as
pills on the project page's rows, on one line under the label. When the line runs out, the last pill gives
way to "+2", and its tooltip names them. The pills also show in the pickers after the label, under the name
in the GETs' Participants panel, and on Trajectories. The bars over a participant's screens name them in
their tooltips.

Trajectories used to have its own tags. The first time the project page listed the project, those tags
became each participant's values in a Tags category of free words. Each word kept the colour Trajectories
gave it, and both files were copied to `_Archive` first. Trajectories now shows the pills of the shown
categories in place of its tags, and its editor's Tags are the Tags category's. Sort them with Move to, for
example Female into Gender and 40 to 49 into Age range.

On the GETs Export card, under Participants table, there are two choices. One row each puts a column for
each ticked category after the label, with the pen portrait on a line of its own under each row. In sum
keeps the table as it was and adds a short table that counts each category's values, "Female (2), Male
(1)", as a write-up reports a sample. In sum is a thematic analysis project's first choice. A tick for each
category says which ones go. The ones shown as pills are ticked until you change one, and the project keeps
both settings. On PETs, Pen portrait puts the same categories' words on a line under the label. Export as
REFI-QDA carries each category as a variable and each participant's values on their case. When you bring in
a REFI-QDA project, the import card's Demographics tick turns its variables into categories. A value on a
case goes to the participant the case becomes, and a value on a document goes to the participant whose
interview it is. Demographics can identify someone in a small study. So nothing leaves the project unless
you tick it. In sum gives the counts without a row that ties a pseudonym to an age. The starting set offers
age bands and never an age. The app refuses a value that holds a name from the project's list of names to
replace.

**Rename (16 October).** A pseudonym you gave once sometimes changes. Rename... gives the participant a new
one (a tester's ask, Adam's word). It is in a participant's fields (Edit participant profile in the dots),
after the greyed name. Its card holds the name now, a field for the new name and one unticked row, Rename
the folder too. Under them is one line (12 November 2026, Adam: the long list was more frightening than it
needed to be): "Ada's name changes on every passage, in the workbook and in Source." If the participant has
no transcript in Source, it says "in the workbook." alone. Then comes "A copy of each file is kept first."
and a folded Details. Details stays closed until you open it. It lists the participant's name on the
passages of each sheet it stands on, as in "Ada's name on 54 passages of the "Initial" sheet and 30 of the
"2d" sheet". It names the workbook after that only where two workbooks hold the name. Then come "The PETs
boards and GETs show the new name", "Their place in the order, picture, label and pen portrait stay with
them" and, while the folder keeps its name, "The folder keeps its name, P1 - Ada". Renaming never moves a
participant in the project's order. The app draws the list before it writes anything, and again as you
type the name and tick the row. The command line's `--dry-run` and the MCP server still give the full list,
including the folder's moves when the folder is ticked. The copies are kept where the app's backups go: the
participant's `_Archive/` for their own files, and the project's for the GETs file and the project file.
Each is named `(pre-rename <date-time>)`. Rename, the filled button, changes them all. Cancel and Esc change
nothing. The card's kicker, Participant, stands in the soft ink, as every card's kicker does since 17
October, later. Before, it stood in the crux orange. design.md keeps that orange for a crux, a quote and the
filled button, so Rename alone is orange and its refusal is amber. Afterwards the renamed row stands in the
middle of the window, clear of the line at the foot that says the rename, "P1 Ada is now P1 Bea.". This
works on a phone too. The card refuses Rename in one line, with nothing changed, in these cases: when no
name is typed, when it is the name the participant has, when it is not one capitalised word (as New
project's pseudonyms are), when it is the project's interviewer's name (Project settings) or another
participant's name in the project, when Excel has a workbook of the participant open ("P1 Ada - EN &
ES.xlsx is open in Excel. Close it in Excel first, then try again."), when a folder or a file the move lands
on is there already, and when a file cannot be written. In that last case it puts back everything it wrote
before. While a refusal shows, the list of what will change goes away, because nothing will change. Both
come back as you type the name again (17 October). The line "A copy of each file is kept first." goes and
comes with them, because a refused rename keeps no copy (17 October, later). Rename stays ready to press, as
a dialog's button does. So after you close the workbook in Excel, a second press renames. Rename never
touches the interviewer's passages and name, the backups in `_Archive/`, or the transcripts in `Source/` as
they were dropped. It leaves exports already written as they are. Afterwards the row, the PETs and GETs
boards, the bar of Experiential statements, the participant picker and Add transcripts show the new name
with no restart. A trim's or an assignment's copy is found in the folder it moved to. If the folder keeps
its name, the project's file keeps the new name against the folder's, in `names`, which every screen reads.
The files keep their names, as Files shows them. The demo's names are fixed, so its rows have no Rename. A
workbook sitting in the root itself has none either.

Since 11 November (renamefix) Rename carries the participant through every file of the project that names
them. The list adds "The project's LGETs" when the LGETs hold the participant, "The Trajectories board" when
they are on it, and "The project's list of names to replace" when it has an entry for them or writes their
name. In that case it writes the new name. Everything they had on the LGETs and on Trajectories stays
theirs: their LPETs' cards and where each stands, their trajectory and their place in it, their label,
tags, note and picture, and the LPETs hidden there. Their PETs boards at every timepoint take the new name.
When the folder row is ticked, a workbook that takes the new name keeps its LPETs and its PETs boards at
every timepoint. Their own picture on Trajectories, named after them, takes the new name too: "Their picture
on the Trajectories board takes the new name". Since 11 November (pbiobuild) their picture, label and pen
portrait go with them, "Their picture, label and pen portrait in the project". When the row is ticked,
their own picture's file takes the new name too, "Their picture in the project's pictures folder takes the
new name". The list of names to replace keeps no copy in `_Archive/`, because it holds real names and the
app copies it nowhere. Rename is also refused when a file it would change is there and cannot be read,
"idiograph-trajectories.json could not be read, so nothing was changed.". It is refused as well when the
folder would move while Working together is on, because the team knows each participant by their folder.

The list finds each participant's annotated workbook and its raw source, and nothing else. That is a
workbook under a project's root with a Name, a Timestamp and a Transcript column. The app finds columns by
their headers, so another study's CSV layout (`Speaker | Time | Experiential statements | Text |
Exploratory notes`) can be added later without touching the rest. The list leaves out anything under
`_Archive` or `Working`, anything deeper than a participant's own `Source/`, and every backup copy wherever
it sits. A backup is a workbook whose name ends in a bracketed note starting `pre-` or `complete`, such as
`(pre-trim)`. That covers the app's own copies and the coordinator's.

**Your order.** The rows stand in the order you are working through them. The more settled ones are at the
top and the ones still to begin are further down. You set the order by dragging a row by the handle at its
left, six small dots. The row takes its place among the others as it passes each one's middle. The handle
takes the focus as any button does. Alt + Up and Alt + Down move its row one place, which is the drag for
the keyboard. The handle keeps the focus, and a screen reader is told the row's new place. Either way the
app saves the order at once in the project's file as `order`, a list of the participants' labels, and keeps
every other key of the file. A participant the list does not name, such as a participant's folder that is
new since, goes after the ones it names, in participant order. P2 comes before P10, then a folder with no
P-number in its name, then a workbook sitting in the root itself. A label in `order` with no participant
behind it is passed over. A project with no `order` shows participant order. The demo's rows have no
handle, and their order, Juno, Rowan, Mabel, is fixed.

The counts come from the workbook, read once, and the progress file beside it. The statements' mark comes
from the progress file and the PETs' mark from the themes file. The server keeps each until its file
changes, so the screen appears at once. A file that cannot be read shows no mark. Home is fetched afresh
every time it shows, including through the back arrow. The back arrow saves a field you typed into and did
not save, as any move does. Showing Home reads the themes file's head, where the Current board's mark sits,
and writes nothing. A page in front of a server that has not been restarted draws one section of its root.
It has a row for each participant from the old rows, without the counts, and every participant still
opens.

A raw source workbook has three columns. It is marked "create annotated workbook" under Files, and Start
takes it on a participant not started. It opens the create card. The card builds `P<n> <Pseudonym> - EN &
ES.xlsx` in the participant's folder with the headers, widths and formatting of the reference workbook, a
finished case. That is the format the app writes and exports in. The card never writes into a `Source/`
folder. It names the source by its participant and its file, or by the file alone where the file's name
already holds the participant's, as in "Ivy - interview.xlsx" where it read "Ivy · Ivy - interview.xlsx"
(17 October, later). The make a workbook card does the same. The card asks only for the new file's name.
The app refuses a workbook that Excel has open, with a line saying to close it in Excel first.

A transcript in another shape is offered from the participant's own `Source/` with "make a workbook", under
Files and through Start on a participant with no raw source. It can be a VTT or SRT file, plain text, a
Word file, or a CSV or Excel file whose columns go by other names. Its card is in the create card's style.
It shows the first eight passages as the app reads them, with the speaker, the timecode and the words. It
shows the speakers found, with the interviewer chosen from them. The app presets the interviewer to the
interviewer's name in Project settings when a speaker's name or its first word matches. Otherwise it
presets the speaker with the most question marks. You can always change it. A Word table, a CSV or an Excel
file shows every column it has, each with a chooser at its head: Speaker, Time, Transcript, Exploratory
notes, Experiential statements, Quote or Leave out. The app guesses each from the column's heading, or from
what the column holds when there is no heading. A change reads the file again. A column headed Notes,
Comments, Thoughts, Memo, Reflections, Reflexive notes or Analyst notes is guessed as Exploratory notes. One
column takes each role, and one must be Transcript. If two columns have the same role, the card says so in
one line and Make waits. The preview below then shows the first eight passages as they will land. It has a
column for each role chosen, in the order Speaker, Time, Transcript, Exploratory notes, Experiential
statements. The notes stand beside the words they are about, so a glance tells you whether the columns were
found right. On a phone the preview scrolls sideways inside its own box. Under it the card counts the
passages, says how many come with notes, and names any column left out. Add transcripts' rows read a
dropped file in the same way. Make writes the columns beside the file as `<file name>.xlsx`, or `<file
name> (converted).xlsx` for an Excel file. It never writes over a file already there. It puts the
interviewer's passages under the interviewer's name from Project settings, so they read as context. When
the names differ, the card says so under the choice. Make then goes straight on to the create card above.
The file is not offered again once its workbook stands beside it. In a VTT or SRT file a `<v Name>` tag
names a speaker, as Teams writes it, or a leading `Name:` does, as Zoom writes it. Cues of one speaker in a
row make one passage at the first cue's time. If a file names nobody, each cue stays a row under Speaker.
In plain text a line that opens with `Name:` starts a passage, and the lines after it carry it on. A time at
its head, `[00:01:23]`, `00:01:23` or `1:23`, is the passage's time. Without times the player stays quiet,
as it does for any workbook without them. The app reads a file as UTF-8, with or without a byte order mark,
or else as Windows-1252. If it can make nothing of a file, it says so in one line and writes nothing. The
app reads a `.docx` one paragraph to a line, as it reads plain text. The exception is a table of transcript
and exploratory notes, laid out as the IPA book does. Then each row is a passage, and the notes beside it
come in as that passage's exploratory notes, one line of the cell to a note, just as if you typed them on
the Experiential statements screen. Notes on the interviewer's passages go to your Interviewer notes. A
heading row finds the columns, such as Speaker, Time, Transcript, Notes, Exploratory notes, Comments and
Experiential statements, in any order. With no heading, the column with the speakers' words is the
transcript, a column of times is the time, a column of a few names is the speaker, and the fullest of the
rest is the notes. If there is a third column with no heading that the card can place, it is left out until
you choose a role for it. Words outside the table are left out, and the card says so. A row that opens with
`Name:` names its speaker. A row without one carries on the speaker before it. A time at a row's head is
its time. A row is never split. A row with notes but no words adds them to the passage before it. A
spreadsheet's notes and statements columns come in the same way, by their headings or by your choice.

**Quotes from a column (9 November 2026).** A column headed Quote, Quotes or Key quotes is guessed as
Quote, and you can set any column to it. Its cell holds one quote to a line. Each line goes with the
statement on the same line of that row's statements cell: the first quote with the first statement, the
second with the second. If a cell has more quote lines than statements, the app keeps the extra ones, and
the passage waits under Quotes for you to pair them. If a cell has fewer, the last statements have no
quote. A quote that is a run of words in the passage is marked there, as any quote is. A quote that is not
word for word is still kept as its statement's quote, but it is not marked in the words, so nothing is
lost. Under the preview the card says how many passages come with quotes. Add transcripts reads an Excel
file of two sheets or more at its first sheet with anything in it. A Sheet chooser on its row reads
another.

**Work done elsewhere (20 October).** A researcher may bring an old project, or want only PETs and GETs,
with the transcript marked up to any degree. A statements column puts each statement on its passage, with
several in a cell one to a line. So the participant opens ready for PETs, with or without notes. Under the
preview the card lists every speaker, each with a chooser: Interviewer, Participant or Other speaker. The
app guesses the interviewer as before and makes every other speaker a Participant, and you can change them.
One transcript is always one participant. Two people interviewed together, such as a couple, are one
participant with one set of PETs, and each passage is under its speaker's name. Another speaker, such as
someone heard off camera, stays in the participant, and a column headed Other speaker marks their turns.
Moving from passage to passage passes them, as it passes the interviewer's. A click opens one if you want
to give it a note or a statement. If there are two interviewers, or no participant, the card says so in one
line and Make waits. Beside the column choosers, Time codes shows the format the app found the Time
column's times in, "As found, 1:02:03". A chooser sets it by hand, and each format is named by an example:
1:02:03, 02:03, 1:02:03.5, 62.5 seconds, and "1:02:03:12, frames" with Frames a second beside it. Frames a
second is 25 unless you change it. The app reads times with one or two figures for the hours or the
minutes, in brackets or not, with a fraction after a full stop or a comma as SRT and VTT write them, and
seconds as a number. A format set by hand reads only that format, though 1:02:03 and 1:02:03.5 read each
other. The preview shows each passage's time as it will land, and never breaks a time across two lines. If
the format cannot read a time, the preview shows it struck through, and a line under the preview names it:
"The time 0:0x:12 on passage 2 cannot be read as 1:02:03, so it comes in without a time." On a phone the
preview's columns stack. Each passage's name and time stand over its words, and its notes and statements
under them, each with its heading. Recording, at the foot, offers the recordings beside the file and in the
participant's Source folder. On a Mac, Choose picks one from elsewhere, and None takes none. Make copies
the chosen recording into the participant's folder, where the player finds the sheet's recording, in
`Source/Transcript/Source/`. It names the copy by the participant's pseudonym and timepoint, `Wren T2.m4a`,
or `Wren.m4a` in a project of one timepoint. It never uses the file's own name, which may hold a real name
(9 November 2026). A REFI-QDA project's recordings are named the same way. Offset in seconds, plus or
minus, is 0 unless you change it. Use it for a recording that is a little different from the one the times
were taken on. The time codes stay as they are, and playback moves by the offset, later for plus and
earlier for minus. The app keeps the offset beside the recording as `offset.json`, so it holds across a
restart. Under the player, the Offset button stands beside the recording's name. Once an offset is set, it
reads "Offset +1.5 s" or "Offset −1.5 s". It opens a card to change it, with Seconds, plus or minus, and
Save. On a phone the recording's name and the Offset button take a line of their own under the player's
bar. The name shows whole where it fits and is cut at its end where it does not, and the pointer shows the
whole name. The PETs screen's player and the GETs trail use the offset too. `template/Transcript
template.xlsx`, beside the app, has the three columns with three invented rows, for a transcript you type
or paste in by hand.

**The marks.** Idiograph's mark is an orange dot between two square brackets. The dot is the participant's
experience, held where the researcher's hand enters a quotation. The wordmark at the head of Home is that
mark with the name beside it in the mark's square stroke. Its colour is a deep blue, about 7 to 1 against
the page in both appearances (15 October, later). The mark stands on every title bar of the app between the
arrow back and the project's name, 7 pixels from the name at every width. Where the bar runs out of room,
the name after it is cut short with an ellipsis. Experiential statements, PETs and GETs show Idiograph's
mark. In Settings the chosen category's rule is in the app's colour. In a title bar and in Settings the mark
is drawn again for its small size, 18 or 16 pixels, with every line on a whole pixel, so it reads as sharp
as the words beside it. The app uses its colour only for its mark and its Settings rule, never for a
decision. The browser tab shows the mark on its paper tile, dark when the system is dark. The Mac and
Windows icons are the same mark, drawn for 16 pixels at the smallest sizes so it stays crisp.

**The bars since 26 October 2026.** Adam chose option C of the bars' drawings, and every screen's head now
reads the same way. At the top left stands the app's lockup, its mark and its name, and clicking it goes
Home. The Preview Edition stamp stays on Home and in About. After the lockup come the stages as tabs:
Experiential statements, PETs and GETs, or in a project with timepoints ES, PETs, LPETs, LGETs and
Trajectories. Every tab looks the same. At the right stand the screen's own tools, such as Export on PETs
and View and Guidance on Experiential statements, then a rule, then Search, Feedback and Settings, with
Settings at the far right. Each tool shows its word where the bar has room. Where the bar runs short, the
words go first, and then Experiential statements becomes ES. The back arrow has gone. Under the bar, the
research question's band starts with where you are. It shows the project's name. On a participant's stages
it shows the participant's chooser, and on a timepoint's PETs or statements the timepoint's chooser. The
name opens the project's menu, and the choosers open their menus as the one in the tab did. On every stage,
LPETs included, the chooser shows the participant's name alone, such as Wren for P1 - Wren. On PETs, LPETs,
GETs, LGETs and a thematic analysis project's Themes, the toolbar under the band starts with the board and
Auto-saved, Canvas and Table and Export. Then come the tools, and it ends with Undo and Redo. This holds
whether the tools are docked there or floating on the canvas (16 November 2026, the toolbar standard: the
tab's own items and Export at the left, Undo and Redo at the right end on every tab). The two sidebars open
from slim tabs on the canvas's edges. Each tab shows its icon over its name, written up the tab, as
JetBrains' tool windows and Visual Studio's auto-hide panels have them. Unplaced is at the left edge, with
the count of what it holds, which is 0 once everything is on the board. Inspector is at the right edge. While
a sidebar is open, its tab hangs on the sidebar's edge. Every board's left sidebar has the one name,
Unplaced (Adam, 16 November 2026). It holds what is not on the board yet, which you drag onto it, grouped by
participant or by timepoint as before, with Set aside at its foot. On PETs it holds the statements waiting.
On GETs, LPETs and LGETs it holds each participant's or timepoint's PETs (LPETs on LGETs) that have no card
on the board. A PET leaves the list once its card is placed or set aside. On a thematic analysis project's
Themes it holds the codes in no theme. Its keys and tooltips are as they were. Canvas and Table stand on the
toolbar directly after Auto-saved (Adam, 26 October: it is not a status bar thing). They stay there in the
Table view too, so the way back to the canvas is always in reach, and T still switches. The status bar
holds the counts and its tools alone. Where it runs short, as at 1280 with the sidebar open and every count
ticked, the tools' words give way first. Fit all, Minimap, Quotes and Shortcuts then stand as icons with
their words in their tooltips. So the counts always say the whole sentence there, "18 ES: 17 in PETs, 0
stacked, 0 set aside, 1 unplaced | 3 PETs" on the demo's Mabel (Adam, 26 October). Since the same day
(Adam's option B) Align and Spread stand under the toolbar's three dots, after Auto-arrange. The dots open a
menu of two sections. Align has Left, Centre and Right, Top, Middle and Bottom. Spread has Across and Down.
Each item has its icon and its word and does to the selection what its button did. The items are faint, as
the buttons were, when nothing or one card is selected, and Spread's two are faint until three are. So at
1280 Sticky note, Group, Auto-arrange, Undo and Redo keep their words. Where the toolbar runs short, Select
all loses its word first. Then every tool shows its icon alone, with its word in its tooltip. On
Experiential statements the sheet moved to the status bar before the place, and the round, the clock and
Mark complete moved after the counts. Trajectories' bar gained Search and Feedback. Keyboard shortcuts are
unchanged. Since the same day the app's window is never narrower than 720 pixels (Adam, 26 October 2026:
360 is dropped). At 720 Idiograph's bar keeps its one row, with the tabs in their short names beside the
lockup and the tools as icons. The toolbar stands on two lines. The sidebars' buttons, the board,
Auto-saved and Canvas and Table are on the first line, over the tools.

**The band since 6 November 2026.** Adam chose option D, after a tester found that the lockup and the
path's Home did the same thing. On every project screen the lockup at the bar's left is the way Home, and
the band under the bar has no Home. The band reads on one row. First comes the project's name with a small
chevron. Then comes the participant's chooser, followed in a project with timepoints by the timepoint's
chooser. Then come the rule, Research question and the question. On the screens that are not one
participant's, GETs, LGETs, Trajectories and the Code list, it reads the project's name and its chevron,
then the question. The project's name looks and works as the participant's chooser does. A press opens a
menu under it, the arrow keys move through the menu, and Esc shuts it. The name is no longer a way to the
project's page, because you can do everything that page does from inside the project. A long name stops at
22em with an ellipsis. The chevron is still there, and the tooltip shows the whole name. Its menu is the
one the project's card has on Home, with the same items in the same words: Share a copy…, Export as
REFI-QDA…, Show in Finder (Show in Explorer on Windows, Show in Files on Linux, and only in Idiograph's own
window), Project settings, Project history and Remove from Idiograph…. A demo's menu has Project settings
alone, as its card does. Remove from Idiograph asks first, in the same card as on Home. Then it leaves the
screen as Home does, saving what you typed, and takes the project off Idiograph's list. The project's folder
and files stay as they are, unless you ticked the card's tick to move the folder to the Bin. It ends on
Home without the project.

**The tabs keep their place.** The tab in front is in bold. Every tab is always as wide as its name in
bold, so switching stage moves none of them (6 November 2026). The boards', Trajectories' and the code
list's bars start their tabs where the statements screen's bar does.

**Auto-saved under the board's name.** On PETs, LPETs, GETs and LGETs the save state stands under the
board's name in smaller words. So the pair takes no more width than the name, and Canvas and Table stand
closer (6 November 2026).

**The statements screen's toolbar.** Under the band of Experiential statements runs a toolbar in line with
the boards' toolbar (6 November 2026). Its grip is at the left. Then come Find and replace, which opens the
Find and replace card as `Cmd + Shift + F` does, and Previous passage and Next passage, as `Cmd + J` and
`Cmd + K`. At its right end are Undo and Redo, the screen's own, as `Cmd + Z` and `Shift + Cmd + Z`. While
a field's typing is newer, they are the field's own undo. Each is an icon and its word. The words give way
where the row runs short, and the tooltip names the key. If you drag the toolbar by its grip, it floats
over the columns as the boards' toolbar floats over the canvas. It becomes a column on the card's paper,
and the row under the band goes. If you drag it back under the band, it docks again, and a dashed slot
shows where. This computer keeps where it stands. The small Replace in the transcript link in Search's card
stays.

**One title bar.** Every bar in the app works the same way (12 October). Its parts are in one order on
every screen (16 October, after a tester found Appearance on some screens and not others). Each tool on a
bar is its icon and its word. On Experiential statements the tools are View, Guidance, Search, Shortcuts,
Feedback and Settings. On GETs Participants is at the left end of the bar. Then come Sticky note, Group,
Undo, Export (on PETs alone), Search, Shortcuts, Feedback and Settings, and Inspector is at the right end on
PETs and GETs. Search, Feedback and Settings are at the head of Home. Each tool shows its word where the bar
has the room, from 761 pixels of window. Where the bar runs short, the icons stand alone, and each is named
on hover (since 26 October. Before, the words showed from 1280 pixels). From the keyboard, every tool on a
bar, its tabs and its switchers take the app's one focus ring, the orange wash every button takes. So does
every tick and every one-line field. Before, a tool given the focus back from its menu, such as View after
Esc, and a tick drew the browser's own blue ring, and a field such as Rename's New name showed none (17
October, later). A card's close in its corner takes the same ring. Before, the guidance's close drew the
blue one (18 October). Since 8 November every card, including Settings and Shortcuts, keeps the keyboard
inside it while it is open. If you open it from the keyboard, its first field takes the focus, or else
Done does. `Tab` and `Shift + Tab` go round inside it, and when it closes the focus goes back to what
opened it. Since 12 November a click outside a card closes it as `Esc` does. A card with words you have
typed and not yet saved, or one still at work, stays open. A screen reader hears each card as a dialog
named by its title. View, Export, the boards and the participants on PETs, and a participant's menu on a
project's page, take the arrow keys. If you open one from the keyboard, the first item has the focus. `Up`
and `Down` move, `Home` and `End` go to the first and the last, `Enter` chooses and `Esc` closes back to the
button. `Tab` now leaves a participant's handle on a project's page, where before it stayed put, and `Alt`
and an arrow still move the row. On Coding, `Tab` from the notes goes on to each extract's Add a code. A
screen reader says the line at the foot and the statements screen's Saved (on Linux the app's window says
the line at the foot to Orca itself). Each screen has a heading for a screen reader. On Linux, Orca 46 keeps
its one-letter navigation keys while you write in a field, so it takes most letters as its own. Press `Orca
+ Z` to turn those keys off while you write, and again to turn them back on. With Orca on, a Tab to the
statement's quote or to Columns no longer stops the window (9 November 2026). The app's own words use
straight quotation marks and apostrophes throughout, including the "Initial" sheet. A participant's words
and the printed quotes keep their own (17 October, later). The lockup stands at the left of every bar and
goes Home. Since 26 October it replaces the way back's arrow. Idiograph's tabs on its bar name every screen
of Idiograph (see Idiograph's tabs). The tools keep one order on every bar. The screen's own tools come
first, the ones only that screen has. Then come the ones that write or send, then the rest. Last come the
tools every bar ends with: Search where the screen has one, Shortcuts where it has keys, Feedback and
Settings. Search took Find's place on 17 October and came to Home on 18 October (see Search). A sidebar's
button stands at its own side, over the sidebar it opens. Participants is at the left end of the GETs bar,
and Inspector is at the right end of the PETs and GETs bars. Each is the standard panel icon with its own
side filled. Every button with a key names the key in its tooltip, as in "Group (G)" and "Search (Cmd +
F)", with Ctrl in place of Cmd on Windows and Linux. The shortcuts card stays. Since 17 October every key on
the statements screen is named the same way, in its hints, the quote's empty field, its lines at the foot
and its shortcuts card. It says Cmd on a Mac and Ctrl elsewhere, Option or Alt, and Home and End for a
line's ends off a Mac. So "Ctrl + Enter saves" never stands beside "Hold Cmd", and the card names one key
where it said "Cmd / Ctrl". Every key on a button stands in the faint ink, and a key beside a decision's
word stands in the word's own colour. Until then each stood at a little over half its button's word and
read under 4.5 to 1 (17 October, later). Since the same day the time on Back to where I was also stands in
the faint ink. Before, it stood in the crux orange, which means only a crux, a quote and the filled button.
The `?` of Shortcuts stands in the icons' 15 pixel box at the weight of their lines on every bar (17
October). Before, at the bar's own small size, its thin strokes read fainter than the icons beside it. Appearance,
the light, dark or system choice, left every bar for Settings, General the same day (see Light, dark or the
system). To make room for the words on Experiential statements, the line to today's target leaves its bar
below 1440 pixels. Below 1280 pixels its first tab, Experiential statements, reads ES (see Idiograph's
tabs). At 1280 pixels a name of 30 letters stays whole on every bar, except where a bar holds the most:
Experiential statements marked complete with passages still undecided. There the name ends in an ellipsis
and shows whole on hover.

**Keys in capitals (17 October, later).** Every letter key stands in its capital, as keyboards and the
Mac's and Windows' menus print it. This holds on every shortcuts card, in every tooltip, as in "Group (G)",
and in every line, as in "Select the words inside the passage first, then press Q.". Until then
Experiential statements and PETs wrote theirs in lowercase. You press the key as before, without Shift.
Since 18 October Experiential statements takes its letter keys with Caps Lock on too, as PETs always did.
Until then `Q` and the rest did nothing with Caps Lock on.

**Idiograph's tabs.** Each of Idiograph's three bars has a fixed tab for each stage, after Idiograph's mark
and the project's name. The tabs are Experiential statements, PETs and GETs, in the book's order: steps 2
to 5 for one participant, Step 6 for each participant in turn and Step 7 across the participants (Smith,
Flowers and Larkin, 2022, ch. 5). With two or more timepoints the bar is drawn for five tabs: Experiential
statements, PETs, LPETs, LGETs and Trajectories. A tab shows only once its screen exists. Since 21 October
all five do, and LGETs stands where GETs would. With five tabs below 1600 pixels, the first reads ES and
the tools show their icons alone, so each bar stays on one row at 1280. A tab is never closed or doubled.
File, New Window gives you two side by side. The tab in front stands in the page's paper on the bar's lower
edge. It holds the participant picker, the participant's name and a small chevron. The picker lists the
project's participants with the one in front ticked. Each opens on their statements, with Open in a new
window beside each. On PETs the picker lists them with Open beside this one and Open as table. GETs belongs
to the project and has no picker. In a project with two or more timepoints, the timepoint stands just
after the tabs.

A tab opens its screen for this participant. On Experiential statements it saves the passage in front
first, and on PETs and GETs it saves the canvas first. On a project's GETs opened from its page,
Experiential statements and PETs open the participant you opened last in that project. Their tooltips name
that participant, as in "PETs for Mabel". Until you have opened one, they open the first participant. On
LGETs they open that participant at the timepoint whose PETs you opened last. On GETs opened from a
participant's PETs they stay with that participant. Where the way back goes to the same screen, the tab is
the way back. So Experiential statements reached from PETs comes back on the passage you left, and PETs
reached from a statement's card comes back on the board as you left it. Otherwise the screen opens afresh,
and its way back returns to the one you left. Since 26 October there is no arrow on the bars. The lockup
goes Home, and Back returns to where you opened the screen from. `P` on Experiential statements opens PETs.

The tabs read at 15 pixels. Below 1280 pixels Experiential statements reads ES, with its whole name in its
tooltip. So the tabs fit 1280. Below 1440 pixels the tools show their icons alone, with their words in
their tooltips. At 760 pixels and below the bar stands on three rows. The lockup and the tools are on the
first. The tabs are on a row of their own, scrolling sideways under a fade when five stand there. The sheet
or the timepoint and the place, or the board, are on the third. The keyboard reaches every tab with Tab.
Left and Right move along them, and Home and End go to the first and last. Until 20 October the stages were
small steps of words after the participant's name. Before those came on 18 October, a tester had found the
way from statements to PETs to GETs too hard to see.

**Rounds.** Rounds are a pace of the author's own, not a step of IPA, so they are a setting. Work in
rounds is in the statements screen's View (it was in Settings until 17 November 2026). While it is ticked,
its transcript minutes per round and rounds a day stand under it as small numbers beside their labels.
Since 17 November 2026 (Adam's ruling, as for the nudges) the three are each project's own:
`work_in_rounds`, `round_minutes` and `daily_target` in its project file. A project made from then on
starts with Work in rounds off. If a project's file has none of them, the app reads each as the app's
settings held it for every project until then (`config.json`'s, which is off on a new install). So the
author's own projects keep what they had. Nothing is written to the file until View or an agent sets one.
A demo's rounds are off and fixed. An agent reads them with `project show` and sets them with `project set
--rounds on|off --round-minutes N --rounds-a-day N` (MCP's project_set, `work_in_rounds`, `round_minutes`
and `daily_target`), as View does. With Work in rounds off, nothing about rounds shows anywhere. There is no
round count or its short bar in the top bar, no round clock, no round markers across the transcript, no
line to today's target or streak, no round card in mid-sheet and no confetti for a round. The card still
comes at a sheet's end and at the participant's end, without round figures, target or streak (see Round
complete). The quiet control that marks the phase complete still comes once every passage is decided (see
Complete). The app still cuts the rounds. Each still closes with the server, quietly, as its last passage
is decided, so the daily tally is true on the day you tick the setting. With it ticked, everything below
holds as it did. The app cuts each sheet into rounds of transcript time, 10 minutes by default. It cuts at
passage boundaries, so no passage is split. A round never spans two sheets, so the last round of a sheet
can be short. Rounds belong to their sheet. Each sheet has its own set, numbered from 1, and the end of a
sheet is a natural place for a break, even in a participant with several sheets. Every round number on
screen is the sheet's. Underneath, each round keeps a number that is unique across the participant, sheet
by sheet. The progress file, the daily tally and `/api/round-complete` are keyed by it, so a progress file
written before this reads without change. The demo's Initial sheet has 22 transcript-minutes and 39
participant passages, and comes out as 3 rounds.

**Round markers.** With Work in rounds ticked, a thin rule runs across the transcript column before the
first row of every round on the sheet. Round 1 is at the top of the column. So the sheet shows where one
round ends and the next begins: above the line is round 3, below it round 4. At its left, in the margin's
small capitals, a label names the round by its number on the sheet, "Round 4". Its state stands under the
name where a passage has its timecode. A closed round reads done, with the small tick, and its rule is in
the faint rule colour. The round holding the passage in front of you reads now. Its words and its rule are
in the ink of the current passage's rule, which was orange until 17 October. A round not reached yet reads
to do, faint. Since 17 October, later, it is in the faint ink at full strength, as the interviewer's name
in the margin is, and is told apart by its lighter weight. Before, a fading took both under 4.5 to 1. A
closed round that still holds the current passage reads done. The states follow every move and every round
close in place, so the column is never redrawn for them and the sheet does not jump. A click on a marker
goes to the round's first undecided participant passage. When every passage in the round is decided, it
goes to the round's first participant passage. This works the way a click on a speaker's name goes to a
passage. The marker's tooltip says which, as in "Round 4, 12 passages, 30:02 to 39:55. Go to its first open
passage.". The passages counted are participant passages, and the times are those of the round's first and
last rows. A marker is never a passage. The keys never land on it, it is never the current passage and it
is never counted. Below 1000px the margin lies along the top of each passage, and the name, the state and
the rule sit on one line. A sheet with one round shows one marker. A page in front of a server that sends
no rounds shows none.

**The count.** Each move on that decides a passage makes the new place in the round flash over the middle
of the transcript column. Those moves are Next after a save, a save with nothing in it, Skip, and passing a
blank passage with `Cmd + K`, the arrow or a click further on. The flash reads "8 / 20" in the numeral face
and the ink. Until 17 October, later, it was in the crux orange. The numbers stand alone with no box
around them. They grow out of a blur as they fade in, keep growing a little, and grow on into a blur as
they fade out, 850ms in all. With Work in rounds off, the place is the passage's place on its sheet, as the
top bar has it, "8 / 120". It reads Halfway at the sheet's midpoint and Last one on its last passage. Only
the move that ends a sheet or the participant raises none. At the round's midpoint passage, the first place
at or past half its participant passages, it reads Halfway, and on its last passage Last one. In the same
instant the place in the top bar, "passage 8 of 20 in this round", brightens on its numeral, from the faint
ink up to the ink. Until 17 October, later, it ticked in the crux orange. This way the eye learns where the
number lives. It counts the passages of the round, never statements. A click back, `Cmd + J`, a marker's
click, the sheet switcher and undo raise nothing. Neither does the move that closes a round, because the
round card and the confetti have that moment. A new flash replaces one still showing. It never sits over
the fields and never takes the pointer or the focus. Under reduced motion nothing shows at all.

**Experiential statements (the statements screen).** The top bar names the part after the participant name.
It says Experiential statements in the place where the bar in PETs says PETs, then shows a thin rule and
the sheet. Since 21 October the speaker of the passage in front of you and its place (15 October) stand at
the left of the status bar under the player. Until then they stood in the top bar after the sheet (see The
status bar on the statements screen). With Work in rounds off, the place is the passage's place among the
sheet's participant passages, "Juno, passage 8 of 120". In a participant with more than one sheet, its
tooltip gives the participant figure too, "Juno, passage 8 of 120 on this sheet, 128 of 300 in the
participant". With Work in rounds ticked, it is the place in the round, "Juno, passage 8 of 20 in this
round", with the round's short bar, "round 2 of 4", the round clock and the line to today's target. Since
17 October the screen has the book's three columns (see The three columns): experiential statements, the
transcript and exploratory notes, side by side under their headings. Each of the participant's passages is
a row across the three. The speaker and the timecode hang in the left margin of every passage's words, and
the player is at the foot of the three. The passage being worked on has its statements as a card in its
row of the statements column, and its notes as the notes field in its row of the notes column. Until then
the fields stood in a panel at the right for that passage alone. The guidance slides in over the right of
the screen from Guidance on the bar (see Experiential statement guidance). Until 16 October it stood in a
column of its own. The passage being worked on is large and at full contrast. The rest of the sheet is
smaller and dimmed around it, unless the view draws every passage at one size. Every passage shows its
quotes marked in its words and, once decided, its bar at the edge of its words (see Quotes in the passage
and Done marks). The three columns keep the whole height of the screen and scroll as one. The card and its
row grow with the statements you write. Every move centres them again on the current passage, but never
so far that its speaker and time go out of sight. A passage taller than the column stands with its name
and time just under the column's faded head. That head is below the title bar and the research question at
every width, and the app measures their height as they stand. Before, at 360, the notes' field under the
words had taken the name and time up under the question (17 October). Scrolling the columns by hand moves
nothing else and leaves the cursor where it was. The interviewer's passages are context and never a stop.
If you scroll the passage out of sight, a "Back to where I was" button appears with its timecode on it. It
stands in a strip of its own at the foot of the columns. The columns give up that strip while the button
shows, so it never covers a line at any width (16 October). `Esc` does the same from anywhere on the page,
and leaves whatever is in the fields alone. The wheel takes the columns as far from the passage as you
like, either way. Over a long passage's card it scrolls the card and then the columns. A click on a
passage, `Cmd + J` and `Cmd + K` move at any time, and you can revisit any passage.

**The status bar on the statements screen (21 October, Adam's drawings).** A status bar runs along the
window's foot under the player, as the PETs and GETs boards have one. The player keeps its size above it.
At its left stands the place, "Juno, passage 7 of 39" (with Work in rounds ticked, the place in the round).
Then comes the participant's statements counted, "41 statements". The passage being worked on is counted
as its fields hold it. Since 30 October the count holds still as you move from passage to passage. Before,
it went up or down by the statements of the passage you left and the one you opened. It changes only when
you add, remove or empty a statement. A statement is counted as you type it, before it is saved. It counts
every statement in the workbook, including one on an interviewer's turn, as the PETs board's status bar and
the agents' `statements` count them. At its right stand Minimap, Quotes and Shortcuts, each an icon and its
word. Minimap shows or hides the map as `M` does. It is pressed in while the map shows, and it goes away
when the map is set to Off in View. Quotes is pressed in on a new install, and each statement's quote shows
in full. When you press it out, every quote's words are hidden, with no first line and no arrow. Only its
Quote label and chevron are left, so the statements stand clear on their own (Adam, 21 October: until then
Quotes off folded each quote to its first line). Each quote also folds and opens on its own, whatever Quotes
says (21 October, for long quotes set several to a statement). A set quote's Quote label has a small
chevron. It points down while the quote shows in full, and right while it is folded or hidden. A press on
the label folds or opens that quote alone. When you fold one alone with Quotes on, the quote keeps its
first line, ending in an ellipsis, and a press on that line opens it. When you open one alone with Quotes
off, it shows in full. A quote of several pieces folds to one line that holds them all. A press on Quotes
puts every quote back to what Quotes says. An empty quote is never folded or hidden, so its line and its
arrow stay in reach. The app keeps Quotes in the settings, so a reload or a restart keeps it. Shortcuts
opens the shortcuts as `?` does. The place and Shortcuts stood in the top bar until 21 October. On a phone,
360px wide, the place drops the speaker's name, "passage 7 of 39". The count and the recording's name
beside the player go, and Minimap, Quotes and Shortcuts keep their icons alone, each named in its tooltip.

**The three columns (17 October).** Smith, Flowers and Larkin (2022, *Interpretative Phenomenological
Analysis: Theory, Method and Research*, 2nd edn, Box 5.4, Step 3) lay the transcript out in three columns:
experiential statements, the transcript and exploratory notes. They type the notes "into a column that runs
alongside the transcript" (Chapter 5, step 2). A tester asked for the notes beside the transcript. So the
statements screen stands in those three columns, by Adam's decision of 17 October. Until then the
statements stood in a panel at the right for the passage in front of you alone, and the passages not in
front of you showed none. Each column has its heading over it, with a grip before its name. You choose the
order. On a new install it is the book's: statements, transcript, notes. You can set any of the six orders
by dragging a heading's grip to another place, and a bar in the ink marks where it goes. You can also use
`Alt` and the left or right arrow with a grip in focus. Back to the book's order, in the menu of Columns at
the right of the headings, puts the book's order back. Until 18 October that menu listed the six orders,
the book's first, and Settings did too (see Show, hide or stack the columns). Columns says its word alone at
every width, and its tooltip names the columns shown. Until 18 October it said the order beside its word,
but only where the last heading left it room, which happened at 800px alone. Where a heading's longest word
would not stand whole beside the word, as at 801px, Columns keeps its chevron alone. Its menu opens under
it at the right. Where the menu would leave a strip of the last column showing beside it, such as a sliver
of the notes field, it takes that column's whole width. The app keeps the order in `config.json` as
`statements_columns`. A settings file from before kept the notes right or left of the transcript or under
the statements. It reads as the order nearest the screen it drew: transcript, notes, statements for right,
notes, transcript, statements for left, and transcript, statements, notes for under. The old key leaves the
file on the next save. In every order the margin with the speaker, the timecode and the done bar stands at
the left of each passage's words, in the transcript's column wherever that column stands.

Each of the participant's passages shows its statements read-only in the statements column beside its
words. Each is numbered as in the card, in the reading face. A click on one goes to that passage with the
caret in that statement, the way a click on its quote's mark does. So the statements and the quotes marked
in the words keep the same numbers. A statement still to write shows its quote in the faint ink, so every
number keeps its place. The passage being worked on has its statements editable in its own cell, in a card
a size larger. Each pair has its number beside its statement field, with its word count and nudges under
it. Then comes its Quote label with Remove at its right, then its quote field (see Pairs). At the card's
foot are Add another, AI suggest while the AI features are on, and the one filled button (see The buttons).
The card is made for one statement as a rule, sometimes two and rarely three, with room for six or seven.
The card and its row grow with them, and it never becomes a box that scrolls on its own. While a card of
several pairs runs past the column's foot, the card's foot keeps to the column's foot, so Next stays in
reach as you write. The row takes no wash while the pointer is in the card. The foot then ends the card
there, with a hairline and the paper under it, so nothing of the card shows below Next. The fields above it
fade into it, so none is cut through its letters at its edge (18 October). A field grows with its words,
and an empty one grows with its prompt, so a prompt of two lines reads whole. The notes stand in their
column beside each passage. The current passage's notes are the notes field itself. It starts about five
lines tall and grows with its words as the card does, and it never becomes a box that scrolls on its own.
So a note longer than the passage beside it takes the room it needs, and the row grows with it. Until 18
October it started at two lines, and a long note felt cramped. It saves as it always has, with Next, `Cmd +
Enter` or any move, and `Tab` reaches it after the last quote. The other passages' notes are read-only, in
the faint ink with the field's own padding, so their words sit where the field's would. A click on them goes
to that passage with the caret in its notes. The interviewer's passages have neither statements nor notes.
An interviewer note on one stands in the notes column beside it (see Interviewer notes).

The three stand side by side down to 801px wide. Each column narrows to its own least width: the
statements 210 pixels, the transcript 300 and the notes 160. At 1280 the statements and the notes are about
320 pixels each and the transcript about 530, with its words about 420. At 801 the statements are at their
210, and the transcript and the notes share the rest. From 800px down to a phone's width the notes go under
each passage's words in the transcript's column. A hairline divides them, so a faint note never reads as
the speaker's words. Their heading goes with their column, and the statements keep a column of their own.
At 600px and below, on a phone or in a narrow window at Text size Large, each passage stacks: its name and
time, its words, then its statements and its notes in the columns' order. The headings go. The minimap
keeps its corner, and the guidance's sheet slides over the columns as before.

**The column edges (20 October).** On a wide screen the three columns used to stop growing at about 1,480
pixels and leave the rest of the window empty either side (a tester's letterbox at 2560). So now you can
drag every column edge, Adam's choice from a drawing: the outer edge of the first column and of the last,
and the edges between them. Since 6 November the two edges between columns show at rest. Each is a faint
rule down the columns with a small handle on it, a pill of two upright bars at the middle of the columns'
height. The handle stays in view as the passages scroll under it. Adam had found the edge between
Transcript and Exploratory notes invisible, with nothing to say it could be dragged but a slow hover
(option C of three drawn for him). Each edge between columns is 12 pixels wide to take the pointer. The two
outer edges, the margins, show nothing at rest and are 8 pixels wide. Over any edge the pointer turns to
the resize cursor, and the rule darkens and thickens. Over the two between columns the handle fills in the
soft ink with its bars in the paper, so the handle itself shows that it is under the pointer. A drag moves
that edge alone. The columns either side take up the room, and the transcript takes the rest. With the
widths dragged, the transcript's words run the width of their column. `Tab` reaches each edge, and the
left and right arrows move it a little at a time, more with `Shift`. A double click on an edge puts that
edge alone back where the screen opens. The app keeps the widths for each size of screen, so a laptop and
a wide screen each keep their own. A window narrower than the one the widths were dragged on gives up its
margins first, then the side columns, and the transcript keeps its 300 pixels. Reset widths, at the foot of
Columns' menu under Widths, puts every edge back for this screen. Since 21 October it also puts every
column back alone (see Stack by dragging a heading). It is faint while every edge stands where the screen
opens and nothing is stacked. A screen never dragged opens as it always has, with the columns sharing the
width as the statements 2, the transcript 3 and the notes 1, whatever their order (6 November). These come
from the widths Adam kept himself, about a third, a half and a sixth. Before, it opened at 3, 5 and 3. Each
column is held to its least width, so under about 1,090 pixels the notes stand at their least, 160 pixels,
and the other two share the rest as 2 to 3. When stacked, the statements and notes stand beside the
transcript in the same 2 to 3, and up to 800px the statements and the transcript do. Widths dragged before
stay as they were, and Reset widths puts every edge back where the screen now opens. In a narrow notes
column the heading takes two lines. Columns keeps its chevron alone where its word would not stand beside
the heading's longest word. Its tooltip then says Columns and the columns shown, and a screen reader hears
Columns. At 800px and below the edges give way to the narrow layout above. Only the transcript keeps its
reading measure, and there is no edge to drag. The columns stand still at every Text size, with the widths
dragged or not. Before, a Mac with a mouse plugged in drew scroll bars that took room (12 November).

**Show, hide or stack the columns (18 October).** Working in his own order, Adam wanted to hide the
exploratory notes, or the experiential statements, or both, with the transcript always shown. He also
wanted the notes under the statements in one column beside the transcript. He chose four layouts and one
menu from a drawing. Columns' menu has three parts. Under Show there is a tick for Experiential statements
and one for Exploratory notes, each ticked from its whole row. When you untick one, that column and its
heading go and the others share its room. When you tick it again, it comes back where it stood in the
order. Hiding never deletes anything. What you wrote stays in the workbook and shows again with its tick.
The card and the notes field keep the current passage's words out of sight, so `Cmd + Enter` still saves
and moves on. With the statements hidden the caret goes into the notes. With both hidden the transcript
stands alone at a reading measure in the middle of the screen, and its grip goes because there is nothing
to change places with. Under Statements and notes you choose Side by side, the columns as above, or
Stacked, notes under statements. Stacked makes the transcript one column with its passages' words alone.
Beside it, on the statements' side, stands a column of two halves. The current passage's statements are
above, and its card is still the place to write them, with Next at its foot. Its notes are below. Each half
scrolls on its own if it must, and a divider between them starts at half. You move the divider by
dragging it, or by the up and down arrows with it in focus, and Home and End take it to either end. A
double click puts it back at half. The app keeps its place. Dragging the statements' heading or the
transcript's to the other side moves the stacked column there, as `Alt` and an arrow do. With a column
hidden, Stacked has nothing to stack. So its two rows are faint and not offered, and the choice is kept for
when both are shown. Under Order is Back to the book's order, which closes the menu. Since 20 October,
under Widths, there is Reset widths (see The column edges). Since 21 October Back to the book's order also
puts the statements back above the notes in a stack. While the notes stand above, Stacked's row says
"Stacked, statements under notes". If you open the menu from the keyboard, its first tick takes the focus.
`Tab` keeps to the menu, `Space` ticks, the arrows choose between Side by side and Stacked, and `Esc`
closes it. Narrower windows follow the rules above for whatever is shown. The notes go under the words up
to 800px, including when stacked, and each passage stacks at a phone's width. A hidden column stays hidden
at every width. An interviewer note opens under the interviewer's words while the notes are hidden or
stacked. The app keeps each choice in `config.json` beside the order, as `columns_hidden`,
`columns_stacked` and `stack_split`. A settings file with none of them reads as the three columns side by
side. These ticks and choices are in Columns' menu alone.

**Stack by dragging a heading (21 October).** This comes from Adam's backlog. Drag a column's heading by
its grip and let it go over the other column's lower half, and the two stack in one column with the
dragged one below. Let it go over the upper half, and it goes above. While the heading is over a half, a
box in the ink stands round that column. The half it would take shows in a faint tint that leaves its
words as readable as the rest. A line in the ink shows where the two would meet, in the gap between two
statements nearest the middle, never through words. Over a gap between columns the bar marks the place as
before. The statements and the notes are the two that stack, and the transcript keeps its own column. The
stack stands where the column you dropped it on stood. The lower column's heading and grip stand over its
half. The divider between them moves and is kept as above, and its place is the upper half's share. Each
half scrolls on its own. While more of it lies below or above its edge, it fades there, as the transcript
does. The card fades out just over Next, and Next itself stays whole. Drag the lower heading back out to a
gap between columns, and it stands alone there again. Drag it over the upper half, and the two change
places. The upper heading moves the whole stack, as `Alt` and an arrow do from either grip. For the
keyboard, and for anyone who would rather not drag, the heading has a menu. A click on a heading's grip,
`Enter` or `Space` with it in focus, or a right-click on the heading opens it. While the two stand side by
side, it offers Stack under Exploratory notes or Stack under Experiential statements. While they are
stacked, it offers Stand alone. Reset widths puts every column back alone as well as every edge, with the
statements above for the next stack and the divider at half. It is offered while a stack stands. At 800px
and below the screen stands as before, with no drop on a half and nothing in the heading's menu. The app
keeps the column above in `config.json` as `stack_top`, beside `columns_stacked`.

**View.** Two things about the statements screen are a matter of taste. So you choose each, and neither is
hidden in Settings (16 October, after a tester's feedback). View is the first of the top bar's tools, an
icon of a page in two columns and its word. It opens a small menu under it with a tick, Larger current
passage. From the evening of 16 October to 17 November 2026 it also held the minimap's Auto, On and Off.
The status bar's Minimap button now takes those alone (see The minimap). Until 17 October its first three
rows chose where the notes stood: right or left of the transcript or under the statements. The three
columns and their order under Columns took their place. Each row ticks from anywhere on it. Each change
shows at once and is kept, and the menu stays open, so you can try the views one after another. `Esc`
closes it, and so does a click anywhere else. Since 17 November 2026 View also holds Work in rounds (Adam's
ruling: a screen's own settings live in its View, and Settings holds only the app's own). While Work in
rounds is ticked, its Transcript minutes per round and Rounds a day stand as small numbers beside their
labels. A new number of minutes opens the participant again where it is, with the rounds cut afresh. Under
Nudges, View holds the open project's nudges, each with its circled i (see Nudges). It shows them only for
an IPA project, and a demo's are shown and fixed. The copy of these choices that stood in Settings has
gone. The columns shown and their stacking belong to Columns. A thematic analysis project's Coding screen
has the same View without the nudges. A control lives in one place only (Adam's ruling of 17 November 2026
about 12:40). Nothing on a screen's status bar is repeated in its View. A screen whose View would be empty
has no View button. So the boards (PETs, GETs, LPETs, LGETs and a thematic analysis project's Themes),
Trajectories and the Code list have none. Their minimap, quotes, notes, close pairs and compact belong to
the status bar. Every screen's top bar has Guidance. On a board it opens the right sidebar on its Guidance
tab, and on Trajectories its Guidance sidebar. On the Code list it opens a sheet over the right of the
screen, as the statements screen's does. The sheet has eight lines about working on the list of codes as a
whole, each with its Less this and More this. They come from `ta_codes_guidance.md`, written from Braun and
Clarke's reflexive thematic analysis. A status bar button with more than two states works as the boards'
Quotes always has. A click takes the next state. A right click or a held press opens a small menu over it
to jump straight to one, with the one in use ticked. So the Minimap on the statements screen and on every
board takes Auto, On and Off in turn. Its tooltip says which, as in "Minimap: auto", and its menu holds the
three. Trajectories' Quotes, Off, Short and Full, has the same menu. M still shows or hides the map until
the next passage or pan. A two-state button stays a plain toggle. The app keeps the choices in
`config.json` as `statements_columns`, `larger_passage` and `minimap` (`auto`, `on` or `off`). A settings
file without them reads the defaults: the book's order, the current passage larger and the minimap on
Auto. The columns shown and the stacking are kept beside them, and when they are absent every column is
shown side by side (see Show, hide or stack the columns). Reset widths in Columns' menu puts the column
edges back for this screen at once (see The column edges).

With Larger current passage ticked, as on a new install, the passage being worked on is drawn large and at
full contrast. Its name in the margin and the rule beside its words are in the full ink, never the crux
orange, which in the transcript marks only a quote (17 October). With it unticked, every passage is drawn
at one size. The passage being worked on is at full contrast on a band of the sunk paper with a fine rule
round it, never in the crux orange, which means a crux. So the column no longer grows and shrinks as the
current passage moves down it.

**The minimap (16 October).** A tester lost their place in a long transcript and asked for a wider
scrollbar or a minimap. Adam chose the minimap, a part of the screen you choose yourself, not a setting
buried in Settings. It is a card at the bottom right of the transcript column. Until 17 October it was a
strip down the column's full height, which took too much of the screen for a quick look (Adam's word, 17
October). Since the evening of 17 October it is drawn to Adam's own drawing. For a few hours before that it
stood in short columns side by side. The card is one size, about 135 by 300 pixels, whatever the
interview's length, and what it holds is scaled to fit it, like a measuring jug. The transcript stands in
it as one narrow column, as if its words were wrapped narrow. Each of the participant's passages is a solid
block in a mid grey, as tall as its words. Where a passage would come out under about 4.5 pixels, it is
joined with its neighbours into one block. So a short interview shows every passage, and three hours shows
a few passages to a block. Past an hour the column is drawn finer. The least block and the gaps between
grow evenly smaller, to about 2.5 and 1.6 pixels at three hours. So three hours stands in more and smaller
blocks than an hour, as Adam's drawing has it. Until 18 October three hours looked like an hour, 31 blocks
against 30. The interviewer's passages are a thin pale mark, about two fifths of the column's width, where
they fall between blocks. A track 4 pixels wide runs down the column's left. The green of saved stands
beside each passage done, at its place, and a skipped passage counts as done. Nothing stands beside a
passage not done, only the track's outline, and there is no light green anywhere. The part of the
transcript in view is a box drawn in a solid line of the ink 2 pixels thick, near white in dark. It is
never under about 12 pixels tall. The column outside it is dimmed, with its blocks fainter, a little less
in dark. So the part on screen stands out clearly and shows at once where you are, at an hour and at three
hours (18 October, Adam's choice from four looks drawn for him: one's solid line with another's dimming).
Since 17 October, later, it had been a light wash of the ink with no edge, which could not be seen, at its
least a faint sliver of 6 pixels. At first it was a thin edge in the soft ink. The line holds 3 to 1 or more
against the card, the blocks and the dimmed blocks in both themes, and it stands on the card clear of the
green. The blocks in view keep their grey, and the dimmed ones stay in sight. Under the pointer a light
wash fills the box. The time stands at the column's right in the faint ink, like a jug's dashes. Each
label stands at the place its minute falls between the timecodes either side. In an interview under half
an hour there is a label every five minutes. Up to ninety minutes there is one every fifteen, and beyond
that every thirty, with short dashes and no label at the fifteens between. The first label reads 00:00.
Past an hour the labels run on in minutes, 90:00 and 180:00, never hours. Nothing else stands on the map:
no quote's mark, no round's rule and no mark for the passage being worked on. The box shows where you are.
The card holds the map alone. Since 21 October its button is Minimap on the status bar (see The status bar
on the statements screen). Until then it stood outside the card in the corner, as a small card of its own
on the card's bottom edge. At first it stood inside the card beside the last label. Each block and the
green reach 3 to 1 or more on the card in both themes, and the time's labels reach 4.5 to 1. A click
anywhere on the card brings that place to the middle of the column. A drag on the box scrolls it. A click
and a drag together carry on from the place clicked. The wheel over the card scrolls the transcript as it
does over the words. With the pointer on a passage, a small tip gives its speaker and its timecode. Only
the column moves. The passage being worked on stays as it was, and the caret stays in the fields. Back to
where I was shows as it does after any scroll by hand, to the card's left on the same bottom edge. The
card keeps its place. At first it rose by 44 pixels and moved under the pointer in the middle of a drag,
and then it stood 4 pixels higher than Back to where I was (17 October, later). The box follows the column
as it glides to a new passage. The card is drawn again as you work, so a statement saved or a view changed
shows in it at once. It works in every order of the three columns and with Larger current passage on or
off, because each passage's place on the card is tied to where it stands in the column. The column keeps
its own scrollbar, and the card stands clear of it. The column's foot keeps room under the last passage, so
that passage scrolls clear of the card.

The Minimap is a choice of three, Auto, On and Off, made with the status bar's button alone. A click takes
them in turn, and a right click or a held press opens a menu of them (17 November 2026). It is Auto on a
new install and for a settings file from before. In such a file the old tick's on reads as Auto and its off
as Off. In Auto the card appears as you scroll the transcript, by the wheel, the scrollbar or the keys, or
move to another passage. It stays while the pointer is on it or a drag lasts. It fades out about two
seconds after, leaving its button alone in the corner. The box over the part in view fades with the map (18
October. Before, the box went first). On keeps the map there, and Off leaves nothing in the corner. Since
18 October the same choice rules the map on the PETs and GETs boards (see The minimap under PETs). In Auto
and On, the button, with "Minimap (M)" in its tooltip, shows the card until the next passage. So does `M`
anywhere outside a field, as the shortcuts card says. While the card shows, they hide it until then. The
words you are writing and the passage being worked on never stand under the card. When the current
passage's words, its exploratory notes, a passage open for correction or a field in focus would stand under
it, the card gives way to its button. If they would be under the button too, the button goes as well, at
every width. Each comes back as soon as they are clear. Before, at 1100px and below, the button stayed over
the last line of the passage (17 October, later). The passage being worked on stands in the middle of the
column. So the card gives way only when you scroll the passage into the corner or a passage is very long,
and never while the pointer is on it or a drag is under way. At 1100px of window and below the card would
cover much of the last column, so it gives way to its button there. Until 17 October the sheet and the
fields stacked at that width. The strip gave way below 620px in the same way. A press on the button or `M`
opens the card over the column, as a press does while it has given way at a desk width. When you open it
yourself, the card shows over whatever stands in the corner. It lasts until what you are working on comes
under it. That happens once the passage being worked on, its notes or a field in focus reaches the corner
after the corner stood clear, once you click into a field under the card, or once your pointer leaves the
card or you scroll the words while they stand under it. Then the card closes to its button at 1100px and
below, and gives way as at any time at a wider window (17 October, later). Before, an opening lasted for
the whole passage and at 1024 wide covered the notes being written. A move to another passage ends an
opening too. Where a card you opened stands over the transcript's words, as at 360px, the column's words
fade out under the card across its full width, from just above the card to the column's foot. So the
card's edges never cut a line. A field you are writing in never fades (18 October. Before, the card
crossed the lines beside it). At 1100px and below, the button alone does the same where it stands over a
passage's words, as at 360px, so it never covers a word (18 October, later). Where the column has no room
for Back to where I was beside the open card, as at 360px, the column's words fade out in a strip at its
head. Back to where I was stands over that strip at the card's right edge, so it never cuts through a line
and the words never move. Before, it stood squeezed to two lines into the words, and then over a line above
the card.

**Narrow windows.** This is not a phone app, but down to 400px nothing overlaps and nothing scrolls
sideways. Since 21 October the place and Shortcuts stand on the status bar under the player, which keeps
them at every width (see The status bar on the statements screen). What follows about the place giving
way in the top bar is its history. The top bar keeps to one line and gives way in order. The participant
name truncates with an ellipsis at any width, with the whole name in its tooltip. Below 1440px the line to
today's target goes, and the tools stand as their icons alone, each named in its tooltip. Below 1280px the
first tab, Experiential statements, reads ES (see Idiograph's tabs). At 760px and below the bar takes its
three rows, with the tabs on the middle one (see Idiograph's tabs). With Work in rounds ticked, the
speaker's name and the round's short bar also go below 1440px. Each says what the bar says beside it, the
participant name and the round's counts. So at 1280px a name of 30 letters stands whole with Guidance and
Search on the bar. Before, a name of 25 letters lost its last letters, and the speaker's name and the round's
short bar went at 940px and 760px (17 October, later). Below 940px the round clock and its reset go. Until 3 October 2026 the bar said
Statements, which went at 760px with the short bar, and the clock went at 900px. Experiential statements
is twice that width. Kept to those steps, it pushed the cog off the bar from about 1000px down, and just
above 900px the bar ran past the window even with the short word. The place keeps "passage" and its
numbers whole at every width. It gives way in order, the speaker's name first, then the sheet's label (16
October). With Work in rounds ticked the place is longer, so the speaker's name goes below 1440px, as in
"passage 9 of 16 in this round". Below 1440px "in this round" and "round 4 of 5" also give way to "passage
9 of 16 in round 4". Below 620px "in round 4" goes to the place's tooltip, so the bar reads "passage 9 of
16" and keeps the word passage. Until 16 October, later, the sheet's label and the word passage went
instead. With Work in rounds off, the speaker's name goes below 620px, "passage 9 of 39". With it on or
off, the sheet's label goes below 760px (540px until 18 October). A participant with more than one sheet
keeps the switch's chevron where its label was, and it opens the same list. The place's tooltip says the
speaker's name and the round's count whole, "Juno, passage 9 of 16 in this round, round 4 of 5". A
participant marked complete with passages undecided shows its mark before the place, so there the place
takes its short form at every width. Below 620px the separators go, and the band stacks its label over the
question. Since 17 October the three columns keep the rest of the screen's height at every width. So the
page itself never scrolls, and a drag selecting words in the transcript never takes the question with them
(17 October, later). Every card stops at the window less its gutters. A card's buttons wrap and never run
off it. The row's menu stays inside its row, and its entries wrap below 620px. Below 480px the bar's
spacing tightens, and the cards and the shortcuts table take less room. In a participant with two sheets
the sheet switch is as wide as the sheet it shows, so the bar fits a phone 360px wide. Below 480px a
participant marked complete keeps its tick without the word, and the tooltip says it in full. So the
participant name keeps its letters at 360px. It read "Juno …" beside "passage 7 of 39" with Guidance on the
bar since 16 October, and "Juno - E…" before that, since Appearance left the bar. It read "Juno…" while
View and Appearance both stood there, and a few letters beside the demo tag (16 October). On a phone,
Settings' categories become a row of tabs over the content (see Settings). A participant marked complete
gives way in the same steps (see Complete). Once the build has the collector's address, Send feedback's bug
is there (see Send feedback). It sits just before the cog at every width, as it does on the PETs and GETs
bars, so it stands in one place throughout. View stands first of the tools, with Guidance after it (16
October). Then come the magnifier, which is Search's since 17 October (see Search), and the shortcuts. PETs
has gone from among them to the tabs (see Idiograph's tabs), so Settings stands last (see One title bar).
Below 480px View is the one that takes the tools to the right edge (16 October). The rest of the bar gives
way before the tabs do, so the tabs keep their words and the participant's name keeps its letters. Below
1440px "Statements complete" reads "Complete", because the tab names the screen, and the round's words
take their short form. So a name of 30 letters stays whole at 1280px. Below 760px the shortcuts go with the
sheet's label, and `?` still opens them. Below 480px View goes, and Guidance takes the tools to the right
edge. This was measured on 18 October, before the tabs, on the demo's invented participants. An unfinished
participant with rounds on is the fullest the bar gets. It keeps all of its name or all but its last
letters from 1600px down to 480px. Below that it keeps its first letters and the ellipsis, "Jun…" at
360px. The bar's sides are 8px below 480px, and its tools are 16px wide below 400px. A finished
participant keeps more, a name of 30 letters whole at 1280px. The icons at the right of the bar stand 4px
apart, where the bar's other items stand 8px apart (12px until 13 October). Below 620px they stand 3px
apart and 24px wide, and below 480px 2px apart and 18px wide. That is what gives the magnifier its room.
Each icon takes 30px of the bar, 27 below 620px and 20 below 480px, and the participant name gives that
up. So just above 940, 620 and 480px the name keeps a letter or two, as it did before the magnifier. The
bug stands among the icons at the right and slims with them.

**Sheets.** When a participant has more than one sheet, the sheet name in the top bar becomes a switcher.
It shows the same words, "Initial" sheet, with a small chevron after them, and lists the workbook's sheets
in order. Choosing one goes to the first undecided participant passage on that sheet. If every passage is
decided, it goes to the sheet's first passage. It moves the way any move does: the column is redrawn, the
player is cued and a field you typed into is saved on the way. `Ctrl + Cmd + Up` and `Ctrl + Cmd + Down` go
to the sheet before and the sheet after in the same way (`Ctrl + Alt` and the arrow on Windows and Linux).
They use the same modifiers as the seek, because `Cmd + Shift` and a bracket are the browser's own tab keys.
The shortcuts card lists them under Moving about with `Cmd + J` and `Cmd + K`. With Work in rounds ticked,
rounds are numbered sheet by sheet. So "round 2 of 4" in the top bar is the second of the four rounds on
the sheet in front of you, and the sheet's name is already beside it. Its tooltip gives the participant
figure, "round 6 of 9 in the participant". The round bar shows the round the passage is in, and the
participant line counts every sheet. The app works out passed passages sheet by sheet, so working 2d before
Initial passes nothing on Initial. A workbook with one sheet keeps the plain label, with no chevron.

**Entry.** Each statement has its own field, with its quote under it (see Pairs). `Cmd + Enter` does what
the filled button at the card's foot says, Skip or Next (see The buttons). So every passage you go on from
is decided, and the count of unvisited passages stays honest. If you move past a blank passage with `Cmd +
K`, an arrow key or a click, without pressing Skip or Next, it is passed. Moving past it is a decision not
to code it. A passage counts as passed once a passage further on in its own sheet is decided, or once the
last passage saved sits further on in that sheet. The app works out passed every time it reads the
participant and never writes it, so moving between passages writes nothing. A passed passage counts exactly
as a passage saved empty counts, in a round, in the bars and in the numbers. The notes stand open on every
passage in their own column (see The three columns). Until 17 October you could shut them under their
heading in the panel, and a dot beside it said whether they held anything. `Tab` goes through the fields in
the order they sit in: each statement and its quote, pair by pair, then the notes. `Shift + Tab` goes
back. Since 18 October each pair's bin comes after its quote, and the fields of a hidden column are passed
over. The line in the first statement's empty field is a craft prompt, a fresh one on every passage.

**Pairs.** The first quote belongs to the first statement and the second to the second. So each statement
is a field of its own with its Quote field under it, a pair. The screen once copied Excel's habit of one
box of statements and one of quotes. A passage opens with its pairs, or with one empty pair if it has none.
Add another, at the card's foot under the last pair, adds an empty pair and puts the caret in its
statement. Each pair is numbered beside its statement, 1, 2 and on, as the passage's statements are
numbered in the column. The numbers change as pairs come and go. From 14 to 17 October each pair opened
with a heading, Experiential statement 1, and its statement keeps that name for a screen reader. Remove is a
small bin with no word at the top right of each pair, level with its statement's first line. The statement
field ends short of it. The bin is in the soft ink, and red under the pointer or in focus. Its tooltip and
its name for a screen reader are Remove this statement (18 October, Adam's drawing). Until then a red-edged
Remove with its word stood at the right of the Quote label. It was too near the fields and too loud for an
act this rare. Now the Quote label stands alone on its line. Remove takes away the whole pair, the
statement and its quote, in one step of undo. A passage always keeps one pair. `Tab` reaches the bin after
its pair's quote, and `Enter` presses it. While the pointer or the keyboard's focus is on the bin, a red
line round the pair shows what goes (14 October). `Enter` never breaks a line in a pair. In a statement it
goes to its quote. In a quote it goes to the next statement, or under the last pair it adds another. The
pair being worked on is the one whose statement or quote last had the focus, or else the last pair. The
same words may be the quote of two pairs. A quote with no statement is kept, written after the pairs that
have one, until it has its statement. The workbook keeps its two columns. The statements stay in theirs
and the quotes in theirs, one for each statement in the same order. So once a passage has a quote, its
quotes cell holds exactly one entry per statement, with "(no quote)" for a statement with none. Idiograph
reads "(no quote)" as empty everywhere and keeps its place. A cell that has it from Excel reads the same. A
passage with no quote at all keeps its cell empty.

**A passage changed since the page was loaded (18 October, the words of 19 October).** A save carries the
passage as the page last loaded it. Sometimes something else has saved that passage since: another window,
an agent working through the command line or the MCP server, or anything else that writes the workbook.
Then nothing is saved. The page stays on the passage with what you typed still in the fields. A line at the
head of the card says the passage has changed since this page was loaded, with Reload and Overwrite.
Reload loads the passage as it now is into the fields. It keeps what you typed under the line, in plain
text you can copy from, with Put my words back to bring it into the fields again. Overwrite saves what you
typed over the change. Until 18 October the later save replaced the earlier one without a word.

**A resize while typing (18 October).** When you narrow or widen the window, the field holding the caret
keeps its place in the column. If no field holds it, the passage being worked on keeps its place. So
neither scrolls out of view.

**A drag takes whole words (18 and 19 October).** A drag over a passage's words selects whole words as it
goes, as a word processor's drag does. So the highlight is the words that a quote, an assignment or
anything else takes, and none holds part of a word. Punctuation touching a word goes with it: an ellipsis,
a comma, a semicolon or a full stop at its end, and quote marks or brackets round it.

**The buttons.** At the foot of the current passage's card sit the operations on the passage in front of
you, each with a small drawn line icon. Add another is at the left, with AI suggest beside it while the AI
features are on. At the right is one filled button in the crux orange, which reads in both themes and says
what it will do. With every field empty it reads Skip, with the skip icon. Skip records the passage as read
in the progress file and touches not one cell of the workbook. With words in any field it reads Next, with
the tick. Next writes the fields to the workbook, records the passage as done, and brings up the next
passage. So Next is the one button that saves and moves on. The word changes as you type, with nothing
redrawn, because both words sit in the button and one of them shows. If a passage had words in the
workbook and you have deleted them all, it reads Next. The empty fields have to be written over the old
words, and Skip never does that. `Cmd + Enter` does what the button says, and the tooltip names the key. A
click on a passage, `Cmd + J` and `Cmd + K` move between passages from anywhere. The shortcuts card lists
the keys under Moving about. Previous stood at the left of the row and Quote before the filled button until
17 October, when the three columns came. Now a click on a passage moves, or a scroll and a click, and a
quote comes from the toolbar by the selected words (see The toolbar by the selection). Until 3 October 2026
Previous passage and Next passage sat in a row under the player, and Skip and Next were two buttons beside
Flag for later. Highlight stood before Quote until 16 October, and New statement after it for that
morning.

**The word count.** Each statement's count sits under it, "8 words", with its nudges under that. So
neither has to say which statement it means. When a statement is past fifteen words, its whole count goes
into a badge, "17 words", reversed out in the paper colour on the amber, which reads at a glance in both
themes. Nothing is said about a short one. The words are counted the way the length nudge counts them, so
the number and the nudge never disagree.

**Quotes, one key (16 October).** Select words in the passage and press `Q`, or press Quote on the toolbar
beside them. Quote under the fields did this until 17 October. The words go word for word, in inverted
commas, into the quote of the pair being worked on while it has none. Otherwise they go into a new pair
under the last, as Add another puts one, with the words as its quote. Either way the caret lands in that
pair's statement, so you write the statement next, in your own words for the passage. To change a quote,
clear it and then press `Q`, so `Q` never writes over one. The line at the foot says "The quote is added
word for word." `Cmd + Z` takes it back in one step. An empty quote that was filled is empty again, with
"(no quote)" back where it stood, and a pair it added goes. A statement you wrote in that pair since stays
where it is with its quote emptied, so an undo never takes your words. `Cmd + Shift + Z` puts it back. Until
16 October `Q` put the words into the pair being worked on in place of any quote there, and a second key,
`S`, made the new pair (see A new statement from the selection). A PET's picks follow the quote as they do
when you edit the quote by hand. A quote can be made of more than one piece of the same passage. Select the
first piece, then hold Cmd and select the next. Each piece gets a light mark in the passage, and the
assembled quote shows as one line under it. The pieces are sorted into transcript order and joined with an
ellipsis where they are not next to each other. Overlapping pieces, and pieces with nothing but a space
between them, become one. `Q` commits the whole thing. A plain selection starts again, and so does a save or
a move to another passage. Quotes already in other pairs are left as they are.

**A quote across her passages (30 October).** One quote can take in the same participant's passages just
before or after the one being worked on, when nothing but the interviewer's words stand between them. That
is the thesis rule: adjacent passages combine into one block quote with a range of timecodes when their
order is kept. It is still one quote, never two. Select the first piece in the passage being worked on.
Then hold Cmd and select words in the participant's next passage, or the one before. The piece is marked
there as the first is, and the candidate under the passage takes it in. The pieces are in transcript order
with an ellipsis at every gap. The interviewer's words between them are never in it. `Q` puts it in as any
quote. If you hold Cmd and select words in the interviewer's turn, the line says "A quote holds only the
participant's words. These are the interviewer's." In another speaker's passage it says "A quote holds one
speaker's words. These are another speaker's." In a passage further off it says "A quote can take in only
the passage just before or just after. Only the interviewer's passage can stand between them." You take in
more of the participant's passages the same way, one after another, so no passage of theirs is skipped. The
quote stays with its statement, in its own row of the workbook, so the statement keeps its place and every
board keeps its card. Its words are marked in each passage they come from, in the statement's colour, and
a click on a mark there brings its statement forward. Everywhere the statement is named with where it is,
it shows the range, "Initial, 25:51–26:50", from the first passage's timecode to the last's. That covers
the PETs and GETs boards' cards and quotes, the Table view, the print view, its PDF and the Word document.
A quote inside one passage keeps its one time. A correction, a trim or a find and replace under a piece is
followed as it is for a quote of one passage. Replace all changes the quote's words with the passage's. If
the quote does not take a change, it stays unmarked until it reads as the passages do again.

**The arrow by the quote (21 October).** Some people select the words first and then write the statement
(a tester, through Adam). Beside each statement's Quote box stands a small arrow. It is lit in the crux
orange whenever words are selected in the passage being worked on, or pieces are held with Cmd. A press
makes the selection that statement's quote, as `Q` and Quote by the selection do. The words go word for
word, in inverted commas, into that statement's quote while it has none. Otherwise they go into a new pair
under the last, so a quote is never written over. The caret lands in that pair's statement, and the line at
the foot says "The quote is added word for word.". `Cmd + Z` takes it back, and Next saves it to the
workbook as it saves any quote. With nothing selected the arrow is faint, and a press says "Select the words
inside the passage first, then press the arrow." The empty Quote box says "Select in the passage, then
press Q or the arrow. Hold Cmd to add another piece." (Ctrl off a Mac). Until 21 October it named `Q`
alone.

**Each statement level with its quote (21 October).** Each statement is a box of its own, numbered. The
card's foot, Add another and Next, ends the last box. In a long passage each box sits beside the top of its
own quote. Once a statement's quote is set, by `Q`, the arrow or Quote by the selection, its box moves level
with the quote's first line. When two quotes are close together, their boxes stack in order, the second
under the first, never over it. A statement with no quote yet stays where it is. The first one is at the
passage's top, and the rest are under the one before. It does not follow a selection, and its box moves only
once its quote is set. A box never moves while you type. The app places the boxes again when the passage
opens, when a quote is undone or redone, and when the columns or the window change size. Where the
statements stand under the words, as on a phone or with the notes stacked under the statements, the boxes
keep their order under the passage as before.

**The card in reach beside a long passage (30 October).** Sometimes a passage is too long for the column to
show it with its card, as at Text size Large in a small window. Then the card stays in view as the column
scrolls. Beside the words, it keeps between the column's head and foot, level with its quote where the quote
is in view. Where it stands under the words, it keeps to the column's foot and the words pass behind it. A
card taller than that scrolls inside itself, with Add another and Next at its foot. A passage that fits the
column is as before.

If you select words in another of the participant's passages on the screen and then press `Q` or Quote,
the app goes to that passage first, the way a click on it does. It saves the passage being worked on on
the way. Then the words go into that passage's pairs as above. A selection in one of the interviewer's
passages, or across two passages, gets the line about selecting first, as it always did. With an
interviewer note open, `Q` keeps the note first, as a click on Quote always kept it. So the quote never goes
into a pair out of sight. Until 16 October the key left the note open and filled the pair hidden behind it.

A drag across passages selects only their words. The names, timecodes and row menus in the margin and the
exploratory notes beside the words stay out of it. Until 18 October the drag took them in, in the browser's
own blue.

The assembled line is labelled **Quote candidate**, with the key that commits it beside the label. Before
it had a label, it read as something the app had already done. Nothing is written until you press `Q`. A
plain click in the column that leaves nothing selected clears the pieces and the candidate with them. `Esc`
does the same, before it goes back to the passage or closes a panel.

**The toolbar by the selection (16 October).** A tester found too much hidden behind keys and right-click.
They pressed `C` with the caret in a statement, so it typed a c. Now, when you select words in one of the
participant's passages, a small toolbar appears beside them, in the menus' paper. It has Quote, which does
what `Q` and Quote do, and Give to another speaker, which offers what `C` and the right-click's Assign
entries offer. Each names its key in its tooltip, as in "Quote (Q)", and on the shortcuts card. Until 17
October each also showed its key on its face. A line beside the quote candidate's label also said "q adds
it to quotes", so with the selection `Q` was explained four times at once. The candidate keeps its label.
Quote under the fields kept its word, with its key in its tooltip, until it went on 17 October, when Quote
here became the one button for a quote. The toolbar stands above the selection's first line, or under its
last where the column has no room above. It stays inside the column, so it never covers the words, and it
follows them as the column scrolls. It is never wider than the column. At 360 its two buttons stand on one
line since their keys left their faces. At first it ran past the column's right edge, and then it wrapped
onto two lines. Where it meets the minimap's card, it stands over the card. Where the notes stand beside the
words, it keeps to the words' side of them. Since 17 October that is in the transcript's column, with the
statements and the notes in theirs. Its buttons go one above the other if they must. It stands 6 pixels
clear of the highest and the lowest of the selected words, at every width and in both themes. At 1280 it
once sat on the first line and the notes' edge (16 October, later). It also stands clear of the passage's
speaker line, which is the name and time over the words at a phone's width and in the margin at a desk
width. Where the two would meet above the selection, it goes over that line. Where there is no room there,
it goes under the selection. At 360 it once covered the name (17 October, later). Its far edge never cuts a
line of words through its letters. Where it would clip a line by a few pixels, it steps clear of it, still
clear of the selected words. Where it would cut the letters themselves, it grows over that whole line, with
its buttons in its middle. Where only the room under the letters is clipped, it stays as it is. Until 18
October it could cover half a line above the selection. It fades in where it stands. Before, it rose from
below over the line under it. Selecting words moves the keyboard to the transcript, out of any field the
caret was in, so `Q` and `C` act at once. `Esc` takes the toolbar away with the selection and the pieces
under it, and so does a click anywhere else. A selection in one of the interviewer's passages brings no
toolbar, and `C` and the right-click work there as they always did. The keys stay for those who use them.

**A new statement from the selection (16 October).** For that morning `S`, or New statement beside Quote,
made the selection the quote of a statement still to write. It filled the pair being worked on while that
pair had neither a statement nor a quote, and otherwise added a pair under the last, with the caret in its
statement. The same afternoon it went into `Q` and Quote (see Quotes, one key), which fill a pair's empty
quote whatever its statement holds. So `S`, the button and its line on the shortcuts card are gone. The
quote-first way of working stays one act. The statement is in your own words for the passage, and the
passage is the unit. A pair made this way is saved like any other. If you leave one without its statement,
it is kept as a quote with no statement until it has one (see Pairs).

**Quotes in the passage (16 October).** A tester lost track in long passages of the words they had already
drawn on. So every statement's quote is marked where it stands in its passage, with the crux orange's wash
and a fine rule in it under words that keep their passage's ink. Since Highlight went the same day, it is
the one orange in the text. In a passage set in the faint ink, which is every passage but the current one,
the quote's words take the soft ink so they read on the wash. In the dark appearance they used to stand
faint (17 October, later). Where a quote wraps, its wash and rule stop at its last word on the line. Until
that evening they ran on over the space at the edge, and its words were orange. A quote put together from
pieces with an ellipsis is marked piece by piece, each piece where it stands. A word of your own in square
brackets, as in "my rational [mind] tells me", is your clarifying insert and not the passage's. So the app
never looks for it, and marks the words either side of it where they stand (20 October). The passage being
worked on is marked from the fields as they stand, so a quote shows the moment `Q` puts it in or you type
it. Every other passage is marked from its pairs as saved. The app finds each piece after the one before it.
Any run of spaces reads as one, capital and small letters match each other, and curly and straight inverted commas
and apostrophes match each other. If the passage no longer holds a piece of a quote, because its text was
corrected since, the quote goes unmarked and nothing else changes. A mark's tooltip names its statement,
"Experiential statement 2", or both when two pairs hold the same words, "Experiential statements 1 and 3".
A plain click on a mark brings its statement forward. On the passage being worked on, the caret goes to
that pair's statement. On another passage, the app moves there first, as a click on its row does, and then
the caret goes to the pair. Since 21 October the statement's box also scrolls into sight in the statements
column when it was out of sight, by no more than it takes. So with many long quotes to a passage, a click on
the words finds the statement that quotes them. A drag across marked words still selects them for a new
quote and opens nothing. A click on words two quotes share opens the first statement by number. A quote
under the pointer or holding the caret lights its marks in the passage, with a stronger wash and a firmer
rule. The marks read in light and dark, on the current passage and the dimmed ones, in every order of the
three columns, and with the larger current passage on or off. The shortcuts card lists it under Mouse,
"Click a quote", "Shows its statement". That morning it read "Its statement".

**A colour per statement (18 October).** Each statement's quotes take the statement's own colour in the
passage, so you can see at a glance which parts of a passage each statement draws on. Statement 1 keeps the
crux orange's wash and rule. Statements 2 to 6 take the participants' colours of the GETs board in its
order: Blue, Plum, Brown, Indigo and Teal. A seventh starts again at the orange. This screen holds one
participant, so here the colours mark that participant's statements. On the boards and every other screen
they mark a participant as before. Olive is left out, because it reads as the orange to a colour blind eye.
Each wash is a bright tint of its colour, as light as the orange's, so it reads as that colour, and the
words on it read as well as on the orange's. On the card each statement's number stands in a dot of its
colour, and its quote has a stripe of that colour at its left. The numbers beside every other passage
stand in their dots too. The colour follows the statement's place in the list, so removing or moving one
recolours the rest at once. Words that two statements share keep the first one's wash and take a rule for
each. The first's rule stands where it always does, and the second's stands under it. Words three share
show the first two's rules, and the tooltip names all three. Each rule reads at 3 to 1 or more on the
paper. The words on each wash read at least as well as on the orange's in the same appearance.

**Done marks (16 October).** Each of the participant's passages that you have worked shows a thin bar at
the edge of its words. It stands in the margin where the current passage's rule stands, in the green of
saved and never the crux orange. It is full where the passage has at least one statement and fainter where
you skipped it. There is none while the passage is undecided or only passed. A passage you jumped over on
the way further, passed, has no bar. So jumping ahead to passage 30 leaves passages 1 to 29 bare, and
nothing reads as done up to here (Adam's word, 16 October). Each passage says its own state, so work done
in any order shows as it is. The bar runs the whole height of the row, so passages next to each other join.
The interviewer's passages between two of the participant's carry it on at the fainter of the two, so a
stretch of worked passages reads as one. The current passage's rule stands over its bar, solid, with the
orange taken toward the paper, so the green never shows through it as brown. The full bar is the green at
its whole strength, and the fainter one is about half. In light the full one used to read grey (16
October, later). The minimap's track takes the green at its whole strength for both. Below 1000px the
margin lies along the top. There the bar stands at the row's left edge, with the words 12 pixels clear of
it, because at the right edge it read as the column's scrollbar. The current passage's bar does the same.
With Larger current passage off, its band keeps its hairline above, below and at the left, so nothing of it
stands in the scrollbar's lane at 360. The counts and the rounds are as they were. A passage passes the way
it always has, once a passage further on in its sheet is decided, and it counts as decided there, with no
bar.

**The recording.** The player sits at the foot of the sheet's column and takes its whole width. It is built
from the app's own parts: a play button at 48px, the elapsed time, a scrub bar that fills what is left, the
total, and the file name, faint, on the right. The track holds a floor of 120px, so a long file name is cut
with an ellipsis and the bar does not thin out. With no recording nothing shows at the foot (17 October). A
click on a timecode or `Space` then says "No recording found for" the sheet as a line at the foot. Until
then the player stood as that line alone on every participant without one, taking the width and wrapping
on a phone (15 October, later). The player follows the passage. Every move cues it to that passage's
timecode. It carries on from the new place if it was playing and stays put if it was paused. Under the
pointer the play button and the track go to the ink, as any control does. Until 17 October, later, they
went to the crux orange.

An arrow icon with a small 5 stands either side of the play button (8 November). The one on the left goes
five seconds back, and the one on the right five seconds forward, from wherever the clock sits. They do
what `Ctrl + Cmd + Left` and `Ctrl + Cmd + Right` do, and neither runs past the start or the end of the
recording. Their tooltips name those keys. Like the play button they are not in the Tab order, so the
cursor stays where it is in a field.

Clicking a timecode in the margin plays from there. Clicking the same one again pauses. A click after that
carries on from where it stopped and does not go back to the timecode, because a pause is a place you
chose. Another timecode jumps there and keeps playing. Any other cue, and a drag on the scrub bar, end that
toggle. A double-click on a timecode corrects it (see Correcting a timecode). Its first click has played
from there, and its second leaves the player alone and does not pause it.

Outside a field, `Space` plays or pauses from wherever the clock sits. `Ctrl + Cmd + Left` and `Ctrl + Cmd
+ Right` (or the two arrow buttons beside play) jump five seconds either way, and they work inside the
fields too (`Ctrl + Alt` and the arrow on Windows and Linux). The chord is the app's own, because on a Mac
`Cmd` and an arrow belong to the text: they go to the line ends, and with `Shift` they select out to them.
One chord must mean one thing wherever the caret is. Both move the playhead mark and the elapsed time at
once. The app finds the file at `<case>/Source/<Sheet>/Source/`. It is the one called `P<n>-<Sheet>`, or
else the largest `.m4a` that is not a per-speaker track. Timecodes are the recording's own clock, with no
offset. A missing file, or one iCloud has evicted, shows one quiet line where the controls would be, and
nothing else changes.

**The playhead.** The passage the recording is in, playing or paused, has its timecode in bold in the
accent, not the crux orange, with a small play triangle before it. It draws no line of its own beside the
words, where the passage being worked on has its rule. While the timecode is open for correction it has no
triangle. (28 October, Adam's choice of three drawn. Until then a quiet rule in the accent stood just
before the words, 2 pixels from the rule of the passage being worked on, and the two read as a double line.
It had stood there since 18 October. Before that it stood at the row's outer edge, 100 pixels from the
words, where it read as a stray rule between the columns.) The span runs from a passage's own timecode to
the next one, including the interviewer's passages. The column glides to keep the marked passage in sight.
It leaves the column alone while a selection or a drag on the scrub bar is under way, and the passage being
worked on never moves with it. Any cue moves the mark to the cued row, playing or paused, so the mark and the
clock never say different things. Pausing leaves the mark where it stopped.

**A click on a row.** A plain click anywhere on a row acts, on the margin and the text alike. On one of the
participant's passages it goes to that passage, the way the speaker label always did. So the recording cues
there and carries on if it was playing. On one of the interviewer's passages, the passage being worked on
does not change. The recording cues to that row, jumping there and playing on if it was playing, and the
playhead mark moves to it at once. The timecode keeps playing from there, and the small control beside it
opens the row's menu. Some clicks pass through untouched: a click that selected or extended text, a click
that travelled far enough to be a drag, and a click with Cmd, Ctrl, Shift or Alt held. The text has to stay
free for you to select for a quote, built from one piece or several. A plain click on a quote's mark brings
its statement forward (see Quotes in the passage). A faint wash on the row under the cursor and a pointer
over the margin show that the row is a target. Since 17 October, later, the wash is the sunk paper of a row
under the pointer, and the row's timecode and its ⋯ read on it as well as on the page.

**Interviewer notes.** The participant's passages take the statements, quotes and notes. Your own
interventions as interviewer are worth a note too: one that moved the participant on, a poor one, a place
where the next question belonged. A plain click on one of the interviewer's passages cues the recording and
marks the row as before. It also puts one field in the notes column beside it, headed Interviewer note with
the row's timecode beside it. The field holds the note the workbook has for that row (17 October). Until
then the field stood in the panel in place of the pairs and the notes, and hid them. The current passage
keeps its card and its notes as they stand. The note closes on any move to one of the participant's
passages: a click on one, `Cmd + J`, `Cmd + K`, a sheet switch or the next stop. The passage being worked on
does not change while the note is open, and the bars, the clock and the progress strip stand as they were.
The line in the empty field is a craft prompt, a fresh one each time it opens, such as "What did this
intervention do?", "What might have served them better here?", "A question, or a lead?" or "Where were they
going before this?". While the note shows, the filled button reads Next, with the tick, as on the
participant's passages. It and `Cmd + Enter` do the same thing: the note is kept and its field goes. A
click anywhere but the field, its row and the player keeps it too. So does any move, the way a field you
typed into is saved on the way. `Esc` closes it with nothing written. If the workbook refuses a note, the
note comes back in the field the next time you click that row. A row with a note shows a small pen in its
margin, on the timecode's line, so you can see the notes down the column. The pen goes when you clear the
note.

The note goes to `/api/interviewer-note` and into the workbook's Interviewer notes column (see
[docs/internals.md](internals.md), How the workbook is written), and nowhere else. It is never a stop, never
counted and never nudged. It is in none of the CSV, the PET draft, the themes file, the prompts or anything
sent to a model. Nothing in the progress file changes, so the rounds, the row states and the passed passages
are as they were. The route refuses a workbook that Excel has open, with the passage screen's line. It
refuses a row whose speaker is not the interviewer named in Project settings with "Interviewer notes belong
to the interviewer's passages." An empty note clears the cell, and a note that has not changed writes
nothing. A page in front of a server that has not been restarted finds no note on any row, and a click on
the interviewer's passage cues the recording as before.

**The row's menu.** A right-click anywhere on a row, on the margin or the text, opens one menu, in the
menus' paper. The small control in the margin, three dots on the timecode's line, opens the same one. Since
16 October the control stands in view on every row in the faint ink. Until then it showed only with the row
under the cursor, and a tester found the menu by chance. Its entries come in groups with a thin rule
between them. The assignments come first (see Assigning words to another speaker). Until 16 October
Unhighlight stood before them. Then come Edit text, which does what a double-click on the text does, and
Edit timecode, which does what a double-click on the timecode does. Then come the two cuts, "Cut this
passage and 73 before" and "Cut this passage and 3 after", each with its rows and timecodes in small type
under it, as in "74 rows, 00:44 to 17:09" (see Trimming the ends). Esc closes the menu, and so does a click
anywhere else. Shift with a right-click keeps the browser's own menu. A right-click inside the passage
editor or the timecode box opens the box's own menu.

**Highlights (gone 16 October).** Until 16 October you could select a phrase in the passage and press `H`,
or Highlight under the fields. It became an orange run (theme 9, tint 0) in the Transcript cell, the crux
that the annotation pipeline and the guides name. Adam decided on a tester's feedback to take Highlight
away and give its place to the quotes, which are now the marks in the text (see Quotes in the passage). So
nothing on the screen makes a highlight. `H`, the button, its line on the shortcuts card, the Unhighlight
control and its entry in the row's menu are gone. Highlights already in a workbook stay in the file exactly
as they are. A save never rewrites or strips them, and the app draws them as plain words. A correction and
a replace still find them again by phrase and keep them where their words survive, naming any that is
dropped (see Editing a passage). The find still counts the occurrences inside one, because a replace there
drops it from the file. A trim's card still names a row that has one, and a split or a merge keeps them on
their characters. No export, print or prompt ever carried them, and none does now. `/api/crux`, which wrote
them, stays on the server for a page from before, with `add` and `remove` as it always took them. Nothing
on the page calls it.

**Editing a passage.** The transcript has slips, such as inverted commas missing from a stretch of internal
speech. `E` opens the passage being worked on. A double-click on the text opens any passage, the
interviewer's as well as the participant's, and so does Edit text in the row's menu. The box holds the plain
text of the cell with every run flattened. It grows as you type into it, and it has the hint and two small
buttons: `Cmd + Enter` saves, and `Esc` cancels with nothing written. The box is about the text alone, and
its save sends only the text. You correct the timecode in the margin (see Correcting a timecode). One
passage is open at a time. Opening another cancels the first, and a move to another passage cancels it too.
A double-click no longer feeds the quote builder, so the word the browser picks out goes to the editor and
not into a quote.

While the box is open it holds the caret. A click inside it places the caret and does nothing else. The
column does not navigate, does not centre again and is not redrawn, and a drag inside the box belongs to
the box and is not a piece of a quote. Before this, a click in the box bubbled up to the column's whole-row
handler. That handler read it as a click on the row the box sits in and put the caret back in the statement
field. So you could open the box on the passage being worked on and never type into it.

Saving goes to `/api/edit-turn`, which writes the text into that row's Transcript cell and nothing else. The
cell keeps its font, its alignment and its number format, and never gains a fill. The app finds the orange
runs again by phrase. If a run's phrase still occurs, the run keeps its highlight at the first occurrence in
the new text and in the font it already had. If its phrase has gone, the run is dropped and named on
screen as `Workbook highlight dropped: "..."`. Until 16 October that line said Highlight, the name of a tool
that went that day. What lies between the marks comes back as the cell's body text, because the text has
been rewritten and there is no character to carry a run on. Text that has not changed writes nothing. The
app refuses an empty passage, and never edits the header row. A changed timecode is written into the
timestamp cell in the form the cell already holds, which is a `datetime.time` in every workbook so far. The
app refuses one it cannot read, with a line, and writes nothing. The old and the new text both go into the
progress file under `edits`, beside the trim record. When the timecode changed too, the old and the new
timecode go beside them. So a participant rebuilt from their raw source can be reconciled with what you
corrected here. The source CSV the participant was built from is not touched. The statement fields, the
pace clock, the speaker and the playhead all stay where they were.

**Find and replace.** Sometimes the transcription made a slip the same way many times, such as a "so" that
wants a comma after it. You put it right once for the whole workbook. `Cmd + Shift + F` on the statements
screen (`Ctrl + Shift + F` on Windows and Linux) opens one card, Find and replace. It works from the fields
as well. Replace in the transcript under a This participant search opens it too (see Search). The card is in
the trim card's style, but it stands at the top right with no veil, so the sheet stays in sight under it. It
stands under the research question, as the guidance sheet does, so the question reads whole while it is
open. At 1280 its top once hid the question's end (17 October, later). Below 1100px it stands at the foot of
the window over the columns, and the line the app says things in rises above it. Until 17 October the sheet
and the fields stacked at that width. Below 700px it takes the window's whole width there, so no strip of
the fields under it shows their labels cut beside it (17 October, later). It has Find and Replace with, two
ticks, Whole word, ticked, and Match case, not ticked, a count line, Previous and Next, Cancel, Replace and
Replace all. Since 17 October each box is in the ink, as Settings' boxes are. Before, it was in the
browser's own blue. A passage open for correction is cancelled as the card opens. Words selected on one line
of the column start the find. Esc closes the card and takes the washes with it.

The match is literal, never a pattern. With Whole word ticked, an occurrence may not run into a letter or a
digit at an end that is a letter or digit itself. So "so" never touches "also" or "sofa", and it does find
"so," and, with Match case not ticked, "So". With Match case not ticked, each replacement takes the capitals
of what it replaces. So "So" at the head of a sentence becomes "So,", "SO" becomes "SO," and "so" is
written as you typed Replace with. With it ticked, the replacement is written as typed. The find runs over
the Transcript column, every row of every sheet, including the interviewer's passages. As you type Find,
the page counts over the text it already holds, a moment after the last key. The line reads "14 on
Initial, 3 on 2d", with "17 on 2 sheets" in the small type beside it, or "No occurrences", or nothing while
Find is empty. Occurrences inside a highlight the workbook holds are counted after a dot, "2 inside workbook
highlights", because a replace there drops the highlight. Until 16 October it said "inside highlights",
naming a tool that went that day. Since 26 October Replace all also changes the words in the statements,
the quotes, the exploratory notes and the interviewer's notes. So the line then reads "8 in all: 3 in the
transcript, 5 in your analysis" (singular where it is one, "1 in the transcript"), and Replace all's
number counts them with the transcript's.

Every occurrence on the sheet on screen has a yellow wash, never the orange of a quote and never written
anywhere. The one in focus has a stronger wash with an edge, and the column is taken to it the way the
playhead takes it. Since 17 October the stronger wash in dark is two fifths of the yellow. At half, its
words read under 4.5 to 1. The words under every wash stand in the ink, so one found in the interviewer's
fainter passage reads as well as any. The focus starts at the first occurrence at or after the passage being
worked on. Next and Previous, and Enter and `Shift + Enter` in Find, walk them in transcript order, round
from the last to the first. One on another sheet is reached through the sheet switcher's own path, which
lands on that sheet's first undecided passage, with the caret back in the card. The focus only ever sits on
the sheet on screen, so Replace never touches words out of sight.

Replace, and Enter in Replace with, replaces the occurrence in focus. It moves the focus on past the words it
put in, and never round to the top. Replace all reads "Replace all 17", so you see the number as you press
it. It is disabled while there is nothing to replace. Both go to `/api/replace`, which counts again by the
same rules. It refuses a workbook that Excel has open, with the statements screen's line, and it refuses an
empty Find. It does nothing when Replace with reads the same as Find. For Replace it names the occurrence by
its place among the row's matches. If the passage no longer reads as the page holds it, it refuses with a
line. It never touches the header row. It loads the workbook once and writes each changed cell through the
write a correction takes. So the cell keeps its font, its alignment and its number format, gains no fill
and has its highlights found again by phrase. Then it saves once. Replace all changes the words wherever a
passage holds them (26 October): the transcript, each statement, each quote, the exploratory notes and the
interviewer's note, one statement, quote or note at a time. So a name you take out of the transcript also
goes from the quote that copied it and from the statement and the note that named it. A "(no quote)" keeps
its place. A statement that the replace would leave empty keeps its words. Every PETs board of the
participant takes the new words with the workbook, and so does every copy of them: the GETs' copy and,
since 30 October in a project with timepoints, the participant's LPETs and the LGETs. So no card shows as
changed for it, and the participant stays in. Replace, the one occurrence in focus, changes that occurrence
in the transcript alone. The page redraws only the rows that changed, counts again and says what it did, as
in "17 replaced, 14 on Initial and 3 on 2d. Cmd + Z puts them back.". Each highlight dropped is named after
it with its sheet and timecode, as in `Initial 03:55, highlight dropped: "..."`. Every row changed goes into
the progress file under `edits` as a correction does, with its old and its new text. All of one press goes
under one `batch` id, with `find`, `replace` and the occurrences replaced. For a row that lost a highlight,
it records where the highlight sat. It also records the old and new words of each statement, quote or note
cell it changed. Cmd + Z puts all of it back, with the boards and every copy. The source CSV is not touched,
and the nudges, the pace clock, the speaker and the playhead stay where they were. The fields of the passage
being worked on show its new words. Words you typed there since the last save stay, and the save then says
the passage has changed, as it says for a change from another window. An AI agent runs the same replace
(see the guide for agents). A page in front of a server that has not been restarted says "Restart the
server to finish this update." and changes nothing.

**Quotes to pair.** A passage saved before the pairs existed pairs its statements and quotes by order: the
first quote with the first statement. A statement past the last quote shows an empty quote, and a quote
past the last statement shows as a pair with an empty statement. Nothing in the workbook changes until you
edit that passage. Under Find and replace, Quotes to pair lists every passage with at least one quote whose
count of quotes differs from its count of statements. Each is a line with its sheet (when the participant
has more than one), its timecode and its counts, as in "03:55 3 statements, 1 quote", and it opens its
passage. Saving the passage writes it paired, so it leaves the list. The list shows only while it holds a
passage.

**Correcting a timecode.** A single click on a timecode plays from it, and the same timecode again pauses,
as before. A double-click opens a small box in the margin in its place. The box is filled in the way the
project writes its timecodes (see Timecodes, in Project settings), with the text selected. Edit timecode in
the row's menu opens the same box. `Enter` saves, and `Esc` cancels, as does a click anywhere else. The
first click of the double-click has already cued and started the player at that timecode. The player is
left as that click left it, so the second click neither pauses it nor cues it again. Saving goes to
`/api/edit-turn` with the row's text unchanged and the new timecode, which the server writes as above. If the
server cannot read the timecode, it refuses it with its line, and the box stays open. The row's timecode,
the cue point that a click on it or a move to the passage takes, and the playhead mark all change at once,
with no reload, and the player is not touched. `Cmd + Z` puts the old timecode back. The undo entry for an
edit holds the old and the new timecode beside the text.

**Assigning words to another speaker.** A passage sometimes holds words the other speaker said, such as a
short question of the interviewer's in the middle of the participant's answer, transcribed as the
participant's. That used to mean splitting the row by hand in Excel. Select the words in any passage,
the interviewer's or the participant's, and press `C`, or right-click them and choose from the row's menu.
They become a passage of their own with the speaker they belong to. The rows either side keep the original
speaker, so one row becomes three: participant, interviewer, participant. Words at the very start or end of
a passage make two rows, not three. The selection widens to whole words, never half of one, and it must sit
inside one passage. The app refuses a selection across two passages, or one with no words in it, with a
line. A selection goes straight through, because it is precise and you can undo it.

With nothing selected, `C` assigns the whole passage, and that shows a small card first, in the style of the
trim confirm. It has one line naming exactly what will merge, as on the demo: "Juno 00:51 is assigned to
Adam. It joins Adam 00:46 and Adam 01:21 into one passage." It says what the rows carry across, which is
statements, quotes and notes. Enter goes ahead, and Esc cancels.

A sheet's speakers are its distinct names, in the order they first appear. There is no limit on how many,
so a focus group of six works the same way as an interview of two. On a sheet of two speakers `C` assigns
to the other one at once. On a sheet of three or more it opens the row's menu with the assignments alone,
and Esc cancels it. The assignments list one entry for every speaker except the passage's own: "Assign to
Adam" for the selected words, and "Assign this passage to Adam" always. They never quote the words, because a
selection can be a long passage. The last entry, Assign to someone else, asks for a name in a small box. A
new speaker is fine and becomes one more name like the others. A name already on the sheet is taken as it is
spelled there. In the right-click menu they come first, above Edit text, Edit timecode and the two cuts (see
The row's menu). `C` works outside the fields and outside the passage editor, like `Q`. Selecting words in
one of the participant's passages takes the keyboard out of a field, so `C` acts at once. Give to another
speaker in the toolbar by the selection does what `C` does (see The toolbar by the selection). The
interviewer named in Project settings stays the one speaker who is never a stop.

A row that lands beside a passage of the same speaker merges with it. After an assignment, a row joins its
previous and next neighbours only when they have the name it was just given. Otherwise it stays a row of its
own. So a whole passage given to the interviewer between two of the interviewer's passages joins them into
one, and the sheet never reads Adam, Adam, Adam. At the first or last row of a sheet it merges with the one
neighbour it has. Words at the start of the participant's passage that you give to the interviewer join the
interviewer's passage before it in the same way.

The cut falls at the edges of the widened selection. The spaces there are trimmed, and no character is
invented. The orange runs travel with their characters. So a highlight through the cut is cut there and
stays on the words it was on, and every other attribute of its font survives. A merge joins the texts with
a single space, in sheet order, and keeps every run. The first row keeps its own timecode. Each new row
takes an estimate from where the cut falls. The app shares out the seconds from this passage's timecode to
the next passage's, whoever speaks it, by character offset. It rounds to the second, and never goes before
this passage or past the next. The last passage of a sheet is taken to run 0.4 seconds a word. The estimate
is written the way the neighbouring cells hold a timecode, and you correct it by double-clicking the
timecode.

The statements, quotes and notes of a split passage stay with the first row that keeps the original
speaker. That is the row before the cut, or the row after it when the selection starts the passage. The
rows made for the other speaker start empty. A merge adds the merged rows' statements, key quotes and notes
line by line in sheet order. Each row's quotes stay with its own statements, and "(no quote)" holds the
place of a statement with none. The merged row takes the furthest state any of them had got to. Nothing you
wrote is ever dropped.

Rows are inserted or deleted in place, through the trim's own path. The header row is never touched.
Widths, freeze panes and zoom are kept. Custom row heights move with their rows, and a new row gets its
share of the height of the row it was cut from. No cell gains a fill. The cells of a new row take the style
of the row they were cut from. Before any row moves, the app copies the workbook to `_Archive/<stem>
(pre-assign <date-time>).xlsx`, a separate copy for every assignment. `/api/rows` carries it, with `op` of
`assign`, `preview` for the card and `restore` for the undo. A page in front of a server that has not been
restarted says "Restart the server to finish this update" and does nothing else. The participant then
reloads in place, the way it does after a trim, on the passage you were on. If that was the passage you
assigned from, it reloads on the first row that kept the original speaker. The player is untouched and the
playhead is marked again.

The progress file moves with the rows. Row states, edit records and the last passage saved all go through
the one re-key the trim uses. The assignment goes in under `assignments`, beside `edits` and `trims`. It
records the sheet and the row, the kind (`assign`, or `merge` when rows became one), the offsets, the two
speakers, the text of the rows before and after, the backup and the time. That is what reconciles the
workbook with a participant rebuilt from their raw source later. The themes file moves with the rows in the
same request, every board and every revision. So a merged passage's cards stand on the one row after the
cards of the passage it joined, the way its statements stand in the cell. The undo puts them back on their
own row, in their PETs.

**Undo.** `Cmd + Z` reverses what the app itself did, several levels deep and newest first. It reverses a
key quote taken with `Q`: an empty quote that was filled is emptied again, and a pair it added goes with
it. It puts a pair you took away with its Remove back where it stood. It reverses a passage corrected in
place with `E`, which goes back through the same endpoint and finds the highlights again. It reverses a
timecode corrected in the margin, with the same entry holding the old and the new timecode. It reverses
words assigned to another speaker with `C`, a split or a merge as one step, and a trim cut at either end.
The server undoes an assignment from its own archive copy. The rows it made go, and the rows it replaced
come back cell for cell: values, rich text, styles and heights. The progress file is re-keyed back and the
record is marked undone. If you have since written a statement, key quote or note into a row the
assignment made, it is added to the restored passage and never dropped. Redo applies the assignment again
from the offsets it recorded. A trim is undone the same way from its own archive copy, and redone with a
fresh cut (see Trimming the ends). A kept interviewer note is one entry with its row and the old and the new
text. `Cmd + Z` writes the old text back through the same route and opens the note on that row again.
`Cmd + Shift + Z` writes the new text. A replace, of one occurrence or of all of them, is one entry with its
batch id. Its passage is the first row it changed on the sheet on screen. `Cmd + Z` writes every row's old
text back through `/api/replace-undo`, puts any highlight it dropped back on the words it covered, and marks
the records `undone`. `Cmd + Shift + Z` applies it again from the same records. The app refuses either one
whole when a row it changed now reads otherwise. `Cmd + Shift + Z` puts an undone step back. Every entry
knows its passage. So undoing one that belongs somewhere else goes to that passage first and then reverses
it there. The reversal reaches the workbook and the progress file as well as the screen, because a quote
already saved is saved again without it. Past sixty steps the oldest goes. From 14 October a quote that `Q`
replaced was held on the stack while its passage was open. Since 16 October `Q` replaces none. Undoing a
quote leaves its pieces selected in the passage, so a second `Q` takes the same quote again. Its line says
so: "The quote is out, and the pieces are still selected." For a pair that `Q` added it says "The statement
is out, and the pieces are still selected.". A pair put back with Remove's undo says "The statement is
back.". Until 16 October they said pair and marked. Now marked means a quote shown in its passage. Typing in
the fields keeps the browser's own undo. While the field you are in took a keystroke more recently than
anything on the app's stack, `Cmd + Z` belongs to the field. The stack is in memory for the open workbook,
and it goes when another workbook opens.

**Light, dark or the system.** Appearance, as the Mac names it, is a setting under Settings, General. It has
three radio rows, Light, Dark and Same as this computer, each ticked from its whole row. The app applies it
the moment you tick it, with no Save (16 October). Until then a button on some bars cycled the three states
with a glyph for each, and it left every bar (see One title bar). A fresh browser starts in Same as this
computer. It follows the appearance set in macOS and changes with it, with no reload. Light and Dark hold
whatever the machine is doing. The browser keeps the choice under its old name and values, `system`,
`light` or `dark`. A choice stored before this, of two states, is still honoured. In both appearances the
small grey type, such as a timecode, a count or a line of fine print, stands out from its paper at 4.5 to 1
or more. A card that could not do what you asked says why in the amber of a warning, never the orange of a
crux (15 October). The orange of a crux and the amber of a warning also read at 4.5 to 1 or more as words.
The orange is a shade deeper in light. In dark the orange is Excel's own, so the bar beside a chosen row
never reads as Maybe's amber.

**Trimming the ends.** Every recording opens with consent talk and closes with scheduling and goodbyes.
Those passages are transcribed but are not data. The row's menu, from a right-click anywhere on a row or
from the small control in its margin, ends with the two cuts, "Cut this passage and 3 before" and "Cut this
passage and 11 after". Each has the number of rows and the timecodes they cover under it. The passage you
cut at is always one of the rows cut. Until 30 September 2026 the entry read "Cut this and everything
before", which left you to find that out. Choosing one goes straight to one card, **Trim the transcript**,
which holds only what decides. It has the line naming the cut, as in "Cut 4 rows: this passage and the 3
before it, 00:00 to 01:35." or "Cut 12 rows: this passage and the 11 after it, 13:12 to 14:09.". For two
rows it says "this passage and the one before it", and for one row "this passage only". It has a line when
any of those rows holds a statement, a note, a quote or a workbook highlight. A workbook highlight is an
orange run of the workbook's own, named as Find and replace names it since 17 October, later. Before, the
line said a highlight. Enter cuts, and Esc cancels. When both ends are offered, the card takes the room to
hold its three buttons on one row wherever the window has it. `T` opens the same card on the passage being
worked on with both ends offered. The cut toward the nearer end of the sheet is on the filled button, and
the other end is beside it. Each button says its cut the short way, "Cut this passage and 3 before". Before
a row goes, the app copies the workbook to `_Archive/<stem> (pre-trim <date-time>).xlsx`. Whole rows are cut
on one sheet, so the sheet stays in sequence. The header row is never touched, and the orange runs, widths,
freeze pane and zoom of the surviving rows come through unchanged. The progress file is moved onto the rows
that survived, edit records and all, through the same re-key an assignment uses, and the trim is written
into it as a record. The themes file moves with them in the same request, every board and every revision. A
card on a row that was cut goes under its board's `cut` list with the trim's id, its PET, its discard and
the picks on its row. The trim's undo puts them back where they were. An edit record on a row that was cut
stays in the file, marked `cut`. A field you typed into and did not save is saved first. The participant
then reloads in place, so a cut at the front can renumber the rounds. It reloads on the passage you were on,
wherever it has moved to, or on the nearest passage left if yours went with the cut. The line under it
reads "4 rows cut. Cmd + Z puts them back."

A trim is one step of undo, in order with the rest of the stack. It does not clear the stack. `/api/trim`
answers with its record: an id, the sheet, the direction, the first and the last row cut, the count, the
backup and `undone` false. Beside them are the boundary timecode and the first words that the record always
kept. `Cmd + Z` hands the id to `/api/rows` with `op` of `untrim`. Rows open at the place of the cut and take
the cut rows back from the backup, with their values, rich text, styles and heights, the way an assignment
is put back. The rows that survived only move, so a statement, quote or note you wrote on them since stays
where you wrote it. The header row is never touched, and no cell gains a fill. The progress file is moved
back with the inverse of the trim's re-key. That covers the row states, the edit records, which are no
longer marked `cut`, and the last passage saved, which goes back to where it was before the cut when
nothing has been saved since. The record stays, marked `undone`. The participant reloads in place. It
reloads on the passage you cut from if you have not moved since, and otherwise on the passage you are on.
Two cuts from the top come back newest first. The app refuses an older trim on a sheet while a later one on
it stands. It also refuses an undo whose rows beside the cut no longer read as the backup reads them there,
because the sheet has been changed some other way, and it writes nothing. The trim's re-key never moved an
assignment record. That record stays in the numbering it was made in, which is the numbering its own undo
reads. The stack takes a later trim back before it reaches an earlier assignment. `Cmd + Shift + Z` cuts
again with a fresh call on the same sheet, row and direction, which makes a backup of its own. A page in
front of a server that has not been restarted gets no id back from a trim. `Cmd + Z` then says "Restart the
server to finish this update" and does nothing else.

**Round complete.** With Work in rounds ticked, a round is done once every participant passage in it is
decided: saved with a statement, saved empty, skipped or passed. It closes by itself. A save of its last
passage closes it at once. A round closes once, so the card shows once for it. A save on the last passage
of a round already recorded moves on as any save does, with no card, whether or not the participant is
marked complete. Every move, including a save or a skip, closes each round below the passage it lands on
that is done and not yet recorded. So a round whose last passage was passed closes as soon as a passage in
the next one is decided. Opening a participant closes every such round quietly, with no card. That is what
closed the rounds finished before a passed passage counted. Each goes to `/api/round-complete` once, oldest
first. The server records it only when it finds the round done too, so a page working from stale numbers
cannot add to the tally. A round closed on open counts toward today's tally even when you read its passages
on an earlier day, because today is when the count was taken.

The card shows confetti, one line, and the numbers: rounds done, rounds left, and the time left at the
measured pace. They are for the round just left, or for the last of several closed at once. The confetti
comes in three levels, and each runs longer and throws more than the one before. Six cannons stand at the
left and right edges, at a quarter, a half and three quarters of the window's height. They spray inward
and upward a beat apart, from the bottom up. This lasts about three and a half seconds when a round closes,
and about five when the round closed finishes a sheet. When it finishes the participant, it lasts about
seven, and two more cannons at the top corners fire down. A level fired while one runs replaces it. Nothing
is drawn over the card, so its words stay clear, and nothing at all is drawn under reduced motion. The
pieces take the app's own tints, including the crux orange, in the appearance on screen. The target line
under them is one sentence, "1 more round today meets the target.", or else the target met and the streak.
The pace is minutes of clock time per completed round. It is taken from the gaps between saves. A gap over
five minutes counts as a break and not as work. The seconds the window spent hidden or out of focus are
taken off the gap before that test. Nothing is shown before the first round is finished. The daily target
is 2 rounds by default, with a streak across days. "2 rounds to today's target" shows in the top bar in a
window 1440 pixels wide or wider, and counts rounds closed today, however they closed. Nothing anywhere
counts statements, because zero on a passage is often right.

Until a round has been timed, the pace figure is a sentence in the small type, "measured after the next
round", and not a number in the numeral face. Rounds closed on open have no time, and that is what leaves a
participant in that state. When the round closed is the last one in the participant, the card is the
participant-complete card. It has the round's own kicker, the title "Participant complete.", and the rounds
done and left with no pace beside them. The line "Every passage of this participant is decided." comes
before the target sentence. Take a break stands beside Back to the participant list, in place of a Next
round that does not exist, and Mark complete comes after them as the filled button. Enter presses it. The
phase is then marked (see Complete). The button goes, the card reads "Experiential statements marked
complete, 3 Oct 2026." with a small tick, and Back to the participant list becomes the filled button. A
participant already marked shows that line and no button. A page in front of a server that has not been
restarted shows no button at all.

In a participant with more than one sheet, the card counts the sheet the round closed on. Rounds done and
Left on this sheet are that sheet's. The time left at your pace is the time left on that sheet. The kicker
names the round by its number on the sheet. When other sheets remain, one small line sits under the
figures, "Then the 2d sheet, 5 rounds.". It names the next sheet in workbook order with rounds left on it,
and the rounds left there. When the round closed finishes its sheet and the participant is not finished,
the card is the sheet-done card instead, with the second level of confetti. Its kicker is "Initial sheet
done", and its title "The 2d sheet is next.". Its figures are Rounds on this sheet, Sheets left and the time
left at your pace on the rest of the participant. It has the target sentence as on any round, and Take a
break beside Next sheet, the filled button. Next sheet goes to the next sheet's first undecided passage, the
way the switcher does. Enter presses Next sheet, and Esc is Take a break. The card never speaks of stopping,
which is your call. Take a break closes it and says the next round or sheet is there when you are ready.
The round that finishes the last sheet shows the participant-complete card as above. The summary the server
sends has `sheetRounds`, which gives every sheet's rounds, rounds done and left, and minutes left at the
pace. It has `sheetsDone` and `sheetsLeft` for the participant, and every round has `on_sheet`, its place
on its sheet. A participant with one sheet reads exactly as it did in every number and every line. A page in
front of a server that has not been restarted finds none of these and draws the card as it always did.

With Work in rounds off, a round closes the same way, quietly, with no card and no confetti. The count still
flashes on the move that closes it. The card comes only for the round that ends its sheet or the
participant, with the same confetti, and Celebrations governs it. The sheet-done card keeps its kicker,
"Initial sheet done", and its title, "The 2d sheet is next.". It has two figures, Passages on this sheet and
Sheets left, no target line, and Take a break beside Next sheet. The participant-complete card reads "Every
passage decided" over "Participant complete.". It has two figures, Passages decided and Sheets, and no
target line. It has Take a break and Back to the participant list, with Mark complete as the filled button
until the phase is marked, as above (15 October). On the participant-complete card, Take a break says "A
break at the end of the participant."

**Today's haul.** Take a break, on the round card, the sheet-done card and the participant-complete card,
closes the card. Where the card stood, it shows one quiet line in the card's style for about four seconds
before it fades: "Today: 3 rounds, 47 passages, 1 h 12 min.". It gives the rounds closed today in the
participant, the participant passages in them, and the time measured on them, which is the seconds the
pace counts. A click or a key takes it away at once and does what it always does. The figures come with the
summary, as `todayRounds` with `todayTurns` and `todaySeconds` beside it. A round counts on the day it
closed, as the tally counts it. If the server does not send a figure, as a server that has not been
restarted does not, the line leaves it out, as in "Today: 3 rounds.". It also leaves out a time under half a
minute. With Work in rounds off the rounds are left out, as in "Today: 47 passages, 1 h 12 min.". The line
at the foot that says the next round is there when you are ready stays as it was. Under reduced motion the
haul shows and goes without the fade. With Celebrations off it never shows (see Celebrations).

**The two bars.** The thin line under the top bar is the whole participant, with Work in rounds on or off.
It shows the participant passages decided (saved, skipped or passed) over all the participant passages in
it. So it moves on every Next, every Skip and every passage passed. Beside "passage 9 of 16 in this round" in
the top bar, which is the place of the passage in front of you, there is a short bar of the same thin line,
40px long. It shows the passages decided in that round over the passages in it, and it shows only with Work
in rounds ticked. Both are drawn in the green of a decided passage's bar at the edge of its words, because
they count decided passages. They are never in the crux orange, which on this screen marks only a crux and
a quote (16 October, later). Each gives its numbers in a tooltip: "80 of 108 passages decided" and "9 of 16
done in this round". Since 16 October the line's own word is decided. Before, it said done. The round after
them, "round 2 of 4", is the sheet's (see Sheets). In a participant with more than one sheet, its tooltip
gives the participant figure, "round 6 of 9 in the participant". The thin line stays the whole participant.
"2 rounds to today's target" stays in rounds however they fall across the sheets, and the pace stays minutes
per round. The summary the server sends has `turnsDone`, `turnsTotal` and, for every round, its decided and
total passages and whether it is recorded, beside every key it always had. A page in front of a server that
has not been restarted counts from the states instead. Once every participant passage is decided, and once
the phase is marked complete, the bars give way as Complete says.

**The round clock.** With Work in rounds ticked, the clock in the top bar shows the time you have spent on
the round in front of you. Each round keeps its own count of the time at this screen while the passage in
front of you is in it. The seconds the window spends hidden or out of focus are left out. So it stands still
within a second of your leaving and goes on when you come back. Moving into a round shows that round's count,
00:00 the first time. Going back to an earlier round resumes its count where it was. So a step back to check
a passage never wipes the round you are on. Its tooltip names the round: "Time on round 4 so far. Time away
is not counted." A small circular arrow beside it, with Reset the clock in its tooltip, sets the current
round's count back to zero and touches no other. It has no key. Opening a participant clears every count.
The pace keeps its own count of the time away, which starts again at every save, so the pace and the round
card's figures are as they were. Nothing about the clock is saved anywhere, so a reload starts it again.

**Complete.** IPA is iterative, and you can always revise a statement. But working through the transcript to
write the statements is a phase, and it ends. This mark belongs to that phase, the statements'. The PETs
phase has a mark of its own (see The Current board). Whenever every participant passage in the participant
is decided and the participant is not marked, the round text in the top bar gives way to one quiet control.
The round text is "passage 8 of 8 in this round" with the short bar and "round 5 of 5". The control reads
"Every passage decided · Mark complete", the words that the participant-complete card's kicker uses (16
October). It is underlined like Reset demo, with the numbers in its tooltip. That is how a participant
finished before this came in is marked on its next open. The participant-complete card offers the same (see
Round complete). When you press it from the bar, it fires the third level of confetti once, the level the
participant-complete card opens with. Once marked, the bar shows "Statements complete" with a small tick in
the app's green and the date, "3 Oct 2026", in place of the round counts and the short bar. The thin line
under the bar goes, and its 2px stay in the paper so the band keeps its place. "2 rounds to today's target"
goes, and the round clock stays. The tooltip gives the time it was marked and the numbers, "39 of 39
passages decided · round 3 of 3", saying decided as the line under the bar does (16 October). With Work in
rounds off, the place, "Juno, passage 39 of 39", gives way in the same way, and the tooltip gives "39 of 39
passages decided" alone. A click on the mark opens a small card in the trim card's style, with Statements
complete at its head. It says "Marked complete on 3 Oct 2026 at 14:05." and one line, "Statements can still
be revised. Reopen puts the counts back.". It has Reopen, the filled button, beside Cancel. Enter reopens,
and Esc cancels. Reopen clears the record, and the line under the bar and the target come back. With every
passage still decided, the control stands where the mark stood.

Passages stay editable while the phase is marked. Next and Skip work as they always do. A round already
recorded is not recorded again, so a save on the last passage of a recorded round moves on with no card, as
it does in a participant not marked (see Round complete). A passage can become undecided while the phase is
marked, for example when an untrim brings one back. Then the mark stays where it is, and the counts come
back beside it: the round text, the short bar and the line under the bar. The mark reads "Complete · 2
passages undecided", so nothing is hidden. At narrower widths the mark gives way with the rest of the bar.
"Statements complete" becomes "Complete" below 1440px, and the date goes below 620px. A mark with passages
undecided reads "Complete · 2 undecided" below 1140px, keeps its tick alone below 940px, and below 760px
stands beside the counts with no rule between. Beside the mark the place takes its short form at every
width, "passage 9 of 16 in round 4" with no speaker's name (16 October).

The record is `complete` in the progress file beside the workbook, `{"at": "<iso time>"}`. It is absent until
you mark the phase, so a progress file written before this reads as not complete. `/api/complete` takes
`{"workbook": ..., "op": "mark" | "reopen"}` and writes that key and nothing else. It reads the progress file
as it sits, sets or takes away the one key, and writes it back in the shape the app always writes it in, so
every other byte stays as it was. It never touches the workbook. Marking a participant already marked keeps
the first time. Reopening one that is not marked writes nothing. The app refuses a progress file it cannot
read, and does not write over it. The summary the server sends has `complete`, the time or null, and the
rows and the workbooks under Files have it too. A page in front of a server that has not been restarted
finds no `complete` and draws the bar as it always did. A page from before this sends nothing new. PETs says
nothing about this mark, and keeps a mark of its own in the themes file. Reset demo puts the mark back as
each demo participant ships. Each of the three pristine progress files has its mark, because the demo is a
finished project.

**Settings.** Settings is one card, about 760px wide and never wider than the window less its gutters. It is
the same from Home and from every screen. Its categories run down the left, and the chosen one is on the
right, with its rule in the app's colour. The categories are General, Language and formats and AI features.
Since 17 November 2026 (Adam's ruling) Settings holds only the app's own settings, the same on Home and
inside a project. A screen's own settings are in that screen's View, on its top bar (see View). A project's
settings are in its Project settings (see Project settings). General holds Your name (see the print views'
foot), then Appearance: Light, Dark and Same as this computer, applied as you tick each (see Light, dark or
the system). Then, in Idiograph's own window, comes Text size (see Text size), then Celebrations, Updates and
Closing. For Language and formats, see Language and formats. The app keeps Appearance in its own settings as
well as in the browser. AI features comes last (see AI features). With its switch on, it holds under the
switches the Experiential statements prompt and its test bench. Under PETs it holds the PETs screen's own
model for the suggested titles, which is Same as Experiential statements unless you choose another, and the
key when only that screen needs it.

Until 17 November Settings also held an Experiential statements category and a PETs one. The first held the
interviewer, Work in rounds, the statements screen's view and the nudges. The second held the status bar's
on or off, and the model. Work in rounds, its numbers and the nudges are now in the statements screen's View,
and the columns shown are in Columns. The interviewer's name is in Project settings. The status bar is
always there, and its setting has gone. Every key in `config.json` stays where it was: `work_in_rounds`,
`round_minutes` and `daily_target`, and `nudges` and `interviewer`. Nothing writes those now. A project from
before that has none of its own reads each of them (see Rounds and Nudges). On a new install the interviewer
is empty and every nudge is off. The PETs screen's model is `pets_provider` and `pets_model`. The most PETs
that a New AI board proposed, under `themes` as `cap`, went with New AI board on 11 November 2026. A file
that holds it keeps it, and the app does not read it. Settings opens on General from every screen. A line
that names a choice made in Settings names its category, as in "as chosen in Settings, General". The chosen
category holds while the card is open. The next time you open it, it goes to General again, so nothing about
it is kept in the browser. Below about 700px the list becomes a row of tabs over the content, and the row
wraps on a phone. Each field narrows with its row and stops short of the scrollbar, so none loses its right
edge. Below 480px each label stands over its field. Save at the foot saves every category. A page in front
of a server that has not been restarted since this came in shows "Restart the server to finish this
update." in place of what the server has not got yet. The rest of the card, Save included, works as
before. Opening the page reads the settings and writes nothing to `config.json`. Starting the app writes
nothing to it either, unless a setting it needs is missing, and then it writes only that setting (see
`docs/internals.md`, Settings file).

**AI features (experimental).** This is the last category in Settings (21 October). It opens with a short
paragraph on why these features are not advised, in plain type with a rule under it. It says that guidance
on AI in research is changing, that AI makes mistakes, and that what you ask about goes to the provider you
choose. It advises you to keep them off unless you are researching AI. Then one large slide switch, AI
features, Off or On, turns every AI feature of the app on or off. A new install starts with it off, and a
settings file that has it keeps its value. When you turn it on, a small card first shows over Settings, AI
features (experimental), with a fuller warning. It says that AI is not recommended for most analysis, and
that learning to do the analysis by hand matters if you are new to it. It says that AI makes mistakes and
can sound surer than it is, that what you ask about leaves your computer for the provider you choose, and
that you may need to acknowledge its use when you publish. Its two buttons are Back to safety (keep off),
the default, which Enter and Esc both press, and I understand the risks, turn on, plainer beside it. Save
keeps the switch, as `ai_suggest`. While it is on, these follow in this order: Provider, a line saying where
the passages go, the Address for a provider that has one, API key with Check key beside it, Model
(Deployment for Azure OpenAI), and then a switch for each of its AI features, ticked until you untick it.
Check key asks the provider which models the key can use. It says "This key works." and fills the Model list
with them, or says "This key was not accepted." and leaves the list as it was. When a key you typed in the
field is accepted, the app stores it, each provider's separately. With the field empty, Check key checks the
stored one. A refused key says who refused it and why, in the amber, as in "Mistral refused the key (HTTP
401).". Idiograph's features are Suggested statements for a passage, Suggested titles for a PET and
Suggested titles for a GET. An unticked feature shows none of its controls and asks no model, and the server
refuses its calls. With the switch off, no screen shows an AI control, tab, menu entry, shortcut, tooltip or
line. There is no AI suggest or AI suggest PET titles, no `N` row in the shortcuts, no AI sentence at the
foot of Guidance and no statement's short id. The server refuses every call to a model. Settings then shows
the switch, its line and Using your own AI agents (below), and nothing else about the AI. It shows neither
the provider, the model, the key, the prompt and the bench, nor the PETs model. Project settings does not
show the agents' tick, their guide or Add Idiograph to Claude Desktop. The page asks the server nothing
about them. The record of what an AI made stays whatever the switch says: "with AI" after the name of a
board an agent made, the reason an agent gave under a card, and History. At the end of the page, whether the
switch is on or off, Using your own AI agents says that you can work with your projects through AI agents
you already use. Examples are Claude Code, OpenAI's Codex and Google's Gemini CLI, working through the app's
command line and MCP server. It gives a box of words to paste into the agent, with Copy. The words say where
this copy of the app keeps its command line, its MCP server and its guide for agents. They also tell the
agent to run every change as a dry run first and show you the result before it writes. The paths are this
install's own: the Mac app's, the Windows app's or a copy run from source. With the switch on, every feature
shows as before.

**What agents change** (13 November 2026). An agent's change runs at once, as if you made it yourself, and
nothing waits for your yes. You review afterwards. The project's record of agents' changes, inside its
folder, keeps each change an agent makes. It records when, which agent, what the agent says you asked, what
it did and to which participant, board, sheet and row, what changed in a line, and how to undo it. Before an
agent's first change in a session, Idiograph keeps a restore point of the project's workbooks and boards. So
you can undo the whole session at once, back to how the project stood before it. A session is one
conversation's connection, or an agent's changes within 30 minutes of each other. The app refuses an undo,
with nothing changed, when it would lose a change made since by you or another agent, and it names what
changed. The record and its restore points never go with a copy you share. The app keeps restore points for
30 days, and keeps the last 10 sessions' points whatever their age.

**Reviewing what agents changed** (13 November 2026). When agents have changed a project since you last
looked, its card on Home says so at its foot, "Agents made 37 changes since you last looked.". It has Review,
which opens Project history at By an agent. There each session of an agent is a group under its day. It shows
the agent, its times and how many changes it made, New until you have seen it, and what the agent says you
asked. Under it each change is one line, saying what it did and where, as in "Wrote the board's note  Mabel,
PETs", with Undo at its right. The newest session shows its first lines and Show 2 more. The others show
Show the 5 changes. Undo puts back what that one change touched, as it was just before it. Undo this run, at
the session's right, undoes all of them. If you have edited a change since, it says so in place of its Undo,
as in "You changed Mabel's boards at 09:05, so this can no longer be undone.". The session's button then
reads Undo the other 4. It undoes the rest and keeps your edit. If a later session changed a change again,
the line says that session comes first. An undo never writes over a later change of yours. If one came since
the list was drawn, the undo is not done, and the reason shows under the change. A change that was undone
says when. Opening By an agent marks every change as seen, so New and the line on Home go.

A few things are yours alone, because no undo reaches them. They are sending a copy of the project to
someone, Working together's invites, people, relay code and anything sent to a teammate, Settings, and
taking a name off the list of names to replace. An agent can add a name to that list when you give it the
name. An agent that asks for one of these is told where to do it in the app, and nothing waits. If an
agent's actions were still waiting for your yes when this changed, they are cleared the first time the
project opens and never carried out. The agent log says how many.

**The agent log.** At the end of Using your own AI agents, the Agent log line says how many entries it holds
from the last 7 days, as in "12 entries in the last 7 days", with Open, or "Nothing in the last 7 days.".
Each time Idiograph refuses an agent through its command line or its tools, it keeps an entry. That covers a
project that does not allow AI agents, a command it does not have, one only you can do in the app, one given
the wrong way, and one refused inside a project. Open shows them in a card over Settings, newest first, one
line each. A line says what was asked and in which project, why it was refused and when. Details opens the
agent, the project, the command, the refusal and what the agent says you asked, with Copy. A project that
does not allow AI agents is never named, only counted. The same refusal again within a minute adds to the one
entry. The log keeps the last 7 days and drops what is older by itself, so it never needs tidying and
nothing clears it. It is kept in the app's own folder beside its settings and never in a project. So it
never goes with a copy you send or a note you send us. It never keeps what an agent handed in, only the
command's flag names. Agents can read it but never change it.

**Restart and Quit.** A short section at the foot of Settings, at the left of Save, holds Restart Idiograph
and Quit Idiograph, so you need not double-click the app for either. Each saves what is pending first, as a
move does: the passage's fields, an interviewer note and the canvas's last save. Restart shows Restarting.
The server waits for any write in hand, answers, closes its port and starts again in the same process with
the same arguments. So the pid file a launcher keeps still names it. The page reloads itself once the server
answers again. Windows cannot run a program again in the same process. So there the server starts anew as a
process of its own, in run.bat's window from source and through its launcher in the Windows app. It comes
back to the screen it was on: the same participant and passage, or PETs or GETs on the same board. It goes to
Home only when that participant or board is gone. Quit says "Idiograph is closed." with how to open it
again, by the way it was started: from Applications for the Mac app, the Start menu for the Windows app,
Idiograph.app in the app's folder, or run.command, run.sh or run.bat. The restart line, "Restart the server
to finish this update.", has the same Restart wherever it shows, because a restart is needed when a page is
newer than its server. A server from before them has no such route. So the line stays as it was, with no
button, and the foot of Settings shows it in place of the two. Both answer only the server's own page, never
a page served from anywhere else. With the tick under Closing on, the server also quits by itself a few
minutes after its last tab closes (see Closing).

**Text size.** In Idiograph's own window, Text size is under General in Settings, before Celebrations. It has
three rows, Small, Medium and Large. The one you tick applies at once to every window. It is the same as
View's Bigger Text, Smaller Text and Actual Size, and the two keep in step: Medium is the actual size. If the
keys have left a size between the three, such as 110% for one step up, none of the rows is ticked and the
heading says it, "Text size: 110%". Picking a row sets it again. The window keeps it for the next time. When
the keys or View's items change the size, a line at the foot of the window says it for a few seconds, "Text
size 110%", and again at each step. Picking a row in Settings does not show the line, because you see the
size there. In a browser's tab the browser's own zoom does this, so the rows and the line do not show (20
October, 30 October).

**Language and formats.** This is a page of Settings of its own, after General (28 October 2026). It holds
Language, then Dates, Times of day and Numbers. Each starts on Same as this computer, with what this computer
gives beside it. Each choice is written as an example of itself: Dates 28 Oct 2026, Oct 28, 2026 or
2026-10-28, Times of day 14:05 or 2:05 pm, Numbers 1,234.5, 1.234,5, 1 234,5 or 1’234.5. The one you tick
applies at once. The page loads again and comes back where you were, with Settings still open on this page.
The setting decides the order of a date, and the language decides the month's name. Every date, time of day
and number the app shows follows them. That includes a board's History, Mark complete's day and time,
Updates' last check and Search's count, and also a print view's date and the interviewer notes file's
Exported on. The end card's time left and the break's line say a length of time one way, as in 45 min, 1 h
or 1 h 25 min. Before, the end card said 85 min and 1 h 30. Under Language, "Help translate Idiograph into
your language." opens a page on translating the app, which comes with the app.

**Language.** Language has three rows. The first is Same as this computer, with the language the app reads in
on this computer beside it. Then come English (UK) and English (US). The one you tick applies at once: the
page loads again in that language and comes back where you were, with Settings still open. English (US)
changes only what American English writes differently: colour as color, centre as center, ticked as
checked, and dates as October 28, 2026 while Dates is Same as this computer on an American computer. The
window's menus are the same in both (28 October 2026). The Shortcuts card's X reads Set the selection aside in
both, the words of the boards' sidebar. Until 28 October it read Bin the selection.

**Celebrations.** Under General in Settings, after Appearance, a small heading, Celebrations, has a switch
for each of Idiograph's screens: Experiential statements, PETs and GETs (20 October). All three are on by
default. Each switch is for its own screen's confetti and counts. On Experiential statements that is the
confetti, the count after each passage and today's haul on a break. On PETs it is the statements left and
the confetti when the last is placed or the PETs are marked complete. On GETs it is the PETs left and their
confetti. When you untick a switch, it turns off its own screen's celebrations and leaves the others. A
settings file from before the three switches has one Celebrations switch, and all three read as that switch
said. The line under the switches names what is celebrated. With Work in rounds off it reads "Confetti at
the end of a sheet or a participant and when a board's last card is placed, the count after each passage and
the cards left on a board.". With it ticked, the same line starts "Confetti at the end of a round, a sheet or
a participant". It follows the tick as it stands in the card. Sound is off by default. It plays a soft tick
on each move on that decides a passage, a short two-note chime when a round closes, and a longer one when a
sheet or the participant is done. The chime goes with the confetti, so the last statement placed on the PETs
screen brings the longer one. The PETs count itself is silent. Sound plays only with a Celebrations switch
on, and its tick greys while all three are off. Ticking it plays the tick once, so you know how loud it is.
The page makes the sounds with the Web Audio API. They are quiet and use no audio file, the tick lasts under
200ms, and reduced motion leaves them alone. Save writes them to `config.json` as `celebration_screens`,
`celebrations` (on while any screen's is on) and `sound`. A page in front of a server that has not been
restarted knows neither, so it reads Celebrations as on and Sound as off.

**Updates.** In Idiograph's own window, on a Mac, Windows or Linux, a small heading, Updates, stands under
General before Closing (18 October). A copy run from source in a browser shows nothing of it. Its first row
is the version you have, "Idiograph 0.9.1", with What's new beside it, which opens that version's notes.
Then come two ticks, Check for updates and Download updates without asking. The second waits on the first.
The line under them reads "Once a day Idiograph asks GitHub for a newer version. GitHub sees your internet
address and version number. It never sees your work." With Check for updates on, Idiograph checks a few
seconds after it opens and once a day while it is open. Check now asks at once, whatever the ticks say. The
last check's time stands beside it, as in "Last checked today at 14:05". A line under it says what the check
found: that this is the newest version, that a newer one is available, that its download is under way, or
that it is ready. A check or a download that fails says why in one amber line. It may say that GitHub could
not be reached, that its answer could not be read, that the update could not be downloaded, "Idiograph could
not confirm the update is genuine, so it was not installed.", or that Idiograph could not put it in place.
Each update is signed when it is made. Idiograph keeps one only when its signature holds against the key
built into every copy, so it never installs anything but an update its author made. Save keeps the two
ticks, each only once it has moved.

The first time Idiograph opens, Home asks once, at its head, "Check for updates?". The line about what
checking sends stands under it, with two buttons, Check and Don't check. Your answer sets the tick under
Updates, and the question never comes again. With Download updates without asking off, Home offers a newer
version at its head, "Idiograph 0.9.2 is available.", with Download and Later. While it downloads, the line
says how far it has got. Once it is ready, the line says "Idiograph 0.9.2 is ready. Relaunch to use it.",
with Relaunch now and Later, and Settings shows Relaunch now too. Relaunch now saves what you typed first, as
Restart Idiograph does, and says "Relaunching Idiograph.". Then it installs the update and opens the new
version where you were. On Windows a small progress bar shows while it installs. If what you typed does not
save, it says "Your last change could not be saved, so Idiograph did not relaunch.". If the relaunch itself
fails, it says "Idiograph did not relaunch. Quit it and open it again." Later hides the line until
Idiograph next opens. The update installs as Idiograph quits, so the next time it opens it is the new
version.

**What's new.** The first time a new version opens, a line at the foot says "Updated to Idiograph 0.9.2."
with What's new and a close mark, once. While it shows, Home leaves room for it at its foot, so Home's last
line, Add transcripts on a project's page, scrolls clear above it. Until 18 October that line stayed partly
under it at 360px. What's new opens a sheet of the notes of every version since the one you had before,
newest first (29 October 2026). So going from 0.9.10 straight to 0.9.13 shows 0.9.13 and then 0.9.12. Each
stands under its own number and date, with a plain line for each change. The versions scroll inside the
sheet, and Done is always at its foot. Under the last, Earlier versions adds every older version below,
newest first. The sheet also opens from Settings, General, What's new beside the version, and from Help,
What's New in Idiograph on a Mac and What's New on Windows. There it shows the version you have first and
Earlier versions under it. While an update is waiting to install, What's new in Settings shows that update's
own notes first, then the version you have. The notes come with the app, so they open with no internet.

**The Preview Edition (21 October).** While Idiograph is in preview, its lockup has a stamp, PREVIEW EDITION in
the crux orange. It is tilted a little, under the end of the name, as the launch video shows it. The mark and
the name stay as they are. The stamp stands on Home's head, where the lockup is a little larger than before.
It stands at the top of About Idiograph, which opens on the lockup in place of its name. It stands small
beside the mark on every title bar, where it and the mark are one button that goes Home. At a phone's width
the bars drop the stamp and keep the mark. When the preview ends, the stamp goes from every place at once. On
Home, a quiet panel under the line and its four items says what the preview means (13 November. Since 22
October it had stood right under the lockup). It says that this is an early proof of concept, not fully
tested or reviewed and not for anything important. It says that your data could be damaged or lost, so you
should keep copies, and that it is not yet a replacement for the software you use day to day. It asks you to
tell Adam what you think with the bug button or by email. Because the preview is private, it also says
"Please keep it to yourself for now: don't share it or post about it." (29 October). A small warning sign in
the crux orange stands at the start of its first line. The panel goes with the stamp.

**The mark coming in (22 October).** When Idiograph opens on Home, the mark at its head comes in, in one
movement. The two square brackets turn round each other and land while the dot drops and bounces into place,
and the two come to rest together. The name fades in as the brackets turn. Then PREVIEW EDITION is stamped
on. It takes under two seconds, once each time the app opens, and you can use Home while it plays. With
reduced motion turned on in your computer's settings, the mark simply stands still.

Since 23 October that is one of seven ways the mark comes in, a different one each time the app opens: every one
plays once before any plays again, and never the same one twice running. In Pong the brackets are paddles in a quick
rally, moving only up and down, the dot a ball as in the first video games, with angled shots and last moment saves. In Pinball they are flippers: the dot rolls down the left one nearly to its end, which flips it up to three faint bumpers
above them, and on back and forth, each hit lighting a run of neighbouring letters of the name. In the anagram the name arrives as HI GO RAPID, stays that way for a moment, and the brackets sort it, lifting and carrying letters into place. In Football
they kick the dot to each other, one heading it on the way, in the kiss the dot holds them together until it pops out, and in the race all three
hurry to their places: the right bracket sprints in from beyond the window's right edge, the left close behind, both running on
over the tops of the letters, and the left overtakes the right just before the finish. The dot comes third, a ball
thrown hard from beyond the window's edge that bounces off the G and the right bracket's top arm, losing pace at
each, and drops quickly into the middle. Since 23 October the spin's brackets come
in from further out as solid things, fading in as they come, their arms turning away from you and back as they
circle each other and come down onto the page. Each ends on the mark as it always stands, then the stamp, within
four seconds, the anagram five and a half.

**About Idiograph.** A card with the app's name, the version you have, its author, Adam Knowles, the
licence and the acknowledgements. A copy built from the code between releases names its build after the
version, "Version 0.9.23, build e45b1af", and a note from Send feedback includes it too. The licence's line
says "© 2026. Free and open source under the GNU AGPL v3. It comes with no warranty. github.com/Pharkie/idiograph".
GNU AGPL v3 opens the licence's full text, which comes with the app, in a window of its own. The address opens
the code's home on GitHub in your browser (21 October). The acknowledgements thank Curt Strangward for his
article on IPA in ATLAS.ti, with its reference, and for testing early builds of Idiograph on Windows. They
end with the line "Adam Knowles made Idiograph working with Claude Opus 5.5, an AI model by Anthropic, in
Claude Code." The card opens from About Idiograph at the foot of Settings, in a browser tab or the window,
from the Idiograph menu on a Mac and from Help on Windows (20 October). Its links out of the app open in your
browser. Done or Esc closes it. If you opened it from Settings, Settings is still there.

**Support Idiograph.** "Other ways to help", beside Ko-fi's button at the bottom right of Home, and Support
Idiograph, beside About Idiograph at the foot of Settings, open a card of short parts (28 October). Under its
heading it says that Idiograph is in a private preview and asks you to keep it to yourself for now (29
October). Cite it gives the citation with the version you have in place of x.y.z, "Knowles, A. (2026).
Idiograph (Version x.y.z) [Computer software]. https://idiograph.app", and Copy. Translate it is the line
under Language. Send feedback opens Send feedback. Contribute code says the code is open for you to change
and build on, and links to it on GitHub. Fund it says what the app costs Adam, in pounds, with Ko-fi's
button. Thanks says who can be named in the Acknowledgements. After your first Word export of PETs, the note
it leaves says once, under a thin rule, "Idiograph is free. If it helps your work, there are ways to support
it.". The link opens the card. It never shows again.

**Closing.** Last under General in Settings, a small heading, Closing, has one tick, "Quit Idiograph a few
minutes after its last tab closes". It is on for a new install (16 October). Idiograph is a small server on
your computer, and its tab is a window onto it. So closing the tab alone used to leave it running until
Quit. With the tick on, it quits by itself about five minutes after its last tab closes, the way Quit does,
with every write finished. Something still running holds it: an AI request, a save or a backup, or a Restart.
The five minutes start again once it ends. A tab left open in the background keeps it running, and so does
an AI agent working through the running app. Opening Idiograph again starts it at once. A tab that comes back
to it after it has quit, as one the browser put to sleep can, says "Idiograph is closed." with how to open it
again. With the tick off, it runs until Quit. Save writes the tick to `config.json` as `quit_when_closed`,
and it holds at once, with no restart.

**The PETs model.** In AI features, under PETs, Model offers Same as Experiential statements first, which is
the default. Then come every Anthropic model the Experiential statements select offers, then the local models
when Ollama answers, then the models of the other provider chosen for Experiential statements. Each has its
provider's name, as in "mistral-large-latest, Mistral", and is labelled as it is there. A line of small type
under it names the model the PETs screen uses now, as in "Uses Haiku 4.5, the Experiential statements
model." or "Uses Opus 5.5.". It follows both selects as they change. AI suggest PET titles and AI suggest GET
titles ask this model. The test bench stays on the Experiential statements model. With Local under
Experiential statements and an Anthropic model for PETs, the key row stands under the PETs model instead,
with the same field and the same keychain item.

**Send feedback.** Send feedback lets a tester send Adam a quick note, a bug or an idea, with no email. A small
bug icon sits at the right of every top bar, just before the cog, with Send feedback in its tooltip. It is a
quiet line icon with no sparkles, because it is not the AI's. So it stands in one place on the Experiential
statements, PETs and GETs bars. Since 16 October it also stands at the head of Home beside Settings. Until
then only the statements, PETs and GETs bars had it (see One title bar). A press opens one card in the trim
card's style, Send feedback. It has a box of a few lines, "A bug, an idea, a shortcut you missed", and a line
under it, "Your name or email, if you want a reply", which can stay empty. Then comes one line of small
type, "Sent with the app's version, your system and the name of this screen. Nothing from your participant
goes.", and Send beside Cancel. Esc cancels. `Cmd + Enter` sends, and so does Enter in the reply line. Send
is greyed while the box is empty or holds only spaces, and comes on with the first character, so `Cmd +
Enter` with nothing written does nothing either. While the note travels, the button says Sending. When a note
is sent, the card closes and the line at the foot says "Sent, thank you.". A failure says why in one line in
the card, with the words still in the box. The words stay in the box while the app is open, so a card you
closed by mistake loses nothing. Only a note sent clears it. A long note scrolls up and down in the box and
never sideways, at any zoom. Until 29 October, in the Mac window at a zoom above 100%, the empty box drew a
sideways bar. The note goes only when you press Send, and exactly this travels with it: the words, the reply
line as typed, the app's version (`VERSION` in `server.py`, 0.9.1 for now), the system in plain words with
Python's name for it, as in "macOS 26.5, darwin", the browser's user agent string, one short word for the
screen it came from, and the time. The word is `home` on the first screen, `project` on a project's page, or
`statements`, `pets` or `gets`. It comes from a fixed list that the server and the collector both keep. Any
other word goes as none, and the page's own text never goes (16 October. Until then only `statements` and
`pets` were kept). Settings has no bug of its own, because it opens as a card over a screen. The app adds
nothing else to what you type. It never sends a participant, a file name, a path, a participant's words, the
key or the settings. It never sends a screenshot, the clipboard or anything else from the page. The page
posts `{"text", "contact", "screen", "agent"}` to `POST /api/feedback`, which refuses a GET. The server adds
the rest and posts the JSON on to the collector through `urllib`, as the AI calls go, with a 15-second wait.
It answers with the row's id, or with one line. An empty note is refused. A note over 8 KB is too long to
send in one go. If the collector is out of reach, it says "The note could not be sent. Check the connection
and try again.". If the collector answers anything but 2xx, it says "The note could not be sent just now
(HTTP 503). Try again later." with the status in brackets, never the collector's own answer (17 October,
later). The collector is Adam's own, a Cloudflare Worker on the free tier that writes each note as a row of a
D1 table. He reads them with `notes.sh` (see `feedback-worker/README.md`). Its address is `FEEDBACK_URL` in
`server.py`, the Worker's `workers.dev` address with `/v1/feedback` after it. `feedback_url` in
`config.json` stands in for it on one machine, and must be an http or https address alone. With neither,
the bug is hidden on every bar, and the route answers "Feedback is not set up in this build." `/api/cases`,
`/api/open` and `/api/themes` have `feedback`, which is true when there is an address. A page in front of a
server from before this finds none and keeps the bug hidden.

**Export.** The PETs board's Export menu, Markdown and CSV, or an agent's `participant export`, writes every
statement in the participant to `<case>/Working/<stem> - All Experiential Statements.csv`. It uses the format
of the reference CSV: a byte order mark, `Interview,Timestamp,Experiential statement,Proposed PET (blank for
you)`, and timestamps as HH:MM:SS. Then comes a last column, `Quote`, with each statement's own quote without
the marks the workbook keeps round it, or empty when it has none (`Key quote` until 22 October). The PET
column is empty for a participant with no themes file. For a participant with one, the column is filled from
the board current on its PETs screen. Each statement gets the labels over its card, top-most first and
joined with ` / `, as in "PET" or "PET / Sub-theme". A card set aside gets `Set aside` (`Discarded` until 19
October, `Binned` until 20 October), and an unplaced card gets nothing. The rows then go PET by PET in canvas
order. Each PET's statements come in the order the canvas reads them, top to bottom and left to right along a
row. A sub-theme's statements come where its frame's top sits among the PET's cards. Then come the unplaced
ones, and last the discarded ones, both in transcript order. A participant with no themes file keeps
transcript order throughout. The PETs board's Export menu, Markdown and CSV, writes that board's markdown
draft and the same CSV (see PETs, Export), saving the canvas first. Settings' Export pane, with its Export all
statements to CSV and Export the PET draft, went on 5 November 2026. An agent writes the CSV alone with
`participant export`.

Under Markdown and CSV in that menu is a tick, Include interviewer notes. It was in Settings' Export pane until
5 November 2026. It is off until you tick it, and the browser remembers it under `idiograph-export-notes`.
When it is ticked, the export also writes `<case>/Working/<stem> - Interviewer notes.md`. That file has a
heading with the participant name and one line with the date of the export. Then come the notes in
transcript order, sheet by sheet. The sheet name is a heading only in a workbook with more than one sheet.
Each note stands under its timecode as HH:MM:SS, with one blank line between notes. The line on screen then
says "40 statements and 3 interviewer notes written" and names the notes file with the other two. A
participant with no notes writes no file and says so. The CSV stays statements alone in the reference
format, and the PET draft is as it was.

## PETs

PETs is the IPA step after the statements. You group a participant's experiential statements into personal
experiential themes on a canvas, the work Miro and Freeform did until now. You can try named boards side by
side, each with its history. You pick the quotes that carry each PET in the sidebar beside the canvas, and
you export the grouping as a PET draft.

**Opening it.** Each annotated participant's row has a PETs half, and its workbook under Files has a quiet
PETs, even when Excel has the workbook open. The Experiential statements bar has the PETs tab (see Idiograph's
tabs), and `P` outside a field opens it too. From the statements screen, a field you typed into and did not
save is saved first, and the recording stops. Back returns to where you opened the screen from, on
Experiential statements, PETs and GETs alike. Back is the browser's Back, a mouse's back button and Cmd + [
on a Mac (Alt + Left Arrow on Windows). It returns to the participant list, fetched afresh, to Experiential
statements on the passage you were on, or to the GETs it was opened from (the arrow at the left of the bar
went on 26 October). Forward, the mouse's forward button or Cmd + ] (Alt + Right Arrow), opens again the
screen you came back from. It opens the passage from the same card, or does nothing where that is not
possible (19 October, after Adam pressed his mouse button on a passage he had opened from a PETs card). What
you were typing is saved on the way. The shortcuts card (?) lists Back and Forward under Moving about, and on
PETs and GETs under General, each key as the machine names it. A project's page is a screen of its own in
that history too (20 October). Back from it, including a mouse's back button, returns to Home, and Forward
opens the project again. In Idiograph's own window on a Mac the mouse's two buttons work as they do in
Safari. Home is one click from every screen. Idiograph's mark at the left of the statements, PETs and GETs
bars is a Home button, and so are View, Home and Cmd + Shift + H (Alt + Home on Windows). What you were
typing is saved on the way. If the canvas cannot be saved, you stay where you are. The top bar reads, left to
right: Idiograph's lockup, which is the Home button, then the tabs, Experiential statements or ES, PETs in
front, and GETs (see Idiograph's tabs). On the right are Export, Search, the bug for Send feedback once it is
set up, and Settings (see One title bar). Under it the band holds the project's name, with the demo tag on the
demo, and the participant by their pseudonym with a small chevron (see Another participant's PETs). The
toolbar under the band holds the sidebar's button, the board switcher and its save state, "Board 1 ·
Auto-saved", the Canvas and Table switch and the tools. At its right end is Inspector, the sidebar's button (6
November, see The band since 6 November 2026). Inspector is the standard panel icon in the rail toggle's
style, a frame with its right part filled. It is pressed in while the sidebar is open (see The sidebar).
Until 19 October the counts, Sticky note, Group, Undo and the shortcuts stood on the bar too, and at exactly
1280 it took two rows. They went to the status bar and the palette (see The status bar and the palette), and
the bar stands on one row at 1280 and wider. Under the bar runs the band that the statements screen has:
Research question and the whole question in the serif. It is the same band from the same project file, and
the canvas takes its height off its own through the same `--band` measure. With no question set, the band
says so and points at Project settings, as the statements screen's does. `/api/themes` has `project`, as
`/api/open` does. A server from before it sends none, so the band says there is no question yet.

**Statements left.** When an act takes statements out of Unplaced, into a PET or a sub-theme or onto the pile,
the count of those left rises over the middle of the canvas, "4 left". Since 17 October, later, it is in the
ink. Before, it stood in the crux orange. It is the passage screen's count (see The count), in the same face
and the same 850ms. When the last unplaced statement goes, the third level of confetti fires, the
participant-complete card's, and one line stands in the count's place, "Every statement placed.". The counts
before and after the act decide it. So an act that leaves Unplaced as it was raises nothing, and an undo or a
redo that brings a statement back raises nothing either. On the GETs board the count is of the study's PETs
and sub-themes in no GET. One with no card on the board counts as well, and one whose every card is in the
bin does not. So "Every PET placed." stands only when it is true, and an act that only bins raises nothing
(20 October: Select all and the bin raised it, and so did going back and forward). Nothing is written,
because it belongs to the page alone. It takes no pointer and no focus. Under reduced motion it never shows,
and Celebrations in Settings silences all of it.

**The bar at narrow widths.** The bar keeps to one line and gives way in order, as the statements screen's
does. The participant name truncates with an ellipsis at any width, with the whole name in its tooltip. So
does the board's name, but both only once the counts have stepped down. Each keeps its first letter and the
ellipsis, so neither is ever cut through a letter (17 October). At any width where the participant's, the
project's or the board's name would still be cut once the counts have gone, the bar takes two rows. The way
back, the tabs and the tools stay on the first, with the counts beside them again where they fit. The mark,
the names and the board move to a row of their own under them. So on a phone 360 wide "Juno", "Living with a
dog" and the board's name read whole at their usual size (17 October, later), and so does a long name on a
desk. Wherever everything fits, the bar keeps one row, on PETs and GETs alike. Where it runs a little short,
before it takes two rows, the save state keeps its mark alone and then Experiential statements reads ES. So
the board, its save state and the Canvas and Table switch stay on the one row after the tabs, at 1280 and
wider, even with long names (23 October). On the second row, where it is needed, the switch stands inside the
bar. A name too long even for the second row ends there with its ellipsis, with the whole name in its
tooltip. The way back is a place and not a tool. So on PETs and on GETs alike it never takes a tool's box, at
rest or under the pointer, and its arrow goes to the ink under the pointer (17 October). Nothing in the bar
belongs to the AI, so the AI switch makes no difference to it. Below 900px the save state keeps its mark
alone, with the words in its tooltip. Below 740px the counts go. Since 18 October no word stands beside the way
back to go below 560px, as the words Experiential statements did until then. The arrow says where it goes in
its tooltip at every width. At the statements screen's 620px step the gaps close up. The rule before the
board stays on PETs and GETs, so "GETs" never runs into the board's name as one phrase (17 October, later).
At its 480px step the buttons slim. The tabs keep their words at every width, with Experiential statements
reading ES below 1280px. At 760px and below they take a row of their own (see Idiograph's tabs). The icons at
the right of the bar stand as the statements screen's do: 4px apart where the bar's other items stand 12px,
3px apart below 620px and 2px apart below 480px, with the bug for Send feedback among them. It was measured on
5 October 2026 on Rowan's participant opened from Experiential statements, counting the bug and the Current
board's ribbon. The bar needed 896px at its fullest and 833 with the save state's mark alone. It needed 577
without the counts and the GETs link of the time, which went together below 740px. It needed 537 once the
gaps close up, 400 without the words on the way back and 335 with the buttons slimmed. The ribbon takes 16px
of each, and the bug 30, or 29 once the gaps close up and 22 once the buttons slim. So the save state's step
sits 4px above the 896. Just above 740px the counts still show a little over half of themselves, and just
above every step both names keep their whole width. Down to 400px nothing overlaps and nothing scrolls
sideways. Until 5 October 2026 the bar also had the Inspector's button, Board's button and the shortcuts at
its right, 60px more, and its widths stand where they stood. On 16 October Group, Undo and the shortcuts came
to the bar. Measured again on Rowan's participant opened from the participant list, with its longer workbook
name, it needed 879px at its fullest, 813 with the save state's mark alone, 546 without the counts, 506 once
the gaps close up and 398 with the buttons slimmed. So the widths stay where they were. It was measured again
on 18 October with the steps of the time, Sticky note on the bar and no word beside the way back, on Rowan's
participant opened from Experiential statements. It needed 975px at its fullest, 836 with the save state's
mark alone, 673 without the counts, 652 once the gaps close up and 522 with the buttons slimmed. So it kept
one row down to about 670px and took its two rows below that, with the steps on the first row with the way
back and the tools. Since 20 October the tabs take that place, and at 760px and below the bar stands on the
three rows of Idiograph's tabs. Below 480px Sticky note, the first tool since 18 October where Group was,
takes them all to the right edge. The participant's name and the board's give way in full to their
ellipses. Before, their small share of the shrinking left the bar 50px past a phone 360 wide. The save state
shows only a failure, so the names keep a few letters at 360.

**Another participant's PETs.** The participant picker in the PETs tab is a switcher, in the board switcher's
style. It shows the name and a small chevron. A click opens a menu under it with every participant of the
project that has a themes file, listed by pseudonym, with the participant on the screen ticked. Under each
name sits the board it opens on: its Current board with the ribbon when it has one, and otherwise the board
last open. Open as table stands at its right (see Print). A click on another participant saves anything still
to save and opens that participant's PETs at once, on that board, and the way back goes to the participant
list. So two participants' boards are a click apart, and you never need a trip through the participant list
and the statements screen. Opening one writes nothing in its themes file. The file names the board as the one
last open only once you change something there. The demo is a project of its own and lists its three
participants, Juno, Rowan and Mabel, whether or not each has a themes file. Esc closes the menu, and so does
a click anywhere else. The page asks for the list each time the menu opens, through `/api/themes-cases`. A page
in front of a server from before it says "Restart the server to finish this update." in the menu. Each other
participant also has Open beside this one, over Open as table. It splits the canvas and puts that
participant's board beside this one, read-only (see Open beside this one, under GETs).

**Cards.** There is one card per experiential statement: every line of column C, on every sheet, keyed by
sheet, row and line, as in `Initial:12:0`. A card is 200px wide. It shows the statement in the serif and the
row's timecode under it in the code face, the way the project writes its timecodes, as the player's clock
does. A long statement stops at four lines, with the whole of it in the card's tooltip. A card from a sheet
after the first shows that sheet's name, small. A double-click on a card opens its statement for editing on
the card, as a double-click on a PET's title opens the title. A double-click on its statement in the
Inspector does the same (see Editing a statement). Go to the passage in its right-click menu opens its
passage on Experiential statements (see From a statement to its passage). Since 20 October a first open puts
nothing on the canvas. Every statement waits in the sidebar's Unplaced in interview order (see The sidebar).
Put all on the board, or New board, all on the canvas, lays them in a compact pile in the middle of the
canvas, with the margin between neighbours. Until then every first open did that.

**The canvas.** The canvas follows Miro's model, which Adam knows. The wheel zooms about the pointer, from 15%
to 250%, and so does a pinch. A sideways wheel pans left and right, such as the thumb wheel of a mouse like the
MX Master or a trackpad's sideways swipe. The wheel with Shift held does the same, and the wheel with Alt held
pans up and down. Space held with a drag pans, and so does a drag with the middle button. A plain drag on
empty canvas draws a lasso and selects every card and label whose middle falls inside it. A click selects one
card or label. A click on empty canvas clears the selection, as Esc does. Shift or Cmd adds to the selection
(Ctrl on Windows and Linux). With a click it adds one card or label to the selection or takes it away. With a
drag it draws another lasso over what is selected already, inside a PET's frame too. So you can pick
statements scattered across the canvas, or inside a PET, and then group them with `G` or take them out with
Backspace. A drag on a selected card moves the whole selection. A drag on a card that is not selected selects
it alone first.

`H` is the hand. With it, a plain drag anywhere pans, and the cursor is a hand. `H` again, `V` or Esc gives
the pointer back. Two small controls at the bottom right, the pointer and the hand, show which is on and
switch between them. Beside them is the zoom: minus, the level, which goes back to 100% when you click it,
plus, and Fit all. Fit all brings everything into view and never zooms closer than 100%. Since 20 October Fit
all leaves room for the palette, which floats over the canvas, so no card or frame is left under it, at 360
as at 1280. Each takes the side that costs least: the palette a strip down the left, and the bin a strip
down the left or, on a phone, off the foot. Going to a theme, a card or a close pair does the same. The canvas
opens fitted, and below 620px the words Fit all go. A board too big to show whole even at the least zoom,
15%, shows its top left there (30 October). Before, its middle could be blank canvas. The line at the foot
stands just over the zoom bar and the bin wherever it would cover them, as on a phone. Until 18 October it hid
the zoom bar. From 5 to 16 October the shortcuts button, `?`, sat at the end of the zoom bar, where Figma and
Miro keep help. Now it stands on the top bar, as on every bar.

**The status bar and the palette (19 October, Adam's choice A).** A status bar runs along the canvas's foot,
as Excel's and Photoshop's do. Its left holds the board's counts in plain words, each number in the mono face.
A count of nothing is said too, so the counts hold their place. Since 26 October (Adam's wording C) the total
comes first, then where the cards are, then the PETs: "46 ES: 25 in PETs, 5 stacked, 2 set aside, 14
unplaced | 3 PETs". When cards lie loose on the canvas, "3 in no PET" is among them. The 25 in PETs count each
card once, including a stack's top. The statements stacked under a top are counted separately, so the parts
add up to the total. On the GETs, LGETs and LPETs boards a card is a PET or a sub-PET, so the count is of
cards: "11 cards: 7 in GETs, 1 set aside, 3 unplaced | 2 GETs". While anything is selected, its count follows
the PETs: "1 ES selected", "2 cards selected" on GETs, or "3 selected" when PETs or notes are among it. Until
26 October the counts stood apart with no total: "3 PETs", "25 in PETs", "14 unplaced", "2 set aside" and "5
stacked". A right click on the bar opens a tick for each, PETs, In PETs, Stacked, Binned and Unplaced, in the
order the bar says them. The app keeps what you tick at once. A statement stacked under a top counts as
stacked, and its top stands for it in the rest. If a count that holds anything is unticked, the total goes,
as in "ES: 25 in PETs, 14 unplaced", because the parts shown no longer reach it. The bar's right holds the
pointer and the hand, the zoom, Fit all, the minimap's button, Quotes on cards, Close pairs on the PETs board,
Notes on cards on the GETs board, and Shortcuts. Since 20 October (from a tester's feedback) the minimap's
button reads Minimap beside its icon, Quotes on cards reads Quotes and Notes on cards reads Notes. Each gives
way to its icon alone where the bar runs short, as Fit all and Shortcuts do. Since 17 November 2026 the bar is
always there (Adam's ruling). Until then Settings and the window's View menu turned it off. Where the bar
runs short, it gives way in the order Adam set on 26 October, with the counts last. First the tools' words
go, and each tool keeps its icon, with its word in its tooltip. Then a count beyond the total and its parts
goes, such as how many are selected or the close pairs. Then the spacing closes up. Then the tools go: the
pointer and the hand, the minimap's button and Shortcuts. Then the zoom's minus and plus go, then Quotes,
Notes and Close pairs. Only then do the counts go, the PETs first. So at 1280 the bar always says the whole
sentence, and at 720, the app's smallest window, the total and its parts still show. In a canvas narrower
still, the total goes with every part except In PETs and Unplaced, as in "ES: 25 in PETs, 14 unplaced". So it
never stands over parts that do not reach it. Then In PETs goes, so no count or button is ever cut off. The
bin and the map stand above the bar. In the Table view the bar keeps its counts alone.

**Quotes on cards (19 October, from a tester's reflection on IPA in ATLAS.ti, Adam's way A).** A button of two
inverted commas stands among the status bar's tools, after the minimap's, with "Quotes on cards" in its
tooltip. It shows each statement card's own quote under its statement, inside the card, in italic behind a
short orange rule, on the PETs and the GETs boards alike. It is pressed in while the quotes show. It is off on
a new install and kept across a restart. A quote runs to three lines at most, and the whole of it is in its
tooltip. A quote in pieces shows them in order, joined by the ellipsis it was saved with. A card with no quote
shows nothing more. A click on the quote selects the card and shows the whole quote beside it. It shows on the
card's right or left, or under or over it, wherever it covers least of the cards around, and otherwise on the
side with more room. It stands under Quote and its timecode, with a play button on the PETs board when the
sheet has a recording. Show in passage opens the passage, as Go to the passage in the card's menu does, and
Back returns to the board. A double-click on the quote shows it whole, as a click does, and edits nothing.
Esc, a click anywhere else or the wheel puts it away. The taller cards take their room as an open stack does.
What stands below a quote in its column moves down as far, and turning the quotes off puts everything back
where it stood. That room is only a view. So the file keeps where everything stands with the quotes off, and a
card you let go below a quote stays where you let it go. Since 23 October (from a tester's report), with the
quotes shown, a card moves only when you move it or when your move sends it clear. Then it moves as far as it
would with the quotes off. A card moved a little moves alone. A label that grows sends clear just what it
reaches. Turning the quotes off and on again leaves every place in the file as it was. The app makes the room
for the quotes and for an open stack again once the type has loaded, so an open stack keeps its height. Since
30 October a sub-PET under two that grew moves down as far as the one that needs most, never by both
together. That covers a sub-PET under two sub-PETs whose cards both show their quotes, or one with an open
stack. So it shows as close under them as the board has it, and a drag up brings it to rest a margin under
the lower of them with nothing else moving. (Adam had reported that a sub-PET under two side by side kept a
large gap under them, and that dragging it up pushed them up the board instead.)

**Quotes in three ways, Off, Short and Full (30 October, Adam: "full quotes on each card without having to click anything additional").** Quotes on cards has three ways. Off shows no quote. Short is the quote as
above: three lines at most, with the whole in its tooltip and a click away. Full shows each quote whole on its
card, every piece, with no ellipsis except the ones it was saved with. Each click on Quotes takes the next way,
Off, Short, Full and back to Off. Its tooltip says which: "Quotes: off", "Quotes: short" or "Quotes: full". It
is pressed in for Short and Full. After its word a small mark of two lines shows Short, and one of four lines
shows Full. The room for the mark is kept at Off, so the tools beside it never move under the pointer. A
right click on it, or a held press, opens a menu headed Quotes on cards with Off, Short and Full, and the one
in use is ticked. A choice is kept at once, and the menu stays open, as Close pairs' menu does. Esc or a click
elsewhere puts it away. The way is kept across a restart. It is Off on a new install, and a version from
before reads Full as Short. At Full a click on a quote is a click on its card, which selects it. A
double-click edits its statement, as one on its words does, because there is nothing more to show beside it.
Its play button stays in the Inspector, and so does Go to the passage in the card's menu. The canvas makes room
for the whole quotes as it does for short ones. What stands below a quote in its PET or sub-PET moves down,
the frames grow and nothing overlaps. The minimap and Fit all take the taller board, and Short or Off puts
everything back where it stood. On the GETs board a PET unfolded in place also shows its statements' quotes
whole at Full. Quotes has no key. Since the same day Esc also puts away the status bar's counts menu and Close
pairs' gap menu. Until then only a click elsewhere did.

**Notes on cards (20 October, from a tester's feedback).** On the GETs board a button of a page with lines
stands after Quotes. It reads Notes, with "Exploratory notes on cards" in its tooltip. It shows the exploratory
notes of each statement card's passage under the card's quote, upright in the sans face behind a faint rule.
They run to three lines at most, with the whole in the tooltip. Several notes on one passage are joined by a
dot. The button is pressed in while the notes show. It is off on a new install and kept across a restart, as
the quotes are. The cards' room is measured with the quote and the notes together. It is not on the PETs
board, where the passage is one step away through Go to the passage in a card's menu.

**Close pairs (20 October, after supervision, Adam's way B and way 1).** Adam's rule is that statements from
the same passage of the same sheet stack under the best one, unless they say radically different things. A
button of two linked cards stands among the status bar's tools, after Quotes on cards, with "Close pairs" in
its tooltip. It draws a thin dashed amber line between the two cards of every close pair on the PETs board. A
close pair is two statements in the same group, or in the same PET when it has no groups, from the same sheet
and within a minute of each other by their passages' times. On a sheet with no times a row counts as half a
minute, so a minute is two rows. A small dot marks where the line meets each card. When one card stands over
the other, the line is a short straight line from the upper card's foot into the lower card's top. The line
keeps to the gaps between the cards and runs under them, so it never crosses a card's words. It never meets
the ⋯ at a selected card's top right corner. Where its way passes that corner, it stops short of it and starts
again beyond, and a dot there is cut back with it. It is quiet at rest, and strong while either card is under
the pointer or selected. Its tooltip says how far apart the two are: "12 s apart", "1 row apart", or "Same
passage" for two statements of one row. A card close to two others has a line to each. Selecting it, or
pointing at it, strengthens both, by design, because it belongs to both pairs. A card stacked under another
is in no pair, so a pair is gone once stacked. The button is pressed in while the lines show. It is off on a
new install and kept across a restart. A right click on it, or a held press, opens a menu of the gap: 15
seconds, 30 seconds, 1 minute, 2 minutes or 5 minutes, kept at once. Under it are the pairs marked Not the
same, each with Show again. While the lines show, the status bar's counts end with "5 close pairs" and with ‹
and ›, which step through the pairs, as in "2 of 5 close pairs". Each step selects both cards and glides the
canvas to bring them into view. A click on the count steps too. Where the bar runs short it reads "5 close".
In a bar shorter still, the ‹ and › and the zoom's minus and plus give way, and a click on the count still
steps. A click on a line, or on a dot, opens a small menu headed by the gap. It offers Stack under 12:04 and
Stack under 12:16. Each stacks the other of the two under the one it names, as a drop on its middle does, in
one step of undo. Then comes Not the same, which takes the line off that pair for good. The board keeps it,
and it is one step of undo. Then comes Inspect both, which selects the two and opens the Inspector on them,
one under the other, each with its time and its quote, with Stack the later under the earlier and Not the
same under them. Two statements that share a time, or have none, are named by their first words. In the Table
view each row of a close pair shows a link mark with the gap, "12 s apart". Its click opens the same menu, with
Stack the other under this one or Stack this one under the other. Close pairs never show on the GETs board.

A palette floats at the canvas's left edge, as Photoshop's tools do. It holds Sticky note and Group, then
under a rule Undo and Redo. They are icons alone, each named in its tooltip with its key, as in "Group (G)"
and "Redo (Shift + Cmd + Z)". Its grip of six dots at its top drags it anywhere on the canvas. When you let
go, it settles against the nearer side edge at the height you let it go, and that place is kept across a
restart. While cards are dragged it goes faint, and a drop over it lands on the board under it. The Table
view keeps it with Group, Undo and Redo (see Canvas and Table).

**The toolbar (21 October, Adam's choices of 20 October, from a tester, who missed the floating palette and found many things only shortcuts).** The palette now stands docked by default as a toolbar under the
research question, on PETs and on GETs. Each tool has its icon and its word: Sticky note, Group and Select
all, then Auto-arrange, then Align (Left, Centre and Right, Top, Middle and Bottom), then Spread (Across and
Down), and at the right end Undo and Redo. Align's six are faint until two or more cards are selected, and
Spread's two until three or more. A grip of six dots at its left end pulls it off. Drag it, and it floats on
the canvas as the palette did, with the same tools and the same words in a column, so it reads as one
toolbar in two places. When you drag it back by its grip, a dashed slot across the top of the canvas shows
where it docks, and letting go there docks it. This computer keeps whether it is docked or floating, and
where it floats, for every board, across a restart. On a narrower window it gives way a step at a time and
never cuts a word. First Select all keeps its icon alone, then Align and Spread keep theirs, then every tool
keeps its icon alone. At a phone's width Align and Spread go under a button of three dots, which opens the
same eight in a menu. Since 26 October the docked toolbar always keeps Align and Spread under its three dots,
as two sections of its menu. The floating one keeps them in its column while the canvas is tall enough. The
Table view keeps Group, Select all, Undo and Redo.

**Align and Spread (21 October).** With cards selected, Align moves them to the edge or the centre of the
outermost of them: left, centre or right, top, middle or bottom. The cards not selected stay where they were.
Cards that would then overlap move on along the line, in the order they stood, just far enough to keep the
margin between them. Spread keeps the first and the last where they stand and spaces those between evenly,
across or down. Where they need more room than the two give them, the last moves on. A selected label moves
with all it holds. Each is one step of undo. The same eight stand under Align in the right-click menu of a
selection of two or more, and open beside it as the pointer comes to Align.

**Descriptions (21 October, Adam's idea and his ruling on the drawings).** A PET, a sub-PET and a GET can
have a description as well as a title. The title stays the short version to scan. The description is
longer and sits under it as a secondary heading, smaller and lighter, so you can read the step from the
statements up to the theme. A sub-PET's description is smaller again than its PET's. On the board the
title's card runs wider to show it whole. It is as wide as what its PET or sub-PET holds and never wider than
its frame, so a PET's runs across its own frame and a sub-PET's across the sub-PET's (31 October, Adam: he
would rather it were wider than deeper). Where what it holds is narrow, a single column of statements, the
card keeps the width it always had. The title wraps at the same width. A description too long even for that
takes up to six lines, and the rest of it is in the title's tooltip and the Inspector. Until 31 October it
took two lines. What stands near a card that grew is moved clear of it, as it is when a title takes a line
more. A title with no description runs as before. To write one, double-click the title, or choose Add
description in its right-click menu. Under the title's box a second box opens, with "Description" in grey
while it is empty. The boxes open over the title where it stands, with its words where they were, and
nothing on the board moves while they are open or when they close. Enter keeps the title and the description
and closes the boxes in one press, from either box. Tab or Shift + Enter goes from the title to the
description, and Shift + Tab goes back. Esc leaves them as they were. A box left empty means no description
at all. Once a label has one, its menu reads Edit description and Remove description. Remove description
takes it off in one step, and Undo brings it back. The same words are in the Inspector, in a box under the
title in its head, and whatever you write in either place is the same. There is no limit on its length. It is
a field of its own, separate from the label's note. On the GETs board a GET takes one in the same way, and a
PET's card there shows its PET's description under its title. The Table view shows each description whole
under its title inside the heading's band, in the serif and never in capitals. The print view and the Word
document show it under its title too, while Descriptions is ticked. That tick sits under Export with the
others, beside Board note on the print view and on the GETs print card. It is on for a new install and kept
as you leave it. A board with no descriptions looks, saves and prints as before. Since 22 October a
description stays through every other change to the board: a rename, a reorder or a move on the canvas, an
AI revise, a write by an agent, a restored revision or a PET copied to another board. Until then any save from
the canvas took every description off.

**The minimap (18 October).** A small map of the whole board stands above the zoom bar at the canvas's bottom
right, in Miro's and tldraw's way, as the transcript's minimap stands at the bottom right of the statements
screen (Adam's choice, 17 October). It is a card as wide as the zoom bar and 160 pixels high, and it draws
the board fitted to every card on it. Each card is a small rectangle in the tint of the PET it stands in. A
card in a sub-theme takes its PET's own tint, and a card in no PET is in the faint ink. Each sticky note is on
its own paper, and every PET's and sub-theme's frame is an outline in its tint. A discarded card is left
out, as the canvas leaves it out. A board of a few cards fills the map's width as a big one does. Until 18
October it sat small in the middle, never drawn at more than a fifth of its size. The part of the canvas in
view is a clear box inside a solid line of the ink, near white in dark, with the rest of the map dimmed, as
the transcript's minimap draws it. Until 18 October it was a light wash of the ink with a quiet edge. Where
the view reaches past the map, the box keeps its size and the map's edge cuts it. Until 18 October it shrank
to the part inside the map. Where it would reach past the map on every side, as after Fit all, the map draws
the view's box whole with the board inside it as the canvas shows it. Until 18 October the whole map was
washed over, with no edge to say where the view was. A click on the map glides the view there, and the place
clicked comes to the middle of the canvas. A drag on the box pans the canvas. A click and a drag together
carry on from the place clicked. The wheel over the map zooms and pans the canvas as it does anywhere on it.
The map is drawn again at most once a frame: its box on every pan and zoom, and the rest as cards move. While
a drag lasts, it keeps the scale it had when the drag began and moves only the marks of what moved: what is
dragged, what makes way and the frames that reach out to it. On the drop it is drawn whole and fitted to the
board again (18 October. Until then it wrote every mark of the board again on every frame of a drag).

The transcript's one setting rules it: Minimap's Auto, On or Off, the status bar's button on the statements
screen (a click takes Auto, On and Off in turn, and a right click or a held press opens their menu). In Auto
the map appears as you pan or zoom, by the wheel, a drag, the zoom bar or Fit all, and as a board opens. It
stays while the pointer is on it or a drag on it lasts, and fades out about two seconds after. On keeps it
there, and Off leaves no map and no button. In Auto and On its button at the end of the zoom bar, which shows
the same map as the transcript's button, with "Minimap (M)" in its tooltip, and `M` show the map until
pressed again. While the map shows, they hide it: in Auto until the next pan or zoom, and with On until
pressed again. While the map shows, the button is pressed in, on the sunk paper inside a firm edge, as the
pointer and the hand show the one in use. Until 18 October only its ink darkened, and it read as not pressed.
Whatever the button or `M` said goes when the screen opens again or the setting changes. Below 768px of
window the map and its button go, as tldraw's does below a tablet's width. The export's line opens over the
map. Below about 900px a sidebar lies over the canvas and stops above the zoom bar, and there the map gives
way while the sidebar is open. At first its foot showed in a strip under the sidebar's.

The shortcuts card, `?` or Shortcuts on the top bar, has two groups, headed Experiential statements and PETs
and GETs. Under Experiential statements, moving about, the audio and the mouse are small headings, and under
PETs and GETs the mouse and trackpad are. Each row is a key, a key combination or a mouse act that is not
obvious, with a phrase of two to six words in the small sans. The phrase sits on one line where the card has
room and wraps where it runs short, with its key whole beside it, as in "g · Group the selection" and "Option /
Alt + wheel · Pan up and down". Until 17 October, later, a phrase never wrapped, and a longer one ran out of
the card. A feature with no key of its own has no row, and neither has a plain click or drag. Since 5 October
2026 (item 190) the card also lists the mouse acts. These are the wheel and the pinch, the sideways wheel,
Shift and Alt with the wheel, the middle button, the double-clicks on a card, a label and the canvas, and the
right-click. On the statements screen they are the timecode's click and double-click, the text's
double-click and the row's menu. Over this screen the card shows the PETs and GETs group alone, with the
general row that still applies there, `?` itself, and none of the transcript's rows. There a double-click on
a card edits its statement (30 October. From 16 October it read "Go to its passage"). Over GETs it says a
statement's passage or another card's Inspector, as it does there (16 October). Over Experiential statements it
shows both groups.

**Motion.** Movement here has weight you can see, in the register of the Finder and the iOS home screen, and
nothing is bouncy or slow. A card or a PET you pick up lifts, by four per cent with a deep shadow over 120 ms.
While you drag it, it leans into the way it travels, up to six degrees at full speed, and stands up again
when the pointer stops. A PET dragged by its label or its frame carries its cards with it. Every card leans
the same way as the label, so the whole PET tilts as one body, and the cards trail the label by 140 ms. A
card dragged on its own leans the same way. So does one dragged out of the PETs board's sidebar or the GETs
Participants panel (21 October). It lifts as it leaves its row, sways with the pointer, and lands where you
let it go, as a card dropped on the canvas does. Several rows dragged together come as a card each, laid out
as they will land and leaning as one. While it is dragged, it leans a step each frame with the pointer and
eases only as it stands up. The trail is worked out each frame too. Until 18 October each was a transition
that WebKit, the engine of the Mac window, began again on every move of every card. That held a drag there to
30 frames a second on the demo's board and 8 on a crowded one. Since 13 November a drag keeps the screen's
pace in the Mac window on a large board too. Before, the whole board on screen was drawn again on every frame,
so on a board of about a hundred cards laid out square it fell well behind and the lean moved in steps. A PET
dragged by its title, or several cards at once, keeps that pace too. Whatever is dragged moves an even step
from frame to frame. Before, it went short and long with the mouse's own timing. On the drop it lands over
220 ms with a visible overshoot. It comes down to its own size and stands up from its lean as it lands, so a
drop has settled inside 250 ms. A card or a PET pushed clear by the margin slides to its new spot over 240
ms and does not jump. So do the cards an Auto-arrange gathers. One that makes way for a drag slides aside
over about 160 ms (see Nothing overlaps). All of it rides on CSS transforms. Nothing in it waits on the
layout or delays a save. With reduced motion set in the system, all of it is off. A drag takes one step a
frame, to the pointer's latest place, however many moves the system sends in that frame. While it lasts, the
board's map moves only the marks that moved (see The minimap).

**Nothing overlaps.** Every card, every label and every frame has a margin round it, and nothing else comes
to rest inside that margin. It is one constant, a twentieth of a card's width, 10px on a 200px card: `MARGIN`
in `themes.py` and `TH_MARGIN` in the page. It is the space in the first pile, round a drop, a nudge, a card
put back, a new card, the AI's layout and an arrange. The rule holds between neighbours. On the canvas the
neighbours are the cards in no PET and the PETs, each PET counted by its frame. So a PET's frame keeps the
margin clear of every other PET's frame and of every card in no PET, and the margin between two frames is the
same one. Inside a PET the neighbours are its own cards and its sub-themes, each sub-theme counted by its
frame. So a sub-theme's frame keeps the margin clear of the PET's own cards and of the frames of the
sub-themes beside it, and the same holds inside a sub-theme. A label stands inside its own frame, so a label
and what it holds never count against each other. Nothing inside a frame counts against what lies outside
it, because the frame stands for all of it there. A card in no PET is never inside a frame without belonging
to it. If you let it go in a PET's body, it comes into that PET (19 October), and one that a push leaves
inside a frame joins that PET. A sticky note is a neighbour as a card is. It is on the canvas while it is in
no PET, and otherwise inside the PET it sits in, whose frame runs round it. A note in no PET that is left
inside a frame comes into that PET in the same way (see Sticky notes).

Whatever you drag, a card, a sticky note, a selection, a PET with all it holds or a sub-theme, no PET or
sub-theme moves out of its way (31 October, design A, Adam's choice after the drag audit). Before, a PET you
aimed at ran from the pointer. Only what is inside the PET, sub-theme or group whose body is under the
pointer makes room, and only where a drop would land in it. Its own cards and notes make room, each one that
comes inside the margin of what is dragged. A card or a note is measured by its box, a selection by each
member's box, and a PET or a sub-theme by its frame. Each slides clear by the least distance over about 160
ms. It never slides onto a sub-theme of the PET or onto its title. It pushes a third item as a growing frame
does (below). The sub-themes in it hold still, and every title on the board stays where it stood, so a title
never runs from the pointer. What makes room follows the drag live. The app works it out each frame from
where everything stood when the drag began, so an item the drag moves away from slides back to its own spot.
On the open canvas nothing makes room. What you drag lands exactly where you let it go, and what made room
stays where it went. The drop then settles the rest. A frame that grows sends clear what it reaches, and that
slides there over 240 ms, so nothing overlaps. This includes the frame of a PET a member was dragged out of.
The whole drag is one step of undo: what was dragged, all that made room and all that the drop sent clear.
Esc during it puts everything back. A drop on a title strip takes what is dragged one level under that title
(see PETs). While the pointer is over it, that PET's frame is outlined in its tint and nothing moves, and the
drop makes room for it. If you let go in a body, what is dragged goes into the PET, sub-theme or group under
the pointer at the line shown, and keeps its level. Statements and notes go into the innermost one
(statements since 19 October). A sub-theme goes into the PET, a group into the sub-theme, and a PET into none
(31 October). While the pointer is in such a body, that body is outlined in its tint and its title tinted. It
stays where it is, its own cards make room, and what is dragged shows that it is leaving its own. A member
let go on the open canvas, or in its own PET, stays a member unless you hold Alt (see PETs). Each frame that
holds it reaches out to it, and pushes nothing until the drop. With reduced motion set, what makes room moves
without the slide. You can drag a PET, a sub-theme or a group up to its neighbours in its own place, such as
the last sub-theme of a PET to the ones above it. It then stops a margin from them and lands there, and none
of them moves (26 October). While it meets them only by a little, it rests at that small, even gap. If you
pull it further over one, it lies over it until the drop settles the two. The line that shows where a drop
comes in a theme's order shows only when the drop changes that order or brings something in. A frame can grow
because a card joined its PET, because a card inside it was moved to its edge, because its label was renamed
longer or took a note's mark or a pick's mark, because a sub-theme was made or moved inside it, or because it
was arranged. (A pick's mark counts since 17 October, later, when a picked quote could take a title onto one
more line and over the card above it.) A frame that grows stays where it is. A neighbour it comes near shifts
clear by the least distance: a card on its own, and a PET or a sub-theme as one block with all it holds. A
neighbour pushed into a third item pushes that one too, for eight passes at most, and then it stops. A PET's
frame follows whatever moved inside it and sends its own neighbours clear in the same way. All of it is
inside the one step of undo of the act that caused it. A statement edited on the canvas that takes one more
line settles the same way. Its card moves clear of what it comes to rest on, and its frame sends its
neighbours clear (17 October, later). Sometimes a board was laid out where its words or its type stood at
another size. Examples are a line read again on open, or a PET retitled in its participant and taken in on
GETs that takes one more line, or a board from another computer, an agent or a hand. Such a board makes room
once the page has measured it, on opening and once the type has loaded. A card or a note resting on a PET's
or a GET's frame, including its title, goes to the nearest free spot clear of it. Of two frames, the second
moves, as a drop there settles, so a title never stands over a card. Nothing is written until the next act
(17 October, later). Since 31 October two cards or notes too near each other make room in the same way. This
happens on opening, on taking a change made in a conversation and on a reload, at Quotes Off, Short or Full.
The one that reads first stays where it is, and the other moves clear, as when a card is dropped there,
pushing on what it then meets. So a card that an agent gives longer words no longer stands over the card
under it until you drag it. An agent's own changes make the same room before they are saved, using the
server's sizes. What a change moved, made or made taller stays, and what it comes near moves clear by the
least distance. This happens after every `board apply`, after `turn write`, after Find and replace, and on the
other boards that an edit on the canvas reaches. A card put back from the pile, and a new line read since the
board was made, take the nearest free spot to the middle, clear of every frame. The page measures sizes. The
server estimates them for a layout made before the page has drawn: the first pile, a new line, an AI proposal
and a copy. The server's estimates come from the widths of the page's own type. Each is a little over the
page's and within a margin of it, so a layout the server makes needs no shift when the page draws it. A
note's estimate still makes room for the square it was before it fitted its words. So it runs wider than the
page draws it, and a layout the server makes still needs no shift. Since 17 October, later, a label's estimate
is its title and its marks alone. Before, it made room for the count it showed before the badge, a line more
for a title that filled its line, so Rowan's and Mabel's boards in the demo were laid out again from their
source. A revision on view is read-only and shifts nothing. A board saved before this keeps the spacing it
had until something there is moved.

**PETs.** Select cards and press `G`. A label appears above them with a box for its title. Enter keeps what
you typed, Esc keeps the title it had, and a title left blank is Untitled. Group on the bar does the same (16
October). The cards then belong to that label. Membership is stored, and never read off where a card sits. A
label sits above what it holds, with its left edge on theirs. It follows them as they move, and shows its
title alone. Its count is a small badge on its frame's bottom edge at the left corner. The badge gives the
number of its statements at any depth, or 0 when it holds none. It is in the small sans, not bold, in the
PET's tint for its text and its outline, with its corners rounded as the frame's are. Its figures take the
PET's own tint a third of the way to the ink, so they read in both themes. Before, a sub-theme's lighter step
and the paler tints read faint. Its outline keeps the step (17 October, later). On a card inside a PET or a
GET, the timecode and the count of statements stand in the soft ink, which reads on every tint's wash in dark
(17 October, later). Half of the badge lies in the frame's padding and half in the margin beyond, so it never
covers a card, and it never takes a click. A badge that would lie over a sub-theme's badge at the same corner
steps right past it. A label with nothing in it draws no frame and so no badge. The label's tooltip and the
Inspector keep the full words: "3 statements", on a PET over sub-themes "2 sub-themes · 7 statements", and on
a sub-theme or a group over groups "2 groups · 7 statements". They count the labels it holds itself and the
statements at any depth. Every PET draws its frame, a faint rounded rectangle in its tint round its label and
its members. The frame follows them wherever they go. A frame that grows into a neighbour stays where it is
and sends the neighbour clear by the least distance (see Nothing overlaps). The PET's cards take its tint, as
a wash and a rule down the left edge. The tints never repeat. PETs take eight in turn, each its own. A PET
keeps the one its number gives it while no PET before it holds that tint. A PET past the eight is a neutral
grey, so no tint already in use repeats. A sub-theme takes its PET's tint a step lighter, and a group a step
lighter again. None of them is the crux orange.

Drop a card on a PET's title strip, its label, and it joins that PET. The same works on a sub-theme's or a
group's strip at any depth. What you drag goes one level under the title you let it go on. A sub-theme goes
into that PET, and so does a PET, which becomes its sub-theme. While the pointer is over a strip that a drop
would merge into, the strip lights in its tint and reads "Merge into" and its title. Its frame is outlined in
its tint, and the drop makes what is dragged a member there. No title moves while a drag lasts (31 October),
so the strip stays under the pointer. From 19 October the place where a strip stood before it moved aside
took the drop, and that has gone. In a body, a line in the tint of the PET, sub-theme or group it goes into
shows where it comes in the order that one reads in (see Higher is better). The line stands in the gap beside
the statement it comes before or after, or lies across the gap between two rows. Statements and notes let go
in a body move into the innermost PET, sub-theme or group the pointer is in, at that line, at every depth (19
October, Adam on the shots. Before, one let go in another PET's body went back into its own). Since 31
October a sub-theme let go in a PET's body goes into that PET, and a group goes into the sub-theme it is let
go in, keeping its level. A PET let go in another's body only moves. On the open canvas each stays in what
holds it. Undo is as it was. Drag a label, and everything it holds moves with it. A drag that starts on the
empty space inside a PET's frame, off its cards and its label, does the same. A click there selects the PET,
as a click on its label does. Double-click a label to rename it. The box keeps the title's width and wraps as
the title does, as tall as its words, so you edit a long title whole. Enter keeps it, and Esc leaves it as it
was. Leaving a PET is an act of its own. A member you drag anywhere stays a member, and its frame stretches to
follow it live, during the drag and not only on the drop. So a card taken far shows its frame reaching out to
it. A sub-theme dragged inside its PET stretches that PET's frame in the same way. A frame stretched like this
pushes nothing while the drag lasts, and the drop sends clear what it reaches (see Nothing overlaps). A card
or a sub-theme leaves its PET in five ways. Backspace or Delete with it selected, or Take out of PET in the
Inspector or in its right-click menu (Take out of sub-theme when a sub-theme holds it), leaves it where it
stands without the tint. A drop with Alt held (Option on a Mac) takes it out and leaves it where it lands. A
drop on another PET's title strip or in its body moves it to that PET. For a card, a drop on the sidebar also
works. While you hold Alt during a drag, the frame lets go of what is dragged and it loses its tint, so the
leaving shows before the drop. Alt joins nothing (31 October). With Alt held, no title, body or card's middle
takes what is dragged, whether it is a card, a sub-theme or a PET. It leaves the PET it was in and lands where
you let it go, and no strip says Merge into. Until then a card let go with Alt on another PET's strip joined
it. Each is one step of undo, and the drop settles clear what it lands beside or over (see Nothing overlaps).

While you drag a card in a PET, or a sub-theme, a small tip follows it a little below and to the right of the
pointer, in the small type on a quiet chip. It reads "Hold ⌥ to remove from PET" on a Mac and "Hold Alt to
remove from PET" elsewhere. With Alt held it reads "Release to remove from PET". When a sub-theme holds the
dragged card or sub-theme, it says sub-theme in place of PET, as in "Hold ⌥ to remove from sub-theme". It
says group when a group holds it. It never shows for a card in no PET or for a PET dragged by its own label.
It goes the moment the drag ends, and nothing about it is saved.

A right-click on a card or a label, or inside a frame for its label, opens a small menu for that one item, in
the style of the statements screen's row menu. It holds Take out of PET when the item is in one, or Take out of
sub-theme or Take out of group, by what holds it. Then on a label come Auto-arrange, Rename and Note (see PET
notes). Then comes Set aside on a card, with X at its right, and Delete this label on a label. Esc puts it
away, and so does a click anywhere else. The same menu opens from "⋯", a small round button on a selected
card's top right corner, clear of its words, as a selected sticky note shows its cross. On a label it is at
its top right corner, beyond its cross, and shows with the label's other small controls. So nothing there is
reached by the right-click alone (16 October). Since 13 November a label's small controls come and go with
nothing else on the board moving. Before, in the Mac window, every outline and word on the board shifted a
little for a moment each time the pointer went into or out of a PET's or a sub-PET's label. Until 17 October,
later, the "⋯" on a label stood in the title's line and took a long title's room there, so a GET's title
wrapped onto one more line than its board leaves it. The entries that take something away, Delete this label
and Delete note, are red with a bin, as every Remove and Delete is. Take out of PET, of GET, of sub-theme or
of group is a move. It was Remove from PET until 20 October, when a tester read its bin as binning the card.
Since 20 October the card goes back to the sidebar's Unplaced, with `Backspace` at its right, beside where it
stood. The entry shows an arrow out of a frame in the ink.

**Group and Ungroup (20 October, from a tester's feedback).** A right-click on a card offers Group. It does
what G does with what is selected, or with the card alone when it was not selected. It offers Ungroup when
the selected cards are the whole of one PET, GET, sub-theme or group and nothing else. Ungroup deletes its
label and keeps the cards where they stand, as Delete this label does. Each is one step of undo.

**Auto-arrange.** The small grid beside the cross on a label, and the entries in the Inspector and in its menu,
all read Auto-arrange. They tidy the PET's cards under its label into a compact block. The rows are about as
wide as the square root of what is in the PET, with the margin between them. The cards keep the order they
read in now, top to bottom, with ties broken left to right. Each sub-theme is arranged inside its own frame
first, and then set in the block as one piece where it read. The label stays where it stands, and so does the
PET. A neighbour that its new frame comes near shifts clear by the least distance, as it does for any frame
that grows. It is one step of undo.

Since 21 October Auto-arrange has three ways, each with its icon. Grid is the block above. Column puts one
card above another in the order they read down the PET, which keeps its hierarchy: each sub-theme stays whole
as a block in its place and is arranged the same way inside. Row puts them all side by side. On the toolbar a
click on Auto-arrange repeats the last way, and the button shows that way's icon. Its small arrow opens the
three, with the last one ticked. A choice runs at once, and this computer keeps it for the button. The
toolbar's Auto-arrange tidies each selected PET or label, or the one a selected card is in. With nothing
selected it tidies every PET on the board, in one step of undo. The control on a label and its menu entries
take the last way too.

Since 12 November a Grid lays a PET's sub-PETs out in rows across it, and never one under another in a single
column. Auto-arrange on the toolbar with nothing selected lays out the whole board. It tidies each PET inside,
then sets the PETs themselves side by side in rows, starting from where the top-left PET stood. The board ends
up about as wide as a 1280 by 800 window. Statements in no PET keep their places. They move together below the
PETs only when the PETs would reach them. Everything stays in the order it read: the first PET at the top
left, then left to right, row by row, and the same inside each PET and each sub-PET. So the Table view and the
exports read exactly as before. Its undo step reads "Arranged the board". A board that Claude or another
agent builds comes out laid out the same way, and the agent can tidy a whole board with the same arrange.

**Higher is better.** Inside a PET, higher means a better example or better quotes. So the canvas reads top to
bottom, and left to right along a row. Statements whose tops sit within half a card's height count as one row.
The PET draft, the print view, the Word document and the CSV list a PET's statements in that order. They put a
sub-theme where its frame's top sits among the cards (see Export, Word document and Print).

Select labels, or labels and cards, and `G` makes a label over them. It is the same object one layer up, and
that is how sub-themes are drawn. A label at the top of the canvas is a PET, a label inside a PET is a
sub-theme, and a label inside a sub-theme is a group. Groups can sit inside groups as deep as you like. The
Inspector, the counts, the menus and the exports name each one that way. A board from before groups had a name
reads the same way, with nothing lost. You nest a PET or a sub-theme in another by dragging it onto that one's
title strip. While the pointer is over the strip, it reads "Merge into" and the title, as in "Merge into
Mornings". The drop makes it a sub-theme of a PET, or a group inside a sub-theme or a group, at any depth. A
sub-theme let go in another PET's body goes into that PET as its sub-theme and keeps its level. A group let go
in a sub-theme goes into it. A PET let go in another's body, or beside it, only moves (31 October). Nothing it
passes moves out of its way. The strip says it the moment the pointer is on it and stops the moment it leaves,
at the drop. It also says nothing over the strip of the theme that already holds all that is dragged, because
nothing would merge. Until 18 October a PET or a sub-theme nested wherever the pointer was more than the margin
inside another's frame, under a large Merge across that frame. A sub-theme stays in its PET wherever you drag
it on the open canvas, until Take out of PET in the Inspector takes it out. Cards that all sat under one label
make a label inside that one, in their place, so a sub-theme drawn out of a PET stays in it. A label never goes
inside a label it holds. Select a label and press Backspace or Delete, or use the small cross on it, and the
label goes. What it held stays on the canvas, in the label above it where the deleted one stood, or standing
free. Nothing else is lost. With cards and labels selected together, Backspace does both in one step.

**The sidebar: Unplaced and Set aside (20 October, Adam's way A).** The bin went on 20 October. A tester had
said that PETs had two places for what is off the board, the Unplaced pile and the bin, while GETs keeps what
it has unplaced in its Participants panel. The PETs board now has a sidebar of its own at the left of the
canvas, as GETs has. Its button, Statements, is at the left end of the bar. It is the panel icon with its left
part filled, pressed in while the sidebar is open, with the count of statements waiting beside its name. The
sidebar's cross sits at its head, then a search over its statements, then two sections. **Unplaced** holds the
participant's statements that are not on the board, in interview order. Each shows its time first, and a
sheet after the first shows under its own name. The count is at the right of the section's head. A stack waits
as one row at its top's time, with "2 stacked" under it. A statement whose line has gone from the workbook
comes last, under Missing from the workbook, with Remove. If an agent left a statement out with a reason, the
reason is under it in the small type. So is the reason for one a New AI board left out before 11 November
2026. **Set aside** is pinned to the panel's foot and folded until you open it. It holds what the bin held,
each with Put back, which sends it to wait in Unplaced. Its count is at the right of its head. Every board from
before opens with its binned cards under Set aside, and the file keeps them as it did.

The canvas holds only what is placed. You can drag a row of either section onto the canvas. If you let it go
in a PET's body or on its title strip, it goes into that PET. If you let it go on empty canvas, it lies there
loose, on the board but in no PET yet, ready to be grouped, as slips lie on a table. Rows select as the Table
view's do: a click, Shift for a run and Cmd for one more. The selected rows drag together. The first is under
the pointer with the number being dragged on it, and the rows stay as faint outlines while they are in the
air. If you let go back over the sidebar, or press Esc, nothing changes. Put all on the board, under
Unplaced's head, puts every waiting statement on the canvas as one pile in the middle of what is in view. That
is Adam's own way of starting ("chuck all on the canvas"). A card dragged from the canvas onto Unplaced waits
there again, and one dragged onto Set aside is set aside.

Take out of PET in a card's menu and `Backspace` send a card back to Unplaced, at its own time in the order. The
row lights for a moment, and the list scrolls to it. On a card loose on the canvas, `Backspace` and Back to
Unplaced in its menu do the same. `X` and Set aside in a card's menu set it aside, and Set aside's head lights
for a moment when it is folded. A stack's top taken out takes its stack with it. Set aside is never emptied,
and nothing on this screen deletes a statement. The menu shows each entry's key at its right, Backspace and X.
On the status bar "5 unplaced" and "1 set aside" open the sidebar on their section. "3 in no PET" counts the
cards loose on the canvas, and shows only when there are any. Below about 900px the sidebar lies over the
canvas. At a phone's width it is a sheet over the board, its whole width.

**A new board offers both starts.** The board menu's New holds two choices. New board, empty, leaves every
statement waiting in the sidebar. New board, all on the canvas, puts every statement on the canvas as a pile in
the middle, in no PET yet. A participant's first open starts empty.

**Select all.** `Cmd + A` (`Ctrl + A` on Windows) selects every statement on the canvas. In the Table view it
selects every statement the view lists. After a click on a row of the sidebar, it selects every row of that
section. Select all on the palette, under Group, does the same as the key on the canvas.

**Group, stack or set aside.** Most statements go into a PET, grouped with the ones they belong with. When a
participant says one point several ways close together in the transcript, stack the others under the
statement that says it best, which stands for them. Set aside is for a statement with a reason to go: it does
not answer the research question, it is badly evidenced, or it is irrelevant in some way. Setting one aside is
rare, so record why (Adam, 19 October). It can always come back. The Guidance tab says the same.

**Stacks (19 October).** A stack is statements under a better one, the top. The top stands for them in the
PETs table and the exports, and the others stay one click away for the audit trail. A stack is not a PET and
not Set aside. A top shows paper edges under it, one for each statement stacked under it. So a stack of two
shows one edge and a stack of five shows four. Past five it shows four, with a small plus on the corner where
they end (19 October, later). Its count is on its foot, "3 stacked". To stack a statement under another card,
drag it onto the middle of that card. The card shows an outline while the dragged one is over its middle, and
the card you drop onto is the top. A drop nearer a card's edge moves as any drop in a body does, and a title
strip still merges. Or select the statements and press `S`, and they stack under the highest of them, because
higher reads as better. The right-click menu on a card with others selected has Stack the selected statement
under this one (or Stack the 3 selected under this one), which makes that card the top. While a drag is over a
card's middle, the tip about Option or Alt goes, because the drop stacks. A stacked statement leaves its PET,
Unplaced or Set aside. After that it goes wherever its top goes, into a PET, Unplaced or Set aside. A top
stacked under another brings its own stack with it, so a stack is one level deep. Copy to board brings each
top's stack with it. When an agent makes a board that keeps another's layout, it keeps that board's stacks.

The count on a top's foot, Show stack in its menu, or `S` with only the top selected, opens the stack in place.
Its statements stand under the top, a little in, each a card like any other, with a rule of their tint down
their left, and Stack again under the last. What stands below moves down to make room, and the PET's frame
grows round them. Each card of an open stack opens its statement for editing on a double-click, shows its
quote in the Inspector, and has its own menu, Make this the top and Take out of the stack. Make this the top
puts it in the top's place, with the old top first under it. If you drag a card out of an open stack onto the
board, it lands where you let it go, out of the stack, as any card does. Take out of the stack leaves it
straight after its top in the top's PET, in the order the PET reads, and the others move along to make room. A
stack opened near the foot of the canvas glides up until its last card is clear of the zoom. Stack again, the
count, `S`, or Esc with nothing selected stacks it again, and what moved down moves back up. Opening a stack is
a view. It changes nothing, has no step of undo, and the board saves as if it were shut. Every stack, take out
and Make this the top is one step of undo. The PETs table, the Word document and the PET draft show the top
alone unless Include stacked statements is ticked under Export (see Print). The statements CSV lists every
statement, with a stacked one straight after its top and "Stacked under:" and its top's words in the Proposed
PET column. The counts on a label and a PET's badge count the tops alone.

**Sticky notes.** Sticky notes are your notes to yourself on the canvas, as Miro's post-its are: "not sure
about this", "merge with group 4", "think about splitting this one". A sticky note is never a statement and
never becomes one. A double-click on empty canvas puts one there, yellow, with the caret in its words. So does
New sticky note, the one entry of the menu that a right-click on empty canvas opens, in the row menu's style.
Since 18 October Sticky note on the PETs and GETs bars puts one of the canvas's own in the middle of the canvas
in view, clear of a sidebar lying over it. It settles at the nearest place clear of every PET and card, as a
card dropped there does. A double-click on the empty space inside a PET's frame puts one in that PET. Enter
keeps the words and leaves the box. Shift + Enter starts a new line. A click away keeps them too. Esc on a note
with no words takes the note away. Making a note and its first words are one step of undo. A double-click on a
note opens its words again. A note fits its words. It is as wide as they run, 64px at the least and 160px at
the most. Past that they wrap and the note grows down. It is as tall as its lines, with no square to fill and
no inner scroll, so "Yeah this needs a look" makes a small slip. It fits them as you type, and every measure of
the spacing takes the size the page measures on it. A new note settles with the room its words will take: the
widest a note runs and three lines more than it has. So it never comes to lie over a card as you type. If your
words outgrow that room, the note alone moves clear again. Until 18 October a new note made beside a card could
grow over it until its words were kept. A note already there whose words grow over a card as you type moves
clear in the same way, with room to grow. Until 18 October it moved only once its words were kept. It has a
slight paper shadow and no border. It comes in four soft colours, yellow, pink, green and blue. They are tokens
of their own beside the PETs' tints, none of them is a tint, and they read in both themes, light and dark. The
words are set in a handwriting face from the system: Bradley Hand on a Mac, with Noteworthy, Segoe Print,
Segoe Script and Comic Sans MS after it. So nothing is downloaded and no font file ships. The ink is a dark blue
that reads on all four colours. The words are about a card's size, and they zoom with everything else.

On the canvas a note behaves as a card does. It drags, keeps the margin, sends and is sent clear, falls in a
lasso, joins the selection with Shift or Cmd, and lifts, leans and lands, with reduced motion as for a card.
Dropped on a PET's title strip, it comes into that PET and rides with it, and the frame stretches round it. A
drop with Alt held, Backspace with it selected, or Take out of PET in the Inspector or in its menu takes it out
again and leaves it on the board. With cards and notes selected together, `G` groups the cards, and the notes
come along inside the new PET. A note is never a member, so it is never counted. "3 statements" stays "3
statements" in the tooltip with a note inside, and the badge keeps its 3. Auto-arrange sets a PET's notes at
the end of its block. A deleted label leaves its notes in the label above it or standing free, as it leaves
its cards.

A note selected alone shows its four colours in a small strip just under its bottom edge, with its own colour
ringed. One click there recolours it. The strip zooms with the canvas and sits clear of the cross on the top
corner. It goes while the note is dragged or its words are open, and when the note is no longer selected
alone. A right-click on a note offers the four colours too, with its own ticked, Take out of PET when it is in
one, and Delete note. The Inspector has the colours as dots. A colour change from any of the three is one step
of undo. Delete note, or the small cross on a selected note's corner, takes it off the board. One step of undo
brings it back where it was, in the PET it was in. The sidebar is for statements alone. A note never goes
there, and one dragged onto it goes back where it was, as a label does. A note goes nowhere a statement goes.
It is not in the counts, the PET draft, the CSV's PET column, the print view, the outline that the print view
and the titles share, or anything sent to a model. A board an agent makes starts with none. The notes are the
board's `notes` in the themes file (see Autosave and the file). A page in front of a server from before them
says "Restart the server to finish this update." on the double-click and makes none.

**Undo.** On this screen `Cmd + Z` and `Cmd + Shift + Z` have a stack of their own, separate from the
statements screen's. A move is a step on it, one for each drag of a selection, ending where the drag settled.
So are a label made with its first title, a card joining a label or taken out of one, a rename, a PET's note
kept, an Auto-arrange, a label deleted, and a card discarded, put back or removed. So are a quote picked or
unpicked, and a sticky note made with its first words, its words changed, its colour changed or the note
deleted. So is a statement edited in place, whose undo and redo write the workbook (see Editing a statement). Undo on the
bar takes back the last step as `Cmd + Z` does (16 October). Each board keeps its own stack, so if you switch
to another board and back, you find its steps where they were. The stacks are held in memory for the
participant open here, and they go when PETs opens on another participant. A step undone or redone is saved
like any other act. The board ops below are not steps on it. They change the file at once, and a delete asks
first. A restore, and a copy onto the board on screen, are one step each (see Copy to board and History).

**Boards.** When you try one grouping side by side with another, each is a board. The board's name in the top
bar is a switcher, in the sheet switcher's style. It shows the name and a small chevron, and a click or `V`
opens the menu under it. The menu lists every board by name. The board on the canvas is ticked, and the
Current board has its mark after its name (see The Current board). Each has its note under it, the board on
the canvas too. The note is cut to two lines, with the whole of it in its tooltip and in Edit the note. A
click on another board switches to it. The canvas saves anything still to save, and the file records the new
board as the board on the canvas, `current`. That is all a switch writes. The board comes on with its cards in
view (30 October). If the view shows any of that board's cards, it stays where it was, as between a board and
its duplicate, so you can compare two boards laid out alike in one place. Otherwise it goes back to where you
left that board since the participant was opened. Otherwise it fits the board, as an opening does. Until then
a switch kept the view of the board you left, which could open the next one on blank canvas. The board that
comes on after Delete this board does the same. The entries come in two groups, each under a small kicker in
the style of the menu's BOARDS heading. Under the list comes the board on the canvas by name, "BOARD 1", with
what it can do: Rename, Add a note (which reads Edit the note once the board has one), Duplicate, Mark as
current or Unmark current, Save a revision, and Delete this board last. Then comes a hairline, and under NEW
the entries that make a board. New board, empty, adds a board with no PETs, with every statement waiting in
the sidebar. New board, all on the canvas, adds one with every statement on the canvas as a pile in the
middle (20 October, see The sidebar). Duplicate adds a copy of the board on the canvas, with its groups,
places, discards, picks and sticky notes. It is the natural way to try another grouping. Either goes on the
canvas at once with its name, "Board 3" or "Board 1 copy", open in the menu for you to type over. Enter keeps
the new name, and Esc keeps the one it had. Rename opens the same box on the board on the canvas. If another
board has that name, whatever its participant, the menu refuses it with a line. Add a note opens a box of a
few lines in the note's place, for why the board exists. `Cmd + Enter` or a click away keeps it, and Esc
leaves it as it was. A duplicate starts with a note of its own, empty, and a history of its own, empty. Save a
revision opens a box for a name, which may stay empty. Enter or Save beside it keeps the revision, and Esc or
a click away keeps none. Guidance and History are no longer in the menu, because the sidebar's own tabs do
that (see The sidebar). Delete this board shows a card in the trim card's style, "Delete Mornings apart, with
its 3 PETs and the 9 statements placed in them.", with Enter to delete and Esc to cancel. The board beside it,
the one before when there is one, takes the canvas. With one board left, the entry is disabled, and the server
refuses it too. Esc closes the menu, and so does a click anywhere else.

Names are just names. Every new board is "Board N", with the next number free past the boards there are,
whether you made it or an AI agent did through the command line. A name you typed stays as you typed it. After
the name of a board an agent made, a small faint "with AI" follows, in the board menu and in the participant
switcher under each participant. Its tooltip names the tool and its source, the board on the canvas when it
was made, as in "Claude Code in a conversation, from Board 2". The board keeps its state hash as it was made.
Your first save whose state differs from it adds "edited by you since" to both the words and the tooltip. A
save that changes nothing leaves them as they were. A name from before stays as it is, including "AI board
3". A board that New AI board made before 11 November 2026 is an ordinary board now and has no "with AI". A
duplicate is yours and has no "with AI".

**The Current board.** You can mark one board as the one you are going with, the one to send a supervisor. On
screen the word is Current. Mark as current, in the board menu, marks the board on the canvas. On the Current
board the same entry reads Unmark current and takes the mark off. There is one Current board at most, so
marking another moves the mark. The menu shows a small ribbon after the Current board's name, with the word
Current in the small type. While the board on the canvas is the Current one, the switcher in the bar shows the
same ribbon beside the name, with "the Current board" in its tooltip. The print view says "Current board"
under the board's name (see Print). Deleting the Current board takes the mark with it, unless one board is
left. That board then takes the mark as the only board to go with. With two or more left, the mark goes
nowhere and nothing is said. A duplicate never has it, and a file that has only ever had one board marks
nothing by itself. The mark is set and cleared through the board ops `choose` and `delete`, never by the
autosave, and nothing on the canvas changes with it. A page in front of a server from before it says "Restart
the server to finish this update." in the menu. A page from before the last board took the mark leaves it off.
The participant's card names the Current board on its PETs half, and its row under Files names it in its small
type (see Open a participant).

Grouping the statements into PETs is the participant's second phase, and the Current board is where it ends.
Mark PETs complete, the last entry of the board menu, after a hairline under NEW, marks the phase complete on
the Current board, with the PETs in their final shape. It is there while a board is marked Current, whichever
board is on the canvas. With none, it is disabled, with "Mark a board as current first" in its tooltip. It
records `complete` at the top of the themes file, `{"at": "<iso time>", "board": "v3", "name": "Board 3"}`,
through the board op `complete` and never by the autosave. It fires the third level of confetti once, through
the same call the participant-complete card makes. The menu then shows a small tick in the app's green, PETs
complete and the date, "4 Oct 2026", under the name of the board it was marked on. The same entry reads Reopen
PETs, with the time and the board in its tooltip, and takes the record off through the board op `reopen`. The
mark names the board it was marked on. So unmarking or deleting the Current board leaves it as it stands. It
shows the board's name now while the file holds that board, and the name it had when it was marked once it is
gone. Marking PETs already marked keeps the first time. Nothing about the mark locks anything, and you can
still change every board. The cards and the rows under Files read it from the themes file (see Open a
participant). The print view said it under its head until 31 October, when Adam asked for the line to go.

**Copy to board.** A right-click on a label, or inside a frame for its label, offers Copy to board…. It lists
the other boards of the participant by name in the same menu, and a click on one copies the PET there. A
statement is on a board once, so nothing is duplicated. On that board every statement under the PET, at any
depth, leaves whatever PET holds it, and comes out of Set aside if it was set aside there. A PET there that
loses every statement goes, and so does a PET above it that is left with none. One that loses some keeps the
rest. The PET arrives as a fresh one, with its title, its sub-themes in the same shape and its picks. It is
laid out as a round blob, the way an AI board lays a PET out, with its statements in the order they read on
the board it came from. It is set near the middle of that board's cards and four margins clear of every card,
label and frame there. That is the room the AI's layout leaves beside its pile, because a label as the page
draws it can run a little wider than the server's estimate. If nothing nearer is clear, it goes to the right
of them all. Before the copy, the board it goes to keeps a revision, "Before Mornings copied from Board 1", so
it can go back to how it stood (see History). The PET's sticky notes stay behind, because a note is your own
word to yourself on the board you wrote it on. The notes of the board it goes to stay as they were. A note
whose PET the copy empties stands free. The canvas stays as it is, and one line says "Mornings copied to Board
2". While a revision is on view, the menu also offers the board it belongs to, first, as "Copy to Board 1".
That brings a PET of the revision back into the board itself, and the board's revision is then named "Before
Mornings copied from Board 1 at 12:04". The canvas leaves the revision and shows the board with the PET in it,
and the copy is one step of undo there. With one board and no revision on view, the entry is there and does
nothing. The server does the copy, so the file never holds half of one.

**The sidebar.** One sidebar at the right of the canvas holds what is about the selection and what is about the
board, as Figma keeps its properties on the right, one tab at a time. The tabs come in this order: Inspector
(see The Inspector), about the selected card or label, then Guidance (see Guidance) and History, about the
board as a whole. Each of those two stands under the board's name and its note. Its button, Inspector, is at
the right end of the top bar over it. It is the standard panel icon, a frame with its right part filled. It
opens the sidebar on the tab left showing and closes it again, with "Show Inspector" or "Hide Inspector" and its
key, `I`, in its tooltip. It is pressed in while the sidebar is open. Until 16 October it was named Sidebar and
stood before the cog, with "Show the sidebar" or "Hide the sidebar" in its tooltip. A tab at the sidebar's head
shows that tab. `I` outside a field opens it on the Inspector, and closes it again while it shows the
Inspector. Inspect, the first entry in a card's and a label's right-click menu, opens it on the Inspector for
that item, on a revision on view too. Nothing at the edge of the canvas opens it, so when it is closed the
canvas runs edge to edge. A click on a card or a label selects it and never opens or switches the sidebar.
Neither does a lasso or a drag. So a selection made with History showing leaves History showing. A
double-click still opens a card's statement or a label's title for editing. Note in a label's right-click
menu, `N`, and an undo or a redo of a PET's note open it on the Inspector. Esc and a click on empty canvas
never close it. A switch to another board keeps it open on the new board. Leaving the screen puts it away
until the next open. The browser keeps whether it is open, and on which tab, for each screen, PETs and GETs
separately, as it keeps whether the statements screen's guidance is open or closed. So a reload and the next
open of the screen bring it back as you left it. None of that is written to the themes file or to
`config.json`. At a desk width it takes a column of its own, 360px wide and the full height under the band,
and the canvas narrows for it. Below about 900px it lies over the canvas and stops above the zoom bar with its
`?`, so both stay in reach with it open. Down to 400px it never scrolls sideways. Its tabs share its width and
keep to one line. Its buttons never take the focus, so `G`, `X`, Backspace and `Cmd + Z` work on the canvas
with it open. Until 5 October 2026 the Inspector and a Board panel with the other tabs were two panels side by
side, each with its own button in the bar, its cross and a handle at the edge of the canvas.

**History.** Each board keeps its history, as a document in Google Sheets does. The history is a list of
revisions. Each revision holds the board's cards, groups, discards, picks, sticky notes and the AI's reasons as
the file holds them. A revision is made in five ways. Save a revision, in the board menu and at the top of the
History tab, keeps one by hand, under the name you type in the box beside it, or none. While you work, the
page's timer asks for one every fifteen minutes, and the save writes it. The first save after a board comes on
the canvas keeps the board as it stood when it came on. After that, once fifteen minutes have passed with an act
since, the next save keeps the board as it stood before that save, under the time of the save. With no act
waiting, the timer saves at once, so a pause in the work still keeps one. The app makes an automatic revision
only when the board differs from its last revision, by a stable hash of the state. A restore keeps one first,
and so does a copy onto the board. So does an agent's change, named "Before an agent's change" (the request
stays in By an agent). The app keeps every revision made by hand, named or not, and every one made before a
restore, a copy or an agent's change. It also keeps the last 48 automatic ones, so a 49th takes the oldest
automatic one away. Deleting a board takes its history with it.

A statement edit keeps one too (30 October, Adam: "Add a History line"). It does so on every board that holds a
card of the statement, whichever screen you made the edit on: the card's box or the Inspector on PETs, a
statement reworded on the statements screen, or a statement's card on GETs, LGETs or LPETs. Each board keeps
itself as it stood before the edit, with one line for the edit. The line names the participant and the
statement's words before and after, as in `Juno's statement edited: "Lost at sea" to "Adrift at sea"`. A long
statement shows the words round the change: three words of what stayed on each side of it, and an ellipsis for
the rest. Each side is cut at a word past sixty characters. The PETs boards are the participant's boards at
the timepoint of the statement's sheet. A GETs, LGETs or LPETs board has the line when it holds a card of the
statement, and not for a PET's card alone. A save on the statements screen that rewords nothing leaves no line.
A statement moved, added or removed there is not an edit of one. An undo of an edit is an edit back, with a line
of its own. An AI agent's write keeps its own line, "Before an agent's change" (the request stays in By an
agent), on each board it changes, and no second line for the same write. A Find and replace leaves none,
because it keeps no board's old words anywhere, including its revisions (see Find and replace).

The history sits in the sidebar's History tab (see The sidebar), under the board's name. The board's note is
under the name in the small type when it has one. The note is read-only there, because Add a note in the board
menu edits it. A switch to another board keeps the tab open on the new board.

History lists the board's revisions newest first, under the day they were made: Today, Yesterday or the date.
Each shows its time and its name, Automatic for one the timer made, or nothing more for one kept by hand with
no name. Each has Restore. Each shows the time it was made, in the order they were made. Until 30 October 2026
an automatic revision took the time the board was last written, and a statement edit did not change that. So
after an edit, a revision could show between two of today's lines under a day weeks back. On a board saved then,
such a revision shows at the time of the revision made before it, the earliest it can have been made, so the
list reads in order. The board's next save keeps that time. A click on a revision shows it on the canvas,
dimmed and read-only, under a line at the top of the canvas, "Viewing the revision of 12:04 · Restore · Back".
Nothing on it moves. A drag lets go. A key or a control that changes a board says in one line that the
revision is read-only, such as a tick, Put back, Rename, `G`, `X`, Backspace or `Cmd + Z`. The lasso, a click
to select, the Inspector and its player, the pile's list, the zoom and the right-click copy on a label all
work. Back, or Esc, puts the board back on the canvas as you left it. The autosave and the timer wait while a
revision is on view. A board op or leaving the screen puts the board back first. Restore, on the line or on a
row, keeps the board as it stands as a revision named for the one restored, "Before restoring 12:04". Then it
makes the revision's state the board's. On the canvas it is one step of undo, and one line says what was
restored and what was kept.

The history lives in the themes file beside the workbook, under each board, with each revision on a line of its
own. A revision of a hundred statements of about sixty characters, in a dozen PETs, takes about 14 KB. So 48
automatic ones come to well under a megabyte. Statements much longer than that, seventy-five characters and
more on average, take a revision of a hundred past 15 KB.

**The Inspector.** The sidebar's first tab is the Inspector, about the selection. While it shows, it follows
the selection: the selected card or label, or with several selected, the one clicked last. With nothing
selected it has no head, because its tab already says Inspector. Under the tabs it reads "Select a statement or
a PET." in the small type. Esc clears the selection and leaves it on that line, and so does a click on empty
canvas. Its head names the thing. A PET shows by its title in the PET's tint, with the whole title in its
tooltip. A statement or a sticky note shows by its kind, Statement or Sticky note, in the kicker's style, the
style the empty head's Inspector is set in. So a statement shows once, whole, in the body under it, and the
head keeps the card's own tooltip. If you go to another tab, or close the sidebar, a note being written there
is kept, as a click away keeps it.

For a card the Inspector shows the statement, its timecode, and under Quote its own quote, the one in its pair
on the statements screen. It shows the row's timecode and a play button, or "No quote for this statement." A
double-click on the statement there opens it for editing in place, as a double-click on its card does. Its
tooltip says "Double-click to edit" (see Editing a statement). From 16 to 30 October that was the one way in,
while a double-click on the card opened its passage. For a sticky note it shows the note's words in a box.
Enter or a click away keeps them, and Esc leaves them as they were. It shows the four colours as dots, with the
note's own ringed, and Take out of PET when the note is in one (see Sticky notes). A label's head says what it
is, PET, Sub-theme or Group, over its count. A card in a PET, and a sub-theme or a group, show Take out of PET
under the timecode or the count, or Take out of sub-theme or Take out of group, by what holds it. The title of
what holds it stands beside it. It takes the item out and leaves it where it stands. For a label the Inspector
shows the quote of every card under it at any depth, each statement's own, row by row in transcript order.
Each row stands under the statements of the cards on it, so a row two cards share is listed once, and the
label's picks are among them. A label over labels has the quotes of all of them.

The play button cues the recording of that sheet at the row's timecode and plays it. It is the file that the
statements screen's player finds through `/api/audio`. The button is in the accent while it plays, the
playhead's colour, and in the ink under the pointer. Until 17 October, later, both stood in the crux orange.
The same button again pauses, a press after that carries on from where it stopped, and another quote jumps
there and plays. The Inspector's player is its own, built from the statements screen's parts. The audio
element is the engine, and at the Inspector's foot are a play button, the elapsed time, a scrub bar, the total
and the file name. It is separate from the statements screen's, so a cue here never marks a passage there.
Closing the sidebar, going to another tab, clearing the selection or leaving the screen pauses it.

**From a statement to its passage (16 October).** The hermeneutic circle runs from the part to the whole and
back. So a statement on the canvas leads to the passage it was drawn from (a tester's ask, Adam's word). Go to
the passage comes after Inspect in a statement card's right-click menu, on the PETs screen and wherever a
statement's card stands on the GETs screen. It opens Experiential statements at the passage that statement
belongs to. The caret is in that statement, and its quote's marks are lit in the passage when it has one. The
passage's start is in view at every width. A passage taller than the column stands with its first line at the
column's head. On a phone, where the fields stand under the column, the page stays on the passage and not on
the field (17 October). Its speaker and time stand below the title bar and the research question under it, as
tall as they stand. Before, at 360, the question's height was left out and they stood under it (17 October,
later). It stands there on a revision on view too, because it changes nothing on the board. A double-click on a
statement's card did the same from 16 to 30 October, on the PETs screen and on the GETs screen. Since then it
opens the statement for editing on the card, as a title opens, on the GETs, LGETs and LPETs boards too (see
Editing a statement). On the GETs screen a double-click on a statement's row in the Participants panel does the
same, whether or not its card is on the board, and the way back returns to the GETs board (see The Participants
panel, under GETs). The canvas is saved first. The way back is then the tab of the board's screen, PETs or GETs,
or Back. It returns to the board as it stood: the same board, the same place on the canvas and the same
selection, with its undo kept. If the window changed size while the passage was open, such as a phone turned or
a window narrowed, the card you came from is in the middle of the canvas, at the same zoom. A label still
renames on a double-click, whether a PET's, a sub-theme's or a group's. A click still selects. You edit a
statement in place by double-clicking its card or the statement in the Inspector (see Editing a statement). If
a statement's passage is no longer in the transcript, because its row is gone or is now the interviewer's, it
says "This statement's passage is no longer in the transcript." and nothing changes. The board, the screen and
the recent list stay as they were. Opening a participant from their row, or going Home, ends the way back to
the board. The step on the statements bar for the board you came from is that way back too. This holds on PETs,
a timepoint's PETs, a participant's LPETs, GETs and LGETs alike. Until 1 November the LGETs step and a later
timepoint's PETs step opened that board afresh.

**Editing a statement.** Now and then a statement needs a word changed while it is grouped. A double-click on a
statement card opens it for editing on the card, the way a double-click on a PET's or a sub-PET's title opens
the title (Adam, 30 October, for consistency). A box in the card's serif takes the place of its words. It is as
wide as the card and as tall as the words, with the whole statement in it and selected. So a long statement
that stops at four lines on the card opens whole. With the quotes on cards showing, the quote stays under the
box. It is the same on every statement card of the PETs board: loose, in a PET or a sub-PET, a stack's top and
each card of an open stack, and on a timepoint's PETs. The timecode and the sheet's name are part of the card,
so a double-click on them opens the box too. A double-click on the quote shows the quote whole, as a click on it
does. A double-click on the statement in the Inspector opens the same box there, as wide as the Inspector. Until
16 October a double-click on the card opened the box over the card. From then until 30 October it opened the
passage, which Go to the passage in the card's menu does now, and the Inspector was the one way in. Since 30
October, later (Adam: "Edit there too"), it is the same on the GETs, LGETs and LPETs boards. A double-click on a
statement's card, or on the statement in the Inspector, opens the same box. A double-click on any other card
there still opens the Inspector. A statement on those boards belongs to a participant. So keeping it writes that
participant's workbook, the one the statements screen reads, and every copy of the words follows at once. That
covers the participant's PETs boards, the GETs' copy of the participant, which the Participants panel and every
GETs board show, and in a project with timepoints the participant's LPETs and the LGETs. The edit does not mark
the participant Changed since it came in. Until then statements were never edited on those boards, and a
double-click on the card opened its passage. The box keeps the same keys, the same route and the same step of
undo wherever it opens. The card and the Inspector both show the new words afterwards. Enter keeps it, and Esc
leaves it as it was. A click away keeps it, as it does for a label's title. The text stays one line, so a line
break you type or paste becomes a space. The app refuses an empty text with a line, and the box stays open. A
card marked missing has no line to write, so you cannot edit it. A revision on view says it is read-only.
Keeping the edit is the one act on this screen that writes the workbook. `/api/edit-statement` takes the
workbook, `sheet`, `row`, `line`, `text` and `old`, which is what the line read. It replaces that one line of
the row's experiential statements cell, split and joined as the statements screen's save does. It keeps every
other line, and the cell's font, its alignment and its number format, never with a fill. It goes through the
lock guard that the statements screen's save goes through. So it refuses a workbook open in Excel with the
statements screen's line, and it refuses a line that no longer reads as `old`. Nothing else in the workbook or
the progress file changes. On success the server answers with the new text. The page puts it on the card, in
the Inspector and in the board's stored text for that key, the save goes as usual, and nothing shows as
changed. In the same request the server gives the new words to every other board of the participant whose
card for that line held the words it read before. So no board marks the card changed for an edit made here. A
board whose card held other words, from a change made in Experiential statements or in Excel since it last saw
the line, keeps them and its changed mark, because that change is news there. The boards it gives the words to
are those of the timepoint of the statement's sheet. It also gives them to the GETs file's copy of the
participant and to each GETs board's card of the statement. In a project with timepoints it gives them to the
participant's LPETs file and the LGETs file too, each in the same way, so the participant stays in. A
participant with a change already waiting keeps its mark, to be brought in as ever. Revisions are left alone,
and the progress file is as it was. Since 30 October, later (Adam: "Add a History line"), every board that holds
a card of the statement keeps one line in its History for the edit. That covers the participant's PETs boards
and each GETs, LGETs and LPETs board with its card. The line keeps the board as it stood before the edit, and
names the participant and the words before and after (see History). The edit is one step of undo. Undo writes
the old text back through the same route, and redo writes the new, each with a line of its own. A failed write
shows one line, and the card keeps its text. A page in front of a server from before the route says "Restart
the server to finish this update." on the double-click and changes nothing. So does a GETs, LGETs or LPETs
board in front of a server from before 30 October, which would leave the GETs' copy behind.

**Picks.** On a label every quote has a tick, so you can pick the one or two that carry the PET. A PET's quotes
to pick from are its statements' own, each the quote in its statement's pair. A quote you picked stays picked and
shown even when its statement sits under another PET, and it is never dropped by itself. A tick is an act like
any other, saved with the board and one step of undo. A label with picks shows a small quote mark beside its
count. The Inspector shows a label's picks again at its head, under Picked quotes, in the order you picked them.
So you read the quotes that carry it first, and the ticks stay with the statements below. Auto-arrange, Take out
of PET and the note under them stand clear of the last picked quote. Until 18 October Auto-arrange stood over its
foot. A sub-theme has picks of its own, separate from the PET it sits in. A pick is the quote's key: its sheet,
its row and its place among the row's key quotes, as in `Initial:12:0`. That is its statement's key too. A pick
belongs to its label only while a card on that row is under the label. A card that leaves takes its row's picks
with it, a deleted label takes its own, and undo puts them back. A pick follows its quote's words. When a quote
before it leaves the cell, or its row moves, it takes the key of the quote with the same words on its row, or on
a row with a card under its label. A pick whose words are nowhere there, because they were reworded or are gone,
is dropped when the participant is read and when the board is saved. The inverted commas round a quote are not
its words, so a quote that gains or loses them keeps its picks. A label takes as many picks as you tick.

**PET notes.** A PET can have a note, your own words on why it exists, what it holds and what it answers. In the
Inspector, for a label, there is a box of a few lines in the board note's style. It stands under the count and
Take out of PET and above the quotes. It reads "Why this PET", "Why this sub-theme" on a sub-theme, or "Why this
group" on a group. `Cmd + Enter` or a click away keeps what you typed, and Esc leaves the note as it was. A kept
note is one step of undo, like a rename. Undo and redo put the old text and the new back in the box, with the
sidebar open on the Inspector for that label. Note, after Rename in a label's right-click menu, opens the sidebar
on the Inspector for that label with the box ready to type in. A sub-theme has a note of its own, separate from
the PET it sits in. A label with a note shows a small mark of three lines beside its count, drawn as the picks
mark is, and its tooltip shows the note after the count. The note travels with the board. Duplicate copies it,
Copy to board carries it with the PET and its sub-themes, a revision holds it and Restore brings it back. While a
revision is on view, the note shows read-only, as the rest does. With AI features on, AI suggest PET titles sends
the note of the label it names, and the prompt says in one line what a note is. A label with no note sends its
prompt as it did. The note is the group's `note` in the themes file, kept stripped. A group with none has none,
so a file from before the notes reads and writes as it did. `/api/themes` has `notes`. A page in front of a
server from before them says "Restart the server to finish this update." in place of the box, because that
server would drop a note on the save.

**Canvas and Table (19 October).** This is Adam's choice of 18 October, from a drawing. The PETs bar and the GETs
bar have Canvas and Table after the board's name. They are two views of one board, always in step. The one
showing is pressed in, and `T` switches between them, as their tooltips say. The browser keeps the view each
board was left in, across a restart. Table is the table of PETs that the print view sets out (see Print), live.
It shows the PETs in the order the canvas reads them, each lettered as the project labels them, with its
sub-themes and groups under it. Each statement shows where it is and its own quote. Then comes Unplaced. The table
is drawn from the board on the page whenever the canvas changes, so it is never out of date, and the canvas stays
laid out under it. Every PET, sub-theme and statement row has a grip at its left. Drag it to another place among
what sits beside it, or press Alt with the arrow up or down on its grip or its title, and the letters follow. So
1d put above 1c becomes 1c. The order is set as an agent's `order` sets it: each item moves into the place of the
one that read there before, so the canvas moves its cards to match. A statement dragged into another PET,
sub-theme or group goes there, at the line shown, as on the canvas. One in Unplaced goes into the PET you drag it
into. A double-click on a PET's or a sub-theme's title, or a second click on the title of the one selected label,
opens it in a box in place. Enter keeps it, and Esc leaves it. Each change is one step of the board's undo, `Cmd +
Z` in the table as on the canvas, and is saved as the canvas saves. The statements' own words are read-only here.
You write them on the statements screen, because the PETs are built from the statements. Print and Microsoft Word
at the table's top right do what Export does. Its heading is the participant, "P9 Wren", with Table of Personal
Experiential Themes smaller under it and the board's name beside that, as the print and the Word document head
the table (20 October). A revision on view is read-only in the table too. The zoom bar and the minimap leave the
canvas's corners while the table shows. The palette stays, with Group, Undo and Redo, because New sticky note
belongs to the canvas alone. The table takes its measure from the room it has, not from the window. So beside
the Inspector or the Participants panel it lays out as it does in a narrow window, with each statement on a line
of its own and its quote under it. Where it has room, the table starts clear of the palette. Where it is narrow,
as at a phone's width or beside the Inspector in a small window, the palette lies flat in a row at the table's
foot right and floats over it, as it does over the canvas, so the table keeps its whole width. A Shift or Cmd
click, a right click or a double-click on a row selects no words in it, as on a card. On the GETs board the table
is the GET table (see Table under GETs). Each GET has its grip to reorder the GETs and its title edited in place.
Each participant's card stands under it with a grip of its own to move under another GET, and then come the
cards under none. A window of the Mac app, or a tab, on the same participant sees a change made in another, as
it does today, by the line in the top right.

**Everything the canvas does, in the table (20 October).** Adam, 20 October: the table is self-sufficient, so
anything you do on the canvas you can do in the table, and the other way round. He chose the canvas's own keys,
palette and menus on the table's rows, so there is nothing new to learn either way. A click on a statement's row
selects it. Cmd with a click adds one or takes it away. Shift with a click selects the run of rows between the
last one clicked and this one. Esc or a click on the table's empty space clears the selection. You select a PET's
or a sub-theme's row by clicking its title strip. The selection is the board's own, so the canvas shows the same
cards selected after `T`, and the status bar counts them, "2 ES selected", on the canvas as in the table. The
canvas's keys work on the selected rows and mean what they mean there. `G` puts a label over them with its title
box open in its row. It makes a sub-theme when they all sit in one PET, and a group when they all sit in one
sub-theme. The letters below it follow, so 1a becomes 1b. `G` with nothing selected makes a new empty PET at the
end of the table with its title box open, and you then drag the statements into it. On the canvas `G` with
nothing selected makes the empty PET in the middle of what is in view. `Backspace` takes a statement out of its
PET or sub-theme to Unplaced. On a title it deletes the label and keeps what it held. `X` sets aside. `S` stacks
the selected statements under the one that reads first in the table. `I` opens or closes the Inspector, which
follows the selected row as it follows a card. `N` asks for names when AI features are on. A right click on a
row, or the ⋯ at its right end, opens its card's or its label's menu, the canvas's own. A PET's or a sub-theme's
menu also has New group inside. It makes an empty sub-theme inside a PET or an empty group inside a sub-theme,
with its title box open. Auto-arrange is left out of the table's menus, because the table is always in order. A
double-click on a statement's row opens its passage on Experiential statements. The way back returns to the
table where it was scrolled to, with the row still selected. A selected statement's grip drags every selected
statement together, in the order they read, to the line shown. Rows dropped on a label's title strip go into it,
with "Merge into" showing over the strip as on the canvas. Statements join it at its end, and a PET or a
sub-theme goes inside it with all it holds. Rows dropped on Unplaced go back there. A stack's count beside its
top, "2 stacked", shows the statements under it in the rows below. A click on it again, or `S` on the top,
stacks them again, and their menus hold Make this the top and Take out of the stack. The table's foot lists Set
aside, each with Put back, and then any statement missing from the workbook, with Remove, as the sidebar does.
Every one of these is one step of the board's undo, as on the canvas. On the GETs board the same keys and menus
work on the cards. `G` makes a GET from the selected cards, and with nothing selected an empty GET. A card's menu
has Take out of GET, and Place also under when One GET per PET is off. A right click on a participant's name in
a GET's row opens the participant's menu. Its Add participant note puts the note under that GET, in that
participant's row. A GET's menu and a GET sub-theme's also have New group inside, on the canvas as in the table.
It makes an empty sub-theme inside the GET, or a group inside the sub-theme, with its title box open. A GET's
sub-themes stand as rows of their own at the top of what the GET holds. Each shows its title, how many
participants it holds, and its menu. A card dropped on a sub-theme's title strip goes inside it, and the card's
row under the GET then says "in" and the sub-theme's title. A row of the Participants panel dragged onto the GET
table goes under the GET or the sub-theme you let it go on, or into Unplaced when you let it go over that list,
as a drop on the canvas does. Its card comes in, or the one already there moves, out of Set aside if it was
there, in one step of undo.

Since 11 November 2026 an AI agent can do what dragging a statement's row from the Participants panel does, on
GETs, LGETs and a participant's LPETs alike. It brings that one statement onto the board, into the GET or LPET
you name, or onto the canvas in none. It never brings the rest of its PET's statements. It runs a dry run first
and keeps the board as it stood in its History, as its other changes do. The app refuses a statement already on
the board, another participant's statement on their LPETs, or a GET or LPET the board does not have, and changes
nothing (see the guide for agents).

**Export.** Export stands in the toolbar after the board's name, Auto-saved and Canvas | Table (16 November 2026,
Adam's option C: "board 1, canvas table, then export", because you export the canvas or the table). Until then it
stood in the top bar, which keeps the app's own tools. Its icon is the share glyph, a box with an arrow up out of
it, drawn in the app's line style. It opens a small menu under it, in the row menu's paper. Since 1 November the
menu follows the view (Adam: "I always switch to the table view if I want to print or export the table"). In
Table view it holds Print (see Print), Save as PDF, Microsoft Word (see Word document) and Markdown and CSV. Under
a rule comes the heading Include and its ticks, each a plain name: Descriptions, Unplaced, Statements set aside,
Stacked statements, Interviewer notes (the Markdown and CSV's notes file) and Pen portrait. Under a last rule
comes PET labels. Leave out the board's name went on 16 November ("nobody wants it"), from the print view's ticks
too. On the canvas the menu holds Print, Save as PDF and Save as an image, with no ticks, because the canvas shows
what it shows. The GETs, LPETs, LGETs and Themes boards have the same Export in the same place (see Print). Each
has Microsoft Word when the table is chosen, and its first choice is named for the board: GET table, LPET table
or LGET table. A participant's LPETs also export as a PDF beside their workbook, named by them. Trajectories'
Export gives Print, Save as PDF and Microsoft Word, with Each participant's note and Unplaced. The statements
screen's Export gives the Annotated transcript (Coded transcript in thematic analysis), with Exploratory notes,
Experiential statements, Interviewer notes and Pen portrait, beside the workbook. The Code list's Export, in its
own toolbar row, gives Print, Save as PDF, Microsoft Word and CSV, with Extracts (16 November 2026). On the
canvas, Print opens the canvas on one landscape page in a tab of its own, as Canvas on one page did (below). Save
as PDF saves the canvas on one landscape page as a PDF beside the workbook, with no print dialog. It is named as
the table's PDF with "canvas" after it, as in "P9 - Wren - Board 3 - PETs canvas.pdf". Save as an image saves a
picture of the whole canvas, every card whole under the title, as a PNG beside the workbook, "P9 - Wren - Board 3
- PETs canvas.png". It is twice as sharp as the screen, so it stays sharp on a slide or as a figure in a thesis.
Both show the quotes on the cards as Quotes on cards shows them. A short quote, a label's description or a reason
is cut with "…" where the canvas cuts it, and the close pairs' lines show while Close pairs is on. Each adds the
date and time to its name when a file of that name is already there. A panel at the top right names the file once
it is written, with Show in Finder (Show in Explorer on Windows, Show in Files on Linux). Every export on every
screen ends in that same panel. If one cannot be made, the panel says why. Since 9 November 2026 Idiograph makes
every PDF and picture itself, in its own two typefaces. So Save as PDF, Export as PDF and Save as an image are the
same on a Mac, on Windows, on Linux and in a browser's tab, and nothing else needs to be installed. When one cannot
be made, the panel says so in plain words and nothing is saved. Print in the Linux window opens the print dialog
on the page's own landscape A4, as on a Mac. Esc or a click anywhere else closes the menu. Since 31 October each
entry is named for what it gives (Adam: literal words). Before, they read Print table, PDF, Canvas, .md and CSV
and For sending. Each entry's and tick's tooltip says the rest. Print opens the print dialog with the table of
PETs on landscape A4. Save as PDF saves the table of PETs beside the workbook as a PDF, with the same landscape
A4 pages as the print. The canvas's Print opens the canvas on one landscape page in a new tab, to print or save
as PDF. Microsoft Word saves the table of PETs beside the workbook as a Microsoft Word document, a .docx (it is
Microsoft Word since 1 November, and read Word before). Markdown and CSV saves the PET draft as Markdown and the
statements as CSV. Each tick's tooltip says what it puts on the page. Save as PDF saves the table of PETs as a PDF
beside the workbook, where the Word document goes. It is named as the print view names it, "P9 - Wren - Board 3 -
PETs.pdf". If a file of that name is already there, the date and time are added, so none is written over. There
is no print dialog. Idiograph sets the pages itself, with the same foot on every page, and a line names the file
once it is written, with Show in Finder on a Mac. A save still to go is written first. It is the same in a
browser's tab. The canvas's Print (Canvas on one page until 1 November) opens the canvas itself in a tab of its
own. It shows every PET, sub-theme, group, card and sticky note in its tint, under a title naming the participant
and the board, with none of the screen's controls. On screen a statement's card stops at four lines, but on paper
every statement is whole. The canvas's own layout runs on a copy with each card at its whole height. So a PET,
sub-theme or group grows round a longer card and what lies below moves down, with nothing overlapping, in the
screen's columns, nesting and order. The canvas on screen keeps its four lines and does not move. It fits the
whole canvas on one landscape page of the paper the print dialog picks, so choose A3 there for a large board. PET
labels is a choice of two, A B C or 1 2 3. Smith, Flowers and Larkin letter the PETs in Box 5.6, A, B, C, and
leave the sub-themes unnumbered. Idiograph follows the book by default. It gives each sub-theme and group a
reference after its PET's letter, A1 and A2 under A, and A1.1 under A1, so you can name any label in a note or a
supervision. Numbers are a setting: 1 2 3 labels them "PET 1", "PET 1a" and "1a.1" in their place. A press saves
`pet_labels` in the project file at once, for every participant of the project, and keeps every other key. The
menu stays open on it. The Word document, the print view and the PET draft all follow it. Project settings shows
the same choice for each project (see Projects). The demo keeps the book's letters, with its pair greyed.
Markdown and CSV writes the board on the canvas, after saving anything still to save. A line in the top right of
the canvas then names the two files it wrote the way the participant holds them, `Working/<file>`. It never uses
the participant's folder's own name. On a Mac it has Show in Finder, which opens a Finder window on the markdown
draft. The line stays until its cross or Esc. The first file is a markdown PET grouping draft at
`<case>/Working/<stem> - PET draft (<board name>).md`, as in `Juno - PET draft (Board 1).md` on the demo. The
stem is the one the statements CSV uses, and any character in the board's name that a file name cannot hold
becomes a hyphen. Its PETs, sub-themes and groups have the labels the print view and the Word document give them,
in the same order, so the three never disagree (see Print). It opens with a title line, the participant by their
pseudonym and the board's name. Then comes a list of every PET, its sub-themes and their groups in canvas order,
top to bottom and left to right along a row. Labels within a card's height of one another count as one row. A
PET reads "A. Home life (1 sub-theme · 7 statements)", a sub-theme one step in "A1. Mornings (1 group · 3
statements)", and a group a step further "A1.1 Early light (2 statements)". Then each PET comes under its letter
and title as a heading, "A. Home life". A sub-theme is a heading a level down under its PET, "A1. Mornings", and a
group a level further, "A1.1 Early light". A group inside a group, "A1.1.1", is a heading a level further again.
Anything deeper stays at that level, as the Word document's headings do. Under a heading comes the PET's note, or
the sub-theme's or the group's, as a plain paragraph when it has one. Then come its statements and the labels
inside it in the print view's order. Each statement is a list item, `- Statement (Initial, 02:10)`, with its own
quote on the next line in single curly marks, ‘like this’, or none for a statement without one. No picked quotes
are listed, as in the print view. The board's note stays out, and the CSV has no note at all. At the end come
Unplaced and Experiential statements set aside with their counts, "Unplaced (18)" and "Experiential statements
set aside (3)", as the print view and the Word document head them. (Until 19 October the second read Discarded,
and until 20 October Binned experiential statements.) They are in transcript order, each only when it holds
anything, and set out the same way. The second file is the statements CSV. Its Proposed PET column is filled from
the same board, with each statement's own quote last. Its rows go PET by PET in canvas order, with a sub-theme's
rows where its frame's top sits among the PET's cards (see Export, under The loop). The workbook is only read, so
a workbook open in Excel exports as it was last saved.

**Word document.** Microsoft Word, the fourth entry under Export, writes the board on the canvas as a Word
file. It takes the shape of the table of Personal Experiential Themes that Smith, Flowers and Larkin (2022) set
out in Box 5.6, their table of PETs for Elisa. It is plainer than the print view, for when a polished page reads
as finished work. Anything still to save is saved first. The file goes at the participant's folder's root,
beside the workbook, where your PETs Word files live. It is named `<P9 Wren> - PETs (<board name>).docx`, as in
`Juno - PETs (Board 1).docx` on the demo. The participant is named by their pseudonym, and any character in the
board's name that a file name cannot hold becomes a hyphen. It never writes over a file. When the name is
taken, the date and time go in it, as in `Juno - PETs (Board 1, 6 Oct 14.20).docx`. In the rare case that one
is taken too, a count goes after them. The line in the top right of the canvas then names the file the way the
participant holds it, with Show in Finder on a Mac. The document opens with the participant, large, under
Heading 1, "P9 Wren", or the name alone when the participant has no number, "Juno". So Word's navigation pane
names the participant. Under it comes the table's name, "Table of Personal Experiential Themes", smaller, in
Word's Subtitle style (Adam, 20 October). Then come the PETs in the order the canvas reads them, which is the
order you set for the story they tell. Each is lettered in bold capitals under Heading 2, as Box 5.6 letters
them: "A. HOME LIFE", then B and C. The title keeps your casing in the text, and Word's All caps shows it in
capitals, so a copy pasted elsewhere keeps your casing. A sub-theme sits under its PET in bold under Heading 3,
"A1. Mornings", then A2. A group, a label inside a sub-theme, is in bold italic under Heading 4, "A1.1 Early
light", then A1.2. A group inside a group, "A1.1.1", takes Heading 5. Anything deeper, "A1.1.1.1", keeps
Heading 5, the same style as the level above it. With 1 2 3 under PET labels the same headings read "PET 1.
HOME LIFE", "PET 1a. Mornings" and "1a.1 Early light" (see Export). A label's note, when it has one, follows its
heading in italics. Under each heading come its statements in the order the canvas reads them. A label inside
it takes its place among the cards where its frame's top sits. Each statement is a paragraph followed by its
sheet and timecode, "(Initial, 12:04)". On the next line comes its own quote in single curly quotation marks,
‘like this’, set in a little. The marks are never doubled when the workbook keeps its own. A statement with no
quote of its own has no quote line, and "(no quote)" never shows. There is no list of the PETs at the head, no
list of picked quotes and no key, because each reference names its sheet. Unplaced and Experiential statements
set aside come next under plain headings with their counts, "Unplaced (18)" and "Experiential statements set
aside (3)". Each comes only when it holds anything and only when its tick under Export is on, Include unplaced
and Include statements set aside (see Print). Their statements are set out in the same way. A statement no
longer in the workbook says so in its reference, "(Initial, 12:04, no longer in the workbook)". The labels and
the order are the print view's, taken from one place, and the PET draft takes the same labels. The styles are
plain. Normal is in Times New Roman at 11pt, and Heading 1 to 5 keep Word's own names, so the navigation pane
and a reference document take them. They are restyled to the book's look, with no colour, no fill, no list and
no table. The page is portrait A4 with margins of an inch, while the print view's PDF is landscape (see Print).
It opens in Word, Pages and LibreOffice. The workbook and the themes file are only read. `themes_word.py` writes
it, with the standard library alone.

**Print.** Print, the first entry under Export, and Print at the top right of the Table view (see Canvas and
Table) open the board on the canvas in a tab of its own at `/themes/print?workbook=<path>&board=<id>`. The print
dialog opens at once. The server renders the page from the board as the themes file holds it, and writes a save
still to go first. It is the PET document you send your supervisor. It is the table of Personal Experiential
Themes that Smith, Flowers and Larkin (2022) set out in Box 5.6, with the Word document's content (see Word
document) typeset in the app's faces. It is on landscape A4, as the book's tables are set, while the Word
document stays portrait A4. Since 9 November 2026 the print view is set in two typefaces that the app carries:
Charis SIL for the text and Nunito Sans for the headings' labels, where a statement was said and the foot. So it
looks the same on a Mac, on Windows and on Linux, and the PDF made from it is set in the same two (Adam, 9
November). The page's small print is in the app's own faint ink, 5.3 to 1 on the white paper. That covers the
board's name, the labels, a statement's reason and the foot line, and also the GETs print's counts and the
audit trail's places. Until then it read at 3.8 to 1 (17 October). The head is one band across the top of the
first page. The participant is its main heading, "P9 Wren", with the dash of the case key dropped, or the name
alone when the participant has no number. The table's name, Table of Personal Experiential Themes, stands
smaller beside it on the same line (Adam, 20 October: with three tables printed, each opening on the same title,
it was hard to see what told them apart). To their right stand the project and the research question, each after
its small label. The labels are in a column of their own so the two lines start together, and the question
wraps in its column (Adam, 31 October, so the head takes less of the page). No rule runs under the head,
because PET A's shaded band parts it from the table. The date and the board are in the foot. The page no longer
says the PETs are marked complete (Adam, 31 October), though the mark itself shows everywhere else as before. The
board's note stays out. Board note is a tick beside Print, off until you tick it. It draws the page again with
the note under the head, `note=1` in the address, and it is greyed on a board with no note. There is no list of
the PETs at the head. Then come the PETs in the order the canvas reads them. Each is lettered "A.", "B." as the
Word document letters it, or "PET 1.", "PET 2." with 1 2 3 under PET labels. Its title is in capitals, with a
pale band of its tint behind the title and a thin rule of the tint down its side. Then comes the PET's note in
italics when it has one. A sub-theme sits under its PET in bold, "A1. Mornings", and a group, a label inside a
sub-theme, in bold italic, "A1.1 Early light". Each is set in a little further and a little smaller, with a
hairline of the lighter tint beside it. A group inside a group, "A1.1.1", takes the fifth step. Anything deeper
stays at that step's size and indent, as the Word document's headings stop at Heading 5. The headings and the
notes run across the full width. Under each heading come its statements in the order the canvas reads them,
higher first. A label inside it takes its place among the cards where its frame's top sits. Each statement is a
row of two columns, because one line across a landscape page is too long to read. On the left is the statement
in the serif at 10pt, followed by where it is, "(Initial, 12:04)", small and quiet in the sans. On the right, the
wider of the two, is its own quote in italics at 9pt in single curly quotation marks, ‘like this’. The marks are
never doubled when the workbook keeps its own, and the quotes line up in one column down the page. A statement
with no quote of its own leaves the right empty, and "(no quote)" never shows. The picked quotes are not listed,
because every statement has its own. The PETs flow on from page to page. A row never splits, so a statement never
parts from its quote across a page. A title, whether a PET's, a sub-PET's or a group's, is never left at the foot
of a page. It goes to the next page with its first row, and a PET's title goes with its first sub-PET's title
and that sub-PET's first row. Every other row flows on freely, so the pages fill. Nothing spills onto a page of
its own after the last row. Since 31 October the type is a step smaller than on screen, set as a research
document to read at arm's length. The participant is 18pt, a PET's title 11.5pt in capitals, a sub-PET's 10.5pt
in bold, a statement 10pt, its quote 9pt and where it was said 7pt, with room between the PETs and the rows. The
page prints at that size, the same on a Mac, on Windows and in the PDF an agent makes. At the end come Unplaced
and Experiential statements set aside with their counts, "Unplaced (18)" and "Experiential statements set aside
(3)". Until 19 October the second read Discarded. They are in transcript order, with their statements in the
same rows, and a discard has the reason an AI proposal gave under its statement. Each comes only when it holds
anything and only when its tick is on. The two ticks, Include unplaced and Include statements set aside (Include
binned experiential statements until 20 October), sit under Export on the PETs screen, under the four entries,
and beside Board note on the page. There a tick draws the page again with the part or without it. Both are off
on a new install, so the table and the Word document hold the PETs alone. A tick you change in either place is
kept in the settings for the next export of any participant, for the table and the Word document alike (18
October). A third tick beside them, Include stacked statements, puts the statements stacked under a top beneath
it, under a small line, "Stacked under it (3)". Each has its reference in the soft ink and no quote, inside the
top's row, so the page never parts them from it. It is off on a new install, so the top stands for its stack
alone, and it reaches the Word document and the PET draft too (19 October, see Stacks). Leave out the board's
name (For sending until 31 October) was a fourth tick, for the copy you send your supervisor, until it went on 16
November. Before them all stands Descriptions (21 October), on for a new install. It puts each PET's and
sub-PET's description under its title on the page and in the Word document, and leaves it out when unticked (see
Descriptions). After them all stands Pen portrait (11 November), off on a new install. It puts the participant's
label and pen portrait under their name (see The label and the pen portrait in the exports). A small line at the
foot of every page has three parts. At the left is the participant with the board in brackets, the project and
the table, as in "P9 Wren (Board 3) · Living with a dog · Table of Personal Experiential Themes". In the middle
is the name documents carry, Confidential and the date printed, as in "Ada Lark · Confidential · 31 October
2026". At the right is the page, "Page 2 of 4". The name is Your name, in Settings, General. While Your name is
empty, the foot and the author field have no name (17 November 2026: the interviewer's name belongs to the
project and no longer stands in). Word's document has the same name as its author. Until 31 October the foot
named the themes file. Since 1 November the middle part sits halfway between the end of the left part and the
start of the right, so a long left part never runs into it. When the three would still come closer than about 6
mm, the project's name in the left part is shortened at a word with "…" until they fit. The participant, the
board, the table, the name, Confidential, the date and the page are never shortened. Since 31 October the page's
head no longer has the date, the board's name and Current board at its top right. Since 1 November it is a grid
of two by two. At the left is the participant with the table's name under it, smaller. At the right are PROJECT
and the project, level with the participant, and RESEARCH QUESTION and the question, level with the table's
name. The labels are in a column of their own so the two values line up, and the question wraps in its own
column. The GETs print has the same foot, with the project, the board in brackets and the part printed at its
left. It has the same head too. Since 1 November its title is the document's name where the table of PETs has
the participant, "Table of Group Experiential Themes", and the audit trail and the full set have their own.
PROJECT and RESEARCH QUESTION stand to its right as on the table of PETs (Adam: "it should be consistent across
the PETs and GETs tables"). It has no rule and no line saying the GETs are marked complete. The Mac's web view
draws nothing in a page's margin, so until 31 October the Mac's own print had no foot line. Since then the app's
window draws the foot itself on every page, from the page's own words. So the Mac's print and its PDF have the
same foot as Windows's and the PDF an agent makes. Safari's own print, in a browser's tab, still has none. Since
19 October the page opens with the print dialog, where Save as PDF is one step, because you read the table in
the Table view. Print at its top right opens the dialog again. A board with no PETs prints its head, and the
Unplaced list with its tick on. The labels and the order come from the one place the Word document takes them,
so the two never disagree, and the PET draft takes the same labels (see Export). The workbook and the themes
file are only read, and nothing is written anywhere. The app refuses a workbook outside the project folder, and
a board the file does not hold. Each refusal is a page of one line in the print view's faces, as in "That board
is no longer among the participant's PETs boards, so nothing was printed.". Until 17 October, later, it stood in
the system's font and named the themes file. Now it is on the print view's page, centred as its pages are.
Before, it stood at the window's left edge. `auto=0` in the address leaves the dialog shut, for a look at the
page. `/api/themes` has `print`, which says where the view is. A page in front of a server from before it says
"Restart the server to finish this update." and opens nothing. `themes_print.py` renders it.

The same view is a participant's table. Open as table, beside each participant in the participant picker (see
Another participant's PETs), opens that participant's Current board in a tab of its own with `auto=0`, the
dialog shut and nothing on it to change. When no board is marked Current, it opens the board last open. You
can then set two tables or more side by side in separate tabs, to look for what resonates from one participant
to another. The participant on the screen offers it too. It writes a save still to go first, and writes nothing
else.

**AI help.** With AI features on in Settings, and its PETs switch on, the screen has one more control, AI
suggest PET titles in a label's Inspector. It goes out through the PETs model set in Settings under PETs, which
is the Experiential statements model unless you choose another there, with the same key (see Settings, The
PETs model). It sends the project's research question. Its prompt is its own, in `themes_ai.py`. The IPA
guidance it sends is one file, `pet_guidance.md` beside the app. It is written from Smith, Flowers and Larkin
(2022), Smith and Nizza (2022), Nigbur and Chatfield (2025) and the project's own rules. The call sends section
1, what a PET is, with rules 5, 6, 8 and 11 of section 3: the title, its register, negative and unresolved
material as valid, and recurrence as grounding. The app reads the file afresh on every call, so editing it
changes what the AI is told, with no restart. If the file has no rules under its section 3, the app says so in
one line and asks nothing. Nothing moves by itself. A title goes on only when you pick it. Every control that
calls an AI model shows the sparkles, and no other control does. Those controls are AI suggest under the
statement field, AI suggest in the test bench in Settings and AI suggest PET titles in a label's Inspector.
Auto-arrange and the sidebar button do not show them.

New AI board, AI review and AI revise went on 11 November 2026 (Adam). An agent of your own through MCP does that
work better (see Working with an AI agent). A board an AI made before then is an ordinary board now. A board's
review rounds and revise thread from before, `review` and `revise`, stay in the themes file as they were. Nothing
reads them, and they are never sent.

The cog at the right of the PETs bar opens the same Settings card that the statements screen's cog does, on
General. The PETs screen's own model is in AI features, under PETs. When you save, the change shows at once: the
switch and the model's name in the Inspector's titles. The band takes a question changed in Project settings.

AI suggest PET titles, one label with the sparkles, sits in the Inspector for a label alone, a PET or a
sub-theme. It never shows for a card, because a title belongs to a group of statements. `N` outside a field does
the same, and opens the sidebar on the Inspector when it is not showing, because the titles land there. It acts
on the selected label, or the one the Inspector shows. With cards selected and no label, `N` asks nothing and
says in the canvas's line "Group the statements first (G), then ask for titles." A press saves the canvas, then
sends the label by its id and the board by its own id. The server builds the prompt from the board and the
workbook, not from a list the page sends. The system prompt holds these parts in this order. First comes the
introduction, then the research question, then section 1 of the guidance file, what a PET is, read from the
file afresh on every call. Then comes a line on what an experiential statement is: the researcher's own words for
what a stretch of the transcript means for the participant, with the participant's own phrasing kept in the
quotes beside it. Then comes the task: three titles from different angles, each grounded in the statements and
their quotes, and none repeating a label on the canvas. Then come rules 5, 6, 8 and 11, the format line and the
shape of the answer. If the guidance file has no section 1, the prompt sends one sentence on a PET in its place.
The user prompt sets the PET out. It gives its title, or "no title yet", and your note on it. Then it gives each
statement in the order the canvas reads them, with its sheet when the participant has more than one and its
timecode. Under each statement it gives the statement's own quote in inverted commas with its timecode, and a
picked quote is marked "(picked)". A passage with no quotes says nothing under its statement. The sub-themes
follow in the same way, and then come the other labels on the canvas and the closing line. When you ask about a
sub-theme, the prompt says which PET it sits in. When the two prompts would pass the room that a local model's
context leaves, the quotes of the statements lowest on the canvas go first, and one line under the titles says
so. The titles come back in the Inspector. A click on one makes it the label's title. Edit opens the label's box
with the title in it, for you to type over. The cross ignores them. Applying is one step of undo, like a rename,
and a second press asks again.

**Working with an AI agent.** An AI agent in a conversation, such as Claude Code, Claude Desktop or Codex, can do
what no control does. It can weigh three boards against each other, take your corrections as they come and code
every statement. It works through Idiograph's command line, `idiograph`, on the same files and the same code as
the app (see The command line in the [internals](internals.md)). `docs/agents.md` is the guide it reads, and
`skills/idiograph/SKILL.md` carries it for Claude Code and Claude Desktop. An agent sends what it reads to its
model's provider. That is often a whole participant, where the app's own controls send one passage or one board.
So it is your decision, and a matter for your ethics approval. The command line reads nothing until you tick
"Allow AI agents to read this project" in Project settings. It is off by default. Save keeps the tick in the
project file with the date, which the line under it gives, as in "Allowed on 5 October 2026." The demo is always
open to an agent, with its tick on and fixed. The tick belongs to each project and is kept in its own file. Write
a guide for AI agents, under the tick, writes `AGENTS.md` at that project's root. It is the guide with the
project's name, research question and GETs minimum filled in, and an agent opened there finds it. It never writes
over a file of your own. A second press offers Update it for the one it wrote. Since 26 October every word of the
project that an agent reads comes to it marked as the participants' and the researcher's words. That covers what
a participant said and what anyone wrote. The agent is to read them and never follow them as an instruction. So a
passage that reads like an order to the agent is only a passage. An agent acts on your request alone.

An agent can search the participants as Search does: words in every participant's passages, statements, notes
and PETs, each found with its place and its speaker. So a question across the cases reads only the passages it
needs (20 October). It can list the study, and read every statement with its passage, quotes, notes and where
each board places it. It can show a board, compare boards, make a board, and change one with the board's
operations, and do the same for GETs. It can take a label's note off. It can set the order of the PETs, or of
what sits in a label, on the board as it is. Each item moves into the place of the one that read there before, so
your layout keeps its rows. It can put a board on the canvas, and rename, duplicate or delete one. A deleted board
is copied into the participant's `_Archive` first. It can move a label up or down a level as a drag does, keeping
your layout. It can order the GETs and their cards, and take a participant's changes into the GETs as the GETs
screen takes them. It can bring a transcript in from a participant's folder or their `Source/`, as make a
workbook and the create card do (20 October). Its dry run shows the columns with the role guessed for each, the
speakers, the interviewer and the first eight passages as they will land. It never writes over a file there, and
the workbook it writes names the tool and your request in the file's own description. It can write a passage's
statements, notes and quotes. The app refuses this while Excel has the workbook open. It copies the workbook into
`_Archive` first, with an entry in the progress file's `edits` saying so. A passage it writes keeps each quote
with no statement that it does not name. A statement it rewords takes the new words on every board's card, and
the PETs screen says that the board changed in a conversation when it is open. A new quote it writes for a
statement goes with the statement's words into the GETs. In a project with timepoints it also goes into the
LPETs, the LGETs and the key quotes on Trajectories (13 November). If a card or a copy ever falls behind the
workbook, the agent can bring every one back in line with `copies refresh`. It runs a dry run first that names
each by its key. The workbook's words and quotes win, including on a card marked Changed. A card whose statement
has gone stays on the board for you to remove. When a quote is reworded, the PET's pick stays on its statement
with the new words. A key quote's bold on Trajectories moves to the same words in the new quote. Where those
words are gone, the bold is left off, and the dry run lists the cell by participant, timepoint and LPET, so you
can look at it. A statement it removes from a passage takes its card off every board. Every card after it in that
passage moves with its statement, so no card shows its neighbour's words (20 October). On the interviewer's own
passages it writes nothing but a removal (13 November 2026). It can take off a statement or a quote left on one
of the interviewer's turns, a statement with its quote, and its card goes from every board. It can do nothing
else there. Each board it changes keeps the board as it stood first in its History. It can also take off a card
missing from the workbook, as Remove does in the pile, one by one or every one on a board. It never takes off a
card whose statement is there. A board it makes keeps the layout of the board on the canvas for every PET,
sub-theme and statement it keeps, so a rebuild never resets your arrangement. A board it makes is the next board,
"Board 5", with "with AI" after its name, and your own boards stay as they were. The board has no note of who
made it. The record of agents' changes keeps the tool, the time and your request (16 November 2026). Before a
change to a board, History first keeps the board as it stood, as "Before an agent's change" (the request stays in
By an agent), so Restore takes it back. An agent never sets a statement aside. A statement it finds fits no PET
stays in Unplaced, and the Inspector gives the agent's reason under it, "Left out: ...". If you set it aside, the
pile gives the reason under its words under Set aside. With AI features on, a statement's short id, `S12`, stands
small and faint after its timecode in the Inspector. It is the same id the agent names it by, so either of you can
name one in the conversation.

The page notices what an agent writes. When the window gets the focus, and every thirty seconds, the PETs and
GETs screens ask. A change made in another window of this Idiograph is your own (20 October, for two-screen
working). It comes onto the canvas by itself, with your canvas saved first. A change made outside the app, by an
AI agent's command line or MCP or by hand on the file, shows a bright orange card in the top right of the canvas,
"Changes made elsewhere", with Update. Update saves the canvas first, then loads the board where you had it. The
card stays until you press Update or its cross. A board added outside says "Board 5 added in a conversation.",
with Show it, which fits the new board to the view. Nothing jumps before you ask. The server tells the two apart
by the files it wrote itself. Each write of a themes file, a GETs file or a workbook notes the file's time, and a
file whose time has moved since was written by something else. The list of what it wrote is kept in the app's own
state across a restart. So a file left as the app last wrote it is still its own after a restart, and a file
changed while Idiograph was closed counts as from elsewhere. The app refuses a save from a PETs canvas that has
not shown the change yet. It keeps the canvas in the board's History as "The canvas when a conversation changed
this board", so neither your work nor the agent's is lost. A change from a conversation leaves every PET, sub-PET
and statement it was not asked about in the order it read, in the table and the PDF as on the canvas. A statement
it moves into a PET or a sub-PET goes in last there. Room the canvas makes for a board whose type takes more space
than the agent allowed for never changes that order either. Since 19 October every save of a board carries the
board as the window last read it. So the app refuses a save over a board changed since, in another window or, on
the GETs screen, by an agent, and writes nothing. A card in the top right of the canvas says "This board has
changed since this page was loaded, so nothing was saved. Your words are still here.". It has Reload, which puts
the board as it now stands on the canvas, and Overwrite, which saves the canvas over it. Until you choose, nothing
more is saved. An agent's change that carries the version it read is refused in the same way when the board
changed after it read it. Experiential statements does the same for a passage an agent wrote: "A passage was
written in a conversation.", with Show it. Show it saves the passage in front of you and opens the participant
on that passage. One writer goes at a time, because the app and the command line take the same lock around every
write. The command line and the MCP server are your own tools outside the app. So they work whatever AI features
says, and the tick decides which projects they read.

**Add Idiograph to Claude Desktop.** Some researchers work in Claude Desktop or Cowork and never open a terminal.
For them, Idiograph's MCP server offers the command line's commands as tools, doing the same work on the same
code. In Project settings, after Write a guide for AI agents, Add Idiograph to Claude Desktop opens a small card.
The card shows the entry that runs the server on the project shown, with its root as `--root`. For the demos it
is `--demo`, `--demo ta` for the thematic analysis demo, `--demo lipa` for the longitudinal demo and `--demo rta`
for the reflexive thematic analysis demo. From source the entry is the venv's python running `mcp_server.py`. In
the Mac app it is the app's own executable with `mcp` first. In the Windows app it is `Idiograph-console.exe` in
the app's `server` folder with `mcp` first. Add writes it into Claude Desktop's settings file under `mcpServers`
as `idiograph`. That file is `~/Library/Application Support/Claude/claude_desktop_config.json` on a Mac and
`%APPDATA%\Claude\claude_desktop_config.json` on Windows. Add keeps every other entry, and first copies the file
as it was beside it, with `.before-idiograph-` and the time after its name. If the file is not valid JSON, Add
refuses in one line and leaves it as it is. The line under the card then ends "Restart Claude Desktop to use it."
The same card gives the entry to copy for any other client, and the one line for Claude Code, `claude mcp add
--scope user idiograph --` and the same command, each with Copy. User scope lets Claude Code find Idiograph in
whatever folder it starts in. `claude mcp add` alone keeps it to the folder it was run in (20 October). A board
written through the tools is marked as made by the client, with "with AI" after its name. The tick still holds.
With it off, every tool answers with the line that says where to tick it. Beside the tools the server offers a
prompt, Start working with Idiograph, and resources (19 October). So an agent that has never seen Idiograph finds
its way in from the server alone. The prompt is what a new agent takes first. It says that what the agent reads
goes to its model's provider, and that you make every decision. It gives the project as it stands, asks for a dry
run before every write, and says where the rest is. Claude Code shows it as a slash command, and Claude Desktop
among its prompts. The resources are the guide for agents, whole and section by section, the files' schemas, and
the project's `AGENTS.md` once Write a guide for AI agents has written it. With the tick off, the prompt and the
project's `AGENTS.md` give the same line as the tools. An agent adds an exploratory note to a passage and keeps the
notes already there. Before, a write of notes replaced them all.

`/api/themes-ai` carries the titles, with `op` of `names`, the workbook, `version` and `group`, the label's id. It
goes through the same `ai_route` as a suggestion. It refuses with the switch off, and refuses any other op as
something the AI help does not do. It answers with up to three `names`, and `said` when quotes went for room, and
writes nothing. The page also sends `statements`, `label`, `note` and `others` beside the id, the shape a server
from before this reads. A body with no `group`, from a page before it, builds the prompt it always did from them,
so neither side breaks the other. `/api/themes` has `ai`, which says whether the switch is on and which model
answers. It is read from the settings and never includes the key. It also has `platform`, which says whether Show
in Finder can be offered, `project`, for the band, and `config`, the settings that Settings opens with over this
screen. `/api/settings` answers a save with `ai` beside `config`, so the titles take a new model at once. A page in
front of a server from before this reads the switch from its own copy of the settings. A press then says "Restart
the server to finish this update." and does nothing else.

**Guidance.** Guidance, the sidebar's tab after the Inspector, holds a short reminder to have to hand while
grouping, as the statements screen's guidance holds one for statements. It covers how many PETs to make, how to
group, how to title, what to discard, what goes first inside a PET, and what to ask before finishing. The sidebar
button opens the sidebar on it when it was the tab left showing. Guidance, first of the tools on the board's top
bar, opens the sidebar on this tab. Each group's heading is in the label face a step smaller, as the statements
screen's guidance's section headings are. Each line under it is in the serif at that guidance's size, a plain
line with a small mark before it. A line in inverted commas keeps them. The tab scrolls when the sidebar is
shorter than the text. Nothing in the tab calls a model, so nothing in it shows the sparkles.

The lines live in `themes_guidance.md` beside the app, in the format of `guidance.md`. It has an intro the app
never shows, then a `##` heading for each group with its lines under it, each starting with `- `. One parser
reads both files, `guidance_sections` in `server.py`, and it keeps this file's headings as written. `/api/themes`
has them as `guidance`, a list of `{"heading", "lines"}` in the file's order. The server reads them afresh on every
open of the screen, so an edit shows on the next reload with no restart. A missing file is an empty list, and the
tab then says there are no lines to show. A page in front of a server from before the tab gets no `guidance`, and
the tab says "Restart the server to finish this update." The AI never reads this file. What the titles are told
is `pet_guidance.md` (see AI help), the fuller text this one is distilled from.

**Autosave and the file.** Every act writes the whole board on the canvas about 300 ms after the last one, one
save at a time. Beside the board's name the save state reads "Auto-saved" with a tick whenever the canvas is
what the file holds, from the moment the screen opens. So a fresh open says "Board 1 · Auto-saved". It says
"Saving" while a save runs. A save that fails leaves a line there saying why, in the amber, as every failure
line is. Until 17 October, later, it stood in the crux orange, as did the boards menu's line when a board op
cannot go ahead and an AI title's line. The way back then keeps the canvas open. Opening writes nothing. A
participant with no file is offered their first board, and the file is written on your first move or your first
board op. It is `<case>/Working/<stem>.themes.json`, beside the progress file and with the stem the progress
file uses:

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
             "history_head": {"uid": "4b0f14c5a84214cc", "count": 30, "next": 31, "last": "...", "autos": 15,
                              "chunks": [[1, "9c41d0a2e7b3"], [2, "07fe5b1c88a4"]]}}]}
```

Beside it, in `Working/<stem>.themes.history/`, is each board's History in chunks, `<uid>.<n>.<hash>.jsonl`, one
revision to a line, oldest first:

```
{"id":"r1","at":"2026-10-01T22:15:02+01:00","name":"","auto":true,"state":{"cards":{...},"groups":[...],"discarded":[...],"picks":{...}}}
```

`case` is the participant by their pseudonym, for the cross-case step. The second part of a folder name never
reaches it. A card keeps its place and the text it had when the board was made. A group keeps its id, its label,
its note when it has one (see PET notes), its members, which are card keys or the ids of other groups, and the
place of its label. `picks` holds each label's picked quotes by quote key, and a label with none is left out.
`quoted` holds the words of each picked quote as the workbook read them at the last save. The server writes it,
and the page never sends it. `cut` holds the cards a trim cut, a record for each trim under its id, kept until
that trim is undone. `ai` holds why a statement was left out, by an agent or by a New AI board before 11 November
2026. A board with no reasons has none. `review` and `revise`, a board's AI review rounds and revise thread from
before 11 November 2026, are kept as the file holds them. Nothing reads them, and the page sends neither, so a
save leaves the file's as they were. `notes` is the board's sticky notes (see Sticky notes). Each has its id, its
words with their lines, its colour (yellow, pink, green or blue), its place, and `in`, the id of the group it
sits in. `normalise` drops `in` when it names no group, so the note stands free. A note is never among a group's
members. A board with no notes has none, so a file from before them reads and writes as it did and the schema
stays 2. A save from a page that sends no `notes` leaves the file's as they were. A revision holds them, so its
hash takes a note's words, its colour and its place. Restore brings them back and Duplicate copies them. Neither
Copy to board nor a board an agent makes carries one. `/api/themes` has them as `stickies`, because its `notes`
says whether a save keeps a PET's note. Whatever the page sends, the server keeps a member in one group at most,
takes a discarded card out of every group, and keeps a pick only once, only for a label that is there and only
of a row with a card under it. `current` is the board on the canvas. `chosen`, beside it, is the Current board,
the one you are going with, and it never takes the place of `current`. It is set and cleared only through the
board op `choose`, and through `delete`, which gives it to the last board left when the Current board goes. It is
kept only while it names a board the file holds, and a file with none marked has none. `complete`, after it, is
the PETs marked complete (see The Current board). The board op `complete` sets it, and only `reopen` takes it off.
A file with no mark has none. A save from the canvas writes that board in place and keeps the name, the note and
the history the file holds. Those change only through the board ops, so a save sent just before a rename can
never put the old name back. The server refuses a save of a board the file does not hold, so a page left open on
a board deleted since cannot bring it back. With no file yet, only the first board is taken. Since 16 November
2026 a board's History is kept beside the file, never inside it, so the file stays small however long the
History runs. It is a folder named like the file, with `.history` in place of `.json`. Each board's revisions are
in chunks of about 256 KB, named by a random `uid` that the board's `history_head` gives. The head also gives how
many revisions the History holds, the next one's number, the last state's hash, how many the timer made, and the
chunks themselves. A chunk is never written over. Each is named by the start of its own hash, so the board file
names exactly the chunks its History is. A chunk that changes is written under a new name, and the old one goes
only once the board file names the new one. Each revision is one line, oldest first. It has its id, when it was
made, its name (empty for one without), whether the timer made it, and its `state`: the board's `cards`,
`groups`, `discarded`, `picks`, `ai`, `quoted` and `cut` as above. If a project's files held their History inside
them, the app moves it out the first time each file is opened. It keeps a copy of the file as it was in
`_Archive` first, and checks every revision before it writes the file without it. When iCloud has not yet brought
a chunk to this computer, the History tab says the History is not on this computer yet. Nothing changes the
History until it is. A chunk that iCloud moved off to save space is brought back as it is read. A revision keeps
the words its statements had when it was kept. It takes the words they have now when it is shown, restored or
copied from. So a find and replace changes the boards and leaves History as it is. A board's id is `v1`, `v2` and
on, from when the boards were versions, and is never shown. Schema 1, until 2 October 2026, held the boards
under `versions`, named Version 1, Version 1 copy and AI proposal 1. The app reads such a file as schema 2 in
memory, with its names said the new way: Board 1, Board 1 copy and AI board 1, and the "from Version 4" in an AI
board's note too. Opening it writes nothing, and the next save writes schema 2. The screen writes the workbook in
one case only, a statement edited in place (see Editing a statement). Otherwise it reads the workbook read-only
and without the lock guard. So a workbook open in Excel opens here as it was last saved, and nothing is said
about it. The app refuses a themes file it cannot read, with a line, and never writes over it. The demo's themes
file is gitignored, as its progress file is.

`/api/themes`, with `{"workbook": ...}`, answers with the cards merged with the stored board, the key quotes of
every row that has any, the board's picks and `history`, its revisions newest first without their states. With
`board` it shows that board in place of the one last open, and writes nothing. `/api/themes-save`, with the
workbook and the board as `version`, writes it. With `revision` of `auto` from the timer, it answers with the
history when it kept a revision. `/api/themes-versions` carries the board ops, with `op` of `new`, `duplicate`,
`rename`, `note`, `switch`, `delete`, `choose`, `complete` or `reopen`. It takes `id` for the board, which is null
with `choose` to clear the mark and absent with `complete` or `reopen`, and `name` or `note` where they apply. It
answers with the screen's state afterwards. The routes and the fields keep the word they had when the boards were
versions. The answers keep `versions`, `version` and `current`, with `chosen` beside them, the Current board's id
or null, and `complete`, the PETs' mark or null. `/api/themes-boards` carries the rest, with `op` of `copy`,
`revision`, `view` or `restore`. It takes `id` for the board, `revision` for one of its revisions, `group` and `to`
for a copy, and `name` for a revision. `view` writes nothing and answers with the revision as the canvas draws it.
The others answer with the screen's state afterwards. `/api/themes-export`, with the workbook and `version`, writes
the draft and the CSV. It uses the board on the canvas when none is named. It answers with both paths, and
`shown`, the two as `Working/<file>`. With `op` of `word` it writes the board's Word document at the participant's
folder's root instead, never over a file there. It answers with `word` and `shown`, the file's own name, and
`dated`, true when the date went in it. `/api/themes` has `word`, and a page in front of a server from before it
says to restart and writes nothing. With `op` of `reveal` it writes nothing. On a Mac alone it runs `open -R` on
the file named, `file` as `shown` gives it, or on the board's markdown draft. It refuses a file outside the
participant's `Working/` folder or the project folder. A Word document beside the workbook is the one file outside
`Working/` that it shows. Every route refuses a workbook outside the project folder. A page in front of a server
from before them shows "Restart the server to finish this update." and does nothing else. It shows it on the
canvas, in the board menu, in the Inspector where the quotes go, in the History tab, after a copy or after Export.
Its autosave works as before and keeps no revisions.

**Re-reading on open.** Every open reads column C afresh, builds the cards again and lays the stored board over
them, words before index. Rows renumbered by a trim or an assignment never get this far, because the themes file
moves with the rows in the same request (see Trimming the ends). If a stored card's key no longer holds the words
it was made with, the card looks for them first. It takes the key of a line with the same words that no other
card has claimed, setting the spacing aside and keeping the case. It looks on its own row first and then anywhere
on its sheet. So a line inserted at the top of a cell, or taken out of the middle of one, leaves every other card
in its PET and its place with no mark. So does a pair removed on the statements screen, or a pair whose place on
its passage moved. The key changes everywhere the board names it: its PETs, Set aside and the reasons for what was
left out. The file takes the new keys on the next save, because opening writes nothing. A revision follows its
words in the same way when it is shown and when it is restored, so a restore lands on the keys the workbook holds
now. Only then does the rule for a line apply. A stored card whose line reads differently at its key is marked
changed, with a small mark on the card and what it read in its tooltip. The file keeps the text the board was made
with, and the line as it reads now beside it, until you move the card or act on it. Then the live line becomes
the stored text. A stored card with no line is marked missing. In a PET it stays in its place, faded. In no PET
the sidebar lists it last under Missing from the workbook, with Remove to take it out of the board. A line that no
card claims gets a new card, waiting in the sidebar's Unplaced. A pick follows its quote's words in the same way
(see Picks), and so do the CSV's Proposed PET column and the print view.

## GETs

GETs is the step after PETs, across the study. Every participant's PETs stand on one canvas. There the analyst
looks for what they share and where they part, and groups them into group experiential themes. It is the PETs
canvas one layer up, the same code run in a GETs mode, so every act of that screen works here as it does there.

**Opening it.** In an IPA project, GETs is a tile in the row at the top of the project's page (17 November 2026).
Before, it was a wide card after the participants' rows, and until 18 October over them. Its status line, in the
small type, reads as in "3 of 6 participants in · Board 2". It gives how many of the study's participants the
GETs file holds and the name of its Current board, or "No Current board" when it has boards and none is Current.
"GETs complete" follows once you mark it. The tile opens the GETs of that project, from its own root. The demo is
a project of its own and has the same tile. GETs is the third of Idiograph's tabs on each of its bars (see
Idiograph's tabs). It opens the GETs of the project the participant belongs to, or the demo's for the demo, after
saving anything still to save. Back goes to where you opened the screen from: the participant list, Experiential
statements on the passage you were on, or that participant's PETs on the board it was on. The tabs name each
screen of Idiograph on the bar. The GETs bar mirrors the PETs bar. It shows Idiograph's lockup, then the tabs with
GETs in front, and on the right Search, the bug for Send feedback and Settings. Under the band is the toolbar,
with Participants at its left end and Inspector at its right end, each over the sidebar it opens (see One title
bar and The bars since 26 October 2026). The band shows the project's name and no participant picker, because
GETs belongs to the project. Then come the board switcher, its save state, the Canvas and Table switch and
Export on the toolbar (see Print). Until 19 October the counts stood on the bar too, "7 in GETs · 3 unplaced",
with "· 2 discarded" after them only when a card was in the bin. After them stood Sticky note, Group, Undo and
the shortcuts. They went to the status bar and the palette, as on PETs, where the counts read "3 GETs", "7 in
GETs", "15 unplaced" and "0 binned" (see The status bar and the palette).

**The bar at narrow widths.** The GETs bar gives way at the PETs bar's widths. At 760px and below it takes the
three rows of Idiograph's tabs. Its project name is longer than a participant's, so it truncates with the
board's name. Until 19 October it did so once the counts had gone. It was measured again on 5 October 2026, with
the sidebar button in the place of the Inspector's, Board's and the shortcuts. That was on the demo's project as
it is named now, "Living with a dog", with its three participants as ordinary participants of a project folder,
opened from the GETs card. It needed 773px at its fullest, 711 with the save state's mark alone, 481 without the
counts, 441 once the gaps close up and 376 with the buttons slimmed, counting the bug. The word PETs on the way
back added 30. On the demo itself its tag added 63, or 47 once the buttons slim. It was measured again on 16
October with Participants at the left end and Group, Undo and the shortcuts on the bar. It needed 892px at its
fullest, 826 with the save state's mark alone, 589 without the counts, 546 once the gaps close up and 435 with
the buttons slimmed. Below 480px the names give way in full, as on the PETs bar. Below 480px Sticky note takes the
buttons to the right edge. Until 18 October Group did, and until 16 October, with no Export, the Participants
panel's button did. Down to 400px nothing overlaps and nothing scrolls sideways. Measured again on 18 October
with the steps of the time and Sticky note, it needed 852px at its fullest, 789 with the save state's mark alone,
687 without the counts, 663 once the gaps close up and 529 with the buttons slimmed, and took its two rows where
the PETs bar did. The tabs stay at every width (see Idiograph's tabs).

**What comes in.** The study is every participant's folder under the project's root with an annotated workbook,
as the participant list finds them. For a folder holding two workbooks, it is the one with a themes file, then
the newest. A participant goes by the pseudonym their themes file names. Opening writes nothing. Each participant
not yet in shows as they would come in, with their PETs and sub-themes in the pile. The file takes every such
participant on your first act on the screen: a move, a label, a board op or a save from Settings. A participant
with their PETs marked complete comes from the board the mark names. Any other comes from their Current board, or
else the board last open, and their cards show "PETs not complete". A participant with no themes file reads "No
PETs yet". What comes in is a copy. It holds each PET and sub-theme with its title, note, parent, sub-themes,
statements and picks. It holds every statement of the participant, placed, unplaced or discarded, with its
sheet, timecode, words, quotes and exploratory notes, read from the workbook. Every sheet is pooled, and each line
names its sheet. The screen writes a participant's files only when a statement is edited on its card (see
Cards), and then it goes through the PETs board's route.

**Cards.** A card is one participant's PET, sub-theme or statement, or a participant note. Over its words it names
its kind and pseudonym in the small sans: "PET · Juno", "Sub-theme · Juno", "Statement · Juno" or "Participant
note · Juno". A PET's card counts its statements at any depth. A statement's card shows its timecode and its
sheet, with its PET and that PET's GET under its words, as in "Mornings · Starting the day". The marks go at the
foot: "PETs not complete" for a participant not yet marked, and "No longer in Juno's PETs" for a PET the
participant's board has dropped. Every card of a participant, a PET, a sub-theme, a statement or a participant
note, shows the participant's colour along its top edge. A badge before its kicker shows the participant's
initial in a dot of that colour, "J", or two letters where two participants share one, "Ju" and "Ja" (see
Colours). A PET's and a sub-theme's words are read-only here. Since 30 October a statement's are not (Adam: "Edit
there too"). A double-click on a statement's card opens it for editing on the card, as on PETs. Enter writes it
into the participant's own workbook. The participant's PETs boards, the Participants panel and every GETs board's
card take the new words at once, and the participant stays in (see Editing a statement, under PETs). From 16 to
30 October that double-click opened the statement's passage on Experiential statements. Go to the passage in the
card's menu still does that (see From a statement to its passage, under PETs). A double-click on any other card
opens the sidebar on the Inspector for it.

**A PET card unfolds in place (21 October, Adam's ruling of 20 October, from a tester's wish to see a PET's
statements on GETs).** A PET's or a sub-theme's count, "7 statements", has a chevron. A click on it, or Unfold in
the card's menu after Inspect, unfolds the card where it stands. Under its foot, behind a hairline, come its own
statements, then each of its sub-themes by its title with the statements under it. Each statement shows its own
quote and its timecode, and its exploratory notes too when Notes is on. A statement stacked under another on its
participant's board stands under its top, a step in, as on PETs. The chevron again, or Fold in the menu, folds it.
Nothing is placed. Unfolding brings no card onto the board and changes nothing in the GETs file, so it is no step
of undo. What stands below the card moves down to make room, as it does for a quote, and moves back when it folds.
The cards you leave unfolded stay unfolded after a reload. The browser keeps them with the board's view, Canvas or
Table, for each board of each project. Auto-arrange, Arrange by participant and Fit all take an unfolded card at
its whole height. The Table view and the print are unchanged. A PET with no statement and no sub-theme, a
statement's card and a participant note have no chevron.

**The canvas.** It works as on the PETs screen. `G` puts a label over the selection. A label over cards is a GET
and a label over labels a sub-theme, and a GET takes the next of G1, G2. Boards, the Current board, history, undo,
Set aside, sticky notes, Auto-arrange and the Inspector work as they do there, through the GETs routes. The sidebar
holds the Inspector, Guidance and History (see Table and AI help). The minimap stands above the zoom bar as it does
there. Each card is in its participant's colour wherever it stands, and each GET's and sub-theme's frame is an
outline in its tint (18 October). Every PET and every sub-theme of a participant lands in the pile as a card of
its own on first coming in, in no GET. So a sub-theme can sit under one GET and its PET under another. A
sub-theme's groups, at any depth, ride inside its card with no card of their own. Its count takes in their
statements, its Inspector lists them under Groups, and AI suggest GET titles sends their statements with the
sub-theme's. Take, New board and Add every sub-theme all work this way. New board lays every participant's PETs
and sub-themes in the pile afresh, in an order seeded from their keys. Add every sub-theme is in the board menu
after Save a revision. It gives a board made before sub-themes came in as cards a card for each sub-theme of the
study that it has none of. A card set aside counts as one. They go in one pile in the nearest free spot clear of
every card, label, frame and sticky note there, as one step of undo. With none to add it says "Every sub-theme has
a card on this board already, so nothing was added." Copy to board belongs to the PETs screen alone.

**Arrange by participant (19 October, from a tester's reflection on IPA in ATLAS.ti).** It is in the board menu
after Add every sub-theme, and on a right click on empty canvas after New sticky note. It sets out every PET and
sub-theme card that is in no GET and not set aside in a row for its participant. The rows follow the Participants
panel's order. Each PET comes in the participant's PET order with its sub-themes beside it. Each PET after the
first stands a little further off, so it starts a small group of its own. A sub-theme whose PET is in a GET or set
aside goes at the end of its row, so a row reads PET by PET, each followed by its own sub-themes. The rows go
below everything that stays, at its left edge. The GETs you have made, with all they hold, a statement's card, a
participant note and a sticky note stay where they are. It is one step of undo. With every PET and sub-theme in a
GET or set aside, it says "Every PET and sub-theme is in a GET or set aside, so nothing was moved."

**The Participants panel.** This is a sidebar of its own at the left of the canvas. It is the source you make the
GETs from, as Figma keeps its layers on the left and its properties on the right. Its button, Participants, stands
at the left end of the bar over it, before the way back. It is the same panel icon with its left part filled, with
"Show Participants" or "Hide Participants" in its tooltip, as Inspector stands at the right end over the sidebar
at the right (16 October). Until then it stood before the sidebar's button near the cog, with "Show the
Participants panel" in its tooltip. Its cross sits at its head. It is open unless you closed it, and the browser
keeps that. It lists every participant of the study in participant order, with the participant's marks under the
name: "PETs not complete", "No PETs yet", "Changed since it came in" and "Out of the study" with the reason. The
swatch of the participant's colour stands at the right, before the menu (see Colours). A participant with no PETs
says "No PETs yet" once, in that line, folded or open. Until 17 October, later, a participant folded open said it
a second time at the panel's left edge. Since 16 October each participant folds open to a tree, as their board
holds it (a tester's ask, Adam's word). It shows each PET, then under it its own statements and its sub-themes,
each sub-theme with its statements under it. A statement in one of a sub-theme's own groups stands under that
sub-theme, as its card shows them. Last comes a row Not in a PET, holding every statement in none, unplaced or
discarded on the participant's board. Each level folds on its own with the chevron at its left. A PET's, a
sub-theme's and Not in a PET's row count the statements under them, and each statement is marked placed,
unplaced or set aside. The browser keeps the folds as it keeps the panel's open state, for each project. So the
tree is as you left it after a reload and when you come back from a passage. One search over all of it matches
names, titles, notes, statements, quotes and exploratory notes. It shows what it finds with the rows that hold it,
and opens those rows. A participant's name found shows all of the participant, and a PET's or a sub-theme's title
found shows all of it. A chevron pressed during a search opens or shuts its row until the search changes. You can
drag any row onto the canvas as a card, a PET, a sub-theme or a statement at any level. It goes into the GET under
the pointer when there is one. If the row's card is already on the board, the drag moves that card there, out of
Set aside if it was there. A click on a row selects its card and brings it into view. Each is one step of undo. A
double-click on a statement's row opens its passage on Experiential statements, as Go to the passage in its
card's menu does, whether or not its card is on the board. The way back returns to the GETs board as it stood (see
From a statement to its passage, under PETs). A participant's menu, the three dots at its right, holds Add
participant note and Open beside (see Open beside this one). A statement stacked under another on its
participant's board (see Stacks) stands under its top in the panel. Its top's row says "3 stacked", which opens
them a step in, each a row to drag. Until 20 October it stood under Not in a PET. The Inspector of a PET's card
lists them under their top, "Stacked under it". Below about 900px the panel lies over the canvas, as the sidebar
does, and stops above the zoom bar. At a phone's width it takes the whole width. Until 16 October, later, it left a
strip of cut-off cards beside it, with the bin and the zoom bar in view below it and never under it (17 October).
Its list scrolls from right under the search field. Once it has scrolled, its top edge fades over a line's height,
so a row passing under the field fades out and never stands cut in half, as the transcript's column fades. At rest
its first row stands whole (17 October, later). A level folded open has a thin guide line from under its chevron
down to its last row.

Since 20 October the Participants panel has **Set aside** at its foot in place of the bin, as the PETs board's
sidebar has. It is folded until you open it, with its count at the right of its head. Each card set aside shows
its participant's badge and Put back, which puts it back on the board in no GET. A card dragged from the canvas
onto it is set aside, and `X` and Set aside in a card's menu do the same. You can drag a row of it back onto the
canvas. The Participants panel itself was already GETs' Unplaced, so it gains nothing else.

**Colours (16 October).** Each participant keeps a colour of their own on the GETs board. So you can see at a
glance whose PET a card is, and which PETs, sub-themes and statements belong together. The participants stay
visible inside the GETs, as the book asks (Smith, Flowers and Larkin, 2022, ch. 5). This was a tester's ask and
Adam's word. The colours are the participants' palette. There are eight of them, Blue, Olive, Plum, Brown, Indigo,
Teal, Purple and Slate, lighter in dark. None of them is the crux orange and none is red. Each stands apart from
the others and from Supports' green, the amber and the red, under colour blindness too. A participant takes
their place in participant order round the palette: the first Blue, the second Olive and so on, and the ninth
Blue again. The badge, the initial or the two letters, tells two participants of one colour apart. Since 21
October there are 25 colours (see More colours), so the ninth is Moss. The swatch on a participant's row in the
Participants panel shows their badge in their colour. It opens the colour choice under it, "Juno's colour". The
choice has Default, the participant's own place in participant order, then the eight. Each is a whole row with
the participant's badge in its colour, and the one they have is ticked. A choice applies at once, and the cards,
the panel and the Table view are drawn again. The app keeps it in the GETs file under `colours`, which every
screen and the print view read. Default takes your choice away. It is no step of undo, because it is no part of a
board, and it holds on every board of the project. The badge goes with the participant's name in the Table view,
the audit trail and the print view's GET table and trail. The canvas printed under Export keeps the cards as
they are, with their colours.

**More colours (21 October, Adam's choice of 20 October, as a tester's studies have about 20 participants).** The
palette holds 25 colours. The eight come first, then Moss, Spruce, Violet, Aubergine, Pine, Denim, Khaki,
Mulberry, Fern, Periwinkle, Umber, Grape, Ocean, Amethyst, Jade, Navy and Fig, each lighter in dark. A new
participant takes their own place in participant order while no one has that colour, and otherwise the next
colour free after it. So no two participants share a colour while one of the 25 is free. The colour choice shows
Default and the eight. A colour another participant has is faint, with whose it is, as in "Mabel's". Then comes
More colours, which opens the 25 beside the menu in a grid of five. The participant's own colour is ringed, and
each colour another participant has is struck through, with "Another participant's" under them. You cannot
choose a colour another participant has. Every card keeps its participant's badge, so colour is never the only
way to tell participants apart. Neighbours in the picker's order stand apart as seen and under protanopia,
deuteranopia and tritanopia. That covers each colour and the next, and each colour and the one under it in the
grid.

**Colours told apart (16 October, later).** In dark, Blue, Indigo, Purple and Slate had read as one pale lilac on
the cards' edges and in the colour choice. So the dark colours are spread in hue and lightness: Blue a pale sky,
Olive a bright yellow green, Plum a pale mauve, Brown an ochre, Indigo a strong blue violet, Teal a deep teal,
Purple a strong orchid and Slate a grey. Each pair stands apart as the light ones do, as small marks and under
colour blindness too. Default in the colour choice names the colour it gives, "Default (Olive)". Each row shows
the participant's badge in its colour, as their cards will. The badge's letter stays readable at every size it
is drawn. On a card it grows as the canvas zooms out, up to the card's top edge. Below 54% the badge keeps its
colour without the letter, because the letter could no longer be read. It is larger beside a name in the audit
trail, the Table tab and the print view, and the canvas printed under Export grows it as the canvas does. A GET's
title on the GETs board takes its dot and its underline in the ink, so a GET never reads as a participant's
colour. So do the left edge of each card in it, the stripe of its head in the Table view and the underline of
its title in the audit trail (17 October). Its frame and its cards keep its tint as their wash.

**Participant notes.** Add participant note puts a card for your words in the middle of what is in view, with the
sidebar open on the Inspector for it and its box ready. It holds what you know of the participant beyond the
transcript. Enter or a click away keeps the words, Shift + Enter starts a new line, and Esc leaves them as they
were. Each change is one step of undo. A note sits under any GET and never counts.

**The Inspector.** On a PET or a sub-theme, it shows its note, its sub-themes, its statements and its picks. On a
statement, it shows its sheet and timecode, its PET and that PET's GET, its own quote and its exploratory notes.
Under a GET, a PET's picks and a statement's quote have the ticks of Key quote for that GET (see Table). On a
participant note, it shows your words in a box. On a GET, it shows its count and the minimum when the GET is
under it. Auto-arrange and Audit trail stand side by side on one row (see The audit trail). Then come its note,
"Why this GET", and the participants of the study. A participant with nothing under it says "Nothing under this
GET".

**The count and the minimum.** Each GET's badge reads "6 of 8". The first number is the participants with a PET,
a sub-theme or a statement of theirs anywhere under it, sub-themes included. The second is the participants in
the study. A participant note never counts. A second card of a PET counts its participant once, and so does a PET
with its own sub-theme beside it. A PET under one GET and its sub-theme under another count the participant once
under each. A sub-theme inside a GET shows its own count with no mark. The minimum starts at Smith's (2011a)
band: every participant for three or fewer, three for four to eight, and half, rounded up, beyond eight. You can
always change it. A GET under the minimum keeps its place and its cards. Its badge takes a dashed outline with
"Under the minimum of 3" in its tooltip, and the label's tooltip says it too. Nothing is removed or hidden.

**One GET per PET.** This is on by default. A PET or a sub-theme then sits under one GET at most, as every card does
on the PETs screen. When it is off, a PET's or a sub-theme's card has Place also under in its menu. That lists the
other GETs and sub-themes and puts a second card of it under the one you choose. Each card then names the other,
as in "Also under Deciding". A pulled statement or participant note sits under any GET. A PET under no GET stays
in Unplaced, which the counts in the bar give.

A statement's card on the GETs board says under its words where it comes from, as in "PET: Being trusted by the
hive · GET: Belonging". That is the PET it sits in on its participant's board, and the GET that PET's card stands
under. While that card is in no GET, it gives the PET alone. When the statement is in no PET, it says "Unplaced in
its PETs" or "Set aside in its PETs". Until 20 October the line gave the PET's title alone, which read as a note of
unknown source.

**Changed since it came in.** On each open, a participant whose workbook and themes file are both older than the
time they came in is unchanged without a read. Any other is read again and compared with its copy. Since 20
October there is no Take the changes (Adam, from a tester's feedback: "just take the changes automatically"). A
change you made in the app, on the participant's PETs or their statements, in this window or another, comes into
the GETs by itself. It comes as the screen opens, or within thirty seconds while it is open, with "Brought in the
changes to Juno's PETs." at the foot of the canvas, as one step of the board's undo. A change made outside the app
shows "Changes made elsewhere" with Update in the top right of the canvas. Update brings it in the same way. Until
then the participant is marked "Changed since it came in" in the Participants panel. Bringing the changes in
keeps a revision of each GET board, "Before Juno's changes came in", with its line in History. It keeps each PET's
place by its id, and then by its title. It brings in a PET or a sub-theme new to the participant, unplaced, in the
nearest free spot, as it does a top-level PET with no card. It leaves a PET gone from the participant where it is,
with "No longer in Juno's PETs" on its card, and never moves or sets it aside by itself. A card that comes in
taller, because its PET was given a description or a title a line longer, makes room below it. What it would run
over, in its GET or among the cards in no GET, moves straight down just far enough to clear it. What that meets
moves on in turn, so a column keeps its order and nothing moves sideways (22 October). A sub-theme the participant
had when they came in, and that the board never held, stays off the board, and Add every sub-theme brings it. A
participant marked complete since they came in comes in from their marked board in the same way.

**Mark GETs complete.** It is at the foot of the board menu, as Mark PETs complete is. It is refused unless every
participant in the study is in from their marked board and unchanged. The refusal says which participants, as in
"GETs were not marked complete. Waiting on Juno (PETs not complete).", and nothing more. It records the time and
the board: the Current board when one is marked, and otherwise the one on the canvas. It fires the third level of
confetti once. The menu then names it on that board and reads Reopen GETs, which takes it off. The head row says
GETs complete beside its count.

**Table.** The Canvas and Table switch on the bar, or T, shows the GET table of the board on the canvas, drawn
afresh with every act (see Canvas and Table). The sidebar's own Table tab went on 19 October, because the switch
does its job. A sidebar left on it opens on the Table view. Each GET comes in canvas order. Its title is in its
tint with its count, "6 of 8", and with the dashed outline and "Under the minimum of 3" when it is under the
minimum, as on the canvas. Then come its note and Audit trail (see The audit trail). Under it comes a row for
every participant of the study, in participant order. The row shows the pseudonym with the participant's marks.
Then it shows what of the participant sits under the GET, in the order the canvas reads it, higher first: their
PETs, sub-themes, statements and participant notes, each with its grip to move under another GET. A card inside
a sub-theme of the GET names it, as in "in Early starts". Then come the row's quote and your note for the row. A
participant with nothing under the GET reads "Nothing under this GET" in one plain line in the soft ink. A
participant with no PETs at all reads "No PETs, so nothing under this GET", with no mark beside the name. Before,
the screenshot check found "No PETs yet" in amber with the line under it (17 October, later). A participant note
alone leaves it so, because a note never counts. The quote starts as the first pick of the participant's highest
PET there. Failing a pick, it is the first statement there with a quote of its own. On a participant's card under
a GET, the Inspector shows Quote for that GET. It lists a PET's picks first and then its statements' quotes, or a
statement's own quote, each with a tick. The row's quote is ticked: filled when you ticked it, and lighter when it
is the one the row starts with. A tick on another makes it the row's quote, and a tick on the one you ticked takes
your tick off. Note, under a row, opens a box for your note, and a click on a note opens it again. Enter or a click
away keeps it, Shift + Enter starts a new line, and Esc leaves it as it was. Each tick and each note is one step
of undo, and both are kept in the board's `rows` (see The file). Print, Save as PDF and Microsoft Word are under
Export in the toolbar, and the table's head has none of its own (16 November 2026).

**The audit trail.** Audit trail, in a GET's Inspector and under its title in the Table view, saves anything
still to save and then opens a card over the screen for that GET. The card shows its title in its tint, its count
and its note. It has five columns, Transcript passage, Quote, Statement, PET and GET, joined by thin lines in the
GET's tint. There is a block for every participant of the study in participant order, with the pseudonym at its
head and the participant's marks. "Nothing under this GET" stands in one plain line when nothing of theirs counts
there. A participant with no PETs reads "No PETs, so nothing under this GET", with no mark beside the name, as in
the Table and on paper (17 October, later). Its kicker, Audit trail, is in the soft ink, as every card's kicker
is. It is never the crux orange, which design.md keeps for a crux, a quote and the filled button (17 October,
later). Each item under the GET draws its own path from the GET at the right. A PET or a sub-theme runs through
its statements at any depth and their quotes to their passages, with the statements of one passage together in
one box. A statement pulled onto the board runs through its quotes to its passage, with its line crossing the PET
column. A participant note stands alone in its block, marked "Not from the transcript", with its line dashed. The
row's quote is marked Quote, and a statement with no quote goes straight to its passage. A passage shows its sheet
and timecode and the sentence round the quote, with the quote's words in bold. These are read from the workbook,
opened read-only. When the quote is not found, it shows the passage's opening words. Its passages stand at the
trail's own size. A box's small print, its kind, its place and its sheet, is in the soft ink, which keeps 4.5 to 1
on the box's wash in dark where the faint ink did not (17 October). On a participant with a recording, a click on
a passage plays it from the passage's timecode, and a second click pauses it. The lines are drawn from each row,
so they meet at any width and on paper. The card is readable down to 900px, and below that the trail scrolls
sideways. Print in the card prints this GET's trail (see Print). Esc closes the card, and the canvas hears no key
while it is open. Nothing is written. The server draws the trail, through `/api/gets-trail`.

**Open beside this one.** In the PETs participant picker each other participant has Open beside this one, over
Open as table. The canvas splits. Your participant stays on the left as it is. The other stands on the right on
their Current board, or else the board last open. It is read-only, as a revision on view is, under a line
naming the participant, the board and Read-only. Nothing on it moves. A drag pans it, the wheel zooms it, Fit all
brings all of it into view, and its cross puts the canvas back whole. On the GETs screen a participant's menu in
the Participants panel holds Open beside. It puts that participant's board beside the GET canvas in the same way,
using the board their PETs came in from. Below 900px the two stack, with your canvas above. Opening a participant
or leaving the screen closes it. Neither writes anything.

**Print.** Since 16 November 2026 Export is in the toolbar, as on PETs, and its menu follows the view. On the
canvas it holds Print, Save as PDF and Save as an image, then Include and Participant notes. In Table view it
holds Print, Save as PDF and, for a thematic analysis project's theme table, Microsoft Word. Then come What to
print (GET table, Audit trail, All of it in one document), Under each participant (Every statement and quote,
Their key quote only), and Include, with Descriptions, Participant notes, which is unticked at each open, and
Participants table. Each choice's line is in its tooltip. Until then Export stood in the board menu above Mark
GETs complete and opened the card below. A GET's own audit trail still prints from that card. What to print is a
list of four. Each shows its name with a line under it in the soft ink saying what it gives, and the whole row
chooses it (31 October, Adam: never a choice left unexplained). GET table gives "Each GET with a row for every
participant, what of theirs sits under it, its key quote and your note". Audit trail gives "Each GET traced for
every participant, from the transcript passage to the quote, the statement and the PET". All of it in one document
gives "A contents page, each participant's table of PETs, the GET table and the audit trail". Canvas on one page
gives "The GETs board laid out on one landscape page". Until 31 October they were four short buttons, GET table,
Audit trail, Full set and Canvas, with the rest in their tooltips. Under each participant then offers two choices
in the same way. Every statement and quote gives "Everything of theirs under each GET, with its quote". Their key
quote only gives "The one quote chosen for them under each GET". It is the choice the book leaves to the analyst.
Before, they read Full and Selected. Then come Descriptions and Include participant notes, unticked each time.
Since 17 October, later, its tick is in the ink. Before, it was the crux orange. Leave out the board's name (For
sending until 31 October) was the next tick until it went on 16 November. Last comes Participants table (11
November). It is off on a new install and kept as you leave it. It puts a table of the participants on a first
page (see The label and the pen portrait in the exports). It shows for the GET table, the audit trail and all of
it in one document. Canvas on one page prints the canvas itself, as Print under Export does on the PETs canvas
(see Export, under PETs). Every card is whole, on one landscape page under the project's name and the board's.
Under each participant goes while it is chosen. Print saves anything still to save and opens the print view in a
tab of its own, `/gets/print?root=<path>&board=<id>&what=table`, with `trail` or `all`, `detail=selected` and
`notes=1` when chosen. Save as PDF has stood beside Print at the card's foot since 31 October. It saves the same
page as a PDF at the project's root, where the PDF an agent makes goes, named the same way, with no print dialog.
A line names it once it is written. It is there for the GET table, the audit trail and all of it in one document,
which holds the contents, each participant's table of PETs, the GET table and the trail. It works in a browser's
tab too. For a participant's LPETs it opens Print, where Save as PDF is. Since 1 November, with Canvas on one page
chosen, Save as PDF saves the canvas's page as the PETs canvas's Save as PDF does. It goes at the project's root,
as in "Study - Board 2 - GETs canvas.pdf", or for a participant's LPETs beside their workbook. Save as an image
beside it saves the canvas's picture as a PNG named the same way. A participant note shows on either only with
Include participant notes. The page is landscape A4 with a 14mm margin, in the faces of the PETs print. It opens
for reading on screen, and Print at its top right opens the dialog. The head is the table of PETs' head (31
October, and in full since 1 November). Its title is the document's name, "Table of Group Experiential Themes",
"Audit trail" or "Group experiential themes", with PROJECT and RESEARCH QUESTION to its right and no rule under it.
The board and the date are in the foot. Under the head come the board's note and, only when there is one, any
participant not complete, with no PETs yet or changed since they came in. Until 1 November the head also gave the
minimum, "Minimum 3 of 8 participants, Smith's (2011a) band", and what the pages hold, "Every item" or "Quotes
alone". Adam had them taken off, and the settings stay where they are set. The GET table sets out each GET as the
Table view does. Each is in a bar of its tint with its count, the dashed outline and "Under the minimum of 3" when
it is under, and its note. It has a table of Participant, Under this GET, Quote and Note. Their key quote only
keeps Participant, Quote and Note. In the print view on a narrow screen, the table keeps room for its four columns
and scrolls sideways in its own box under the GET's bar. The bar puts its count and Under the minimum under the
title. At 360 pixels the columns used to stand a word to a line (17 October, later). A quote stands in single curly
quotation marks, ‘like this’, in the GET table and the trail, as in the table of PETs. Before, the two used straight
double ones (17 October, later). A participant not complete, with no PETs yet or changed since they came in, stands
in the warning's amber in the header, the table and the trail, as the Table view sets it. Before, it was an orange
brown (17 October, later). The audit trail gives each GET a page of its own and keeps a participant's block whole on
a page. On paper each block with paths opens on the five columns' heads, so every printed page shows them, as a
table's headings do. Before, they stood at each GET's start alone. The screen shows them once under the title (17
October, later). Its words wrap whole, never through a letter. A column too narrow for its longest word takes the
room it needs from the others, on paper and in the card alike. In the print view on a narrow screen the trail
scrolls sideways in its own box under the GET's title. At 360 pixels the PET and GET columns used to break their
words letter by letter (17 October, later). Its five columns keep about 720 pixels together there, as the table
does. Before, they squeezed to a word or two to a line (17 October, later). The full set opens on a contents page.
Then comes each participant's PET table as it came into the GETs, in the print view's table of PETs, labelled the
project's way. Each statement is a row with its own quote on the right, and a sub-theme comes after its PET's own
statements. Their key quote only keeps a row for each PET's picks alone. Then come the GET table and the trail.
Participant notes appear nowhere in any of it unless Include participant notes is ticked. The transcript stays
the XLSX. Every file is only read, and nothing is written. The app refuses a folder that is not the project folder
or the demo's, and a board or a GET the file does not hold. Each refusal is a page of one line. Since 17 October,
later, it is in the print views' own faces on their white paper. Before, it stood in the system's font. `auto=0`
leaves the dialog shut. Every print view says that it is in British English, as the app's pages do. From the audit
trail's card it prints that GET's trail alone. `gets_print.py` renders it.

**AI help.** With AI features on in Settings, and its GETs switch on, the GETs screen offers the PETs screen's AI
titles one layer up, with the sparkles, through the PETs model and the same key. It is AI suggest GET titles in
the Inspector of a GET. It sends the project's research question and section 4 of `pet_guidance.md`, what a GET is
and its rules, from Smith, Flowers and Larkin (2022, ch. 5, Step 7). The app reads the section afresh on every call.
Guidance, the sidebar's tab after the Inspector, shows that section and section 5, the questions a reviewer asks of
a GETs board. Each card goes by its participant's pseudonym, and each PET with its note, its sub-themes and their
statements, by sheet, timecode and words. Participant notes, sticky notes and a row's note never go to a model, and
nothing on the screen writes a workbook or a themes file. New AI board, AI review and AI revise went from GETs as
from PETs on 11 November 2026. A board one of them made is an ordinary board now.

**Guidance on the LPETs, LGETs and Trajectories screens** (17 November 2026). Each of the three has lines of its own
in its Guidance tab, from the literature on following a person's themes across timepoints. They are
`lpets_guidance.md` on a participant's LPETs, `lgets_guidance.md` on the LGETs and `trajectories_guidance.md` on
Trajectories. They sit beside the app in the format of `themes_guidance.md`, and the app reads them afresh on every
open, so an edit shows on the next load. The GETs screen keeps the GETs lines above. Trajectories has its Guidance
in a sidebar at the right. It stays shut until you press Guidance on its right edge, as the boards' sidebars open,
and the screen remembers whether you left it open.

AI suggest GET titles sits in the Inspector of a GET or of a GET's sub-theme, and `N` asks it, as on PETs. It sends
what sits under it across the participants. That is each PET and sub-theme by its title with its statements, with
each participant named, and a participant with nothing there said so. It sends its count against the minimum, as in
"It holds material from 2 of the 3 participants, and his minimum is 3.", and the other GETs' titles, so the three
stay distinct. It sends rules 5 to 8 of section 4: recurrence, negative and incomplete trajectories, the title in
the participants' language, typically five to nine words, and no cause. A click on one takes it, and Undo puts the
old title back.

`/api/gets-ai` carries it, with `op` of `names`. It refuses with the switch off, refuses any other op, and refuses on
a thematic analysis project's Themes board. A page in front of a server from before it shows the control from its
own copy of the settings, and a press says "Restart the server to finish this update."

**GETs' rules.** Project settings holds them under GETs. From 20 October until 5 November 2026 they were Settings'
own category. The cog over this screen opens Settings on General. The rules are One GET per PET, the Minimum
stepper with "Smith's band" beside it while you have not changed it, and the study, with a tick for each
participant. The tick is in the ink, not the crux orange, since 17 October, later, as every tick is. Taking a
participant out asks for one line of reason, such as a pilot, and Save refuses one with no reason. A participant
out of the study leaves the count and the band, and their cards stay where they are. These live in the GETs file,
because the demo's project file refuses a save.

**The file.** It is `idiograph-gets.json` at the project's root, beside `idiograph-project.json`. It is written to a
temporary file and moved over the old one, as the themes file is. The demo's is `demo/idiograph-gets.json`,
gitignored:

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

A card's key names its participant and kind. A PET or a sub-theme goes by its group id, and a second card of one
has `/2` after it. `es` is a statement and `pn` a participant note. `hash` is the copy's hash, as the history hashes
a revision. `state` is `none` for a participant that came in with no PETs. `rows` holds the GET table's rows by GET
and then by participant, as in `{"G1": {"P8 - Wren": {"quote": "Initial:12:0", "note": ""}}}`. It gives the quote you
ticked, by its sheet, row and place among the row's quotes, and your note for the row. A row with neither is left
out, and so is a GET no longer on the board, so a new GET that takes a gone one's id starts with none. The page
sends the rows with the board. A page from before them sends none, and the server keeps the rows the file holds. A
board keeps `ai`, the reasons for what an agent left out, and `review` and `revise` from before 11 November 2026, as
a PETs board keeps them. A `cap` under `settings` from before then, the most GETs a New AI board proposed, is read as
nothing. `colours` holds the colour you chose for a participant, by their label. The value is its place in the
participants' palette from 0, Blue, to 7, Slate. It is missing until you choose one, and a participant not in it
takes their place in participant order (see Colours). Rename carries it to the participant's new label. A page in
front of a server from before GETs says "Restart the server to finish this update." on the canvas, in the board menu
and under GETs in Project settings, and changes nothing. A page in front of a server from before the colours draws
each participant in their place in participant order, and a choice says "Restart the server to finish this
update."

## Search

Search finds words across the app (17 October, and on Home since 18 October). It finds a passage, an interviewer
note, a statement, a quote, an exploratory note, a PET, a sub-theme, a PET's note, a sticky note, a board's note, a
GET and its note, a note on a row of the GET table, a participant note, a participant by their name, and the
research question. It leaves out AI suggestions. `Cmd + F` (`Ctrl + F` on Windows and Linux) opens it on every
screen: Home, the statements screen, PETs, GETs and a project's page. It works from the fields as well. Search on
the bar opens it too. That is the magnifier, in the place Find had on the bars. While a card stands over the
screen, the browser keeps its own find.

The card stands under the bar, with the field first and Search in at its right. While it is open, a wash of the
paper lies over the rest of the screen under the bar. So nothing cut off beside the card or under it reads as part
of it, as with the guidance sheet's wash (17 October, after the screenshot check). A click anywhere in the wash
closes the card and goes on to do what it does. On a project's page the page comes up to the project's name and
the card stands under it, so the name stays in sight. On Home the card stands under the lockup and the head's
tools, so a phone's width keeps its room for the results. While more results wait below, the last one in sight
fades at the card's foot. Every word you type is found, in any order, with case and accents set aside. So "walk
dog" finds "the dog's walk", and "cafe" finds "café". Each word finds its other forms too. So "sleep" finds
"sleeps", "sleeping" and "slept", and "walked" finds "walk" and "walking", each under the wash. Words in quotation
marks are found together and just as typed, so "sleep" in quotation marks finds sleep and never slept.

Beside Search in stand two ticks, Whole word and Match case, as Find and replace has them (6 November, after "cat"
found "catch"). Whole word is ticked when the app starts, as it is in Find and replace, and Match case is not. With
Whole word ticked, each word is found only as a whole word, together with its other forms. So "cat" finds "cat"
and "cats", and never "catch" or "catalogue". A phrase in quotation marks is found only where it starts and ends
on the edge of a word. A letter or a digit beside the word rules the place out, but a stop, a comma or an
apostrophe does not, so "cat" is found in "the cat's coat". Untick Whole word, and a word you type is found inside
a longer one too, so "cat" finds "catch". With Match case ticked, each word is found in the case you typed it in.
So "Will" finds the name and never the verb. Accents are still set aside, so "Cafe" finds "Café". A word's other
forms keep your case. "sleep" finds "slept" and "sleeps" and never "Slept", and "Sleep" finds "Slept". A word of
mixed case, such as "McKee", is found as typed, with no other forms. The two ticks work together. The words under
the wash follow the ticks, and the results change at once when you tick one. The ticks stay as you leave them each
time you open the card again, on every screen, for as long as the app stays open, as Find and replace's do.

Search in starts at This participant on the statements screen and on PETs. So you take a participant in depth and
on their own before another meets them, as the book has it. It starts at This project on a project's page and on
GETs, where meeting across the participants is the step. On Home it starts at Everything, which is every project
Home lists, including the demo. Everything is the last choice on every screen. On Home it is the only one, so
Search in does not show (18 October, later). This project reaches every participant of the project, its GETs, its
participants' names and its research question. If you widen the scope, it goes back to the screen's own the next
time the card opens.

At the card's left stand the kinds found under Kind, each with its count. With This project the participants and
the sheets stand there too, under Participant and Sheet, and with Everything the projects, under Project. Ticking
one shows that kind, participant, sheet or project alone, and ticking two shows either. Each ticks from its whole
row. Where the column is too short for them all, the last row in sight fades at its foot, and the column scrolls to
the rest. Below 700px they stand over the results: the first heading and three whole rows of ticks. More under them
shows the rest, and Fewer shows the three rows again. A row brought into the box by Tab shows them all, as More
does. A heading whose rows are all behind More shows with them, and never over nothing, as Project stood at 360 (18
October, later). A row under the pointer takes a fainter ground than a ticked one, so it never reads as ticked. At
the right each result gives its kind in small capitals and its words, with every word you typed under the find's
yellow wash. A long passage is cut round the first word found. Where it is stands in small type, as in "Juno ·
Initial 03:55", "Board 1 · PET B" or "GETs · Board 1". With Everything the project's name comes first. The first
200 stand in the list, and "200 of 1,234" under them says when there are more. A search that finds nothing says
Nothing found.

Up and Down walk the results. The one in focus is on the sunk paper with the orange bar at its left, and one under
the pointer is on a fainter ground. Enter opens the one in focus, and a click opens any, from whichever screen you
searched on. The screen in front is left as its own way out leaves it. A passage opens on the statements screen at
that passage. An interviewer's passage opens at the participant's passage after it, with the interviewer's in view,
and the note open when the result was the interviewer's note. A statement or a key quote takes the caret in its
pair, and an exploratory note takes it in the notes. A PET, a sub-theme, a PET's note or a sticky note opens PETs on
its board, with it selected in the middle of the canvas. A GET, its note, a row's note or a participant note opens
GETs in the same way. A participant or the research question opens the project's page at the participant's row. If
you opened the statements screen from PETs or GETs, its Back returns to the board, as Go to the passage on a card
does.

Esc, a click outside the card or Search on the bar again closes it. `Cmd + F` again brings back the last words and
their results.

Under a This participant search on the statements screen, Replace in the transcript closes the card and opens Find
and replace with the words typed (see Find and replace). Find and replace keeps `Cmd + Shift + F`.

A search reads the files and writes nothing. What it reads is held in memory against each file's time and size, so
the next search waits on no file. Nothing of it is kept on disk.

## Projects

A project is a root folder holding its participants' folders. Idiograph holds as many as you add, such as two
studies side by side, each with its participants, their Experiential statements and their PETs, and its own GETs.
The app names no study's folder anywhere. It remembers each root you give it. `config.json` keeps them as
`projects`, in the order you added them, each as `{"root": "<path>"}`. The path is absolute, or from the repo root,
or from the app's folder in a downloaded copy. A participant's folder in it is written as a glob on its pseudonym. A
`config.json` from before the projects, with `root` alone, reads as one project with that root. It is written in
the new shape only when Settings saves.

**The project of a path.** Every request that reads or writes a file asks which project the path belongs to: the
project whose root holds it. It then works on that project's root, its project file, its GETs and its participants.
The app refuses a path under no project's root, as it always refused a workbook outside the participant root. The
recent list, the PETs screen's switcher, which lists the participants of its own project, Find and every route keep
their meaning across projects.

**The project file.** A project has settings of its own, with the research question first, because the question is
what an experiential statement answers. They live in one file at its root, `idiograph-project.json`, beside the
participants' folders:

```
{"name": "...", "research_question": "...", "updated": "2026-10-01T12:48:00+01:00", "method": "lipa",
 "agents": {"allowed": true, "at": "..."}, "order": ["P3 - Cal", "P1 - Ada"], "pet_labels": "numbers",
 "timepoints": [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"}]}
```

`updated` is the time of the last save of the name or the question, in ISO form with its offset. `method` is the
project's kind, "ipa", "lipa" (longitudinal IPA) or "ta" (reflexive thematic analysis). You choose it on New project,
and it never changes after that (see New project). A project from before, with "ipa" or no method and two or more
timepoints, reads as "lipa", and the app writes nothing to say so. `agents` is the privacy tick (see AI agents),
`order` your order of the rows (see Your order), and `pet_labels` how the exports label the PETs. `pet_labels` is
missing, and so the book's letters apply, until you pick 1 2 3 (see Export, under PETs). `names` holds the new
pseudonym that Rename gave a participant whose folder it kept, by the participant's folder's label and never its
second part, as in `{"P1 - Ada": "Bea"}`. It is missing until there is one (see Rename). The server reads the file
afresh on every `/api/cases` and `/api/open` and sends it as `project`, with the root as Project settings shows it.
With no file, the name is the root folder's own and the question is empty. Project settings saves it through
`/api/project`. That writes the name, the question and the time, and keeps any other key the file holds. It refuses
a root that is not there, and does not make a folder to hold it.

**The project's own History** (2 November 2026). A change to the project itself keeps a record of when it was made,
what it changed from what to what, and who made it. That is you in the app, or an AI agent by name with the request
you gave it. A record from before 13 November says "approved in the app" or "without asking" where the agent's
action waited for your yes. Each save of the project's name, research question, PET labels, timecodes, timepoints or
statement length keeps one. So does each save of the GETs settings, a participant renamed, and a participant's
statements marked complete or reopened. A save that changes nothing keeps none. The records are in
`idiograph-history.json` at the project's root, and a shared copy never has them. An agent reads them with `project
history`. Project history, on the project's menu on Home (3 November 2026), opens them on a sheet. It shows every
change newest first under its day, each with its time, who made it, every line of what changed, and what the agent
says you asked. All, In the app and By an agent over the list show all of them or one side's alone. By an agent is
the record of every change agents made, with Undo (see Reviewing what agents changed). A long record reads on as you
scroll, and Done shuts the sheet. A project with no change yet says "No change yet.", and the demo's card has no
Project history.

**Project settings.** Each project's own settings are on a sheet of their own, Project settings (5 November 2026).
Until then they stood in Settings under Projects, with a row of every project's name over them. It opens for one
project. You open it from Project settings beside the project's name and question on its page, from the project
card's menu on Home, from File, Project Settings… in Idiograph's own window (greyed on Home), or from the band's link
when the project has no question. The sheet's head names the project. It holds the project's name and its research
question. Then comes its Method, IPA, Longitudinal IPA or Reflexive thematic analysis, which is shown and can never
be changed (31 October 2026). A longitudinal project's Timepoints stand straight under it (see Timepoints). Then come
PET labels, A B C or 1 2 3, the same choice as under Export on the PETs screen, saved at once in the same way, and
Timecodes. Then comes Interviewer name (17 November 2026, moved from Settings). Which speaker is the interviewer is
the project's data. It is the speaker whose turns are context in every transcript of the project, and the project's
rounds, quotes, imports and exports read it there. A project with no interviewer name of its own shows and reads the
name the app's settings held. Save writes it to the project's file once you change it. Then come the project's root
folder with Remove from Idiograph beside it, its Statement length under Experiential statements, and its GETs rules
under GETs (see GETs). With AI features on, the sheet also holds the privacy tick, Write a guide for AI agents and
Add Idiograph to Claude Desktop. A thematic analysis project's sheet has no PET labels, timepoints, statement length
or GETs. An IPA project's sheet has no timepoints. A long folder path runs onto the next line only after a slash,
never inside a folder's name, unless that one name is wider than the line. A demo's sheet is read-only. Save writes
the name, the question, the tick and the GETs rules when they changed, each to its own file. PET labels, timecodes,
timepoints and the statement length save as you change them. Open project is on Home.

**Reflexivity.** Reflexivity stands under the research question in Project settings (17 November 2026, Adam:
"reflexivity is a project setting... it's more a write-up thing"). It holds the researcher's reflexivity statement,
as plain text on as many lines as it needs, in every project, IPA, longitudinal or thematic analysis. Save writes it
to the project file with the name and the question, and an empty box takes it away. It is a place to keep the
statement and copy it into a write-up. No export prints it (Adam, 17 November 2026: "It's just there if you want to
paste it somewhere else"). It is not in the GET table, the LGET table or a thematic analysis project's Table of
themes, in the print view, the PDF or Microsoft Word, and there is no option to print it. The reflexive thematic
analysis demo's statement, its researcher's, is its Reflexivity, read-only like the rest of a demo's sheet. Until
then it was the Themes board's note. Reset demo puts it back as it ships. A shared copy, whether Share a copy's file
or a copy sent to work on together, leaves Reflexivity out, because it is your own positioning and not the
participants' work. A copy coming back never changes yours. There is no journal, and nothing of it shows on the
project's page.

**Working together.** Working together is at the foot of Project settings (8 November 2026). It has one tick, Work on
this project with others. It is off in every project until you tick it, so someone working alone sees nothing else.
The first time you tick it, it makes this computer's keys and makes you the project's lead, under Settings' Your
name. If Settings holds no name, you type one in the row that asks for it. Then it shows Send through, Relay or
Shared folder, with the folder and Choose beside it when Shared folder is picked. It shows People, each with how
many computers they have and the lead marked, with Remove beside everyone but the lead, and Invite and Add a computer
of mine. It shows Who works on each, where you pick a participant's person from a list and the GETs board's person,
with Hand over. Last comes Send the recordings too. Each change saves at once and goes into the project's History.
Invite opens a card with a link and twelve words, each with its copy button. Send the link by email, or read the
words out. It works once, for seven days. When the other person has pasted either into Join, both cards show the
same six digits under Check code. Read them to each other on a call. Then press They match, and they join, or They
differ, and their answer is thrown away. Join stands beside Invite while nobody else is on the project. Remove asks
one line first. Then the project's key changes for everyone left, so the person removed gets nothing new, and what
they already have stays on their computer. Unticking it stops anything more being sent or taken in. Ticking it again
picks the team up as it was.

**The relay code** (9 November 2026). The relay makes a project only for a relay code, which whoever runs the relay
gives out. The first time the lead sends through the relay, Working together shows Relay code under Send through.
Type the code and press Connect. The project is made on the relay, and the row goes. The code is used that once and
kept nowhere. A wrong code, a code that cannot start any more projects, or no connection is reported in one line,
and nothing changes. Invite waits until the project is on the relay. Someone who joins needs no code, and neither
does the shared folder.

Send through is the lead's choice alone, as who is on the team is. On a member's computer it shows the team's route
and nothing to pick. If a member asks to change it, the change is refused in a line, with nothing changed. When the
lead changes it, the change goes to everyone in the signed list of people, and each computer follows. Switching to
the relay waits for the relay code. The members stay on the old route until the project is made there.

**Who works on each participant.** Once someone has joined, the person picked in Who works on each works on each
participant. The GETs board has its own person, the lead until someone else is picked. Only that person's computer
changes the participant's files. On a participant someone else works on, the project's page shows a tag with their
name, as in "Curt's". Every change is refused with a line such as "Mabel is Curt's. Comment or suggest instead.".
Your copy of their work updates by itself. It comes in about a minute after their last change, and a screen you
have open on it says it has changes made elsewhere. A participant of yours goes to the others in the same way, about
a minute after your last change, and at once when you quit. Someone who joins gets a copy of everything at once.
Under the project's question, the project's page says what came in today, as in "Curt's changes to Mabel came in at
16:42". When there is no connection, it says how many of your changes are waiting, as in "3 waiting to send: no
connection". They go when the connection is back. A participant you add, with Add transcripts or an import, is yours
to work on. Once it reaches the lead's computer, Who works on each names you for it.

Since 9 November the lead also has Make lead beside Remove on each other person's row. It asks one line first. Then
that person is the lead, and adds and removes people from then on. The participants and the GETs board stay with
whoever works on them. Anyone on the project can use Add a computer of mine for a second computer of their own. It
uses the same card and the same six digits read off both screens, and the new computer can read the project at once.
When you are not the lead, the computer goes on the list of people the next time the lead's Idiograph opens the
project, and a line under People says so until then. When someone has two computers or more, each is listed under
their name. Remove this computer stands beside every one except the computer you are on, for a laptop lost or sold.
The lead can remove anyone's, and you can remove your own. The project's key changes, so that computer gets nothing
new. What it already has stays on it, as safe as its disk. You cannot remove someone's only computer this way.
Remove takes the person instead. Someone removed sees one line in Working together saying nothing new comes to their
computer.

**Working together through a shared folder** (9 November 2026). Send through, Shared folder, sends everything through
a folder the team already shares, such as a OneDrive, Dropbox or network folder, in place of the relay. Pick Shared
folder, then Choose and pick the folder, on each person's computer. It may sit in a different place on each.
Idiograph makes a folder of its own inside it, named Idiograph and eight letters of the project's id. Each computer
writes only in its own part of that folder, so the sync app never makes a conflicted copy. Everything in it is
sealed, as it is on the relay. Anyone else who can open the shared folder sees file names and sizes, never words.
Each computer looks in it every 15 seconds while the project is open, and again on waking from sleep. A message that
everyone has read is deleted from it. The person joining picks the same shared folder before pasting the invite into
Join. When the invite has not reached their computer yet, they are told it may still be syncing. When the folder is
not there, because a drive is not connected or the sync app is not signed in, a line under it says so: "This folder
is not there. Check that its drive or sync app is connected, or choose it again." When a file in it will not open
yet, a line says to keep the folder on this computer: in OneDrive, Always keep on this device.

**A board sent by a teammate.** With Working together on, you can still make boards of your own on the PETs screen
of a participant someone else works on. New board, Duplicate and every change on the canvas work as they do on any
board. Your own boards are kept on your computer, separate from theirs, and marked Yours in the board menu after
their names. They stay as they are when a new version of the participant comes in. Their boards stay theirs. On one
of their boards, the board menu's Rename, Delete this board, Mark as current, Edit the note and Save a revision are
greyed out, and a change to it is refused. Mark PETs complete and Reopen PETs are greyed out on every board, theirs
and yours, because the mark is theirs. Send board, in the menu of one of your own boards, sends the board on the
canvas to them. On their computer it waits, with nothing added to the participant. It shows on the same line as the
rest of Curt's review, as in "Curt's review of Juno: 2 comments and a board.", or "Curt's review of Juno: a board."
when he sent it on its own. Review opens the card. There "Curt's board of Juno's PETs" says "It comes in as your next
board, beside Board 1.", with Decline and Add as next board. Add as next board adds it as that participant's next
board, never the one on the canvas, named "Curt's board, 9 Nov". Its note says when it was sent and how its
statements came, as in "Curt's board, sent 9 Nov: 63 statements as sent, 2 reworded since.", followed by Curt's own
note. When the participant has no board yet, Curt's board becomes their only board, on the canvas, with no empty
board beside it. Decline adds nothing. Either way Curt's computer hears your answer. A waiting board stays waiting
when the app is closed and opened again. Each send, arrival and answer goes into the project's History, and the
board's own History says who sent it.

**Timecodes.** In Project settings, after PET labels, Timecodes says how the project writes a timecode. Each choice
shows an hour and a quarter in. 75:12 folds the hours into the minutes, 1:15:12 writes them once past the hour, and
01:15:12 writes them always. A new project starts on 1:15:12. The setting belongs to the project, not the computer.
So whoever opens the project sees its quotes cited one way: in the transcript's margin, the player, the boards, the
print views, Word and the PET draft. A press saves it at once. The statements CSV and the notes export keep
01:15:12, and the workbook's own Timestamp cell keeps its form. The demo's timecodes are fixed. The folder becomes a
project after the others and shows at once. The app refuses it when it is a project already, when it sits inside
another project's root or holds one, or when it holds the app or its demo. Cancel changes nothing. Remove from
Idiograph asks first in a small card (see Remove from Idiograph, below). Then it forgets the project. Its folder and
every file in it stay as they are, unless the card's tick moves the folder to the Bin. If you remove it from over one
of its own participants, the page saves what you typed and opens on Home.

**No project yet.** With no project, as the Mac app ships, Projects holds only New project, Open project and Open a
shared copy. Demo projects under it stands open with the four demos' cards. Open project there takes a folder
through the Mac's dialog, or off a Mac a field for the folder's path. The project you add opens on its page.

**New project.** Under the project cards on Idiograph's Home, New project opens a card that sets up a project and
nothing more (17 November 2026, Adam's two steps). Choose takes the folder through the Mac's dialog, or you type its
path, and the card refuses a folder as Open project refuses one. Name and Research question take what a project file
there already says, and you can leave either blank. Method is IPA, Longitudinal IPA or RTA. Longitudinal IPA asks for
its timepoints under it, T1 and T2 to start. Plus adds more, and minus goes down to two but never to one, because a
project of one timepoint is an IPA project. Each timepoint has a label and a description, the rows Project settings
has. Create project makes the project and opens its page, where Add transcripts brings in its transcripts (see Add
transcripts). The method stays the project's for good.

Add transcripts' card takes the transcripts. You drop them anywhere on the card or pick them with Choose files, in any
shape that make a workbook reads, and each is a row. A row shows its first passages and its speakers, each with a
chooser, Interviewer, Participant or Other speaker, as on the import card (since 20 October, in place of one
Interviewer chooser). It shows the participant's number, preset from the folder's next free number, the pseudonym,
which you always type, and the interview's name, guessed from the file's name or else Interview. Files under one
pseudonym are one participant with an interview each, as GRAVITY's Initial and 2d are. Add checks every row and
refuses in one line naming what to fix. Then it writes each participant as `P<n> - Pseudonym`. It writes a copy of
each file in `Source/<interview>/` and leaves the original untouched. It writes the raw source `Source/P<n> Pseudonym
- transcript.xlsx`, with a sheet for each interview. The interviewer's passages go under the interviewer's name from
Project settings, and every participant's passages under the pseudonym. Another speaker's passages go under Other
speaker, or Other speaker 2 for a second one, marked as the import card marks them. So no name from the recording's
labels reaches the workbook. Last it writes the annotated workbook. If anything fails, it takes away what it wrote. A
folder with a second part after the pseudonym, as GRAVITY's folders have, still opens and shows by its pseudonym
alone. Add transcripts makes no such folder.

**Method** (31 October 2026, and three since 17 November 2026). Under Research question, Method is a choice of three:
IPA, chosen as the card opens, Longitudinal IPA, or RTA, reflexive thematic analysis. It is the project's for good. No
client switches it afterwards, not from IPA to Longitudinal IPA and not to or from RTA ("If you want an IPA project,
make an IPA project"). Project settings shows it as text. A folder whose project file already names one shows that
one, fixed. A project from before with two or more timepoints is a longitudinal one, and the app reads it so without
writing its file. A thematic analysis project shows its screens in Braun and Clarke's words: Codes for Experiential
statements, an extract for a quote, Notes for exploratory notes, and Themes for GETs. Its board is the thematic map of
every participant's codes, and each participant's codes wait under Codes in the Participants panel. It has no PETs, no
timepoints and no trajectories. Its project page's rows show the coding alone, its Coding screen has no nudges, and
its board has no Mark complete. Its AI features are its own, and IPA's never show in it (see Thematic analysis's AI).
Its board's Export (1 November 2026) prints, or saves as a PDF, the Theme table, the audit trail, all of it in one
document or the canvas, each in its own words. The Table of themes shows every code with its extract under each theme.
The trail has four columns, Transcript passage, Extract, Code and Theme. The full set has no tables of PETs. Its codes'
CSV is "All Codes", with Code, Proposed theme and Extract as its headings. Every line the app says in the project, such
as a refusal or a line after an export, uses the same words. Search in it finds the codes and the passages, and nothing
that would open a PETs board. It names what it finds Codes, Extracts and Notes.

**The code list** (2 November 2026). In a thematic analysis project a code is a label that many extracts share, and
each extract is still one quote. On the Coding screen each extract of a passage is a box, numbered in the passage after
its last words, with its codes as chips under it. Add a code under the chips suggests the project's codes as you type,
each with how many extracts and participants it has, or offers New code with the words typed. Enter or a click puts it
on the extract. The x on a chip takes the code off. If it was the extract's last code, the extract stays, with no code.
Add an extract, or Q, takes the selected words in the passage as a new extract. Each of these is a step of undo.

Quick keys while coding (9 November 2026). With words selected in a passage, the toolbar beside them has In vivo code
beside Extract and Give to another speaker. Under them is a second line with the five codes used last in the project,
the last one first, with a firmer edge. A click on one makes the words a new extract with that code. The keys do the
same. R puts the code used last on the words, and 1 to 5 put the code at that place on the second line. V makes an in
vivo code: the selected words become a new code's name, without the stop at their end, and it goes on the new extract
at once. Q makes the extract with no code, as before. If the passage already holds the words as an extract, that
extract gets the code. The keys work only while words are selected and the caret is in no field, and never with Cmd or
Ctrl, so Cmd + R and Cmd + V stay the window's own. The right-click menu on selected words lists the same, with each key
in a column at its right: Extract, Extract with the last code, In vivo code with the words, then Recent codes, numbered
1 to 5. In a thematic analysis project the shortcuts card has R, V and 1 to 5. Each is one step of undo. The codes used
last are kept with the project's code list, so they are there after a restart, and a renamed code keeps its place. An
IPA project's statements screen has none of these.

Code list is a tab of its own between Coding and Themes. Every code is on the left, sorted by name, with its Extracts
and Participants, and Search the codes narrows the list. The code open on the right shows its name, its counts, its
Description and its extracts by participant. Each extract has its time and Go to the passage, which opens the passage
on the Coding screen. Rename makes the name a field in place. Merge into another code opens Merge two codes, which says
what the merge will do before it is done. Every extract of the one code goes to the other, an extract that had both
keeps one, and the merged code leaves the list. Delete this code is there only for a code with no extracts. The row's
menu, its three dots, holds the same three. New code beside the search adds a code before its first extract.

A rename and a merge change every participant's workbook and every board at once. The app checks each file first,
and if one is open in Excel nothing is changed. A copy of each file goes into an _Archive folder first. Undo and
Redo at the foot of the screen, or Cmd + Z and Shift + Cmd + Z, put the whole change back or make it again, while
no file has changed since. A project made before the code list has its list made the first time it is opened. A
name typed the same way in any case is one code, and each board keeps a revision first.

On the Themes board a code is one card. It shows Code · 9 extracts and its name, and under it each participant's
letter with how many of its extracts are theirs. Its extracts follow it wherever it goes. On a board made before
the list, a code whose extracts sat in different places goes where most of them were, and the board's History
names it. A new code waits under its participants in the Participants panel until you drag it onto the board.

The Themes board as the thematic map (2 November 2026). The panel at the board's left has two tabs, Codes and
Participants. Codes lists every code of the project once, by name, with its extracts and each participant's count.
Unplaced comes first: the codes in no theme and those that have never been on the board. Then come those In themes.
A code set aside is under Set aside at the panel's foot. Search the codes finds a code by its name or its
description. A row dragged onto the board brings the code's card, or moves the card when it is already there.
Participants is the panel as it was, with each participant's codes under their name. The status bar counts codes
from the code list, as in "11 codes: 9 in themes, 0 set aside, 2 unplaced", so a code that never reached the board
counts as unplaced. Then it counts the themes and subthemes, as in "3 themes, 1 subtheme".

The Inspector on a code's card shows "Code · 5 extracts", its name and each participant's count. It shows its
Description, the same field as on the Code list, and the theme it sits in. Take out of theme and Open in Code list
sit under it, and then every extract by participant, each with its time and Go to the passage. A description you
type here is kept when the box loses the focus, as on the Code list, whose Undo takes it back. Under a theme each
extract has a tick. The ticked one is that participant's key extract for the theme, which the theme table's Their
key extract only shows. Until you tick one, the first of theirs in the theme is ticked faintly. A tick is a step of
undo.

The Inspector on a theme shows its Definition, the theme's central idea, in the box that was its description. Then
it shows how many codes, extracts and participants it holds, with Auto-arrange and Audit trail side by side on one
row. Then come its codes and subthemes in the order of its frame, each participant's extracts counted from every code
under it, and its Note.

**Thematic analysis's guidance** (3 November 2026). A thematic analysis project's Coding screen has its own
Guidance, opened from the bar's Guidance tool or `g`, as the IPA statements screen has. It is Coding guidance:
eleven lines from Braun and Clarke's reflexive thematic analysis, each with its Less this and More this behind the
small arrow, and the paragraph under them. An empty Add a code field says Add a code, and the questions stay in the
Guidance (Adam, 3 November). The rail has no personal examples, because those are IPA statements. The Themes board's
Guidance tab shows the lines on themes: What a theme is, Generating themes, Developing and reviewing, Defining and
naming, The thematic map and Before you finish. They live in `ta_guidance.md` and `ta_themes_guidance.md` beside the
app, in the formats of `guidance.md` and `themes_guidance.md`, and an edit shows on the next load. An IPA project's
guidance is as it was.

**Thematic analysis's AI** (3 November 2026). With AI features on in Settings, a thematic analysis project has one
AI feature of its own, written from its guidance, and none of IPA's. On the Coding screen each extract has AI
suggest beside its Codes, under the Experiential statements switch. A press sends that passage, the interviewer's
passage before it, the extract, its codes and the project's code list. The answer stands under Add a code as AI
suggestions. It gives up to three of the project's codes that fit, each with its extracts and participants counted,
and then up to two new codes as New code "...". A click on one puts it on the extract, as Add a code would, in one
step of undo. Nothing is written until you click. A code you take is an ordinary code, with no mark saying that the AI
offered it. The x puts the list away, and the next passage starts with none. It uses the provider, key and model that
the Experiential statements' AI suggest uses, and sends only the passage in question. The Themes board's AI review
went on 11 November 2026. A board's review rounds from before stay in the GETs file, and nothing reads them.

Compact on the status bar shows each code's card as its name alone, so one screen holds more of the board. The cards
stay where you put them. It is off on a new install and kept, as Extracts is. Press it again to see the cards as
before.

The board's Table view lists each theme in the board's order with its definition, its note and Audit trail. Then it
lists its codes, each with its extracts, and under each code each extract with its participant, time and words. Then
come its subthemes in the same way. Unplaced at its foot lists the codes in no theme. Those on the canvas come first,
and you can drag them into a theme. Then come those never on the board.

The theme table goes to Microsoft Word too (1 November 2026). Microsoft Word is under Export in the toolbar while the
Table view shows, and on the Export card beside Save as PDF while Theme table is chosen. The document is portrait A4,
with the project's name at its head and "Table of themes" under it. Then come each theme in the board's order with its
description and note, and its subthemes under it. Under each come its codes, each with whose it is and where, as in
"(Juno, Initial, 00:14)", and its extract on the next line. With Their key extract only chosen, each theme holds only
every participant's key extract. Descriptions and Include participant notes apply as they do to the PDF.
Participants table puts the participants table on its first page, under Participants, and the themes start on the
next. It is saved at the project's root, where the PDF goes, as "<project> - Board 1 - Theme table.docx", never over a
file there. Its author is the name in Settings, General, Your name.

At a desk's width the card's Folder and Name fields start at one left edge and run to its right. Before, the folder's
field started further left (17 October, later).

**Add transcripts.** Add transcripts stands quietly under the rows on each project's page, or where the participants
will stand in a project with none yet. It opens the card with the project's name over it, and no folder, name or
question to set (see New project for its rows). A file under a new pseudonym makes a participant at the next free
number. A file under the pseudonym of a participant already there is a further interview of that participant. Its row
reads "A further interview of P1 Ada". Its copy goes in `Source/<interview>/`, and its sheet is added at the end of the
raw source and of the annotated workbook. A copy of the workbook is kept in the participant's `_Archive/` first, and
every sheet already there stays unchanged.

**Names replaced as a transcript comes in** (8 November 2026). A project can keep a list of real names and what each is
written as. Every transcript that comes into the project has them replaced on its way in, so no workbook holds a real
name. Each row of Add transcripts has a Real name beside its Pseudonym. The name you type there, and its first word
when it has two, is replaced by the pseudonym in that participant's transcript, and it joins the list. The row's
preview shows each name found in bold. The Names line under the row's fields counts them, as in "Carlos 3, Hope 1 and
hope in lower case 3 found." Nothing is replaced on the way in until you have seen it (17 November 2026). When a file
holds a name from the list, the card's button reads Add… and opens the review over the card. The review shows every
find in its whole sentence, with the participant, timepoint and time (or the passage's number where the file has no
times) and a tick. Untick one, and it stays as it is written, as "Will" in "Will you tell me" should. Back keeps your
ticks. Replace 4 ticked and add replaces the ticked finds and adds the transcripts. A speaker's name is one row, however
many passages it heads. The participant's name in the file's own name and the interview's name are replaced too. Source
keeps the replaced text, not the original. A REFI-QDA project brought in on the same card, and a transcript imported
into a participant's folder from its import card, open the same review first when they hold a name from the list.

Names are found as whole words, so "Ann" is never found in "Annabel" or "annual". The finding ignores case: "HOPE" is
found as "Hope" is, and "hope" is found too but listed separately (below). "Tilda's" becomes "Wren's". Initials such as
"T.M." are found with or without their dots and spaces, by their case. Several spellings of one name go in one entry
with commas between, and the app does not guess a misspelling.

Names to replace, from the Names line or from Project settings, is the project's list. It gives each name, what it is
replaced with, whose transcripts it is in (Everyone, or one participant, for a "Ruth" who is a sister in one interview
and a friend in another) and Except in. Nothing on the list asks you to decide how a name is used. You decide that find
by find in the review. Add a name adds a row. Add from a file reads a two-column CSV or Excel key you keep already, with
the real name then the pseudonym. A key the app wrote keeps Except in in a third column. The app saves the list as you
change it, in one file in the project's folder, `idiograph-names.json`, so it moves with the folder. It is never in a
workbook, the project's History or a copy you share.

Check transcripts already in finds the list's names in the transcripts the project holds: their passages, speakers,
notes, statements and quotes, and the memos a REFI-QDA project brought in. It says how many and where. Review and
replace groups them by name, as in "Carlos → Eduardo 6 found, 1 left as it is", with Tick all and Untick all. Each find
stands in its sentence with the participant, timepoint and time and a tick. Replace 8 ticked writes the ticked ones,
and the PETs and GETs follow the statements. Before it writes, the app keeps each participant's workbook and raw
transcript as they were in their `_Archive` folder, named "(pre-names" and the date. So the real names are still there.
Keep that folder safe, or delete those copies when you no longer need them. Share a copy never takes them, and never
takes the list.

A find with its capital starts ticked. A find in lower case, such as "hope" for Hope, the name that is also a word,
starts unticked. It is folded under its name, as in "hope in lower case: 31, left as they are", with Show to list them.
Tick the ones that are the person. A participant's copies in Source cannot tell one find from another of the same
words. So when you leave one find unticked, every find of those words in that participant's Source copies stays as
written, including the ones you ticked. A copy of the whole project that you share takes Source with it, so check those
copies before you send it. Except in takes phrases that the name is never found inside, such as a book series' title
that is also the surname. You put semicolons between them. A find inside one is not counted, listed or replaced
anywhere. Review each and Also an ordinary word, the ticks a name had on the list before, are gone (17 November 2026).
The sentence beside each tick says what the choice is.

An AI agent can add names to the list when you tell it the names. It can change or take off an entry when you say so,
but not one with a find you have unticked, because only the app takes that off. Its dry run first says for each entry
how many it would find and where, and never the names. The agent's addition is one change under By an agent in Project
history, and its Undo puts the list back as it was. An agent's replace takes only the finds with their capital letter.
It never replaces a find in lower case. Once you have unticked a find of a name, in Review and replace or as a
transcript comes in, the agent leaves every find of that name for you. Those stay yours, one by one, in Review and
replace.

**Projects from ATLAS.ti, NVivo or MAXQDA.** Since 21 October a project exported from ATLAS.ti, NVivo or MAXQDA as a
REFI-QDA project, a `.qdpx` file, comes into a project as participants. It comes in from Add transcripts' card (see The
import card for a project below), or through an AI agent (`idiograph qdpx`, see the agents' guide). Each text source,
or a recording's transcript, is one participant's interview. It is given its pseudonym, its number and its timepoint, as
a row of Add transcripts is, and made as Add makes one: a copy of the `.qdpx` in `Source/<interview>/`, the raw source
and the workbook. A pseudonym already there joins that participant. The text is cut into passages as a plain text file
is. A `Name:` line starts a passage, or else each paragraph is a passage. Then, by default:

- each code on a passage is an experiential statement named by the code, with its quotation there as the
  quote. A code over several quotations in one passage is one statement whose quote holds them all
  in transcript order, with an ellipsis where they are not next to each other, as a quote built with
  Cmd held is. The same code in another passage is the statement once there too. Codes can come in
  as exploratory notes instead, or be left out.
- a comment on a quotation is an exploratory note on its passage, or an experiential statement whose
  quote is the quotation.
- a quotation with no code and no comment is a quote to pair, listed under Quotes to pair until its
  statement is written. It can be left out instead.
- a source's memos go to a text file in the participant's `Source/`, "Wren - memos.txt".
- a recording in the project is copied into the participant's `Source/` for the player, and each passage
  is timed from the recording's sync points.

On request, a PETs board "From ATLAS.ti" (or NVivo, or MAXQDA) is made on each participant's canvas. Each code group
becomes a PET holding the statements its codes made. From a file Idiograph wrote, in a project with timepoints, each
participant's LPETs and the LGETs come in as boards too (see Export as REFI-QDA). A quotation that runs past its
passage's end is cut there. One line says what does not come in: PDF documents and pictures, variables, free memos,
links and networks, sets beyond the PET draft, and codes on the interviewer's passages. The same lines go into each
workbook's History in its progress file. The `.qdpx` itself is only read.

**The import card for a project from ATLAS.ti, NVivo or MAXQDA.** Since 21 October a `.qdpx` dropped on Add
transcripts' card, or picked with Choose files, comes onto the card on its own. The drop place goes. Another file
dropped with it or after it is refused with "A project from ATLAS.ti, NVivo or MAXQDA comes in on its own. Add other
transcripts after it." The cross at its right takes it off the card. Under its file's name, "A project from ATLAS.ti"
(or NVivo, or MAXQDA), each source that can come in is a row, ticked. A row shows its name and its passages, and its
first eight passages as they will land. The columns are Speaker, Time and Transcript and, where any passage has them,
Exploratory notes, Experiential statements and Quote. It shows its speakers, each with the role's chooser. It has the
fields P, Pseudonym, Interview and, in a project of two or more timepoints, Timepoint, as a transcript's row has them.
Untick a row, and that source stays out. Under the rows comes What comes in:

- Codes: As experiential statements (the default), As exploratory notes, or Leave out.
- Comments: As exploratory notes (the default) or As experiential statements.
- Quotations with no code or comment: As quotes to pair (the default), each a quote waiting for its
  statement under Quotes to pair, or Leave out.
- Memos, when a source has any: To the participant's Source folder (the default) or Leave out.
- Recordings, when a source has one: Copy for the player (the default) or Leave out.
- A draft PETs board from the code groups, when codes come in as statements and the project has
  code groups, unticked until you tick it.

Each choice reads the file again. The preview and the lines under the choosers, saying what comes in and what is left
out, change with it. A refusal stands under them once every ticked source has its pseudonym. Add brings in the ticked
sources, and writes nothing until it has checked every one. The card sends the file to Idiograph once, and Idiograph
keeps a copy while the card is open, up to 256 MB. A larger project, such as one with a recording in it, comes in
through an agent.

**A project card's menu.** Since 21 October (Adam's Way A) each project's card on Home has its dots at the top right.
Their menu holds, in order, Share a copy…, Export as REFI-QDA… (since 8 November 2026), Show in Finder (Show in Explorer
on Windows), Project settings and Project history. Under a thin rule comes Remove from Idiograph…, in red with its bin.
Show in Finder opens the project's folder in the Finder, selected in the folder it sits in. It is there only in
Idiograph's own window, because a browser's page cannot open a folder. Project settings opens that project's own
sheet, with its research question, its statement length and the rest of what belongs to the project (see Project
settings). Remove from Idiograph asks in a small card, then takes the project off Home. A shared copy's card, marked
copy, is removed in the same way.

**Remove from Idiograph** (10 November 2026). The card names the project above Remove from Idiograph and says "Its
folder and files stay as they are.". It has one tick, off to start, Move its folder to the Bin too. When you tick it,
the line says that its folder and every file in it go to the Bin. Remove takes the project off Idiograph's list. With
the tick, it also moves the project's folder to the Bin, where the Finder's Put Back brings it back. Cancel or Esc
removes nothing. It is the Recycle Bin on Windows and the Rubbish Bin on Linux, and nothing is ever deleted outright.
Once the project has gone, the foot says so: "Removed Keeping bees. Its folder is in the Bin." The app never moves the
folder when it is not the project's own. That covers a whole drive, your home folder or its Desktop, Documents or
Downloads, the whole of iCloud Drive, OneDrive or another cloud drive, a folder holding the app's own files or
settings, and one holding another project. Nor does it move the folder while the project is open in another window,
or being saved. The foot says each of these, and the project stays in the list. When the system will not move the
folder, the foot says so, and the project stays too. The app keeps a line for each removal, and whether the folder
went to the Bin, in a record beside its settings, never in a project. In Idiograph's own window, every other line the
app asks you to confirm is asked in the window's own message box, with OK and Cancel. The demo's card holds Project
settings alone, read-only there as ever. A card whose folder is not there holds Remove from Idiograph alone. A run of
one project offers no Remove.

**Share a copy.** A project can go to someone else's Idiograph as one file and open there as a copy, such as a
student's project sent to a supervisor. Share a copy on the card's menu opens a small card first (23 October), with
the project's name above its title and two choices. Whole project, chosen to start, sends every participant, their
PETs and the GETs, and the line under it says so. A project of two or more timepoints says LGETs there. A project
with no PETs or GETs yet leaves them out of the line. The file then holds the whole project folder as it is: every
workbook, the project file, the boards, the GETs, Source and History. Under it one tick, Audio recordings, with the
size they add, decides whether the recordings go too. It starts unticked, and a project with no recordings has no
tick.

Choose participants shows a row for each participant, ticked to start. Each row's experiential statements and notes
always go, shown by a muted check. A PETs tick stands on the row of a participant who has PETs, ticked to start. An
Audio recordings tick, with its size, stands on the row of one who has recordings, unticked to start. A participant
with neither has nothing in those places. Untick a participant, and their row shows dashes, because nothing of theirs
goes. The GETs never go this way, because they are made from every participant. So to send one participant to someone
blind to your PETs, choose participants, leave only that participant ticked and untick their PETs. Share… is there once
a participant is ticked. Each tick turns on or off from anywhere on its row.

Under either choice a Boards row (26 October) offers Current board only or All boards, with All boards chosen to start.
All boards sends every board as it is, with its History. Current board only sends each participant's PETs, and with
Whole project the GETs, with only the board each is going with. That is the Current board where one is marked, or
else the board on the canvas. That board's own PET draft and table go with it. The other boards and the History stay
behind, and the copy opens on that board. In a project with timepoints the same goes for the LPETs and LGETs. The row
is there only when it would change the file: when a participant going with their PETs, or with Whole project the
GETs, has two or more boards.

Share… opens the save panel. The file is named `Keeping bees.idiograph`, the project's name with `.idiograph` after it,
and the panel's line says "Idiograph doesn't track changes between copies yet." The file is written straight from the
project's folder, so a project with long recordings is shared as quickly as a small one. In a browser Share… downloads
it, and the same line stands under Share a copy in the menu. Tab moves through the choices and ticks, Space turns one
on or off, Enter presses Share…, and Esc closes the card with nothing sent. Nothing in the project changes, except for
an id that its project file takes the first time (see A copy coming back). The file holds the participants' words and
recordings, so share it in the way the study's ethics allow.

When the copy has been written, a panel at the top right of the screen says "Shared" and the project's name. It gives
the file's name and has Show in Finder (Show in Explorer on Windows), which opens the folder the copy went to. If the
copy cannot be written, the same panel says why.

**Open a shared copy.** Under Idiograph's cards, after Open project, Open a shared copy takes a `.idiograph` file, with
the dialog's line "Choose the shared copy.". Then it takes the folder to put the copy in, with the line "Choose the
folder to put the copy in. Idiograph makes a new folder called Keeping bees inside it.". It uses the window's own
dialogs or, in a browser on a Mac, the Mac's. In a browser off a Mac you choose the file and type the folder's path,
with Open. The copy goes in a new folder there, named with the shared project's own folder name, `Keeping bees`, or
`Keeping bees copy` when that is taken, then `Keeping bees copy 2`. It never goes over a folder already there. It joins
the projects and its page opens. A "copy" tag stands beside its name there and on its card on Home, and a line says
where the copy is. Its card's menu is the same as any project's. A file from a newer Idiograph is refused with "This
project was sent from a newer Idiograph. Update Idiograph, then open it again.". A file that is not a shared project is
refused with "That file is not a project sent from Idiograph.". Neither writes anything. A run of one project, which
hides Open project, hides it too. Taking turns and working on one project at once are not part of it.

**Opening a shared copy from the Finder or Explorer** (6 November). Once Idiograph is installed, a `.idiograph` file
belongs to Idiograph. The Finder and Explorer call it an "Idiograph shared copy" and show it with Idiograph's icon.
Double-click one, drop it on Idiograph's icon in the Dock, or choose Open With and Idiograph. It then opens as Open a
shared copy opens a file you choose, with no file dialog. The app asks for the folder for the copy, and a copy coming
back to one of your projects shows its card first. When Idiograph is closed, it starts and then opens the file. When
it is open, the file goes to the window in front, which comes forward. On Windows the file goes to the Idiograph
already open, never to a second one. On a participant's screen or a board, Idiograph goes to Home first, as Home does,
saving what you typed. If that save fails, you stay where you are and nothing is opened. With a card open, the file
waits until you close it. Files opened together open one after another. A file that is not a shared project is refused
in the same words as above. On Linux, with Idiograph installed from its .deb, the file manager shows a shared copy with
Idiograph's icon, and a double-click or Open With hands it to Idiograph in the same way.

**A copy coming back** (26 October). When you send a copy to another analyst and they send it back, it is still your
project, so you can add their boards to yours. The first time you share a copy, the project file takes an id of its
own. That is the only change a send makes. The copy remembers the id, with how each statement read when it was sent.
Through Idiograph's command line or MCP tool, an AI agent can then bring the copy's boards in when you say so, with a
dry run first. Each comes in as your participant's next board, named with whose it is and when, as in "Curt's board,
30 Oct". It is never current and never replaces one of yours. Its History says "Brought in from" and the file's name.
Since 6 November a board arrives whole, and every card keeps its place on the other analyst's board. A card is matched
by its words first. So a statement that moved up its passage, because you removed one before it, is still found. Then
it is matched by its place in the transcript. A statement you reworded since you sent the copy is linked to yours and
shows your current wording, marked changed, with theirs as what it read. A statement you removed, or one the other
analyst added, is placed in their wording and marked as no longer in the workbook. Nothing else in the project
changes. You can then make the board current, keep it beside yours, compare it with yours, or delete it. A delete
keeps a copy in `_Archive`, as delete always does. A file that is not a copy of the project is refused. When most of a
board's statements are not in your project, open the copy as a project of its own instead. Its name can then say whose
it is, as in "Keeping bees, Curt's copy". A copy sent from 6 November on carries its sender's name, Your name in
Settings, when they have set one.

In the app (26 October, evening, with the card rebuilt on 6 November), Open a shared copy knows a copy coming back.
Once the file is read, and before any folder is asked for, a card says so: "A copy of Keeping bees, sent 30 Oct.". Then
comes Name on the boards, filled in with the name the file carries. Under it the card says what a board comes in as,
"Comes in as: Curt's R2 Initial Grouping, 30 Oct". Then come two choices. Add its boards to Keeping bees is the one it
starts on. It says how many boards would come in, as in "11 new boards, not current" or "A new board, not current".
Under it stands each participant's name, as in "P2 Wren", over a tick for each of their boards, by its own name in the
copy. Every board is ticked to start, and All boards above them unticks or ticks them all. Under a participant's
boards, a line says once how their statements came. It reads "Since you sent the copy, you have reworded 37 of these
statements and removed 5. They keep their places on these boards and show your current wording. The removed ones show
Curt's wording.", or "All 46 statements match yours.". A board of yours that comes back as you sent it, with its cards
where they were when you sent the copy, is left out, whatever you have done to your own board since. Under the
participant a line then says "1 board is your own as you sent it, so it is left out." (8 November 2026). The button
counts the ticked boards, as in "Add 5 boards" or "Add 1 board". With no board ticked or no name, you cannot press it,
and a line beside it says what is missing: "Tick a board.", "Type a name." or "Tick a board and type a name.". It brings
the ticked boards in and opens the first participant's PETs board with its board menu open. The new boards stand in
the list under yours, not current. Each note reads as in "Curt's copy, sent 30 Oct: 80 statements as sent, 37 reworded
since, 5 removed since.", and leaves out a part whose count is 0. Under it comes the note the other analyst wrote on
the board in the copy, word for word, when there is one. Open as its own project goes on as Open a shared copy always
has. Open… asks for the folder, and the copy is named "Keeping bees, Curt's copy". Cancel and Esc open nothing. A copy
whose boards are already in starts on Open as its own project, and the first choice says "Its boards are in Keeping
bees already.". A file that is not a copy of one of your projects opens as it always has.

**Export as REFI-QDA** (8 November 2026). A project, or some of its participants, can go out as a REFI-QDA project,
a `.qdpx` file, which NVivo, ATLAS.ti, MAXQDA and QualCoder open. So a supervisor or a co-analyst can read the work in
the programme they use. Export as REFI-QDA… on the project's menu, on Home or from its name inside the project, opens
a small card with the project's name above its title. It offers Whole project, ticked to start, or Choose
participants, with a tick for each. In a project with recordings it has an Audio recordings tick, off to start.
Export… opens the save panel, with the file named after the project, "Keeping bees.qdpx", and a line says when it is
saved. In a browser it downloads. Nothing in the project changes. In the file each interview is a text, with its
passages as the transcript has them, with their speakers and times. In an IPA project each experiential statement is
a code, applied to its quote. A statement with no quote is applied to its whole passage. Each participant's PETs come
from the board the GETs take. They hold their statements in the board's order, each PET and sub-PET with its
description, and then Unplaced and Set aside. Each PET and each GET is also a set, ATLAS.ti's code group. In a
thematic analysis project each code is one code, with its description, on each of its extracts, and the themes hold
the codes. Exploratory notes are notes on their passage. With the recordings ticked, each interview that has one is
the recording with its transcript, linked by the passages' times. If you bring the file back into Idiograph with
Import and PET draft ticked, it gives the same passages with their speakers and times, the statements in their order
with their quotes, the exploratory notes and the Interviewer notes. Each participant's PETs come back on a new board in
the same order, with each sub-PET inside its PET and each label's description and note. The statements set aside go
back in the bin. The GETs come back as a new board on the GETs canvas, each GET with its description and note holding
the same PETs. A recording comes back with its offset and the transcript's own times. In a project with timepoints,
each interview goes to the timepoint you give it, and each timepoint's PETs go to that timepoint's board. In thematic
analysis the code list comes back with each code's description, and the themes come back as a new board on the Themes
canvas, with each sub-theme inside its theme. Some things do not come back (9 November 2026). Where each card lay does
not, and the new boards lay the cards out afresh. Stacks do not, and their statements come back side by side. The
boards' names, history and other boards do not, nor does a board marked complete. The quote ticked for a PET or a GET
table's row does not, and neither do sticky notes and participant notes, which REFI-QDA has no place for. In a project
with timepoints, each participant's LPETs go too (12 November 2026), from the board the LGETs take. Each LPET is a code
under the participant's LPETs code, with its description and note, and its sub-LPETs inside it. Each LPET is also a set
of every statement under it. Its domain and the LPET table's states and key quotes are notes on that set. Each LGET is
a set of its LPETs and their statements. Brought back into a project with timepoints, each participant's LPETs come
back on a new board of their LPETs canvas. Each LPET holds its description, note and domain, the same PETs of each
timepoint and the same statements on cards of their own, with each sub-LPET inside its LPET. The LGETs come back on a
new board of the LGETs canvas, each with its description and note, holding the same LPETs. The LPET table's states and
key quotes stay in their note, because the table keeps a key quote by where it stands in the transcript, and so does
the bold in a key quote. An LGET inside another comes back as part of it, as a GET inside another does, and a second
card of an LPET stays out. Brought into a project of one timepoint, the PETs come in, the LPETs and LGETs are left out,
and the lines say so.

**Sending some participants, or leaving kinds out** (23 October). Through Share a copy's ticks, the command line and
the MCP server, a send can hold only some participants and leave out what you choose. So another analyst can make PETs
for one of your participants without seeing yours. `idiograph project send --to ~/Desktop --participant Wren --blind`
writes a file with the project's name, research question and settings and Wren alone. It holds her workbook with its
transcript, exploratory notes, experiential statements, quotes, Interviewer notes and other speakers, and her
progress. It holds nothing of your grouping: no boards or their history, no PETs, no PET drafts, no PET tables in Word
or PDF, and no GETs. Opened as a copy, in any Idiograph from 0.9.4 on, Wren's statements are all there and her PETs
canvas is empty, ready to start. Giving `--participant` again sends more participants. `--leave-out` names the kinds to
leave out, `pets`, `gets` or `audio`. So `--leave-out gets` sends the PETs without the GETs, and `--blind` leaves the
PETs and the GETs out. Recordings stay out of such a send unless `--with audio` asks for them, because a voice can name
a participant. `_Archive` copies never go. Your working notes stay out too, unless `--with notes` asks for them. That
means any file in the participant's Working folder that is not Idiograph's own, such as a grouping draft or a
statements CSV, and any other file beside the workbook. The Source folder, with raw transcripts and exports, also
stays out unless `--with source` asks for it, because the workbook holds the transcript. Each participant's folder in
the file is named as Idiograph names the participant, `P1 - Wren`, never with a second part that the folder on your
disk has. With the PETs left out, the participant's History stays out too, because its requests can name a board or a
PET. In the copy it starts fresh, and the statements' progress and completion are kept. GETs hold every participant
they were made from. So when some of those are not sent, the GETs stay out, and the answer says so. `--dry-run` lists
every file it would hold and every file it leaves out, and nothing in the project changes. `--pets Wren` and `--audio
Wren` send Wren's PETs or recordings and nobody else's. So one participant can go with PETs and recordings and another
with the statements alone. `--leave-out audio` on its own sends the whole project, with notes, Source and GETs, but
without the recordings. `idiograph project send --list` says which participants have PETs and recordings, how big the
recordings are, how many boards each has and which is current. It writes nothing. `--boards current` sends each
participant's PETs, and the GETs, with only the current board, the one you are going with, and the PET drafts and
tables of that board only. The History stays behind. `--boards all`, as before, sends every board.

**Timepoints.** A longitudinal study (Farr and Nizza 2019) interviews each participant more than once, for example
before the season, at midsummer and after the harvest. It is a Longitudinal IPA project, which you choose on New project
with its timepoints (17 November 2026). An IPA or a thematic analysis project has none. In Project settings, straight
under Method, Timepoints says how many times each participant was interviewed. You set it with its minus and plus, and
the number rises for a later round of interviews. Each timepoint has a row with its label and its description, such as
Before the season. The labels start as T1 and T2, and you can rename them. A longitudinal project has two timepoints at
least, so the minus stops at 2. A project made at one timepoint before this is still longitudinal and can raise its
number. The number saves at once, and a label or a description saves once you leave it. If a timepoint that would go
holds an interview, lowering the number is refused under the rows, as in "T3 holds interviews of Wren, so the
timepoints stay at 3.", and nothing changes. The project file keeps them as `timepoints`, with its `method` "lipa".

A participant is one workbook at every timepoint, never one workbook for each interview. Each timepoint is a set of the
participant's sheets. An interview in two parts is two sheets of one timepoint, as it always was. An interview at T2,
months later, is new sheets at the end of the same workbook. In a longitudinal project:

- each row on the project's page shows the participant's name over a cell for each timepoint. A cell shows its label in
  bold and its description, then where it stands: the passages decided of the passages there, Statements complete, or
  Not interviewed in a dashed cell that opens nothing. PETs follows them as before, then LPETs, which opens the
  participant's LPETs. Its line gives the Current board's name and "LPETs complete" once marked, or "No LPETs yet" (17
  November 2026). A cell opens Experiential statements at that timepoint. Below 900 pixels each timepoint takes a
  column, with PETs and LPETs on the row under them.
- Add transcripts' rows each have a Timepoint chooser. A row under a participant already there starts at the first
  timepoint at which they have no interview.
- the import card has a Timepoint chooser, starting at the first timepoint at which the participant has no interview.
  When a workbook is already there, the line under it says where the transcript goes, as in "Idiograph adds it to the
  end of P2 Tansy - EN & ES.xlsx as the sheet T3.". Make adds the sheet there, keeping a copy of the workbook in
  `_Archive/` first, and opens the participant at that timepoint. Without a workbook, the create card makes the
  workbook with its sheets at the chosen timepoint.
- the statements screen's bar shows the timepoint where the sheet switch stood, with T2 large and Midsummer smaller
  beside it. The description goes below 900 pixels. From 620 pixels down, View and Feedback give way, so the
  participant's name keeps its first letters, "P1 W..." at 360. Its menu lists the participant's timepoints, each with
  where it stands, and a timepoint not interviewed is greyed. Under a timepoint of two or more sheets it lists its
  sheets. Choosing one goes to its first undecided passage. Ctrl + Cmd + Up and Down still step through the sheets.
  The line under the bar, the passages decided, Mark complete and Statements complete belong to the timepoint, so T1
  can be complete while T2 is under way.
- each timepoint of a participant has its own PETs canvas (21 October). Its statements are those of that timepoint's
  sheets alone, and it has its own boards, its own Current board and its own PETs complete. PETs opens on the
  timepoint in front of you on Experiential statements. The PETs bar shows that timepoint after the tabs, with T2 large
  and Midsummer smaller beside it. Its menu lists the participant's timepoints with where their statements stand, and a
  timepoint not interviewed is greyed. Choosing one saves the canvas and opens that timepoint's canvas.
- the LPETs tab, between PETs and GETs, opens the participant's LPETs canvas. LPETs are longitudinal PETs, made from
  their PETs at each timepoint as GETs are made from every participant's. Each card is a PET or a sub-theme of one
  timepoint, with "PET · T1" over its title, and a label over cards is an LPET. You can start it at any time from
  whatever PETs exist: the Current board of each timepoint, or else the board last open. A change to a timepoint's PETs
  comes in as a participant's change does on GETs. The sidebar at the left, Timepoints, lists each timepoint with its
  PETs and statements, and one not interviewed says so. A statement's time is cited with its timepoint, as in "T1,
  35:55". The participant picker sits in the tab, as on PETs. A double-click on a statement's card edits it as on GETs
  (30 October). Its timepoint's PETs boards, the LPETs' copy and the LGETs' copy take the words at once. The AI's help
  is not on LPETs yet. Since 12 November an LPET's domain shows on its label as its pills, under its title and
  description, with the same words in the same colours as on Trajectories. Add domain in the LPET's menu, or Edit
  domain once it has one, opens Domain in its Inspector, above its note. There you type the domain, with two or more
  separated by commas. Enter or a click away keeps it, Esc leaves it as it was, and an empty box takes it off. It is
  kept on the LPET of the board on the canvas, so Trajectories shows it when that is the board the LGETs take. The
  canvas is saved first, and the change is not part of the canvas's undo. The LPET table's key quote shows your bold
  from Trajectories on the same words, in the table and in its print view and PDF. A key quote taken from the transcript
  on Trajectories is the quote the table shows, with its bold, in the table and in its print view and PDF. The LPETs
  screen's Inspector and its print view and PDF say LPET where they mean one, never GET. Since 17 November an LPET reads
  as your interpretation, and the cards under it as what it draws on at each timepoint. They are its audit trail, never
  its parts (Adam's requirements of that day). Nothing in the app builds, names or summarises an LPET from its cards.
  Its title, its state at each timepoint and its note are yours. The LPET's Inspector says "Draws on T1, T2 and T3"
  where it said "3 of 3 participants". Its Draws on section lists each timepoint with the PETs, sub-themes and
  statements it draws on there. A timepoint at which it draws on nothing says so, with your state there under it,
  which is where you say why. Its label's badge, the LPET table's head and the print view name the timepoints it draws
  on, never a count, and no LPET is ever under a minimum. The status bar says "22 cards: 9 drawn on, 12 set aside, 1 in
  no LPET". The last is the cards on the canvas under no LPET, which is separate from the Unplaced panel's count of PETs
  not on the board at all. A label's tooltip and its delete button say "what it draws on" where they said "all it
  holds". LGETs say the same of the LPETs under them: "Draws on none of their LPETs" for a participant with none under
  an LGET. On a timepoint's PETs board in a project of two or more timepoints, the Inspector on a PET, a sub-theme or a
  statement shows the LPETs that draw on it. Each opens that LPET on the LPETs board, selected, with its Inspector. It
  says "through" the PET or sub-theme whose card holds it, or "in part" where the LPET draws on something inside it, or
  "No LPET draws on it." On a PET or sub-theme that no LPET draws on, a box, "Why no LPET draws on it", keeps your
  reason with its card on the LPETs board. The reason shows under the card's words, in the card's Inspector (the same
  box) and on the canvas's PDF and picture. A reason is hidden while an LPET draws on its PET, and shows again if none
  does. A PETs board other than the one the LPETs took the timepoint from says so in place of the list.

  Rarely, one moment informs two LPETs. A PET's, a sub-theme's or a statement's card on the LPETs board has
  "Also drawn on by…" in its menu, followed by the LPETs it is not already in. Option-drag onto an LPET does the
  same. A second card of it stands in that LPET. Both cards read "Also drawn on by" and the other LPET, and the
  card's Inspector lists both under Drawn on by. You set one aside as you would any card. The LPET table sets out
  each LPET with the timepoints across, as Nizza's Table 8 does. There is a column for each timepoint, with the
  state, the key quote you chose cited with the participant, timepoint and time (none until you choose one), and
  what it draws on there. Each item opens its place on its PETs board or its passage, or the cell says "Nothing at
  T2". The LPET's note stands under it. Its Microsoft Word and PDF are the thesis appendix: the same table, then
  the PETs that no LPET draws on, with your reasons.
- the LGETs tab, after LPETs, opens the project's LGETs (21 October). LGETs are longitudinal group themes, made
  from every participant's LPETs as GETs are made from their PETs, on the same canvas and in the same ways. Each
  card is an LPET, with "LPET · Wren" over its title, in the participant's colour. A label over cards is an LGET.
  Each participant comes in from the board their LPETs were marked complete on, or else their Current board, or
  else the board last open. A statement under an LPET keeps its timepoint, as in "T1, 35:55". A project of two or
  more timepoints has no GETs at a single timepoint. So LGETs stand in the GETs' place: on the bar, for an agent,
  and on the project's page, where LGETs and Trajectories are the tiles in the row at the top (17 November 2026).
  Its file is `idiograph-lgets.json` at the project's root, and a GETs file the project had stays as it was. The
  AI's help is not on LGETs yet.
- the Trajectories tab, last, opens the Trajectories board. It is laid out as Adam's own page lays his study out
  (10 November 2026). Its title is the project's research question. The trajectories belong to the project. You
  make and name them on the board itself, and the app never fixes them. Each is a band down the screen. It has a
  head in its colour with its icon, its title and its sentence. Then come the timepoints across, each with its
  description ("T1: Before the season"). Then comes each participant placed in it, in your order. A participant
  shows their picture, name, own label ("The late starter") and tags. Each of their LPETs is a row: its title and
  its domain, then at each timepoint its key quote over its state.
  - New trajectory, at the end, adds a band, and you type its title at once. You change a title and a sentence by
    typing over them. The trajectory's icon at the left of its title, with a chevron beside it, opens its colour and
    icon under it in two rows (17 November 2026). Colour offers Green, Amber, Red, Blue, Plum, Teal, Taupe, Orange or
    None. Icon offers 22 icons, eight to a line, named in their tooltips (Rising, Falling, Level, Mixed, Up then
    down, Down then up, Up then level, Down then level, Step by step up, Step by step down, One high point, Up and
    down, Ebb and flow, Turning back, A loop, Round again, Parting ways, Coming together, A break, Growth, Fading,
    Unclear), or None. A choice is kept at once. Done, Escape or a click outside closes it, and the focus goes back
    to the icon. Tab reaches every choice, and the arrows move among a row's choices. With no icon, a dot in the
    trajectory's colour stands in its place. The bin at the head's right end, after the count, deletes the
    trajectory at once. Its participants go back to Unplaced with all that is kept on them, as one step of Undo.
    The line at the foot says "Deleted the trajectory Settling in." with an Undo button that does what the
    toolbar's Undo does. A label deleted on any board (PETs, GETs, LPETs, LGETs and Themes), by its bin, its menu
    or the Delete key, says the same, "Deleted the label ...", with the same Undo. (Ungroup frees a label's cards
    and says nothing.) The notice's Undo undoes that delete and nothing else. Another change, an Undo or Redo, or a
    move to another board, participant or screen takes the notice away. The focus goes back to what the Undo
    restored.
  - You move a participant by dragging their cell onto a band, where they land as dropped, or by Move to in their
    cell's menu. You can also use the keys while their cell has the focus: Up and Down within their trajectory,
    Left and Right to the trajectory before or after, and Backspace to Unplaced.
  - A double-click on a participant's cell, or Edit in its menu, opens their editor in place. Change picture...
    takes an image file. The app cuts it square, makes it small and keeps it in the project folder (in
    `pictures/` since 11 November, the participant's own, and in `trajectories/pictures/` before). A picture
    replaced or removed goes to that folder's `_Archive` and is never deleted. Since 11 November (pbiobuild) the
    picture and the label belong to the participant, so the project page, the pickers and the bars show the ones
    set here. A label and a picture that this board kept before move into the participant's own the first time
    the project's page lists them or one is changed. A copy of both files is kept in `_Archive/` first, as
    `(pre-participants <date-time>)`, with one line in the project's History. Choose from the set picks one of the
    app's drawn portraits, with a tab for each set, as on the project's page. Remove takes the picture off, and
    with none the participant's initial shows in their colour. Then come their label and their tags (Add a tag,
    with a tag's cross taking it off). A tag's colour is that word's colour on everyone who has it across the
    project. Then comes LPETs shown, with a tick for each LPET, all shown until you take one off. Done closes it.
  - Each cell is that LPET's row of the LPET table at that timepoint, so the LPETs screen's table and Trajectories
    show the same. The state is the row's note, typed in place. The key quote is the quote the row ticks. Until you
    tick one, there is none (17 November 2026: no quote stands in for your choice, here, in the LPET table or in
    their exports). A click on the quote, or on No quote, opens the quotes it can take, in three parts. In this LPET
    holds the LPET's own quotes at that timepoint. Elsewhere in this interview holds the participant's other quotes
    from that interview, whose statements sit in another LPET or in none. From the transcript comes last. Choosing
    one ticks it there, and nothing else changes: no statement moves, and the workbook is not written. Choose a
    passage... under From the transcript opens the participant's transcript under the row, at that timepoint's
    interview. It has a button for each of their other interviews, a box that finds words in the turns, and each
    turn's words. Select words in a turn and press Take the words selected, or press Take the whole turn, and that
    passage is the key quote (whole words, from any of the interviews, 11 November 2026). A quote from elsewhere or
    from the transcript shows as the LPET's own quotes do. It has the timepoint before its time only when it comes
    from another interview. If a ticked quote's statement, or a passage's words, are later gone, the row has no
    quote until you tick another. Words you choose in a key quote go bold with Cmd+B (Ctrl+B on Windows and Linux).
    The bold is kept with the row and never in the transcript. A timepoint with no quote says No quote over the
    state. A quote shows in the screen's own quotation marks once. The marks its workbook keeps round it are left
    off there, the workbook is left as it is, and its bold stays on the same words.
  - An LPET's domain shows as a pill under its title. An LPET in two or more domains has them separated by commas,
    as in "Relationships, Psychological", and each shows as a pill of its own in its own colour. That is the same
    colour wherever the domain is used across the project. An LPET keeps its domain through every change to the
    LPETs board, made on the canvas or by an agent: a statement brought in, or an LPET retitled, moved or merged.
    The LPETs screen shows the same pills on the LPET's label and sets the domain from the LPET's menu or its
    Inspector (12 November 2026).
  - Undo and Redo stand at the right end of the toolbar, as on every board (16 November 2026). Cmd+Z and
    Shift+Cmd+Z (Ctrl+Z, and Ctrl+Y or Shift+Ctrl+Z, on Windows and Linux) work anywhere on the screen except in a
    box being typed in, where they are the box's own. Each change made on the screen is one step: a key quote
    ticked, its bold, a state, a trajectory made, named or taken away, a participant moved, their label, tags or
    picture, or a note. Undo puts back every file the change wrote, as it was, and Redo makes it again. A new
    change clears Redo. The steps last while the app is open. If something elsewhere has since changed what the
    last step changed, such as an agent, the LPETs screen or another window, the steps start again from there.
    Undo then says so and changes nothing. You undo an agent's own change in Project history, By an agent.
  - The status bar along the foot counts the participants placed and unplaced and the trajectories. It holds
    Quotes, which steps through off, short (three lines) and full, and Notes, which shows each participant's note
    on why they stand there (the old Why box). Notes is off until you turn it on. The app keeps both in its
    settings.
  - While Notes is on, the screen has a note of its own under the research question, for the whole board, such as
    a credit for the pictures. You type it in place as you type a trajectory's sentence. Enter keeps it and
    Shift+Enter starts a new line, and an empty one shows Note. It is kept in the trajectories file with the board
    (10 November 2026).
  - The board is kept in `idiograph-trajectories.json` at the project's root, written on the first change. In a
    project whose LPETs' notes hold their states as paragraphs headed T1, T2, T3, as one made in Excel does, an
    agent moves them into the LPET table's rows (`states_from_notes`) and leaves each note as it was.
- the statements CSV from the PETs board's Export menu holds every timepoint's statements, T1's first. Each
  timepoint's statements come in the order its own Current board gives, with their PETs, and a last column,
  Timepoint, holds its label.
- a timepoint is known by its place, never its label. So renaming T1 to Spring moves nothing. Its LPETs stay as
  they came in, never "changed since", and cite it as "Spring, 35:55".
- PETs and LPETs made in Excel before Idiograph come in through an agent (9 November 2026), with no screen of
  their own. A table of a timepoint's PETs, with the columns PET, Sub-theme, Experiential statements, Location and
  Quote, becomes a new board at that timepoint. It is named From Excel unless you name it. Each row is placed on
  the statement it matches: the same words, or else a statement of the passage at its Location, or one with its
  quote worded nearly the same. The table is the later word. So where its wording differs, the statement on that
  passage takes the table's words, as an edit kept in History. A row with nothing close there can come in as a new
  statement with its quote. A Location may hold two times ("18:15 and 05:59", on two lines, or split by a comma, a
  slash or "&"), and the row matches at any of them. A statement that two rows give is placed once. Every other
  statement waits in Unplaced, and your other boards stay as they were. A table of LPETs, with a row for each,
  holding its title and a line under it and then a cell for each timepoint, becomes a new LPETs board. Each LPET
  has that line as its description and the cells in its note, with a paragraph for each timepoint headed T1, T2,
  T3. The PETs whose statements its cells quote are put under it as a proposal, for you to keep or move on the
  canvas. Every other card waits in Unplaced. The agent shows you every match first and brings nothing in until you
  say so.

Unplaced is the board's left sidebar since 16 November 2026, as on every board. Its slim tab on the board's left
edge, Unplaced with the number of participants on no trajectory, opens and closes it, with Hide Unplaced and Show
Unplaced in its tooltip. The browser keeps the choice for the screen. Each participant on no trajectory is a card in
it, and you drag the card onto a trajectory. A card dragged back onto the sidebar, or Backspace, takes them off
theirs. From 10 November it was a band at the head of the bands, with its button in a bar of its own under the
question. That bar is now the board's toolbar row, where Export stands, with Undo and Redo at its right end.

An IPA project has none of this. It has one PETs canvas for each participant, GETs, and no LPETs, LGETs or
Trajectories, and its files are as they always were.

**One project a run.** A server or a command started with `--root` at a folder is a run of that one project,
whatever `config.json` names. It opens on that project's page, reads and writes the project file in that folder and
nowhere else, keeps its recent list in memory, and adds and removes no project. Restart in Settings keeps that list.
Until 17 October, later, the run came back with none. The file at a real root is seeded by hand, and no test or smoke
run writes it.

**The band.** Under the top bar and over the three columns, a band runs the full width. It shows the label Research
question and the whole question in the serif, on as many lines as it takes. The PETs screen has the same band over
its canvas. It is simply there. Nothing folds it, and nothing about it is kept in the browser. The columns under it
keep the rest of the height: the page measures the band into `--band`, and their heights take it off. With no
question set, the band reads "No research question yet. Set it in Project settings.", and Project settings there
opens the project's sheet.

**The demo's own.** The demo is a project of its own, with its file committed at `demo/idiograph-project.json`.
It is Living with a dog, the project of its three participants. It asks how people experience sharing a home with a
dog, and what the dog comes to mean to them. Opening any demo participant reads that file and never a project's. A
save for the demo is refused, and Reset demo leaves it alone.

A page in front of a server from before the project finds no `project` in the answers. The band then shows the
no-question line, and Project settings says "Restart the server to finish this update." in place of its fields.

## Working together: comments and review

With Working together on in Project settings, each participant has one owner, and a teammate can review a
participant they do not own. Nothing of this shows while Working together is off.

**Asking for a review.** On the project's page, a participant you own has Ask for review in its menu, after Rename.
Its card lists your teammates, each ticked by its whole row, and a box for a line to them, "A line for Curt". Ask for
review sends it at once. The participant's row says "With Curt for review" until his review or his board comes back.

**Commenting.** On a participant a teammate owns, each statement of the passage you are on has Comment under it. For a
passage, select its words and press Comment beside Quote. On PETs and GETs, Comment is in a PET's or a GET's menu.
Each opens a box, Your comment, with Cancel and Add to review. What you add stays on your computer as a draft and
shows under its passage as "You: ...". While any wait, the top right says "Review for Adam: 2 comments" with Send
review, which sends them all to the participant's owner.

**A review that comes.** The owner sees a line at the top right, where an agent's held change shows: "Curt's review
of Juno: 2 comments." with Review. The review card says when it was sent and what you asked. It shows each comment
with what it is on, as in "Comment on a passage, 21:45", the words it is on and Curt's words. Reply opens a box and
sends your reply at once. Resolve marks the comment done, and Reopen brings it back. Done closes the card. It keeps
every comment you left open as unresolved, still showing under its passage on both computers. The cross closes the
card and leaves the review waiting.

Every comment, reply and review is sealed on your computer before it goes, by the relay or the shared folder. One that
cannot go for want of a connection goes by itself once there is one. A board a teammate sends shows on the same line
and card (A board sent by a teammate).

**Suggesting a wording or a title.** On a participant a teammate owns, Suggest a wording sits beside Comment under
each statement, and Suggest a title sits beside Comment in a PET's or a GET's menu. Each opens a small box with the
words as they are now, for you to change into yours, and Why (optional) for a line to the owner. Add to review keeps it
as a draft with your comments, and the top right counts it, as in "Review for Adam: 1 comment, 1 suggestion". Send
review sends them together. Nothing changes on the owner's computer until the owner answers. Under the passage your
wording stays with "Sent to Adam.", then "Adam accepted it." or "Adam declined it.", with his reason when he gave
one.

**Answering a suggestion.** On the review card each suggestion shows Now, what it reads now, and the teammate's words,
with the teammate's reason. Accept makes the change as if you had made it, and History says that the teammate
suggested it and you accepted it. Decline asks Why (optional) and changes nothing. Either answer goes back to the
teammate. When the statement or title has changed since the suggestion, the card says so with the words the teammate
saw, and Accept still puts their words in place of what is there now. When the statement has gone since, the card
says so and offers Decline alone. A review with a suggestion still waiting stays on the line after Done until each is
answered.

## Demo participant

A participant ships with the app, for showing it to somebody or recording the screen without a participant's words
on it. Two more ship beside it for the step across participants. The demo, Living with a dog, is three invented
interviews about sharing a home with a dog, with Juno, Rowan and Mabel. Nobody real is in them. The participants, the
dogs, the households and every word of the transcripts were written for this, and they are a composite of nobody.
Since 26 October the demo is a finished project, a worked example of IPA from the first passage to the GETs (Adam,
24 October: "a complete worked example as if the project was finished"). Juno, Mabel and Rowan each have a recording
(12 November 2026). Juno's is about twenty-eight minutes, and Rowan's and Mabel's are shorter, about eleven and ten.
Each comes annotated. Every passage is decided, with its experiential statements, each beside its own key quote, its
exploratory note and a highlight here and there. The rounds are closed and the statements are complete. Its PETs are
on Board 1, the Current board, marked complete, with three PETs with sub-PETs, a description under every title and a
picked quote on each PET. Juno's board holds 36 statements in three PETs and nine sub-PETs. Rowan's holds 24 in three
PETs and seven sub-PETs. Mabel's holds 18 in three PETs and two sub-PETs, with one of hers unplaced (the analysis was
redone on 12 November 2026). The GETs board across the three is Board 1 of the demo's GETs, the Current board, marked
complete. It holds five GETs, each with its description, from the PETs and sub-PETs of all three. The sub-PETs whose
PET carries them are set aside, and the quote of each participant's row is ticked in the GET table. The GETs are a
home come alive with the dog, the dog as a way back to people or round them, being changed by the dog, holding on to
the dog through what it costs, and the parting from the dog, each lived in the participant's own way. Rowan gave his
dog up and has not settled what that was. The PETs tables and the GET table are the app's own, made from those boards,
so Open as table and the exports show a finished project's tables. Every participant's interviewer is named as the
transcript names them, Adam today.

The demo sits beside the app, in `demo/`, and not under a project's root. The transcripts are in `demo/source/` in the
raw three-column shape, as `Juno - interview.csv` and the two beside it. Each participant's annotations are in `<name>
- annotations.json`, and the GETs board's are in `GETs.json`. Each participant's annotated workbook is at
`demo/<name>/<name> - EN & ES.xlsx`, built from its CSV by the app's own create-from-source, with its sidecars in
`demo/<name>/Working/`. The GETs file is at `demo/idiograph-gets.json`. The copy that Reset demo restores from is in
`demo/pristine/`, with the GETs file. The project file is `demo/idiograph-project.json` (see Projects). That folder
is the one place outside every project's root that the server will open, and only that folder. The server refuses
its parent and every sibling, the way it refuses a live participant to a server started with `--root` at a scratch
folder.

**Opening it.** The demo's card, the first under Demo projects on Idiograph's Home, has the "IPA demo" tag beside its
name and its research question under it. It opens the demo's page as a project's card does, with the same tag beside
the name at its head. The page has the demo's GETs as a tile in the row at the top. It holds a row for each
participant, Juno, Rowan and Mabel, in that fixed order, so no row has a handle. Reset demo stands under them. Each row
has its two halves, its lines and Files as any row has, and a small demo tag. Each opens the way any other
participant opens. While one is open, the tag stands beside the name in the top bar, so a recording of the screen
shows on its face that these are not a participant's words. None ever enters the recent list. On the PETs screen the
participant picker of any demo participant lists the three. Each plays its recording in the player at the foot, as
any participant with one does, and a click on a timecode plays that passage. Each opens on its last passage. Rowan's
and Mabel's last passage was decided with no statement, skipped because zero is a fine answer for a passage. So its
empty first statement, under Statements complete on the bar, is a passage read and left blank. Juno's holds her own
summary of living with a dog. Every passage of each participant is decided.

**The highlights.** Each participant's highlights go in through the same function the `H` key called until 16
October. So they are real runs in the transcript cell, and the demo does nothing different. Since then they stand in
the file as any workbook's highlights do, drawn as plain words.

**Reset demo**, the quiet control under the rows, puts all three participants back from `demo/pristine/`. First a
confirm names every statement, note, quote and board written in them. (It said quote there until 16 October.) Each
workbook, progress file and board goes back as it ships, and so does the demo's GETs file, `demo/idiograph-gets.json`.
It takes away the exports' `demo/Working/`, so you can give the same demonstration twice. A workbook open in Excel
refuses the reset before anything is written. A copy of the demo folder added as a project lists its three
participants once, because its `pristine/` folder is never read as a participant.

**Building it.** `make_demo.py --written`, or a plain run, builds the whole finished demo from its sources, except the
recordings. For each participant it builds the workbook through create-from-source. It takes every passage through
the passage screen's own saves, each statement with its own key quote. A quote of pieces is found piece by piece in
its passage and joined with an ellipsis, as the passage screen joins them. It writes the progress file with its
rounds closed and Statements complete. It lays the board out as an agent's board make lays one out, adds its
descriptions and picks, then saves it, marks it current and marks it complete through the PETs screen's own
functions. Then it builds the GETs board across the three, laid out the same way, adds its descriptions and ticked
quotes, and saves it, marks it current and marks it complete through the GETs screen's own functions. The clock is
held at the times the sources give. Every part of each workbook's zip is dated alike, and the files the GETs read are
dated alike while they read them. So the same sources build the same files byte for byte. It writes `demo/pristine/`
and the live demo, and `--force` lets it replace live workbooks already there. The live sidecars and the live GETs
file are gitignored. The server copies a missing one in from `demo/pristine/` when it starts, so a clone opens the
demo as it ships.

**The thematic analysis demo** (3 November 2026). A second demo, Living with a dog with the "RTA demo" tag, is a
thematic analysis project of the same three invented participants. It is built from the same transcripts, so you can
compare the two methods on the same words. Its passages are coded with one shared code list of 22 codes, each with its
description. Some extracts have several codes, and passages have notes where the coding needed one. Its Themes board,
done in Braun and Clarke's reflexive way, holds four themes, each with its definition and most with a note, two
subthemes, and two codes unplaced. It lives in `demo/ta/`, a project of its own inside the demo's folder. Its project
file, the participants' folders, the code list and the Themes board's file are at its root, and its pristine copy is
in `demo/ta/pristine/`. Its sources are in `demo/ta/source/`: each participant's coding in `<name> - coding.json`, and
the code list and board in `Themes.json`. Its transcripts are the IPA demo's own, in `demo/source/`. `make_demo.py
--written` builds it after the IPA demo, and `make_demo.py --ta` builds it alone, in the same way and to the same bytes
every time. Its project is fixed, as the IPA demo's is. Reset demo on its page puts its participants, code list and
board back as they ship. The IPA demo never reads its participants as cases of its own. Agents open it with `--demo
ta` (see Agents).

**The recordings** (12 November 2026). Each participant's interview is spoken passage by passage in voices made with
Google's Gemini. There are four synthetic voices designed for the demo. The interviewer is a calm man with a southern
English accent, Juno a Spanish woman long in England, Mabel a woman of seventy-three from Lancashire, and Rowan a
quiet young man from Dublin. Juno's runs about twenty-eight minutes, Rowan's about eleven and a half and Mabel's about
ten and a half. Each transcript's timecodes are written from the measured passages, with half a second between them,
so clicking a timecode lands on the words of that passage. They replace the macOS `say` voices the demo had until
then, which spoke only Juno's.

The three recordings are committed in `packaging/recording/`. Each is named by the participant, the sheet and the hash
of the transcript it was made from. Their own licence stands beside them, `LICENSE-audio.md`. It says they are
AI-generated speech, to be copied and shared only unchanged and only as part of Idiograph or a version of it, and
never used to train or evaluate an AI model. The README's licence line says they are the one exception to the AGPL.

**Downloaded the first time one is played** (13 November 2026, Adam: "Text in, recordings on demand"). The installed
app carries the demo's text, its transcripts, workbooks and boards. So Home shows the demo and it opens with no
internet. The app does not carry the recordings, which would more than double the download. A demo participant's
player shows as any other's does. The first press of Play, a timecode or `Space` puts the offer in the player's place:
"This demo's recordings, 9.4 MB. Download?", with Download and Not now. Download says how far it has got, as in
"Downloading the recordings, 2.8 MB of 9.4 MB", with a line filling beside Cancel. Once all three are on your
computer, the player plays from where you pressed. Not now and Cancel put the player back, and the next press offers
it again. The PETs and GETs boards' player offers it in the same way when you press a quote's play. The thematic
analysis demo, Living with a dog coded, has the same three interviews. So its Coding screen offers the same download
and plays the same recordings, and one download serves both demos. With no internet the offer's line says "No
internet connection, so the recordings did not download. The demo works without them.", and Download tries again. A
recording that does not arrive exactly as it should is not kept. The recordings stay on your computer, in the demo's
own folder, and Reset demo leaves them there. Each was made at about 24 kbps, half the bitrate it had before. Juno's
is about 5.3 MB, Rowan's 2.2 MB and Mabel's 1.9 MB, with the voices the same and every timecode where it was.

The demo's own copy of each, in `demo/<name>/Source/Initial/Source/`, is gitignored. When you run from source, the
first time a participant's player looks for it, the server copies it in from `packaging/recording/`. That takes a
moment, with nothing to download. Nothing is spoken on your computer. A transcript edited since its recording was
made has no recording, because its timecodes no longer match the voices. Its player shows nothing, as for any
workbook without one. To put each recording in place by hand:

```
.venv/bin/python apps/idiograph/make_demo.py --audio-only
```

`packaging/recording/voice_demo.py` voices an edited passage again. It speaks that passage alone, joins the recording
again and writes the timecodes, and then builds the demo again (see Internals, The demo's recordings).

## Experiential statement guidance

The guidance stands under one heading, Experiential statement guidance, in the label face a step above the two
section headings inside it. The first section, Holding the craft, has eleven lines distilled from Adam's own guide to
experiential statements. They ask for your own words, and for what the experience was like, with the participant's
stance, not a bare event or a topic. They ask for your own interpretative words, and for the phenomenon the research
question asks about first. They ask you to follow the research question and not the interview, to keep one idea per
statement, and to use the words it needs and no more. They ask for a statement that stands alone, and say that not
every passage needs one. They ask for the movement in it, for the participant's stance kept whole and never smoothed
into gladness, and for force. Under them stands Adam's framing. Lines 1 and 2 are about the experience and
interpretation, 3 and 4 about relevance, and 5 to 8 about form. Form is a matter of judgement, so a statement that
breaks one may show that the line is wrong. Lines 9 to 11 are about what a statement carries, and 9 and 11 are project
rules. A colon after the phenomenon is fine, and no nudge flags one. Each line has a small arrow at its end. It opens
two short example statements on the demo's topic in place, in two columns, Less this and More this, showing what the
line means in practice. One stands open at a time. The arrow is a button, so Enter opens it from the keyboard. The
lines live in `guidance.md`, one per line starting with `- `, so editing that file changes the guidance. Each line's
examples are indented under it as `- Less this:` and `- More this:`. The plain paragraph under the section's heading
there is the framing, which you can reword in the same way. The craft prompts, one of which the first statement's field
shows on every passage, sit in the same file under a Placeholders heading and are read in the same way. The app takes
each section by its heading, so the two never mix. Those lines are written with `*` and not `-`, which keeps them out
of the rail on a server started before that section existed.

Guidance on the bar, an open book and its word after View, opens it. `G` does the same from anywhere outside a field,
with "Guidance (G)" in its tooltip. It slides in from the right edge of the screen, under the bar and the research
question, over the right of the screen. It takes no width from the three columns, so they keep their widths at 1280
wide whether it is open or closed (16 October). That was Adam's decision on a tester's feedback. The tester asked for
the notes in a column beside the transcript, the IPA book's layout, which the three columns of 17 October gave whole.
Under reduced motion it shows and goes with no slide. Its close button at its top right, Guidance again, `G`, `Esc` and
a click anywhere outside it close it. A click outside goes on to do what it does. It is closed on a new install. The
browser keeps whether it is open or closed beside the theme, so a reload opens it the way you left it. Until 16
October the guidance was a rail with a column of its own at the right of the screen, open by default, whose arrow put
it away to a slim tab at the screen's edge. A rail put away then reads as closed now, and so does a rail left open, so
it never opens over the fields by itself.

When open, the sheet has a card's firm edge at its left with a dialog's lift, so the fields under it read as under it.
At 1280 the faint rule once left no edge, and the form beside it looked cut mid-word. Below 520px wide it takes the
whole width, as the Participants panel does on GETs. At 360 a strip of cut words used to stand beside it (17 October).
While it is open, the keyboard is in it, never in a field it covers. A reload with it open, a passage opened from a
board, and a move by `Cmd + J` or `Cmd + K` put the keyboard on its close button, as Guidance does, or leave it where it
is inside the sheet. Until then a reload left the caret in a statement under it. Closing it hands the keyboard to
Guidance on the bar, and a click in a statement takes it there.

Above 1100px wide, the open sheet lies over the whole of the last of the three columns, with its left edge at the
column's edge, so the columns before it stand whole beside it. This happens where that column is 300 pixels or more,
as at 1280 in the book's order, where the notes' column is about 320 (17 October). Until then it lay over the fields'
column, and before that its 340 pixels left a strip of the fields about 70 wide showing, with their words cut. At every
width it stands under the research question, which stays whole above it. Where the last column is narrower, and at
1100px and below down to a phone's width, it is 340 pixels wide. The rest of the screen sits under a wash of the paper,
so what stands beside it reads as under it, and a click there still closes it and goes on to do what it does. The
guidance speaks of the participant as they. So do the craft prompts in the statement's field, the exploratory notes'
prompt and the interviewer note's prompts, because a participant may be anyone: "Mark their stance", "What are they
noticing, doing, feeling here?", "What matters to them, how they say it, what it might mean." (17 October, later).

The second section, Three personal examples, holds three of Adam's own statements, drawn afresh on every passage. They
come from the two pools `config.json` names. `corpus` is a markdown file of statements under one heading per source,
less any source named in `corpus_exclude`. `gravity_reference` is a finished workbook whose statement column is the
register anchor for this project. The tick box under them, Examples from this project only, narrows them to the
reference workbook alone. With neither file on the machine, as in a shared copy, both draw on the statements the demo
ships with in `demo/pristine/`. With no demo either, the section is empty. No statement is written into the code. The
prompt's `{examples}` fills from the same source, six at a time from the reference set.

**AI suggestions, if you want them.** They are off by default, and you switch them on in settings. With them on, an AI
suggest button sits under the statements, where its answers appear. One press takes the button away and puts the
section in its place, under the heading AI suggestions. It shows a line of key concepts, then the candidate statements
listed under it. Clicking a candidate fills the statement of the pair being worked on when that is empty. Otherwise it
adds a pair with the candidate under the last. The X beside the heading closes the answer and brings the button back.
Pressing it again asks again and gets a fresh answer, because the model is sampled each time. The next passage shows
the button again. Nothing it says reaches the workbook on its own. The passage leaves the page only when you press the
button.

The suggestion runs in two passes. The first asks for up to ten drafts, more than will be kept. The second hands them
back with the rules and keeps the strongest one to three. The prompt in Settings is sent unchanged in both, because
what each pass asks for goes in the user message and not in the system prompt.

The call sends the prompt from settings, the project's research question, the statement rules, six of your own
statements from the GRAVITY set, and the current passage with the interviewer's passage before it. When the passage's
pairs already hold quotes, the button sends them too, ten at most. Both passes then ask for statements centred on them
in the light of the whole passage, with "with your quotes" beside the AI suggestions heading. It asks for strict JSON
and reads it defensively, so a bad answer shows as one line in the panel. An error from the API comes back as one line
in plain words with its status in brackets and nothing else. Examples are "Anthropic refused the key (HTTP 401).",
"Anthropic asked for a break from requests (HTTP 429)." or "Anthropic did not answer (HTTP 529).", and from a local
model "Ollama refused the request (HTTP 404)." (17 October, later). Before, it said "The suggestion call answered
529.". No header and no body reaches the page. A refusal from the model is one line too, and so is an answer cut off at
its length limit. The same switch and key serve the AI help in PETs (see PETs). It asks the Experiential statements
model unless Settings gives PETs a model of its own.

Eight providers can answer (aipage, 8 November 2026). You choose one under Provider in settings, and it is stored as
`ai_provider` in `config.json`. Both passes go to the same one, through one function, `complete` in `ai_suggest.py`.
Under the list, one line of small type says where the passages go, as each provider's own published terms put it. That
is the fact an ethics form asks for:

- Anthropic, with your key (`anthropic`, the default), over the Messages API: "Passages go to Anthropic. They are
  stored in the US and may be processed in other countries."
- Mistral, with your key (`mistral`), at its EU address, `api.eu.mistral.ai`: "Passages go to Mistral, in the EU."
- Google Gemini, with your key (`gemini`): "Passages go to Google. On Google's free tier they may be used to
  improve its models and read by its reviewers."
- OpenAI, with your key (`openai`): "Passages go to OpenAI, which may process them in any country."
- Azure OpenAI, your organisation's (`azure`), with its Address and its Deployment, typed in place of a Model
  list: "Passages go to your organisation's Azure. Where they are processed depends on how it was set up."
- Another service, by its address (`other`), such as a university's own or one such as OpenRouter, with its Address,
  the key it asks for and its Model list, or the model's name typed where it lists none: "Passages go to" and the
  address's host.
- Local, Ollama on this machine (`local`), and Local, LM Studio on this machine (`lmstudio`), each with its Address
  filled with the usual one, `http://127.0.0.1:11434` and `http://127.0.0.1:1234/v1`: "Passages stay on this
  machine.", or the host that an address elsewhere names.

Every row except the provider's own is hidden. Choosing another provider shows its rows at once, asks for its key's
state and its list, and loses nothing you typed for the one before. Mistral's, Gemini's, OpenAI's, Another service's
and LM Studio's Model lists are the service's own list, by the models' own names, with no price. An address must be
https, or http on this computer. With AI features off, none of this shows and no list is asked for.

For Anthropic, the Model dropdown lists the current models, Fable 5.1, Opus 5.5, Opus 5, Opus 4.8, 4.7 and 4.6, Sonnet
5.5, Sonnet 5 and 4.6, and Haiku 5.5 and 4.5, each by its name. The chosen model's price per million input and output
tokens stands on its own line under the list, as in "$2 in, $10 out, per million tokens" for Sonnet 5.5. So neither
the name nor the price is cut short. The PETs model list still names each model with its price, as in "Sonnet 5.5 · $2
in, $10 out, per million tokens". With a key stored, the list comes live from `GET /v1/models`, cut to those models and
kept in that order, so a model the account cannot call is not offered. The live list is held for an hour, and saving
or removing the key lets it go. With no key, or when the live list does not answer, the table built into
`ai_suggest.py` stands in. A line under the dropdown says which list you are looking at, and why, in the same plain
words, as in "The built-in list, because Anthropic refused the key (HTTP 401).". It is in the amber when the live list
failed. So is the line beside Check key when the keychain or the key fails (17 October, later). The choice is `model`
in `config.json`, which is Haiku 5.5 by default, at a fraction of a cent per passage. A dated id stored before, such
as `claude-haiku-4-5-20251001`, still works, shows as Haiku 4.5, and stays as it is when the plain id is saved over
it. No request sends `temperature`, `top_p`, `top_k` or a `thinking` field, and none fills in the start of the answer.
The 5.x models think by default, so they get a higher token ceiling and a longer wait, and the answer is read from the
text blocks alone.

For Local, the dropdown lists the models Ollama has pulled, from `/api/tags` at `local_url` (default
`http://127.0.0.1:11434`), and the choice is `local_model`. A suggestion is one `/api/chat` call per pass, not
streamed and held to JSON. Nothing about the key applies, nothing leaves the machine and nothing is charged. When
Ollama is not running, the Local option says so and says what to do. You install it from ollama.com and pull a model,
for example `ollama pull llama3.1:8b`, and the model appears in the list. Its Address is `local_url`.

**The key.** Settings has a hidden field for the API key, with a Check key button beside it (21 October, in place of
Save key). A line says whether a key is stored and where, or what Check key found. Enter in the field does Check key,
which stores the key only when the provider accepts it. These show under every provider that takes a key, and stand
aside under the two local ones, which need none. Saving puts the key in the macOS keychain as a generic password under
the provider's own service name: `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`,
`AZURE_OPENAI_API_KEY`, or `IDIOGRAPH_AI_KEY` and the host for Another service. It replaces whatever was there before.
Remove deletes only the chosen provider's item. The key never lands in `config.json`, in `state.json` or in a log, and
the verbose log prints the path of a key request and never its body. The server reads it at the moment a suggestion is
asked for, and it goes no further than that request. Saving passes the value to the `security` tool as an argument.
That makes it visible in the process list for the life of that call, which is milliseconds on a single-user Mac. That
is the trade for never writing it to a file, and it is accepted here. A machine with no `security` tool falls back to
`.env` in the app's folder at mode 0600, and the status line says which of the two it found. A key already in `.env`
is read first and is left to VS Code. Remove does not touch that file.

**The prompt.** The whole system prompt is a template in `config.json` under `ai_prompt`. Settings shows it in a box,
with a Reset to default beside it. `{research_question}` becomes "The study asks:" and the project's question, with a
sentence saying that every statement answers it. It goes, with that sentence, when the project has no question. A
suggestion on the demo sends the demo's question, and one on any other participant sends the root's. `{guidance}`
becomes the lines of the rail, and `{examples}` becomes six of your own statements, each as a bulleted block. Settings
names the three under the box in one line, "Placeholders: {research_question}, {guidance}, {examples}". A template with
no `{guidance}` or no `{research_question}` in it is sent as it stands, in case you want one without. That is also how a
prompt saved before the placeholder existed still goes out. A template with no JSON in it takes the shape instruction
on the end, so the answer stays parseable whatever else you do to it.

**The test bench.** Under the prompt sits one passage of the demo participant. The participant's passage is in a box,
and the interviewer's passage before it stands above the box, in the smaller faint type the sheet gives an
interviewer's passage. Both are read from `demo/source/Juno - interview.csv` when settings opens, and never from a
project folder, so no participant's words are on it when the app is shown. You can edit both. Its label reads Test
bench (invented sample data). A line of small type under the boxes says "This passage is from Juno, who is made up for
the demo. Nothing from your own participants is sent.", and it stays as it is when you edit the box. Under them is the
AI suggest button, the one under the statements, with its look, its icon and its label. It sends what that button
sends: the passage, the passage before it, its timecode, the speaker and the participant. The one function
`suggestBody` in `distil.js` builds them. It sends the provider, the model, the prompt and the research question of
the participant's own project as saved, and the rest as they stand in the panel, saved or not. The answer takes the
button's place, as it does under the statements. It shows the key concepts and the candidates, with the model and the
seconds it took, and the X brings the button back. Nothing it says is written anywhere, and Reset to default fetches
the passage again. The endpoint is `/api/suggest-sample`. Asked with nothing, it answers with the sample. Asked with
the four fields, it runs the suggestion. A page from before this sends the one box as `text`, with a passage per
`Name:` line, and is still answered. `/api/models` sends Anthropic's list and Ollama's status, and while another
provider is chosen it sends that provider's list alone.

As you type a statement, nudges appear from the checks in `ipa_annotation_audit.py`. They catch a statement past the
project's statement length, 15 words by default (with no minimum), a The/She/Her/A lead, a quoted fragment, a
semicolon, an em dash, an arrow, and the reads-as construction. You switch each on or off in the statements screen's
View, under the small heading Nudges, for the open project. Until 3 October 2026 the screen called them flags. Since 17
November 2026 the nudges belong to each project (Adam's ruling: they are his way of doing IPA, not the book's). A
project made from then on starts with every nudge off, kept in its project file as `nudges`, with the checks on. A
project made before, whose file has none, reads the nudges that the app's settings held for every project until then.
So it keeps what it had, and nothing is written to its file until you tick one. On a new install, whose settings hold
none, a project brought in by Add project reads every nudge off too. A demo's nudges are off and fixed. The app refuses
a nudge set to anything but on or off. An agent reads them with `project show` and sets them with `project set
--nudges` (MCP's project_set), as View does. Nothing blocks a save and nothing is scored. The length nudge has no
minimum.

**Nudges explained.** Each tick under Nudges in the statements screen's View has a small circled i after its label. Tab
reaches it, and a screen reader reads it out with its words. On hover or on focus it says what the nudge catches and
gives an example made up for it, and nothing more (17 November 2026, Adam: never figures from his own projects):

**Statement length.** In Project settings, under Experiential statements, Statement length is the number of words past
which the length nudge speaks and the count under a statement turns amber (5 November 2026). From 21 October it stood
in the length nudge's own row in Settings. The nudge's row in View says "word count past the statement length". Its
tick turns the nudge on or off for the project, and the nudge uses the project's own number. The number belongs to
the project (20 October, after a tester's statements of 28 words). It is 15 by default, and the number's tooltip names
it. Type it or step it with the arrows, from 5 to 60. The app saves it in the project's file a moment after the last
change, and writes it there only when it is not 15. The demo's is fixed.

*Word count past the statement length.* Catches a statement longer than the statement length in Project settings.
That is 15 words unless you change it. For example, "Walking the dog each morning before work becomes the one part of
the day she keeps for herself" has 18 words.

*Opens with She, He or They.* Catches a statement that opens with She, Her, He, His, They or Their. For example,
"She feels calmer once the dog is asleep".

*A quoted fragment.* Catches inverted commas inside a statement. For example, "Feels 'properly at home' with the
dog around".

*A semicolon.* Catches a semicolon inside a statement. For example, "Missing the dog; dreading the empty flat".

*An em dash.* Catches an em dash (the long dash). For example, "Calm at home — restless on the walk".

*An arrow.* Catches an arrow (→ or ->) inside a statement. For example, "Fear → trust on the second walk".

*The reads-as construction.* Catches reads, casts or recasts followed by as. For example, "Reads the barking at
the door as a warning".

A nudge says what it has to say and no longer quotes the statement back, because the statement is just above it. Each
statement's nudges stand under it, so none opens with a line number, as "Line 2:" did while the statements shared one
field.
