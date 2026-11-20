# Idiograph manual

This manual is a reference. Turn to it when something has gone wrong, when you are not sure what a term means,
or when someone asks where your data goes. The screens, their labels and the Guidance tabs explain the rest.
How to run Idiograph from its source code is in the [README](../README.md), and how it works underneath is in
[docs/internals.md](internals.md).

## Start here

Idiograph is software for Interpretative Phenomenological Analysis (IPA) and reflexive thematic analysis. It
is free and open source. It runs on a Mac, Windows or Linux, and your files stay on your computer.

When you make a project, you choose its method. There are three. IPA takes each participant from transcript to
experiential statements to personal experiential themes (PETs), and then all of them to group experiential
themes (GETs). Longitudinal IPA does the same for participants interviewed more than once, and adds themes
across time for each participant and across the group. Reflexive thematic analysis (RTA) codes extracts and
builds themes from the codes. You cannot change a project's method after you have made it. The terms each
method uses, and how they feed each other, are under [The method's terms and how they
relate](#the-method-s-terms-and-how-they-relate).

Settings belongs to the app and holds what is true wherever you work: your name, the language
and formats, and the AI features. Project settings belongs to one project. It holds the project's name,
research question, reflexivity statement, timepoints, interviewer's name, statement length, GETs rules,
whether AI agents may read it, and Working together. When you tick Archive this project, Home lists the
project under Archived projects. It still opens, and you can still change it.

Home has four demo projects: an IPA study, a longitudinal IPA study and two reflexive thematic analysis
studies. Their interviews are invented, and their voices and their analysis were made with AI, which is why
each says "AI-generated demo". They are there to try Idiograph on. They are not an example of a finished
study. You cannot change a demo's settings, and Reset demo puts its participants back as they ship. Reset demo is in
the "..." menu on a demo's card, in the menu on the band inside a demo, and beside Project settings on a demo's page.
When a newer version of a demo comes with an update of Idiograph, its card says "This demo has been updated." The demo
changes only when you press Get the update, and the cross hides the line until the next version.

## Installing and opening Idiograph

Each download is the newest version, from Idiograph's page on GitHub, github.com/Pharkie/idiograph.

On a Mac, download `Idiograph.dmg`, open it and drag Idiograph onto Applications. It runs on Macs with Apple
Silicon (M1 or later). Idiograph is not yet signed by Apple, so the first time you open it macOS says it
cannot check the app. Open System Settings, then Privacy and Security, and press Open Anyway. You do this
once.

On Windows, download `Idiograph-Setup.exe` and run it. The first time, Windows says that it protected your PC.
Choose More info, then Run anyway. Setup installs Idiograph for you alone, with no administrator's password.
Idiograph needs Microsoft's WebView2, and Setup installs it first if Windows lacks it.

On Linux, download `Idiograph-x86_64.AppImage`, make it executable and run it. Ubuntu 24.04 needs the package
`libfuse2t64` for that. On Ubuntu, Debian or Mint you can install `Idiograph-amd64.deb` instead, but that copy
does not update itself.

The first time Idiograph opens, Home asks whether to check for updates. If you say yes, Idiograph asks GitHub
once a day whether there is a newer version. You can change this in Settings, under General. Every update is
signed by Idiograph's author. Idiograph installs an update only when its signature matches the key built into
every copy, so nobody else can send you one. A new version installs over the old one, and your projects and
settings stay as they were.

Uninstalling Idiograph never touches your projects, because they are in folders you chose. On Windows the
uninstaller offers to clear what the window remembers, such as its size and zoom. Your participants,
transcripts and projects stay either way.

## Your files and your privacy

Supervisors, examiners and ethics boards ask where the data is kept and what leaves the computer. This section
answers both.

### Where your files are

A project is a folder you choose, and Idiograph keeps the project's work nowhere else. Each participant has a
folder of their own inside it, named by their number and pseudonym, such as `P1 - Ada`.

The participant's workbook, such as `P1 Ada - EN & ES.xlsx`, holds the transcript, the exploratory notes, the
experiential statements and their quotes, each in its own column. It is an ordinary Excel file, and you can
open it in Excel. While Excel has it open, Idiograph marks the participant "open in Excel" and does not write
to the workbook. Close it in Excel to go on. A change you make to a statement in Excel shows on the boards the
next time they open.

The participant's `Source` folder keeps a copy of each transcript you added, with the listed names already
replaced, and their recordings. Their `Working`
folder keeps the PETs boards and a small file of where you are in the transcript. Their `_Archive` folder
keeps a copy of a file before Idiograph changes it in a large way, such as a rename, a trim or a new
interview. At the project's root are the project's settings, its GETs, LGETs and Trajectories boards, a
thematic analysis project's code list, and the project's History. Each is a file whose name starts with
`idiograph-`.

Your own settings, the list of your projects and the agent log are in Idiograph's own folder:
`~/Library/Application Support/Idiograph` on a Mac, `%APPDATA%\Idiograph` on Windows and
`~/.local/share/Idiograph` on Linux.

### Renaming a participant

Rename, in a participant's profile, gives a participant a new pseudonym. It changes the name on every passage
of their workbook, on every board, in the GETs, LGETs and Trajectories, and in the list of names to replace.
The participant keeps their place in the order, their picture, label and pen portrait, and all their work. The
folder keeps its old name unless you tick Rename the folder too. A copy of each file it changes goes into
`_Archive` first. Rename never touches the interviewer's passages, the transcripts in `Source` or exports you
have already written.

### Names replaced as a transcript comes in

A project can keep a list of real names and the pseudonym each becomes. When you add a transcript, type the
participant's real name beside their pseudonym. Idiograph finds every name on the list in the transcript and
shows each find in its sentence before it replaces anything. Untick a find that is an ordinary word, such as
"Will" in "Will you tell me". The finds you leave ticked are replaced before the transcript reaches the
workbook. The list stays on your computer, and a shared copy never holds it.

If you untick one find of a name, the copies in that participant's `Source` folder keep every find of that
name as it was written. A shared copy of the whole project takes `Source` with it, so check those copies
before you send one.

### What leaves your computer

Your words leave your computer only in these cases, and only when you ask for them.

The update check sends GitHub your internet address and the version of Idiograph you have. It never sends your
work. Send feedback sends your note, your reply address if you give one, the app's version, your system and
the name of the screen you were on to Idiograph's author. Nothing of your participants goes, and no picture of
the screen is taken.

The AI features are off on a new install. When you turn them on and press AI suggest, Idiograph sends that one
passage, or that one PET or GET, to the provider you chose (see [AI and agents](#ai-and-agents)). An AI agent
you use yourself sends whatever it reads to its own provider, which can be a whole participant.

Working together sends the updates between your teammates through the relay at idiograph.app, or through a shared
folder. Everything is sealed on your computer before it goes, so neither the relay nor anyone who can open the
shared folder can read the words. The relay sees each computer's internet address, and the times, sizes and
number of the messages. It never sees names, pseudonyms or file names. Someone who can open the shared folder
sees sealed files with their sizes and times.

The first time you play a demo's recording, the player says how large the demo's recordings are and offers to
download them from GitHub. In Settings, Check key and the list of models send your AI key to the provider it
belongs to, and nothing of your work. Nothing else is sent or fetched.

### Your AI key

On a Mac, the key for an AI provider is kept in the macOS keychain. On Windows and Linux it is kept in a file
in Idiograph's own folder that only your account can read. It is never written into a project, a log or the
settings file, and it goes only to the provider it belongs to.

## The method's terms and how they relate

Idiograph follows Smith, Flowers and Larkin (2022, *Interpretative Phenomenological Analysis: Theory, Method
and Research*, 2nd edn) for IPA, Farr and Nizza (2019) for longitudinal IPA, and Braun and Clarke for
reflexive thematic analysis. Each term below has a short definition and its place in the chain. Where a
setting departs from the book, the last part of this section says so.

### The IPA chain

```
transcript
  └ passage ── exploratory notes
      └ experiential statement + its one quote
          └ PET (one participant, on a board), holding sub-themes

every participant's PETs ── GETs (across the participants)
```

Experiential statements covers steps 2 and 3 of the book for one participant. PETs covers steps 4 and 5, and
you do both for each participant in turn (step 6). GETs is step 7, across the participants.

### Passage

A passage is one person's stretch of talk. It is one row of the transcript. The word comes from the book's
Chapter 5. The participant's passages take statements. The interviewer's passages are context, and you pass
over them as you work.

### Exploratory note

An exploratory note is your descriptive, linguistic or conceptual comment on a passage. Notes stand in their
own column beside the transcript, as in the book's Box 5.4.

### Experiential statement

An experiential statement says, in a few words, what a passage shows about the participant's experience. Each
passage can have any number. Statements are what PETs are made from.

### Quote

Each statement has exactly one quote. It is the participant's own words that ground the statement. A quote is
usually a run of
words in its passage. It can also join the participant's passages just before and after, when only the
interviewer's words stand between them (see [A quote across passages](#a-quote-across-passages)).

### Interviewer note

An interviewer note is a note on one of your own passages as interviewer, such as a question that moved the
participant on, or one that closed them down. Interviewer notes are kept apart from the exploratory notes,
because they are about your interviewing and not about the participant's experience.

### PET

A personal experiential theme groups one participant's statements that belong together. You make one by
selecting statements on the board and pressing `G`, then giving it a title and, if you want, a description
that says more. A statement belongs to a PET because you put it there. Where a card happens to lie on the
board does not matter.

### Sub-theme

A label inside a PET is a sub-theme, and a label inside a sub-theme is a group. They nest as deep as you need.
Every table and export names each level the same way.

### Stack

When a participant says one point several ways close together, stack the others under the statement that says
it best. That statement is the top, and it stands for the stack in the PETs table and the exports. The others
stay one click away for the audit trail, and the statements CSV lists them under their top. A stack is not a
PET, and it is one level deep.

### Close pair

A close pair is two statements in the same PET or sub-theme, from the same sheet and within a minute of each
other, or within another gap you set. The Close pairs button draws a dashed line between them, so you can
decide whether one should stack under the other. Close pairs are off on a new install.

### Unplaced and Set aside

A statement in Unplaced is not yet decided. It waits in the board's sidebar until you place it. A statement in
Set aside is decided against, because it does not answer the research question or is poorly evidenced. Set
aside is rare, and the Guidance tab suggests you note why. Nothing on a board deletes a statement, so anything
set aside can come back.

### Sticky note

A sticky note is a note to yourself on a board. It is never a statement, and no table holds it. The canvas's
print, PDF and image show it as the board does.

### Picks

On a PET or a sub-theme each quote has a tick. Tick the one or two quotes that carry the PET. They show first
in its Inspector. In the GET table a participant's row starts with the first picked quote of their PET there,
until you tick another key quote for the row.

### Board and Current board

A board is one grouping of a participant's statements into PETs. You can keep several, to try one grouping
beside another. The Current board is the one you are going with.
There is one at most for each participant, and it is the board GETs and LPETs take (see [Which board feeds the
next step](#which-board-feeds-the-next-step)).

### GET

A group experiential theme draws together PETs and sub-themes from several participants. On the GETs board
each card is a participant's PET, sub-theme or statement in that participant's colour, and a label over cards
is a GET. A participant note is your own words about a participant on the GETs board. It never counts towards
a GET's badge.

### The count and the minimum

A GET's badge reads "6 of 8": six participants have something under it, out of eight in the study. The minimum
starts at the band in Smith (2011a): every participant for three or fewer, three for four to eight, and half,
rounded up, for more than eight. You can change it in Project settings. A GET under the minimum keeps its
cards, and its badge is dashed.

### One GET per PET

With One GET per PET on, which is the default, each PET or sub-theme sits under one GET at most. Turn it off
in Project settings to place a PET under a second GET as well. Each of its two cards then names the other.

### Complete

Each phase has its own mark. Statements complete marks a participant's transcript as worked through, once
every passage is decided. PETs complete marks the PETs on the Current board as final, and Idiograph refuses
it while no board is marked current. GETs complete marks the GETs,
and Idiograph refuses it until every participant has come in from a board marked PETs complete and has not
changed since. In a longitudinal project LPETs and LGETs are marked complete in the same way, and each
timepoint has its own Statements complete and PETs complete. Trajectories has its own mark too, and Idiograph
refuses it while a participant is in no trajectory or the project has no participant. A mark locks nothing. You can still revise
everything, and Reopen takes the mark off.

### Pen portrait

Each participant can have a picture, a label of a few words and a pen portrait. A pen portrait is a short
paragraph to remind you who they were. The Pen portrait tick under Export puts the label and pen portrait at
the head of the PETs table. No picture goes into any export.

### Reflexivity

Reflexivity, in Project settings, holds your reflexivity statement for the project. It is there to copy into a
write-up. No export prints it, and a shared copy leaves it out. AI agents can read it.

### The longitudinal chain

```
participant
  ├ T1 ── passages ── statements ── PETs at T1 ─┐
  ├ T2 ── passages ── statements ── PETs at T2 ─┼─ LPETs (one participant across time),
  └ T3 ── passages ── statements ── PETs at T3 ─┘  each with a domain, and at each
                                                   timepoint a state and a key quote

every participant's LPETs ─┬─ LGETs (themes across the group)
                           └─ Trajectories (shared courses, each participant in one)
```

You make PETs at each timepoint as in IPA. Then you read each participant's PETs across time into LPETs. LGETs
draw the LPETs together across the group, and Trajectories places each participant on a course that others
share.

### Timepoint

A timepoint is one round of interviews, such as before the season, midsummer and after the harvest. Each has
a label and a description. The labels start as T1 and T2. See [Longitudinal
projects](#longitudinal-projects) for how they are kept.

### LPET

A longitudinal personal experiential theme is your interpretation of one participant across time. Its cards
are the PETs, sub-themes and statements it draws on at each timepoint. They are its audit trail, not its
parts. The LPET's title, its state at each timepoint and its note are yours, and nothing in the app writes
them for you. The LPET table sets each LPET out with the timepoints across, as in Nizza's Table 8, and its
Word and PDF are the thesis appendix.

### LGET

A longitudinal group experiential theme draws together LPETs from several participants, as a GET draws
together PETs. In a longitudinal project LGETs stand where GETs would. There are no GETs at a single
timepoint.

### Trajectory

A trajectory is a course that several participants share, such as "Settling in" or "Up then down". You make
and name trajectories yourself on the Trajectories board. Each participant is placed in one, and a participant
in none waits in Unplaced. A trajectory is about the whole person over time. An LPET is one theme of one
person over time. Each participant on a trajectory shows their LPETs as rows, with a key quote and a state at
each timepoint.

### Domain

A domain is a word or two that names the area of life an LPET belongs to, such as Work or Family. It shows as
a coloured pill on the LPET, and the same domain has the same colour across the project. An LPET can be in
more than one domain.

### State

A state is your sentence on where an LPET stands at one timepoint. It is the LPET table's row at that
timepoint, and Trajectories shows the same words.

### Key quote

A key quote is the one quote you choose to show an LPET at one timepoint. It can be a statement's quote or
words taken from the transcript. Choosing one changes nothing in the workbook.

### The thematic analysis chain

```
transcript
  └ passage
      └ extract ─ its codes
          └ code list  (every code, its extracts across participants)
              └ themes  (codes grouped on the Themes board)
                  └ subthemes
```

### Extract

An extract is a run of words in a passage that you code. A passage can hold several extracts, and each extract
can carry several codes.

### Code

A code is a label that many extracts share. You give it on the Coding screen, as an existing code or a new
one. An in vivo code takes the selected words as its name.

Every change to an extract's codes reaches the Themes board as you save it. When you give an extract another
code, or add a second code, on the Coding screen or on its card on the Themes board, the extract moves at once
beside that code's other extracts, wherever that code stands: in its theme, loose on the canvas or in the Unplaced
panel. A new code stays in the theme the extract stood in, so a code you retype or retitle keeps its theme. An extract you set aside that is given a new code comes in loose on the board, unless it was its old code's last card, when it stays in Set aside. When
you take a code off an extract, the extract leaves that code's card. An agent's change of codes
does the same. Idiograph saves a revision of each board it changes first, so History can take you back.

### Code list

The code list shows every code with its description and all its extracts, participant by participant. There
you rename, describe or merge a code, and delete one that has no extracts. A rename or a merge changes every
workbook and every board at once.

### Theme

On the Themes board each card is a code, and a label over codes is a theme. A theme has a definition, which is
its central idea. It can hold subthemes. For each theme you can tick one key extract for each participant,
which the theme table shows.

### Where the app departs from the book

[Rounds](#rounds) are the author's own pace and not a step of IPA. They are off in a new project. The nudges
under a statement are off in a new project too. When on, the length nudge speaks past 15 words, which you can
change in Project settings. Stacks and close pairs come from the author's practice of keeping one statement
where a participant repeats a point. One GET per PET is on by default, and the minimum is Smith's band until
you change it. An interview in two parts is pooled into one participant's PETs.

## Working on a transcript

### When a passage counts as decided

A passage is decided once you have saved it, saved it empty or pressed Skip. It is also decided once you have
moved past it and decided a later passage on the same sheet, because moving past a passage is a decision not
to code it. Decided passages are what the counts and Statements complete go by.

### A quote across passages

One quote can join the same participant's passages just before or after the one you are on, when only the
interviewer's words stand between them. Select the first words, then hold `Cmd` (`Ctrl` on Windows and Linux)
and select words in the next passage. The quote keeps the pieces in order with an ellipsis between them and
never takes in the interviewer's words. Everywhere it is cited, it shows the range of times, such as "Initial,
25:51–26:50". A quote cannot skip a passage of the participant's or take in another speaker.

### Correcting the transcript

Idiograph can correct a transcript without Excel. Each of these writes to the workbook, and `Cmd + Z` takes it
back.

To correct a passage's words, press `E` on the passage you are on, or double-click any passage's text. To
correct a timecode, double-click it. To give words to the other speaker, such as an interviewer's question
transcribed inside the participant's answer, select the words and press `C`. They become a passage of their
own, so one row can become three.

To cut the consent talk at the start and the goodbyes at the end, right-click a row. Choose to cut that
passage and the ones before it, or that passage and the ones after it. Idiograph keeps a copy of the workbook
in `_Archive` first, and `Cmd + Z` brings the cut rows back.

Find and replace, `Cmd + Shift + F` (`Ctrl + Shift + F` on Windows and Linux), changes the transcript's words
across the whole workbook, on every sheet and in the interviewer's passages too. Replace all also changes the
same words in your statements, quotes and notes, and the card counts those before you press it. Replace
changes the one find in the transcript alone.

The row's menu also opens from the three dots in a row's margin.

### An interview in two parts

An interview recorded in two parts is two sheets of one workbook, and one participant. Its PETs pool the
statements of both sheets.

### Rounds

Work in rounds, in the statements screen's View, paces the work in stretches of transcript with a daily
target. A round is ten minutes of transcript until you change it.

### Search

Search, `Cmd + F` (`Ctrl + F` on Windows and Linux), finds words in passages, notes, statements, quotes, PETs,
GETs, their notes and sticky notes, participants' names and the research question. It looks in This
participant, This project or Everything. It finds other forms of a word, so "sleep" also finds "slept". Words
in quotation marks are found exactly as typed. It leaves out AI suggestions.

## Boards

A board holds one grouping of a participant's statements. The canvas shows what is placed, and the sidebar
holds Unplaced and Set aside (see [Unplaced and Set aside](#unplaced-and-set-aside)). Dragging a card near a
PET does not put it in (see [PET](#pet)).

### The order inside a PET

Inside a PET, higher means a better example or better quotes. Idiograph reads a PET top to bottom, and left to
right along a row, and that order is the order in every table, print, Word file and CSV. A sub-theme comes
where its top edge sits among the cards. Table view shows that order.

### Why keep several boards

Duplicate a board to try another grouping without losing the first. Each board keeps its own undo, its own
History and its own note on why it exists. Delete this board cannot be undone. Idiograph keeps the deleted
board's History in `_Archive`.

### Which board feeds the next step

GETs, LPETs and LGETs each take one board from each participant. They take the board marked PETs complete (or
LPETs complete) if there is one. Otherwise they take the Current board, and otherwise the board that was last
open. A participant who comes in from a board that is not marked complete shows "PETs not complete" on the
GETs board.

### When a participant's PETs change

When you change a participant's PETs after they came into GETs, the GETs board brings the change in by itself
and says so. A change made outside the app shows Update instead. Idiograph saves a
revision of the GETs board first, so History can take you back. A PET the participant no longer has stays
where it was, marked "No longer in" their PETs, and nothing moves by itself.

### Editing a statement on a board

Double-click a statement's card to edit its words. The edit writes to the participant's workbook, and every
board, the GETs and the LPETs show the new words. The same happens when you reword a statement on
Experiential statements.

## Longitudinal projects

A longitudinal project interviews each participant at two timepoints or more. You set the timepoints when you
make the project, and you can add more later in Project settings. You cannot lower the number past a timepoint
that holds an interview.

Each participant has one workbook. Each timepoint is a set of sheets in it, so an interview at T2 is new
sheets at the end of the same workbook. A timepoint is known by its place, so renaming T1 to "Before the
season" moves nothing.

Each timepoint has its own Experiential statements, its own PETs boards, its own Current board and its own
marks of complete. So T1 can be complete while T2 is under way. When you add a transcript, choose its
timepoint on its row. A participant not interviewed at a timepoint shows Not interviewed there.

Then the work goes on to LPETs for each participant, LGETs across the group and the Trajectories board. Their
terms are under [The longitudinal chain](#the-longitudinal-chain).

You can start a participant's LPETs at any time from whatever PETs exist. Each timepoint comes in from the
board described under [Which board feeds the next step](#which-board-feeds-the-next-step), and a later change
to those PETs comes in by itself, as it does on GETs. On the LPETs board, a PET or sub-theme that no LPET
draws on can keep your reason, in Why no LPET draws on it. The reasons go into the LPET appendix. Rarely, one
moment informs two LPETs. Also drawn on by, in a card's menu, puts a second card of it under the other LPET.

On a timepoint's PETs board, the Inspector on a PET, a sub-theme or a statement shows the LPETs that draw on
it. A statement's time is cited with its timepoint everywhere after PETs, as in "T1, 35:55".

The Trajectories board belongs to the project, and its title is the research question. New trajectory adds
one. You drag each participant onto the trajectory they follow, choose a key quote and write a state for each
of their LPETs at each timepoint, and give the participant a label of a few words. The state and the key quote
are the same as the LPET table's, so a change in one place shows in the other.

## Bringing work in and sending it out

### Add transcripts

Add transcripts, on the project's page, takes a VTT or SRT file, plain text, a Word file, or a CSV or Excel
file. It shows a preview of the passages and the speakers before it makes anything. It chooses as interviewer
the speaker whose name matches the interviewer's name in Project settings, or else the speaker who asks the
most questions, and you can change the choice. It also shows the format it found the times in, which you can
set by hand if it guessed wrong. A file under a new pseudonym makes a new participant. A file under a
pseudonym already in the project adds a further interview to that participant. One transcript is one
participant, so a couple interviewed together is one participant.

### A spreadsheet with statements already in it

A spreadsheet can bring work done elsewhere. A column of statements puts each statement on its passage, with
several in a cell one to a line, so the participant opens ready for PETs. A column headed Quote pairs its
lines with the statements on the same row, the first quote with the first statement.

### Recordings

A recording goes with its transcript, as an `.m4a`, `.mp3`, `.wav` or `.m4b` file. Idiograph copies it into
the participant's `Source` folder and names the copy by the participant's pseudonym. The file's own name may
hold a real name, so it is not used. If the recording's times are a little off the transcript's, set an offset
in seconds with Offset.

### Projects from NVivo, ATLAS.ti or MAXQDA

A project exported as REFI-QDA, a `.qdpx` file, comes in through Add transcripts. Each document becomes a
participant's interview. Each code on a passage becomes an experiential statement with its quotation as its
quote, and a comment on a quotation becomes an exploratory note. On request, each code group becomes a PET.
PDFs, pictures, variables, free memos, links and networks do not come in, and the import says so.

### PETs and LPETs from Excel

An AI agent can bring a table of PETs or LPETs that you made in Excel onto a new board, matching each row to
its statement. Ask it to use Idiograph's `board import`, with a dry run first. Where a row's wording differs
from the statement it matches, the import changes the statement to the table's wording, and every board
shows the new words. Your other boards keep their PETs and layout.

### What each export holds

What Export holds follows the view. On the canvas, Export gives Print, Save
as PDF and Save as an image of the board as it lies. In Table view, Export gives the tables: Print, Save as
PDF, Microsoft Word, and on PETs, Markdown and CSV.

```
Export                   From          Holds
PETs table               PETs, Table   Each PET, its sub-themes and statements, each
                                       statement with its quote and time, in the shape
                                       of the book's Box 5.6
Statements CSV           PETs, Table   Every statement with its time, quote and PET
GET table                GETs, Table   Each GET with a row for every participant and
                                       their key quote
Audit trail              GETs, Table   Each GET traced from passage to quote,
                                       statement, PET and GET
LPET table               LPETs, Table  Each LPET with the timepoints across: state,
                                       key quote and what it draws on, then the PETs
                                       no LPET draws on
LGET table               LGETs, Table  Each LGET with a row for every participant
Theme table              Themes, Table Each theme, its codes and their extracts, or
                                       each participant's key extract alone
REFI-QDA (.qdpx)         Project menu  Transcripts, statements as codes, notes,
                                       PETs, GETs and recordings if ticked
```

A REFI-QDA file opens in NVivo, ATLAS.ti, MAXQDA and QualCoder. It holds one board for each participant, the
one described under [Which board feeds the next step](#which-board-feeds-the-next-step). It does not keep
your other boards, History, where each card lay, stacks, sticky notes, participant notes or picks.

## Sharing and working together

### Share a copy

Share a copy, on a project's menu, writes the project as one file that someone else's Idiograph opens as a
copy. It can hold the whole project or chosen participants. For each participant you choose, their transcript,
notes and statements always go, and their PETs go unless you untick them. The GETs go only with the whole
project, because they are made from every participant. Recordings go only when you tick them, because a voice
can identify a participant. A copy never holds the list of names to replace, your reflexivity statement,
Project history or the record of agents' changes. A copy of the whole project with all its boards takes the
`_Archive` folders too, apart from the copies kept before names were replaced. A copy of chosen participants,
or of the Current boards only, leaves `_Archive` out. An AI agent can also send one participant with nothing
of your grouping, so another analyst can make PETs blind.

### A copy coming back

When the other analyst sends the copy back, A copy someone sent you, under Open… on Home, offers to add their boards to your
project. An AI agent can do the same. Each comes in as
a new board named with whose it is, such as "Sam's board, 30 Oct". It is never your Current board and never
replaces one of yours. A statement you reworded since you sent the copy shows your wording.

### Working together

Working together, in Project settings, lets a small team work on one project from their own
computers. Each participant has one owner, and only the owner's computer changes that participant. The GETs
board has an owner too. Your copy of a teammate's participant updates by itself about a minute after their
last change. On their participant you can make boards of your own, comment and suggest, but not change their
work.

Each of you keeps the project's files on your own computer. Only the updates between you go through the relay or a
folder you all share, sealed on your computer first. Never keep one project folder on a shared drive for two people to
open: whoever saves last overwrites the other's work. If it happens anyway, the project's page says when another
computer has the same project folder open.

To start, the lead presses Invite others on the project's page, beside Project settings, or opens Project settings
and presses Invite others to work on this project. Either makes them the lead and opens the invite, and asks for
your name only when Settings has none. Each person invited presses Join a shared project on Home and pastes the link or the
twelve words. Idiograph keeps the project in a new folder, `Documents/Idiograph` and the project's name unless you
type another, and makes it there, named as the lead named it. A link says whether the team sends through a shared
folder, and then you choose the folder. With the twelve words alone, tick The invite came through a shared folder when
the team sends that way. Your name is asked only when Settings has none. Another computer of your own joins the same
way, with no name asked, and you check its six digits against your first computer. Once the lead says the six digits
match, Open opens the project. In a project you already have, Join a project you were invited to in Project
settings does the same for that project. The joiner's project is not shared until the lead says the six digits match. A project that
holds a participant the lead's project does not have cannot join it, and nor can a project that has a team of its
own with someone else on it. A copy of the lead's project can join. A project whose team does not list this
computer says so under Working together, with Join beside it, which makes the project a copy of the team whose
invite you paste. If that invite is from another team than the one the project lists, Join asks first, since the
project leaves its team, and goes ahead only on OK. If you close the Join card before the lead says the six digits match, Working together offers
to finish joining or to stop. If you stop after the lead has said they match, the lead removes you from the list.
Stop working together asks first, then sends and takes in nothing more, and Start working together again picks the
team up as it was. A member who stops tells the lead, and the lead's People marks that person as having stopped, so the
lead knows to remove them. The lead keeps listing them until then.

Each invite you made that nobody has been let in by has a row under People, so closing the invite's card loses
nothing. When someone has answered, the row and the project's page say so, and the row's Check the six digits opens the
invite again at the digits and They match. Cancel the invite closes it, so nobody can join with it. For Add a computer
of mine the six digits are checked against your other computer, not read to someone on a call, and its last line names
the project. When the lead gives you a participant, your page says who gave it, and changes that come in from the others
are said there too.

The study's settings travel with the copy and keep in step: the project's name, research question, method,
timepoints, demographics, the participants' names and each participant's picture, label and pen portrait. Each
person's own settings stay their own and are never sent: your reflexivity statement, the interviewer's name, the
PET labels and timecodes of your exports and how your screens look. When you and the lead change the same setting
at once, the lead's change is kept. A picture is sent once, and again only when it changes. When the lead's settings first come in, a setting of yours the lead's project does not have, such as a pen portrait, is kept and sent to the lead, and the project's file as it was is kept in its _Archive folder.

The lead invites each person with a link or twelve words. An invite works once, and for seven days. When the
lead removes
someone, the project's key changes for everyone left, so the person removed gets nothing new. What they
already have stays on their computer. The team sends its updates through the relay or through a folder everyone
already shares, such as OneDrive or Dropbox. Either way, everything is sealed on your computer first.

### The relay

Anyone with Idiograph can work together through the relay at idiograph.app, and there is no code to type.
Turning Working together on puts nothing on the relay. The lead's first invite starts the project there, and
invites still decide who joins.

The relay keeps its limits small so that it stays free to run. Each project can send 100 MB a day through it, and
files such as recordings can take 80 MB of that, so the rest is always left for changes. One file can be at most
80 MB. A project can keep 250 MB on the relay waiting for the others to fetch it, and up to 100 MB of that can be
changes. A file is deleted from the relay
as soon as every computer on the project has fetched it, and anything left is deleted after 90 days (the bucket that holds the files deletes any file older than 91 days besides). A project
with only one computer on it keeps nothing large there, because nobody is there to fetch it.

When a limit is reached, the project's page says so in one line in place of "no connection", and Idiograph tries
again when the limit can have lifted. The day's limits lift at midnight UTC. A few are tried again after a minute,
and the rest after an hour. While recordings wait, the other changes still go.

If the relay no longer has the project, because it was deleted from the relay, the project's page says so and Idiograph asks again only once an hour. Your copy of the project is as it was.

Send the recordings too sends each recording once, and again only when it changes. A file over the limit never
goes through the relay. To share it, Send through a shared folder, which takes files up to 200 MB.

### Reviews, comments and suggestions

The owner of a participant can ask a teammate for a review. The teammate comments on passages, statements,
PETs and GETs, and can suggest a wording or a title. Nothing changes on the owner's computer until the owner
accepts a suggestion. History then says the teammate suggested it.

## AI and agents

### AI features

AI features are off on a new install. Turning them on in Settings first shows a warning, and you choose a
provider: Anthropic, Mistral, Google Gemini, OpenAI, Azure OpenAI, another service, or Ollama or LM Studio
running on your own computer, which need no key. Then there are three features, each with its own switch.
Suggested statements for a passage sends that passage, the interviewer's passage before it, the research
question, the statement guidance and six of your own statements as examples. Suggested titles for a PET and
Suggested titles for a GET send that one PET or GET with its statements and their quotes, the titles of the
other PETs or GETs on the board, and the research question. In a thematic analysis project, AI suggest on an
extract sends the passage, the interviewer's passage before it and your code list. It offers codes from the
list and new ones. Nothing an AI suggests is written until you pick it. With the switch off, no AI control
shows anywhere.

The prompt for statements is in Settings. You can read it, change it and reset it.

### Agents

An AI agent such as Claude Code, Codex or Claude Desktop can work on a project through Idiograph's command
line and MCP server. It works through the same code as the app and never edits the files itself. An agent
sends what it reads to its own provider. That is often a whole participant, so whether to use one is a matter
for your ethics approval. An agent can read a project only after you tick "Allow AI agents to read this
project" in Project settings. Project settings shows that tick, the guide and Add Idiograph to Claude Desktop
only while AI features are on in Settings. The demos are always open to agents. Write a guide for AI agents
puts a guide at the project's root for an agent opened there. Settings, under Using your own AI agents, gives
words to paste into an agent so it can find Idiograph.

### Adding Idiograph to Claude Desktop

In Project settings, Add Idiograph to Claude Desktop writes Idiograph's MCP server into Claude Desktop's
settings file, keeping every other entry and a copy of the file as it was. Restart Claude Desktop to use it.

### Reviewing and undoing an agent's run

An agent's change happens at once, as if you had made it, and you review it afterwards. Idiograph records
every change an agent makes, and before an agent's first change in a session it keeps a restore point of the
project's workbooks and boards. When agents have changed a project, its card on Home says so, with Review, and the cross after Review marks them as seen without opening them.
That opens Project history at By an agent, where each change has Undo and each session has Undo this run. An
undo never writes over a change you made since. Restore points are kept for 30 days, and the last ten
sessions' points are kept whatever their age.

### The agent log

Each time Idiograph refuses an agent, it notes what was asked and why in the agent log, in Settings. The log
keeps the last seven days. It does not keep what the agent sent, and it is not kept in any project.

## Undo, history and recovery

On Experiential statements, `Cmd + Z` (`Ctrl + Z` on Windows and Linux) takes back a quote, a removed
statement, a corrected passage or timecode, words given to another speaker, a trim and a find and replace. It
takes the newest back first. On each board, `Cmd + Z` has its own steps, separate from the statements
screen's. They last while that participant stays open.

Each board keeps a History of revisions. Idiograph saves one every fifteen minutes while you work, and you can
save one by hand with a name. Restore brings a revision back and saves the board as it stood first, so a
restore can be undone too.

Project history, on a project's menu, records changes to the project itself: its name, question, settings,
timepoints, renames, marks of complete, and every change an agent made, with who made each one.

The `_Archive` folders keep a copy of a file before every large change: a rename, a trim, words given to
another speaker, a new interview and a replaced picture. A deleted board leaves its History there. Idiograph
never deletes from them. To get a workbook back, copy it from `_Archive` while Idiograph is closed, and take
the bracketed note out of its name. The boards stay as they are, so check them afterwards. A deleted board
cannot be put back this way.

Remove from Idiograph, on a project's menu, takes the project off the list and leaves its folder as it is.
Tick Move its folder to the Bin too to move the folder there as well, where you can put it back. It is the
Recycle Bin on Windows and the Rubbish Bin on Linux.

## Keys and the canvas

Every shortcut is on the shortcuts card. Press `?`, or choose Keyboard Shortcuts in the Help menu.

On a board, the wheel or a pinch zooms. A sideways swipe, or the wheel with `Shift`, pans across, and the
wheel with `Alt` pans up and down. Hold `Space` and drag, or drag with the middle button, to pan. `H` turns
the pointer into a hand, so any drag pans, and `V` or `Esc` gives the pointer back. A drag on empty canvas
selects what it encloses.

On Linux, the Edit menu shows no keys beside Undo, Redo, Cut, Copy, Paste and Select All, but `Ctrl + Z`,
`Ctrl + Y`, `Ctrl + X`, `Ctrl + C`, `Ctrl + V` and `Ctrl + A` work as usual.

## When something goes wrong

Each entry starts with the words Idiograph shows.

### Idiograph stopped unexpectedly

What you saved is kept. Close the window and open Idiograph again. If it happens again, tell the author with
Send feedback.

### Idiograph could not start

What you saved is kept. Open Idiograph again. If it says other programs are listening on its ports, quit them
or restart the computer.

### This passage has changed since this page was loaded

Something else saved the passage while you were typing, such as another window or an AI agent. Nothing was
saved, and your words are still in the fields. Reload loads the passage as it is now and keeps your words
below to copy back. Overwrite saves your words over the change. A board shows the same line, "This board has
changed since this page was loaded", with the same choices.

### A quote can take in only the passage just before or just after

A quote can join the participant's passages only when nothing but the interviewer's words stands between them.
Take in the passages one after another, so that none of theirs is skipped. If you need words from further off,
make a second statement with its own quote. See [A quote across passages](#a-quote-across-passages).

### Changes made elsewhere

A board or a participant's PETs changed outside Idiograph, by an AI agent or another program. Press Update to
bring the changes in. On GETs, History keeps a revision of the board as it was before. A change you make in
another window of Idiograph comes in by itself.

### GETs were not marked complete. Waiting on

GETs complete needs every participant to come in from a board marked PETs complete, with nothing changed
since. The message names each participant with the reason. For "PETs not complete", open their PETs and mark
them complete. For "changed since it came in", open GETs and bring the change in. Then mark the GETs again.

### Comment or suggest instead

With Working together on, only a participant's owner can change their work. You can comment, suggest a wording
or a title, or make boards of your own on their participant. To work on it yourself, ask the lead to hand the
participant over in Who works on each.

### Waiting to send: no connection

Your changes are kept on your computer and go to the team when the connection is back. Nothing needs to be
done. If you use a shared folder, check that its drive or sync app is connected.

### This project has sent its 100 MB through the relay today

The relay takes 100 MB a day for each project. Your changes are kept on your computer and go after midnight UTC.
Nothing needs to be done. "This project has sent as many changes through the relay today as it takes in a day"
means the same for the number of changes.

### Recordings and large files are waiting to send

The relay takes 80 MB of a project's files a day, and a set number of files, and the whole relay takes only so many
files a day. When one of these is used, recordings and versions too large for a message wait until after midnight
UTC. Your other changes still go.

### The relay is holding as much of this project as it keeps

The relay keeps up to 250 MB of a project waiting until every computer on the project has fetched it, and up to
100 MB of that can be changes. When either is reached, nothing more is taken until the oldest is fetched. The line names the
computers that have not fetched it yet. Opening Idiograph on those computers lets them fetch it. If one of them will
not be used again, the lead can remove it in Working together, and the relay then lets the rest go. Idiograph tries
again in an hour.

### The relay is full just now

The relay as a whole has reached what it keeps. Your changes wait on your computer, and Idiograph tries again in
an hour. To send meanwhile, the lead can Send through a shared folder.

### The relay is turning away calls from this internet address just now

Too many calls came from your internet address in a few seconds, which can happen when many computers share one
address, as on a campus. Idiograph waits a minute and tries again. Nothing needs to be done.

### The relay has had too many calls from this internet address in the last minute

An invite or a join asks the relay a few times a minute, and the relay takes only so many such calls from one
internet address. Several invites open at once from computers that share an address can reach it. Wait a minute
and try again.

### The relay is not taking calls just now

The relay has stopped taking calls for a while. Your changes wait on your computer and go when it opens again.
Nothing needs to be done.

### Nobody else is on this project yet

A project with one computer on it keeps nothing large on the relay. Recordings and large changes go once someone
has joined.

### A file waiting on the relay could not be fetched by this computer

The relay gives one computer a file only so many times. When this computer has tried that often and failed, the
relay will not give it again, and the others' changes wait behind it. The lead can remove this computer in Working
together and invite it again.

### A file is too large for the relay

One file can be at most 80 MB on the relay, and at most 200 MB in a shared folder. The line names the participant.
The file is not sent, and the line goes once the file is smaller, gone, or no longer sent. To share a recording
larger than the relay takes, Send through a shared folder.

### The relay cannot start any more new projects today

The relay starts only so many new projects a day, and only a few from one internet address. Nothing changed. Try
again tomorrow, or Send through a shared folder, which needs no relay. "This project has made all the invites the
relay takes in a day" is the same for invites.

### The relay could not be reached just now

The first invite starts the project on the relay, and the relay could not be reached. Nothing changed. Check the
connection and invite again. When the line begins "The project is now on the relay", the project was started and
only the invite was not made, so the next Invite makes just the invite.

### Could not be read, so nothing was changed

Idiograph found a file it could not read, so it changed nothing and did not write over it. Most often the file
was cut short by a sync app or a full disk. The `_Archive` folder beside it may hold an earlier copy, and
your sync app or backup may hold a newer one.

### "open in Excel" on a participant

Excel has the participant's workbook open, so Idiograph will not write to it, and Experiential statements does
not open. Close the workbook in Excel, and it opens again. If Excel has closed and the mark stays, look in the
participant's folder for a hidden file starting `~$` that Excel left behind, and delete it.

### Its folder is not there

The project's folder has moved, been renamed or is on a drive that is not connected. Reconnect the drive, or
choose Remove from Idiograph on the card and then Open… on Home and A project folder on this computer at the folder's new place. Nothing in the
folder is lost. In Working together, a shared folder that is not there usually means its sync app is not
signed in. If it says files will not open yet, set the folder in OneDrive to Always keep on this device.

### Idiograph could not confirm the update is genuine

The update did not match the author's signature, so Idiograph did not install it. The version you have goes on
working. Try again later, or download the newest version from GitHub. If an update fails for another reason,
the line under Updates in Settings says why.

### A demo's recordings will not play

A demo's recordings are not in the app. The first time you play one, the player offers to download them, so
they need the internet once. Without it, the demo works with no sound, and Download tries again.

### Sending feedback

Send feedback sends a note to Idiograph's author. Say what you did and
what happened. Leave an email address if you want a reply.

