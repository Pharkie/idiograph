# Sift manual

Sift is an app of its own since 20 October 2026, on Idiograph's code, with its own window, icon and
installer. Its Home holds your Sift projects under Projects, and ends with Idiograph and Trace. Its
settings are its own, Appearance and the AI features among them, once its first start has copied what
it shares from Idiograph's. How to install it is in the [README](../README.md), and how it works
underneath in [docs/internals.md](internals.md).

Sift is screening for a systematic review, one record at a time, in rounds: the records clearly in,
those clearly out and the borderline cases. It reads and writes the review's own CSV, keeps a log of
every decision beside it, and works whole by hand. AI proposals are an experiment, off until he
turns them on.

**A review.** A review is one thing, its searches and then its screening, in one folder, and on
screen a Sift project (9 October). Home's Projects section
holds a card for each Sift project, newest first, with its research question under its name, as a
Idiograph card has its own, and where it stands: its plan, "Plan version 3, registered", No search plan yet
before it has one, and under it the run its Screening step
opens, by its name, and how many of that run's records are decided, or the full text once it is
under way, never a newer run that brought nothing. New project, under
the cards, takes a folder through the Mac's folder dialog, or off a Mac its typed path, then the
project's name and its research question, and Create project makes the review there, a blank plan
ready for its searches, and opens it on Search strategy, as Idiograph's New project opens the project
it makes. A line the card says goes as soon as you change what it was about. A folder that holds anything gets a new folder inside it, named for the
review, and one that holds a review or a screening already is refused. Open project folder takes a
review that stands: a folder holding `search_plan.json`, or `screening.csv` alone for a screening
with no searches, and a run's folder opens its review. A folder that holds one review's folder
directly inside it opens that review, and one that holds several offers each by its folder's name.
Opening writes nothing into the folder, so a
review someone else keeps is never changed by it, and a name you give it stays in the app's list.

**A project's menu (6 November).** Each project's card on Home has a "…" at its top right, and on a project's
screens its name in the band under the title bar opens the same menu: Show in Finder (Show in Explorer on
Windows, in Sift's own window alone), Project settings, which opens Settings on Projects with this project in
front, and Remove from Sift…, which asks first and, from inside the project, leaves the screen and ends on Home.
A project whose folder has gone has Remove alone. Sift keeps no History of a project and makes no shared copy,
so neither is there. The name is no way back to the table from a record, which Esc and the browser's Back still are.

**Its steps.** The review's steps stand at the head of both its screens in PRISMA 2020's order,
Search strategy and then Screening. Screening opens the run you opened last, kept in the app's own
list of projects and never in the project's folder, until you open another from the runs on Search
strategy with Make active, so a new run never takes it over by itself. A project you have never opened a run of
opens its newest run with a screening. A run that brought no records makes no screening, so
Screening keeps opening the one before. A review with no searches has Screening alone. A row opens
its review on the step it was left on, which this browser keeps, else on Search strategy until a run
has a screening and on Screening after, and Sift's mark at the bar's left goes Home from Search strategy,
the table or a record. A screening opens on its table, at the stage, the row and the sort it was left on, and at
title and abstract while no record has passed it.

**The two stages.** You screen every record by title and abstract, stage 1, then by full text,
stage 2, as PRISMA 2020 and a review's protocol have it: the records you mark Yes or Maybe at stage 1
come to stage 2. The title bar shows them with Search strategy as the review's steps, one
row in the order the work goes, Search strategy › Screen by title and abstract › Screen by full text,
each stage named with its verb, since what you do there is screen, each stage with its count of
records and the one you are on marked, the words Screening stage gone (12 October). Each step opens
its screen and stage, from Search strategy as from the screening. Screen by full text stays greyed,
saying why on hover, until a record has Yes or Maybe at title and abstract, and Screen by
title and abstract the same until a run brings in records. Should no record stand at full text while you are on
it, after an undo, stage 2 says so in one line in place of the table.

**The screen.** The title bar holds Sift's mark, which goes Home from every screen, then the review's steps, Search strategy,
Screen by title and abstract and Screen by full text, each stage with its count of records, then Export, Second screener
when there is one, the PDF on a record, Search, Shortcuts, Send feedback, and Settings last, which opens
Settings on Projects, Send feedback in Appearance's place since 16 October, when Appearance went into
Settings, General. Under it the band holds the review's name with a chevron, opening the project's menu (see A
project's menu), then the rule and the research question. Each tool carries its
word beside its icon where the bar has the room and its icon alone, named on hover, where it runs short (see One title
bar). Export opens one menu for what leaves the screening: Export to Zotero, Export included records
and Export PRISMA counts (12 October). The arrows move in it, Enter takes one, and Esc or a press
beside it shuts it. A line under the title bar holds, on the table, Filters at its left, over the
sidebar it opens, and Set columns and PRISMA flow at its right, and on a record PRISMA flow alone in
the same place (12 October). In the table the headings sort, and the filters stand in a sidebar at
the table's left. A bar at the foot says how many records show, "108 of 108", or on a record where
it stands, "12 of 108", Undo once there is a decision, a note or a key excerpt to take back, which takes
back the newest as U does, the record and stage it takes back named on hover, and each decision's count as a
pill. At full text a record's head says where it stood at title and abstract, "At title and abstract"
and its pill, Yes or Maybe. A record shows its number, "Record 12",
where it stands as a pill, its id, year and journal, the title, the authors, the DOI and its web
address as links that open a new tab, its PDF or Add PDF, its count of citations, Cited by 12, and
under the word Database the databases that found it, then the
abstract in large type. Then the three decisions in the stage's words, each with its key in the word's own colour, the one taken filled,
the note, your key excerpts and your own fields. Until 17 October the keys stood faded, under 4.5 to 1, as Enter did on
Accept suggestion, and since then Maybe's wash under the pointer is lighter than the others', so its amber word reads. Any other column of the CSV that holds something stands at the foot,
a web address as a link. On the right the record's PDF, `pdfs/<rec_id>.pdf` beside the CSV, served
from there alone, or "No PDF.", in a pane that folds away. Add PDF stands once, in the record's links,
where the empty pane held a second until 17 October, later. Light and dark follow the
system, with the same toggle as the rest of the app. Under 760 pixels the PDF goes under the record,
the flow stands over the screen from the right when it is open, Export and the shortcuts are put
away, the steps take a row of their own under the mark and the tools, wrapping rather than
scrolling the page, with no chevron left alone at a line's end or start, where until 17 October, later,
one stood at the end of the first line at 360 pixels, and the title bar scrolls in itself when it is still too wide. Under 480 pixels
Set columns and PRISMA flow show their icons alone, named on hover, and the foot bar's pills wrap
under the count, each with its word. The project's name at the left of the band is a button with a small chevron, and
opens the project's menu. On a record a small link stands before it, "Records" with a left chevron, and takes you back to the
table, as Esc and the browser's Back do. The mark goes Home from the table, Search strategy and a record.

**The decisions' words.** Title and abstract is a filter and full text is the decision, as PRISMA
2020 and Cochrane have it, and the words say so (12 October). At title and abstract the choices are
Yes, Maybe and No: Yes and Maybe both take the record on to full text, Maybe marking it unsure, and No
goes no further. At full text they are Include, Maybe and Exclude: Include puts the record in the
review, Exclude leaves it out with a reason, and Maybe keeps it there, neither included nor excluded,
marked unsure. Each button says what it does on hover. A record not yet decided at a stage reads To
screen. The same words stand on the buttons, the pills, the filters, the foot bar's counts, a
proposal, the second screener's workbooks and the command line. Only the words changed: the CSV, the
log and every other file keep the values they always held.

**Decisions as pills.** A decision shows as a pill in the table's Decision column, at a record's
head and in the foot bar: Yes or Include green, Maybe amber, No or Exclude red with its reason's code
a pill of its own after it, its meaning on hover, and To screen grey, the word always beside the
colour.

**Record IDs.** Each record goes by its ID, R10 or R010, the rec_id the screening's CSV gives it
(13 October). The ID is the table's first column always, and a press on its heading sorts the IDs in
natural order, R2 before R10, and again the other way. A record's head names it, Record R10, and the
reasons' heading, Undo's hover and the bench in Settings name a record by its ID too. The plain
number from 1 that stood first until 13 October is gone from the screen, though `sift.json` still
keeps it. Search, `Cmd + F`, finds a record by its ID (see Search).

**The PRISMA flow.** A sidebar at the right of the table and of a record alike, opened and closed by
PRISMA flow at the right of the line under the title bar or the close at its head, and this browser
keeps it as you left it, open the first time. Drag its left edge wider or narrower, or move it with
the arrow keys, and the diagram grows or shrinks with it, the screening keeping the width in
`sift.json` beside the filters' (12 October). It holds PRISMA 2020's flow for a new review (Page et al. 2021), redrawn after every
decision and undo, and it counts the active run alone (16 October), the run Screening has open, since
PRISMA reports the review's own search and not the trial runs before it: the records identified from
each database, as that run's own lines of `log.csv` saved them, the duplicates removed, their sum
less the run's records from databases, and the records from other methods, those whose sources name
citation chasing, a website or the like. Then screening, the records screened, every record after
the duplicates are removed, as PRISMA counts them, the run's own, with those still to screen, To screen,
and those at maybe said inside the box, those excluded by reason, retrieval, the reports sought and
those with no `pdfs/<rec_id>.pdf` yet, eligibility, the reports assessed, excluded by reason and
still to screen, and the studies included. The other runs stay in Sift as they are and out of the
flow. A run that keeps the decisions from an earlier one counts its own searches alone, and a record
only the earlier run found, carried and not found again, stays in Screening with its decisions and
out of every box. A screening of no run whose `log.csv` holds more than one search has no active run,
and its first box says "No active run to count" in place of a sum. A stage under way is edged in
the ink at twice the line, in the crux orange until 17 October, later, and until 18 October in the same
grey edge as every other stage, since the drawing's own colours overrode the ink, and one not yet reached is dashed, its words as dark as every stage's, where until 17
October, later, they were faded to half and hard to read. The same flow is written beside the CSV as
`prisma.md`, a heading and one Mermaid block, after every act that moves it, for Claude or any
other tool to read, and `sift <folder> prisma` prints it. Mermaid ships with the app, so
the flow draws with no connection.

**Suggestions.** The record shows each suggestion the CSV holds under the abstract, edged in its
colour, green for Yes or Include, amber for Maybe and red for No or Exclude, under a title that says
what made it and where it came from (14 October): "AI suggestion, from the CSV", with the sparkles,
for one the screening file says a model made, its tooltip naming the model and version, "AI
suggestion, from Sift", with the sparkles, for one Sift's own AI made, its tooltip naming the model,
"Suggestion by keyword rules, from the CSV" for one keyword rules made, and "Suggestion, from the
CSV" for one the file says nothing of. Under the title come its decision, its reason code and the
code's meaning, its grounds marked in the abstract where the abstract holds them word for word,
whitespace and case set aside, and under it when it does not. A No's or an Exclude's code stands as its red
pill with its meaning beside it, and any other reason, the screening file's own words on a Maybe among them,
as a plain sentence that wraps, where until 17 October, later, it stood as a red pill that ran out of its box
at a phone's width. The sentence ends with a full stop where its words end with none, a question mark or
an ellipsis of their own kept as it is (17 October, later). Participant is set aside since the same day, so grounds of "ten plot holders described" are
found where the abstract opens "Ten plot holders described", and a reason the file gives a Yes or a Maybe is
no longer offered among the reasons for No. A short line over the abstract names what is
marked, "Why it was proposed" for a suggestion from the screening file, "Why Sift's AI proposed it"
for Sift's own or "Why both proposed it", and its Hide takes the marks away, Show brings them back,
and this browser keeps the choice.

Accept suggestion, at the foot of each box and in the suggested decision's colour, does exactly what
pressing that decision and choosing its reason does: the same decision and reason, the note as it
stands, the step on to the next record and Undo. A No with no reason takes No reason at title and
abstract, and at full text the reasons open, as Exclude's press opens them. Enter is Accept
suggestion on the first box. A suggestion whose decision Sift does not know at the stage has no Accept
suggestion. It is your decision, made as any other, and the log never says which control made it.
Instead every decision says in the log whether it matched the suggestion shown, its decision and
reason the same, and what made that suggestion, so `sift <folder> show` says, for one,
"The screener's decision matched the suggestion (keyword rules, from the CSV)" or "did not match the
AI suggestion (Opus 5.5, from the CSV)". The counts, the export and the PRISMA flow count it as any
decision of yours.

**Key excerpts.** Words of the title or abstract that support your decision, where an abstract
mentions recreational use say, kept as quotes are on Experiential statements (14 October). Select
the words and press H: they become one key excerpt. To glue separate bits into one, hold Cmd, Ctrl off a
Mac, while you select each bit after the first, and each stays marked in the text until H. H joins them
in the text's own order with an ellipsis, the title's before the abstract's, never rearranged, so the
bits can be picked in any order. A plain selection starts afresh, a plain click on the text or Esc lets
the marked bits go, and H with nothing selected in the title or abstract only says so. H does nothing
while you type in the note or a field. Make as many as you like: they stand under the note as Key
excerpts, H beside the label in the soft ink at the weight of the decisions' keys, where the faint ink
read at 2.8 to 1 (17 October, later), each in quotation marks in the order made with Remove, and one made
at the other stage says which. Their words stay marked in the title and abstract in a blue of their own, beside
the grounds' wash, the line over the abstract naming Key excerpts, and its Hide hides both. Cmd + Z, U or
Undo at the foot takes back the newest key excerpt made or removed as it takes back a decision, and an
undone one leaves its words marked, so H keeps it again. Each is kept with the stage it was made at and
where its bits stand, so its marks come back whenever the record opens, in a column of Sift's own,
`excerpts`, in `screening.csv`. Export included records adds them as text, and `sift <folder>
show` lists them. Key excerpts are no AI feature, so they work with the AI switch off.

An AI suggestion shows only with the AI switch in Settings on, and a suggestion by keyword rules or
one the file says nothing of shows either way. Once a decision meets a proposal, with the switch on,
the bar counts the decisions that matched the proposal and those overruled, and Decision in the
filters gains Differs from the proposal. With the switch off there is no AI suggestion, no AI control
and no AI setting anywhere in Sift, and screening is whole by hand. The log records the proposal and
its source either way.

**A project in Settings.** In Sift's Projects category in Settings, after Databases, the row of the Sift projects'
names when there are several, the one open first, and for the one chosen its Project part: its name and its
research question, saved with Save at the foot,
kept in the app's own list and never in the project's folder, the folder it is in, and Remove from
Sift, which asks first and takes the project off Home, its folder and every file in
it left as they are. Project settings in a project's menu opens this category with the project in front. Its Second screener part follows (see A second screener). A project with no
screening yet has its Project part and its Second screener part alone, and the parts after them wait
for a run.

**AI proposals.** In Sift's Projects category in Settings, which the cog in Sift's title bar opens, with the AI switch
on, a Sift project's AI proposals stand after its PDFs, for the project chosen in the row of names,
the screening open first. They hold the screening's own switch, AI proposals for this screening, off at first, and the
prompt they go out with, plain
and by the book: judge one record's title and abstract against the stage's reason codes from
`reasons.csv`, answer include, maybe or exclude, a code on an exclude, and a stretch of the title
or abstract word for word as grounds. At full text it sends the abstract too, since the app reads
no PDF's text. `{stage}` and `{codes}` stand for the stage and its codes, and Reset to default
puts the prompt back. With both switches on, AI propose asks for this record, and AI propose for the
rows shown asks for every record still to screen the table shows with no proposal from Sift yet, saying first
how many calls it will make to which model. It says Proposing and how far it has gone, and pressed
again it finishes the call under way and leaves the rest for later, as Find open-access PDFs does.
The calls go through the
provider and model chosen in Settings, General, your key or a local model, which the line under the
prompt names, and Save at the foot of Settings keeps the switch and the prompt in `sift.json` beside
the CSV, only when they have changed. Each control carries the
sparkles. An AI never decides a record: its proposal lands in columns of Sift's own and waits for
yours. Under the prompt, the bench tries it before you turn proposals on or save a change: pick a
record of the stage, and the line under it says what Try will send, one record's title and abstract
in one call, and to which model. Try, with the sparkles, sends the prompt as the box holds it, saved
or not, and shows what came back, the decision as a pill, the reason and the grounds, saying when
the record does not hold them word for word. Nothing is written anywhere.

**A record's PDF.** A PDF dropped anywhere on a record, or chosen with Add PDF in the record's links,
is kept as `pdfs/<rec_id>.pdf` for that record and shown at once, and its
PDF link in the record's head opens it in a new tab. When the record has one already, Sift asks
before it replaces it.

**Find open-access PDFs.** In Sift's Projects category in Settings, for the Sift project chosen there, whatever the AI
switch, since it calls no model. Give your email once, which Unpaywall asks for, and the app keeps it in `config.json` as `sift_email`.
For each record that passed title and abstract, with Yes or Maybe there, the reports PRISMA
seeks for retrieval, with no PDF yet, it looks
the record up by its DOI in Unpaywall and OpenAlex, or with no DOI, as PsycInfo's records come, in
OpenAlex by its exact title and year, and tries the open copies they list. It keeps a PDF only when
the answer is a PDF and its first page carries the record's title, so a library's form or a sign-in
page in a paper's place is refused, and it never writes over a PDF already there. The button counts
as it goes, a second press leaves the rest for later, and the end says the count, "Found 41 of 108,
the rest by hand". Each record's DOI, title and year go to Unpaywall and OpenAlex, and nothing else.

**Fill from OpenAlex.** Beside Find open-access PDFs, for the Sift project chosen there, whatever the AI
switch, since it calls no model (13 October, in place of the citation counts' button of 12 October). A
run fills Cited by and the four columns below from OpenAlex and Crossref by each record's DOI as it is
made, in the same request to OpenAlex as the abstracts and authors, and this fills them for a screening
whose run came before that, fifty DOIs at a time, asking only for what a record still lacks, Cited by
among it. What they say lands in Sift's own columns and nowhere in the review's, but for a record's
keywords, which it fills where a record has none and never writes over (14 October). The button counts as
it goes, a second press leaves the rest for later, and the end says how many it filled, "Filled 98 of
103 records". Each record's DOI goes to OpenAlex and Crossref, with your email for Crossref's polite
pool once Sift's settings keep it, and nothing else. A record with no DOI is never asked and reads
Unknown.

**Retracted, open access, country and key works.** Four columns, hidden at first and shown by Set
columns, each read on the record under its fields and each a group of the filters (13 October).
Retracted or corrected says Retracted, Expression of concern or Corrected, more than one where several
apply, from OpenAlex's mark of a retraction and Crossref's notices, and None once asked with none
found. The record gives each notice's date and its DOI as a link, and a retracted, questioned or
corrected paper says so in a quiet word beside its title, in the table and on the record, so it is
never missed. Open access says Open or Closed, and the record says where a paper is open, in an
open-access journal, in a subscription journal, free to read on the publisher's site, or in a
repository. Country names the countries of the authors' institutions in plain English, each once,
filtered as Journal is. Cites key works names which of the review's key works a record cites (see Key
works under Search strategy), each a tick of its group, and None for a record that cites none. A
record never asked reads Unknown in each, except Cites key works, which reads Can't check wherever
Sift cannot tell, and the record says why: "Crossref holds no reference list for this record, so Sift
cannot check."

**Studies and their reports.** PRISMA 2020 counts the studies included apart from the reports of them,
since one study can have several reports, a thesis and the paper from it, a protocol and its results.
On a record, under its fields, Study shows the study you linked it to and its other reports, with
Unlink, which takes the record out, and the last report left in a study with it. Under it Sift suggests
records that may be reports of the same study, and never links one by itself: each says what they
share, "Shares 3 of 4 authors with R014 (Ida Gannet, Ned Tern and Ann Park)", then what strengthens it,
the same No. of participants, distinctive words both titles carry and years within four of each other,
the strongest first, with Same study, which links the two. Authors are compared as sets, in any order,
by OpenAlex's author ID where both records have one, else by surname and first initial, accents and
case set aside, and a suggestion needs two shared authors, or one who makes up at least half the
shorter list, as a thesis and the paper from it share their one author. Same study with a record's ID
typed beside it links a record Sift did not suggest. A link joins the study either record is in, and
two studies linked become one. The Study column, hidden at first, sorts the reports of a study together
and filters by each study, Not linked for the rest. The PRISMA flow's last box says Studies included in
review and Reports of included studies, the reports you linked counted once among the studies, and
Export PRISMA counts says both. Each link and unlink is a line of the log, as a decision is, and Start
again clears them.

**Export to Zotero.** Export to Zotero, in Export's menu, Sync to Zotero until 12 October and the same
in all but its name, puts the screening's records in your Zotero
library with their PDFs, through Zotero's own Web API on your key (see Settings, Zotero), whatever
the AI switch, since it calls no model. Its card offers the records that go, each with its count:
Included at full text, the default, The rows the table shows, as the stage and the filters have them
now, or Every record. Then one line says what Export would do before you press it, "Into the collection
Heron counts: adds 12 items, updates 3 and leaves 40, and uploads 9 PDFs.", and Export says how far it
has gone and at the end what it did. A refusal, "Zotero did not take that key.", an error or an end
that left items out stands in the amber, as every failure line does, where it stood in the soft ink
(17 October, later). A choice with no records, or nothing to add, update or upload,
leaves Export off. The collection is named for the Sift project and made at the top
of the library when it is not there. Each record becomes an item of its type, a journal article unless
its type says thesis, preprint, book chapter, book, conference paper, report or web page, with its
title, authors, year, journal, DOI, web address and abstract, `Sift:` and its rec_id in Extra, and its
decisions as tags, `sift:include-ta` or `sift:exclude-ft` for each stage decided, and
`sift:reason-E5` for the reason of a No or an Exclude, the tags keeping the values the CSV holds. Its PDF, `pdfs/<rec_id>.pdf`, goes up as the item's
attachment when the item has none. Export again changes what changed and adds what is new: an item is
found by the key Sift keeps for it in the CSV's `zotero_key`, or in the collection by its DOI, or its
title and year, so nothing is ever made twice. An item gains what it lacks, an empty field, the
collection, the line in Extra and a PDF, and its `sift:` tags follow the record, every other tag kept.
A field you have filled in Zotero is never written over. The authors are read however the database
wrote them, "Heron M.", "Birch JJ, Elm AR." or "Pine, Jo", each with a last name and a first
name or initials, and authors that a sync before 12 October 2026 split wrongly, a surname taken as a
first name, are put right when nobody has changed them since. A record that is not chosen now keeps its
item and loses its `sift:` tags. Sift never deletes an item, an attachment or a collection. Each
record's fields and PDF go to Zotero, and nothing else. `sift zotero sync <folder>
--dry-run` says the same on the command line.

**Deciding.** A decision moves on to the next record shown. No or N at title and abstract, Exclude
or E at full text, opens the stage's reasons in a short list over the record or the table, one under
another and numbered, the proposal's chosen when the proposal was No or Exclude, and a number or a
press takes one, one reason a record. At title and abstract a reason is optional, so No reason stands first, numbered 0, and at
full text one is required, as PRISMA 2020's flow diagram gives reasons only for the reports excluded
at full text (12 October, later). Every reason of the project's one list is offered at both stages. Maybe says on hover what it does: at title and abstract the record goes on to full text
marked unsure, and at full text it stays there, neither included nor excluded, marked unsure (12 October). Esc or a press beside the list cancels. A record whose log holds two reasons from an older
line keeps the first. The note goes with the decision, its box named Note on this decision so it is
never taken for Notes, your own field, and a note typed after it is kept when the field is left, and
shown as you left it. Undo, U or the button at the foot, puts back the newest decision, note or key
excerpt, then the one before it, each by a line of its own in the log. Nothing waits to be saved.

**The table.** Sift opens on the table of the stage's records. A click or Enter on a row opens that
record (12 October), and the record's way back, Esc or the browser's Back returns to the table on the
same row, its filters and sort as they were. A press on a star, a guess, a link or a cell of yours
does its own work and opens nothing, words selected by a drag across a row stay selected for copying,
and the second press of a double-click, selecting no word of it, does nothing on the record the first
one opened. A row is a record, every row drawn whole as
plain text, and Search, `Cmd + F`, finds a record by its ID, title, authors, journal or abstract (see Search). The columns at first are the
record's ID, Database, Found by until 12 October, a pill in its colour for each database that
found the record, the pills alone, a record found by citation searching later saying Citation search
there, Title, Authors, Year, No year where it has none, Cited by, how many works cite it in OpenAlex,
its day on hover, No count where OpenAlex gave none, No. of participants, Unknown where nobody has
given it and nought only when you give nought, PDF, a red pill when the record has one and blank when
it has none, Decision, at the stage, as a pill with the reason for No or Exclude a pill after it, and My rating,
your own, never the journal's. Abstract, its first hundred words and the whole on hover, and DOI, a
link, are hidden at first, each read on the record, and Set columns shows either. The review's other columns go by plain names, pub_type as
Publication type, each type a pill in plain words, Journal article for PubMed's Journal Article and
Europe PMC's research-article alike, Dissertation or thesis, Review, Book chapter, Book, Conference
paper, Preprint, Report and the like, the CSV's pub_type left as the databases wrote it,
abstract_from as Abstract source, its database a pill, url as Link. At full text a column of its own
after Decision, At title and abstract, says where each record stood at the first stage, Yes or
Maybe, and sorts as Decision does. Set columns does not offer it, since it is there at full text alone. The foot bar says
how many rows show of the stage's records. A press on a heading sorts by it, a second press the
other way and a third not at all, and with Shift it adds the next key, its arrow in the ink. A heading dragged left or
right moves its column, a bar in the ink marking where it will go, the arrow and the bar in the crux
orange until 17 October, later, and the new order is kept as
Set columns keeps it, so the card shows it next time. Reset to default on the card puts every column back where it first stood, shown or hidden as at first, with your own columns shown at the end. A drag starts once the pointer has moved a few
pixels, so a press that stays put still sorts. The ID stays first, and At title and
abstract stays after Decision. No column resizes by hand, by design: each takes its width from what
it holds and from the window, and the table scrolls sideways when the window is narrow. The
filters stand in a sidebar at the table's left. The rows are set when the stage, a sort or a
filter is chosen, so a decision never moves them. The up and down arrows move the chosen row. The
stage's keys, Y, M and N or I, M and E, with the reasons, decide the chosen row as they do on a record,
and U undoes. A record opened from the table walks
the table's rows in its order with the left and right arrows. The table scrolls in its own box,
sideways on a narrow screen.

**Back and Forward.** The browser's Back and Forward, and a mouse's back and forward buttons, work
between the table and a record (12 October). Back on a record returns to the table where you left
it, its scroll, filters and sort as they were, and Forward goes back into the record you left, the
one you last walked to with the arrows. A note or a field you were typing is kept on the way, as it
is whenever you leave it. The other screens keep no history of their own, so Back on the table goes
where it went before.

**Filters.** Filters, the funnel at the top left of the table, over the sidebar it opens (12
October), opens and closes a sidebar at the table's left, open at first on a wide screen and shut
under 900 pixels, and this browser keeps it as you left it. At phone width it stands over the table
under the strip, and Esc shuts it. While filters are on, the funnel says how many in its word and its
name, Filters (2), a group with anything set counting one, the funnel in the ink with its word, where it
stood in the crux orange until 17 October, later, and Clear all stands beside it. Drag the
sidebar's right edge wider or narrower, or move it with the arrow keys, and the screening keeps the
width in `sift.json`. A long name, a journal's or a publisher's, wraps onto a second line under itself,
the box and the count beside its first, so it reads whole and is never cut, and reads whole on hover
too (17 October, later, where "Journal of Invented Garde…" stood cut at 1280). It
holds a group for each
column you can pick from, shown or hidden, in the columns' order: Database, each database once with
a dot of its colour however many records or lists of them name it, then More than one, and New in
this run after a later run, Year, Cited by, No. of participants, the count or the guess, Full text PDF, with
PDF and No PDF, Decision at the stage, To screen, then Yes, Maybe and No or Include, Maybe and
Exclude, each with a dot in the colour of its pills in the table and the foot bar, To screen grey, so
a colour means one thing everywhere (12 October), with each reason under No or Exclude,
then Differs from the proposal while proposals show and Where we differ while a second screener's
side holds a difference, the one filter of where a record stands, My rating,
the Journal and Publication type always, whatever they hold, any other column of the CSV
when it holds 2 to 30 values, Abstract source among them with an ⓘ that says what it is on hover,
each value once whatever its case or spacing, in the words most records write it, and each choice
column of yours. Year, Cited by, No. of participants and My rating are each a slider with two
handles, the lower and the upper, over the whole numbers the stage's records carry, the rating from
1 to 5 stars, so 10 and under, 11 and over or 4 or 5 stars is two moves. The two numbers stand in
boxes you can type in, with the count of rows between them at the right, a nought in the same faint ink as any
count since 17 October, and a small bar chart over
the slider shows where the rows stand: a bar for each five years, from a year that ends in 0 or 5,
2015 to 2019 and 2020 to 2024, a bar for each five participants up to 50, 1 to 5, 6 to 10 and on,
then wider bars, 51 to 100, 101 to 200, 201 to 500, 501 to 1000 and 1001 and over, and a bar for each
star, and Cited by a bar for nought, then 1 to 5, 6 to 10, 11 to 25 and wider bars to 1001 and over. A bar whose
whole run is in range shows in the soft ink, as does the stretch of the track between the handles, the
handles ringed in the ink as every tick is, where all three stood in the crux orange until 17 October, later. With the pointer anywhere in a bar's
column, its empty part too, a tip over the chart says at once its run and its count of records,
"2020 to 2024: 12 records" or "3 stars: 1 record" (12 October). The year's and the participants' handles move a whole bar at a time, dragged or with
the arrow keys, and each bar stands over its own stretch of the track, so past 50 the track is laid
out by bar and not by number. The boxes still take any whole number, 11 and over among them, and a
number typed between two bars' edges stands its handle at its place inside its bar. The rating's
handles go a star at a time. At its full range a slider
filters nothing. Under each slider a tick of its own takes the records with no number, in plain
words so none is taken for nought: No year, No count, Unknown under No. of participants, and Not rated
under My rating. Every other choice is a tick box with its count at the right, how many
rows of the stage would show were it ticked, the other groups' filters as they stand, so every count
and chart moves as you filter. A count of nought shows faint and stays, there to read but not to tick, and a ticked choice always
shows and can be unticked, in the ink as any other ticked choice even at nought since 17 October, later, where
it stood faint though its box still worked. Every group of names lists its choices by their counts, the most first and the noughts last, a
tie in the order the group gives it, so Show more shows the top of the list first, while a scale keeps
its own order: the sliders, the decision's four with its reasons by count under them, the form's Done
and To do, and your own columns' choices as you set them (13 October, later). The group you tick in
keeps its order while you are in it, so no choice moves under the pointer, and the others take their
new order as their counts change. Ticks in one group widen, any of them, and groups narrow each other, all of them. Clear beside
a group's name clears it, and Clear all at the head clears every one. A group of more than four
shows its first four with Show more, and Show less puts them back. One of more than ten has a find
box at its head that narrows its choices as you type, for a search with many journals. Words in
the title and the abstract are found with Search, `Cmd + F` (see Search). The foot bar's count says how many rows show. The
screening keeps its filters, the ticks, the sliders and the words in the find boxes, in `sift.json`,
so they stand as you left them when you come back to it or reload the page, and a tick for a choice
no record carries any more is let go. Clear all clears what is kept too.

**Country on a map.** Show on map, beside Country in the filters while a record has a country, opens
the map alone over the screen (13 October, later): every country's outline, and a circle for each
country Country counts, its area following the count, its number inside it, a count of 1 too, and the
country's name beside it. Circles that would overlap are nudged apart, the larger staying nearest its
country, and a thin line runs from a moved circle back to a small dot on its country. A name with no
room beside its circle stands a little further out, tied to it by a short line. The same counts
always give the same map. The counts are the ones Country shows at that moment, the other filters
applied. Rest the pointer on a circle, or reach it with Tab, to read its country and count. The line
under the map says how many records have no country, and names any country the map has no place for,
with its count. With no record left by the other filters it says "No records to map.", where it said every
one of 0 records had a country (17 October, later). The note under it names the projection and where the borders come from, and stays in
the app, out of a saved file. The map has no zoom, since there is nothing more to show. Its close, Esc
or a click outside it shuts it. Save as PNG and Save as SVG save it as it stands for a paper, names
and lines included, always in the light appearance on white, named after the run, the PNG about 3000
pixels wide and the SVG's words kept as text. It is drawn on the Equal Earth projection, which keeps
every area true, so a circle's size means the same anywhere, from Natural Earth's public domain
outlines that ship with the app, so nothing is fetched.

**Pills.** Each database is a pill in a colour of its own wherever Sift names it, on the table, the
record, the abstract's source and New run on Search strategy: Scopus orange, PsycInfo blue, Web of
Science violet, PubMed teal, Europe PMC green, OpenAlex pink, citation chasing grey, and any other one
of six more colours by its name, never red, so none is taken for the PDF, and Citation search grey
as citation chasing is. A publication type is a
pill, one for each type a record carries, a reason a pill of its own after No or Exclude with its
meaning on hover, and a proposal's decision and reason are pills too. Nothing in the CSV changes.

**Your own fields.** No. of participants, My rating, Notes, Digest and Critique stand under the note on the
record screen and as columns of the table, with any column you add. No. of participants starts as a guess
from the abstract, "n = 12", "eight adults" and the like, shown with a question mark until you
confirm it with one press, on Confirm or on the guess in the table, or type your own, nought among
them. A count nobody has given reads Unknown, never nought. A guess is never written. My rating is one
to five stars, Not rated with none, and a press on the star it stands at clears it. The stars up to the rating
are filled in the amber and those past it are an outline in the faint ink, where until 17 October, later, they
were filled in a pale line colour that read at under 2 to 1. Notes,
Digest and Critique are boxes on the record screen, and in the table No. of participants, Notes and
a column of yours open for typing with a press on the cell, and the next press on the table ends the
typing and opens nothing (12 October). Each is kept when you leave it.

**Set columns.** Set columns, Columns until 12 October, on the line over the table at its right beside PRISMA flow, shows or hides each column and moves it up or down by the handle at
the left of its row, the same handle as Home's rows: drag it, or press Alt and an arrow
on it to move the row one place. A press anywhere on a row shows or hides its column, its name as
well as its box, and on a row of your own column anywhere but its name box, Remove or its handle (13
October). Each box is in the ink, as Settings' are, where until 17 October it stood in the browser's own blue. The screening keeps the order in `sift.json`. Abstract, DOI, Notes, Digest, Critique, Journal and the CSV's other
columns are hidden at first, and a screening that holds your columns keeps them as you set them, but
for the abstract and the DOI, which a screening whose columns were placed before 12 October hides
once. The ID is in no row, since it stands first always. Add a column takes a name and a type, Text,
Choice list with its choices one a line, or Number, a whole number such as how many analysts did a
study's analysis (13 October). A Number column sorts as numbers, filters in the sidebar by a slider
with the bars No. of participants has, Unknown for a record with none, and opens for typing in the
table and on the record as No. of participants does. A column of yours is renamed or its choices
changed in the same card, and Remove asks first and keeps every value it held in the log. The card
keeps each change as you make it, so Done at its foot right closes it, as the X at its top right
does.

**Extract and appraise.** The step after Screen by full text, Extract and appraise, is where each paper
included at full text has its data extracted and its quality appraised on a form you set up for the
project, as PRISMA 2020's items 9 to 11 ask (13 October, later). The step counts the records included at
full text and opens once a run brings in records. Its table works as Screening's, the same sorting,
filters, Set columns and record, with Form after the ID, Done or Not done, a filter of its own, and the
foot says how many are done. The form's fields are offered as columns in Set columns, hidden at first. A
record opens its form under its head and links, with its PDF beside it, in place of the decisions, and
no key there decides, notes or undoes. A record is done once every field shown on it holds a value or
Not reported, and its head says Done. Benchmark papers, the first group of the filters, lists the
plan's benchmark papers whatever their decision, so you can pilot the form on them before any paper is
included.

**Set up the form.** Set up the form, on the line over the table at Extract and appraise, lists every
column of yours in the form's order, those in no section first and then each section under its heading.
The form is your own columns, one definition: each says where it shows, The form, The table or Both, so
a column on the table moves to the form with its values. A field has its name, its type, Text, Choice
list, Number, Yes or no, Several choices, Long text or Passages, each passage its words and its page, a
choice with the arrow that says it opens as Shows on and Section have since 17 October, later, where it
looked like a box holding its word, as Add a field's Type at the foot is too, its border and arrow the
same, where it stood borderless (17 October, later), and
its key, the column it is written to and exported under, letters, digits and underscores, unique, from
its name until you type your own. Not reported, on at first for a new field of the form, offers a tick
for a paper that does not report it. The card's ticks and the form's own on a record are in the ink, as
every tick is, since 17 October, later, where they stood in the browser's own blue. Shown when shows a field only while another field of choices, Yes
or no or Several choices holds one of the values you tick, and a field hidden that way keeps its value,
counts for nothing and exports empty. Starts from shows a Sift column as a Text, Long text or Number
field's value until you change it, marked From Sift: the citation, title, authors, journal, year, DOI,
country, study, No. of participants or another column of yours. A section's heading groups the fields
under it. The handle moves a field among its section's and a section among the sections, and Section
moves a field to another. Renaming a field keeps its values, a choice taken out of a list leaves the
values that held it in place, marked No longer a choice until you change them, and Remove asks first
when a record holds a value, keeping its values in the log. A section's Remove gives its fields to the
section before it. Add a field and Add a section stand at the foot, and the card keeps each change as you
make it, so Done closes it.

**Filling the form.** Each field is kept as you leave it, a choice and a tick as you make them, a line
of the log as your columns' values are, and nothing in the stage asks an AI. A later run that keeps the
decisions carries the form and its values with the records.

**Export the form.** Export the form, in Export's menu, writes `screening.form.csv` beside the
screening, one row for each record included at full text: `rec_id` and `study` first, then each field
of the form under its key, a field not shown on a record left empty, Not reported as `not reported`,
several choices parted by a semicolon and passages each as `p. 4: "its words"` parted by a bar.

**The search's terms.** Each block of the plan, as Search strategy holds it now, its newest version or
the draft, is a group of the filters on Screening's table (13 October, later): Block 1 and its name, its
terms as you wrote them, each with its count, by their counts, a tie in the plan's order, then More than
one, the records holding two or more of them, with Find, Show more and Show less on a long block. So a
term just added to a block shows what it brought in. A term is found in a record's title, its abstract and, where the run's files from the databases hold
them, its keywords, case and accents set aside: a phrase in double quotes, or of several words, as a
phrase, an asterisk at a word's end for any ending, a hyphen for a hyphen, a space or none, and a word
alone as a whole word. A term in a database's own syntax, a field tag or NEAR and the like, is found by
its plain words, each of them anywhere in the text. The filter is worked out as the screening opens, from
the plan and the screening, so it works on every run made before, follows an edit of the plan the next
time the screening opens, and writes nothing. The record lists the terms of each block it holds under its
facts.

**How a record matched.** A database searches more than the title and abstract Sift holds (14 October).
Europe PMC searches methods sections where the plan asks it to, and most databases search keyword and
index fields of their own, Scopus its index terms, PsycInfo its key concepts, PubMed its keywords, which
Sift never holds in full, and some records come with no abstract. So a record holding none of a block's
terms still matched as written, and the block's group says how. After the terms and More than one comes
a heading of two lines, "None of the above in the title or abstract." and "The database matched at least
one in:", and under it, indented, each with its count and by their counts among themselves: Europe PMC
methods sections for a record a database found by searching the block in methods sections, Scopus,
PsycInfo or PubMed keywords, naming those of its databases that searched keyword or index fields, Europe
PMC full text, naming those that searched the block in a paper's full text, as Europe PMC, OpenAlex and
PsycInfo or CINAHL on EBSCO do where the plan asks and Google Scholar always does, the abstract, which
Sift does not hold, for a record whose abstract is empty, and a field Sift cannot name for a record no
database's fields explain. Each names only the databases that found its records. A record that fits two
stands under both. The heading and its lines show while one of them holds a record, and always whole,
since Show more opens only the terms. The record shows each block's terms with Matched in and where they were found, Title,
Abstract or Keywords, and under Matched in one sentence for each block it holds none of, such as
"Block 1, Boats: none in the title or abstract. Scopus matched at least one in its keywords,
which Sift does not hold, so Sift cannot say which." Several databases read "Scopus or PubMed matched at
least one in their keywords", a record with no abstract "The database matched at least one in the
abstract, which Sift does not hold." and one none explains "The database matched at least one in a field
Sift cannot name." The command line's `show` says the same sentences. Matched in is a column of Set
columns too, hidden at first, saying for each block where its terms were found or its lines in the
filter's own words, Scopus keywords or Europe PMC methods sections, parted by a middle dot, on a line of
its own after the block's name when the plan has several. A run keeps each record's
keywords, the fullest list its databases give, PubMed's with its MeSH headings, or else OpenAlex's, in a
keywords column the record shows, and the terms are found in it as in the title and the abstract.

**Language.** Each record's language by its English name, English, Portuguese or Spanish, two where a
source gives two (14 October). A run takes it from each database's own field, PubMed's, Europe PMC's and
OpenAlex's, and from an export's language field, and where they differ it keeps the record's own
metadata, from PubMed, Europe PMC, PsycInfo, Web of Science, then Scopus, over OpenAlex's, which OpenAlex
works out from the text. Fill from OpenAlex fills it for a record with none and never changes one. A
screening whose review already writes a language column keeps it where it stands, with its values.
Language is a group of the filters, by its counts, with Unknown for the records no source gave a
language, and a column of Set columns, hidden at first, and the record shows it with its other columns.

**One decision filter.** The dropdown of rounds over the table is gone (12 October): Decision in
the filters is the one filter of where a record stands, To screen and the stage's three decisions with
each reason, and Differs from the proposal and Where we differ, each with its count. A round this
browser kept from before is read once into it. The rows are set when a tick is chosen, so a decision
never moves the records under him. Full text holds the records with Yes or Maybe at title and
abstract.

**A second screener.** PRISMA 2020 asks how many people screened each record and whether they worked
apart. In Sift's Projects category in Settings a project's Second screener part passages one on, off on a new project,
with your name or initials and theirs, the share drawn at each stage, every record by default or a
share in per cent, the calibration records, none by default, and the kappa below which Sift offers a
further draw, 0.6 by default (McHugh 2012). Second screener in the title bar opens its card for the
stage showing. The first records of the stage by ID, as many as the calibration records, you and
the second screener decide together, you in Sift as any record, each marked calibration in the log,
and they stay out of the draw and the agreement. Make the second screener's workbook draws the share
at random from the rest, its seed and the records drawn kept in the log so the draw can be made
again, and writes an Excel workbook beside the screening: a first sheet with the review's question,
the eligibility the plan sets and the stage's reasons, then a row for each record drawn, its title,
authors, year, journal and abstract laid out to read, then Decision, Reason and Note, the only cells
that take typing, Decision and Reason as dropdowns, Decision offering Yes, Maybe and No at title and
abstract and Include and Exclude at full text. A workbook made before 12 October, with Accept and
Reject, is still taken back. Nothing of your decisions, proposals or ratings
goes in. At full text the PDFs the run holds for those records go into a folder beside it, named by
rec_id, to zip and send with it, and the draw there waits until every record is decided at title and
abstract. A returned workbook dropped anywhere on the screening, or chosen with Take back a workbook,
is checked as the one Sift made for this screening, a stranger refused, and its decisions taken in,
a row left blank still to screen. Until you have decided every record of a draw the card says only
how many came back. Once both of you have decided them, Sift records at once and for good the
records decided alike and the proportion, Cohen's kappa on going forward, Yes or Maybe, against No,
and the table of your decisions against theirs, and a kappa below the setting offers Draw a further
share, from the records not yet drawn. At full text a decision is Include or Exclude, so a Maybe of
yours there counts as not yet decided.

**Where we differ.** Where we differ, a tick under Decision in the filters, holds the records one of you took forward and the
other left out. A drawn record whose draw you can see shows your decision and theirs side by side,
each with its reason and note, and for a difference its outcome, Agreed: Yes or Agreed: No at title
and abstract, Agreed: Include or Agreed: Exclude at full text, To
a third reviewer and then that reviewer's decision, or Reopen. An outcome that changes your decision
changes it as a decision of yours, marked after discussion in the log, and nothing else ever does.
Make the differences workbook writes the open differences beside the screening, both decisions,
reasons and notes, then a Reply, Agree with you or Keep mine, and a note on it. Taken back the same
way, Agree with you settles the record on your decision and Keep mine leaves it open, for the two of
you to settle or send to a third reviewer.

**Keys.** At title and abstract Y is Yes, M Maybe and N No, at full text I is Include, M Maybe and E
Exclude, each shown on its button, and N or E is followed by a number for the reason, 0 for No reason
at title and abstract (12 October). A and R, the keys before, still take Yes or Include and No or
Exclude at either stage. U or Cmd + Z undoes and ? shows the keys, the decisions in the stage's words.
In the table the up and down arrows move the row and Enter or a click opens it. On a record Enter
accepts the first suggestion, the left and right arrows go to the record before and after, T is the
note, N until 12 October, P the PDF, and Esc goes back to the table. H keeps the words selected in the
title or abstract as a key excerpt, and Cmd held while you select adds another piece to it, Ctrl off a
Mac, each a row of its own on the shortcuts card since 17 October, later, where one row held both. At phone width Esc shuts the PRISMA flow first when
it is open. In the note and your fields every key types, and Esc leaves them. `Cmd + F` opens Search,
a row of its own on the shortcuts card since 18 October (see Search).

**Export.** Export PRISMA counts, in Export's menu, Write the counts until 12 October, writes `screening.counts.csv` beside the CSV: at each stage the records, each
decision, those left out by reason, and the decisions that matched the proposal and those overruled, in
all and by where the proposal came from, `csv` or `sift`, for the paper's statement on AI
assistance. `sift <folder> counts` and `export` give the same on the command line (see
[docs/agents.md](agents.md)). Export included records writes the records included at full text beside
the CSV, as Export PRISMA counts writes its file there, as `screening.included.ris`, for Zotero, EndNote
or any reference manager, each with its type, title, authors, year, journal, DOI, web address,
abstract and its rec_id in a note, and as `screening.included.csv`, the CSV's own cells for those
records and nothing of your decisions or fields, both whole each time. It stands off while no record
is included at full text. With a second screener the counts name the two screeners and add the share,
each draw's seed and records, the calibration records, the agreement and kappa before discussion with
the table of both decisions, and the differences settled by discussion and decided by a third
reviewer, and the PRISMA flow says the same in a box beside each stage.

**Start again.** Start again, quiet under the PRISMA flow, says how many decisions and notes it
clears and then, once you agree, clears every decision, note and field of yours at both stages, with
Sift's own proposals, keeping the old log whole in `_Archive/` beside the CSV, as
`sift <folder> reset --yes` does on the command line.

**With Claude.** Claude in the Claude app reaches a screening through Idiograph's MCP tools: it
lists a round's records, shows one with its log, reads the counts, the export and the flow, adds
records the searches found and writes the review's proposals. It reads your own fields and
columns. No tool decides, notes or undoes a record or writes a field or column of yours. Those are
yours, in Sift.

**The files.** Every decision, note and undo is a line of `screening.log.jsonl` beside the CSV,
never rewritten. After each one the CSV's `decision` and `reason`, and at full text `ft_decision` and
`ft_reason`, added when missing, are written afresh from the log. The review's proposal columns are
written only by the review's side, and Sift's own go in `ai_proposed_decision`, `ai_proposed_reason`
and `ai_grounds`, `ft_ai_` at full text. `reasons.csv` beside the CSV names the reason codes,
`code,meaning`, each offered at both stages, or in a file of before `stage,code,meaning`, each at its
own stage, and without it the codes the proposals name stand bare. Your own fields go in
columns of Sift's own, `participants`, `participants_confirmed`, `rating`, `notes`, `digest`,
`critique`, and `col_` with the name of each column you add, after the last column, each change a
line of the log with the old value and the new. An export to Zotero writes each record's item key in
`zotero_key`, which Start again keeps, and a run or Fill from OpenAlex each record's count of
citations in `cited_by` and the day it was asked in `cited_by_date`, with Sift's own columns from
OpenAlex and Crossref, `retraction`, `retraction_notices`, `open_access`, `countries`,
`openalex_authors`, `openalex_date` and `crossref_date`, and each record's references in
`screening.references.json` beside the CSV, all of which Start again keeps. Your links of reports as one
study go in `study`, each a line of the log, which Start again clears. The second screener's side is a line of the log too, `act`
`second`, which never moves a decision of yours, and `screening.second.csv` beside the CSV holds their
decisions as the log stands. The review's columns are never written. `sift.json`
keeps the screening's AI switch and prompt, the table's columns, your own columns, the filters'
sidebar's width and each record's number, and `prisma.md` the flow. `screening.lock` beside the CSV keeps one
writer at a time, Sift or a script adding records or proposals, and the screen reads the screening
again when the window comes back to it after another writer.

## Search strategy

Sift runs a review's searches too, on its Search strategy, PRISMA-S's name for the step: you write
the search once, as blocks of terms, Sift writes each database's own search from them, runs the
searches, takes in the exports and merges the records into a screening. The screen is one column in
the order of the work, in four numbered parts (12 October): the plan, the searches written from it,
Register and Search runs.

**The plan.** The plan's state is one tag beside its heading, Draft, or Registered with its date. A
version's number shows only once there is more than one, Version 2, draft, and Earlier versions under
the heading opens each earlier version with its reason, where it was registered and its plan as
`search_plan.md` had it. The project's research question stands at the head, under Research
question, when the project has one. Then Search terms, the blocks. A line under Search terms says
what a block is: each block holds the terms for one idea in your question, the terms within a block
are joined with OR and the blocks with AND, so a record is found when it has a term from every
block. Each block is headed Block 1, Block 2 and so on, with its name beside it, which you can change
(12 October, later). Under the heading, Search in sets where the block's terms are looked for, title,
abstract and keywords by default, methods sections or full text where a database has them, and the
terms stand under it, one to a line, a phrase in double quotes and an asterisk for truncation. Their
box opens as tall as the terms with a line to spare, four lines at least and thirty at most, past
which it scrolls, and follows each edit. Search in, by database, a button with a chevron, shut at first on every block, opens a choice for
each database to look elsewhere in that one database, methods sections in Europe PMC for one, Same
as the block until you change it. While it is shut, a line for each database that differs names it,
Europe PMC: methods sections, so a difference is never hidden. A problem with a term, an operator or
a mark a database reads as its own, shows under its block as well as under Register, and each block
has Remove at its foot, which asks first when the block holds terms, since they go with it.
Truncation goes on single words alone (14 October): a phrase holding an asterisk or a question mark,
"community garden*", says under its block that truncation inside a phrase works in Scopus and PubMed
but not in Europe PMC or OpenAlex, and to write each form of the phrase as its own term, "community
garden" and "community gardens". Scopus and PubMed honour the asterisk there, Europe PMC passes over it
and OpenAlex takes none, and the search would run with no sign of the records it missed. While such a
phrase stands the plan is not saved, the tag beside the heading says Not saved and the plan is
neither registered nor run, and the next change once each phrase is written in full saves everything.
A single word keeps its asterisk, allotment*. Then
Limits and restrictions, PRISMA-S's name for them, Years from and to, and the document types. No
language limit is offered: language is applied at screening, so the searches count every language.
Then the databases, in one list in the plan's order, every database Sift knows and then each you
named, a row each with its box to tick, PsycInfo and CINAHL with their platform, how it runs, By API
or By export, and Access not set for one your list in Settings sends By API whose key is not saved,
which goes by export until you set its access under its cog. A row never moves when you tick it. Its box,
and a document type's, is in the ink, as Settings' are, where until 17 October it stood in the browser's own blue. Add
database takes a name and adds it with Add or Enter, to your list and to the plan, as many as you
need, each with Remove, which takes it out of both. A name Sift knows, such as Embase, takes that
database's own row. Then the benchmark papers, papers you know are relevant, which a good search
finds, so each run says how many of them it found: a row for each paper, its DOI in a box with the
paper's title beside it and Remove, and Add a paper under them. When you enter a DOI, Sift asks
OpenAlex for the paper's title by that DOI, sending the DOI alone, and the plan keeps the title with
it. A DOI OpenAlex does not know says Title not found, one that is not a DOI says so, and a paper the
list holds already takes no second row. Last the
exclusion reasons, one list for both stages of screening, a row each with the handle that drags it
up or down, Alt and an arrow on the handle moving it one place, its short code, what it means and
Remove, and Add a reason under them. A line says Screening offers them
when you reject a record, a reason optional at title and abstract and required at full text. Sift
keeps them in `reasons.csv` in the review's folder, written as you edit, so there is no file to open:
a project whose file names each code for one stage reads it as one list, and the file takes the one
list form when you first edit it. A code held twice says so, and only the first is kept. The reasons
are part of the plan's version, written into `search_plan.md`, and a run whose screening has not
begun takes your edit too, while a run whose screening has begun keeps the list it was made with.
Each change is saved a moment after it is made, in `search_plan.json` in the review folder, every
version kept whole.

**Key works.** Under the benchmark papers, Key works lists works the studies of your review would cite,
the method's key book in each of its editions for one, so Screening's Cites key works column shows which
records cite each. Add a key work takes a DOI, or a title and the year it came out, and Find. A DOI is
asked of OpenAlex for its title and kept. A title is looked up in OpenAlex's works, and its first few
are offered to pick from, each with its year, authors and count of citations, and Keep it by its title
and year keeps it with none of them, since OpenAlex sometimes holds a book badly or not at all. The row
keeps the title and year you typed, with the OpenAlex ID of the work you picked, and never its DOI or
its authors. A work the list holds already is refused, and Remove takes one out. A record cites a key
work by Crossref's list of its references when Crossref holds one: a reference counts when its DOI is
the key work's, or when one of its titles, in whichever field the publisher put it, holds the key
work's title and its year is the key work's within a year either way, since a book is often cited by
its online year, one before its print year, or by a reprint's, which still tells apart editions years
apart. A reference that garbles the subtitle or misspells a word of a long main title still counts
when the subtitle's first word follows the main title, and a work that shares the main title alone does
not. Only when Crossref holds no references for a record does OpenAlex's list decide, by the key
work's OpenAlex ID, and a key work kept without one leaves that record at Can't check. The key works are kept in `search_plan.json` beside the plan's versions, never in
one, so an edit to them makes no draft and needs no new registration.

**Searches.** A row for each database of the plan, in the order of the databases, its name, how it
runs and its cog at the left and its search at the right, the two stacked on a phone. A row of your
list in Settings decides for its own database, By API or By export. A database your list does not
hold, and every database while the list is empty, goes Sift's own way: by its API when it needs no
key, PubMed, Europe PMC and OpenAlex, or when its key is saved, Scopus and Web of Science once their
keys, saved under Databases in Settings or under the row's cog, are in the login keychain, read at
run time and never shown or written, and else by export. The cog on a row opens that database's
access under its name, as Settings' Databases has it: its platform, By API or By export, and for By
API its keys, Saved or Not set, with Save, Remove and Check. A change there goes to your list at once,
the same list Settings keeps for every project, and a platform to the plan too. A database searched
on its own site, any other or one your list holds By export, gives its steps in order under its
name: Copy the search, Open the database by its name in a new tab, Run the search there, Export the records as RIS,
CSV or BibTeX, or for Google Scholar Run it in Publish or Perish and Save the results as CSV, then Drop the file here, or choose it, its
place taking the sunk paper under the pointer or a file, where it took the crux orange until 17 October, later,
which keeps the file in the run the screen shows, the day's newest, the one still waiting on its
exports, and writes that run afresh. A drop never goes into an earlier run of the day: when a later
run has been made since the screen was drawn, it is refused in one line and the runs are drawn
afresh, so the next drop goes to the newest.

Each search is written from the plan as its vendor's own help gives it: `TITLE-ABS-KEY` and `PUBYEAR`
for Scopus, `TS=` and `PY=` for Web of Science, `[tiab]` and `[dp]` for PubMed, `TITLE_ABS:`, `KW:`,
`METHODS:` and `PUB_YEAR` for Europe PMC, `title_and_abstract.search` for OpenAlex, its asterisks left
out since it stems, `TI`, `AB` and `KW` for PsycInfo on EBSCO and `TI`, `AB` and `SU` for CINAHL
there, `.ti,ab,id.` on Ovid, `TITLE,ABSTRACT,IF()` on ProQuest and for ProQuest Dissertations &
Theses, `:ti,ab,kw` for Embase, a plain string for Google Scholar within the about 256 characters it
takes, phrases quoted and no asterisk or field, and a plain Boolean string for a database you added
by name. A note under a search says when a database lacks a block's fields or a document type, and
for a database searched on its own site the limits to set there. CINAHL is offered on EBSCO alone
now, so Ovid and ProQuest are no longer among its platforms, and a plan or a list that names one
still reads, its search written with a note that says so. A plan with a year from and no year to
ends Web of Science's and Europe PMC's range at the year of the run, since neither takes an open
end, and `log.csv` records the year as sent, while Scopus, PubMed and OpenAlex take their own open
forms. Edit manually opens one database's search to edit, marked Edited, with its reason beside it,
and Revert to automatic takes Sift's own back. A search Sift runs itself has Copy beside it. Copy and
Copy the search are held while there is no search yet, a plan with no term, and Search terms says
"Write at least one block with a term." under its blocks as Register does (17 October, later). Under
each search, Rewrites lists in plain words what Sift changed from the plan for that database (14
October), so no difference between the databases is left for you to spot: the method block in the
METHODS field, the asterisks removed for OpenAlex, which stems, `DOCTYPE(ar)` from the plan's types,
the plan's years in the database's own words, a type it has no code for left out, and for a search
edited manually its reason.

**Register.** Sift registers nothing anywhere and sends nothing anywhere: you register the plan
yourself (12 October, later). Export search_plan.md writes the plan as it stands, a draft or
registered, the plan and every search in Markdown, to `search_plan.md` in the review's folder, at any
time, then Open search_plan.md opens it in your computer's own app for it and Copy copies its text.
Beside the button two short steps say what to do with it: export the plan, then register it
yourself on OSF Registries or PROSPERO, adding the file there, each a link that opens in a new tab,
underlined in the accent as every link to a page outside the app is (17 October, later).
While the plan is a draft, a line says once you have registered the plan on OSF or PROSPERO, mark it
as registered here, then Mark as registered. It opens a card that says it freezes this version of
the plan, so it no longer changes, and asks where it is registered, OSF, PROSPERO or another registry
by its name, each radio in the ink since 17 October, later, where it stood in the browser's own blue, and its registration number or link, both needed, as PRISMA 2020's item 24a asks for
the registry and the number. Once marked, the part says when and where, Registered on 12 October
2026 with PROSPERO and the number, a link opening in a new tab, the plan keeps both and
`search_plan.md` is written again to say so. Export still works, and your next edit to the plan
starts a new draft version. That draft, version 2, needs a reason for its changes before it is
registered or run. Runs made before registering are trials, and the run made after it is the search
the review reports, as PROSPERO and OSF have it.

**Search runs.** The runs made stand under Search runs in a table, newest first, a row each,
numbered in the order they were made with their date, Run 1, 8 October, Run 2, 12 October and Run 3,
12 October, the year only when it is not this year's (12 October, later). The number is kept in
`runs/numbers.json` from the time a run is made, so a run you remove by hand moves no other run's
number. The columns say Trial for a run of a plan not yet registered or Registered search for a run
of a registered one, the records found, those after duplicates and the benchmark papers found, and
the last says Active on the run Screening has open, in the ink on a firm border since 17 October,
later, where it stood in the crux orange, or holds Make active on another, which opens it in Screening. Nothing opens by itself: a run opens in Screening only when you press Make active, and
Screening opens that run from then on. On a phone each run stands as a block of its own, each count
with its name. A run waiting for an export says which database it waits for under its row, Waiting
for the PsycInfo export, and takes the drop there. A database that failed says so under its row in
plain words, which database, what happened and the status in brackets, "PubMed did not answer (HTTP
503).", "Scopus refused the key (HTTP 401)." or "OpenAlex sent something Sift could not read.", never
an address, a query or what the database's answer held. The run's `run.json` and `log.csv`, the
search log PRISMA-S asks for, keep that detail in full (17 October, later). The same words stand in
Check truncation's table, beside a key's Check in Settings and on every lookup of Sift's that fails.
Every such line is in the amber of a card's failure line, a database that failed under its run and
in New run, what stands in the way of the plan, and the line beside Check, Find open-access PDFs or
Fill from OpenAlex when it says something failed, where Sift's stood in red and Settings' in grey
(17 October, later).
A run that brings no records makes no screening
and says None came in, and the run Screening had open stays the one it opens. Details under a run, a
button with a chevron, gives each database's hits and records saved, the plan's version once there
is more than one, what OpenAlex filled, the decisions kept and the benchmark papers missed, each with
its title where known. Every run is kept: Start new run always makes a new run, `runs/<date>/`,
today's date, in the shape Sift screens, never writing one made before, a later run that day going
into `runs/<date>-2/`, then `-3`. A run an export dropped before the searches ran is the one Start
new run completes. A run whose screening has begun, with a decision, a proposal, its log or a PDF of
yours, is never written again: an export dropped on it is refused, saying Run makes a new run. The
Home's row and Screening's name say a run the same way, Run 3, 12 October 2026, and the
command line by its day and its number that day beside its folder.

**New run.** Under the table, New run says whether the next run is a trial or the registered search,
and says nothing while the plan names no database, where until 17 October, later, it said "It searches
these databases:" over an empty list. It names each database it searches and how, By API or By export, and as a run goes each database's
state, then Start new run, with Keep the decisions from beside it once a run has decisions. Start new
run is held, as Mark as registered is, while something stands in the way of the plan, a line under
Register saying what, where until 17 October, later, it could be pressed and was refused. Check
truncation stands above it when the plan holds a word with an asterisk and a database that takes
truncation goes By API, Scopus, PubMed, Europe PMC or Web of Science (14 October). It counts each such
word alone in its block's fields, with the plan's years and types, with and without its asterisk, in
each of those databases, one request for each form with Sift's usual pause between them, and shows the
counts in a table, a row for the word in each database, and writes nothing. Equal counts in one
database while they differ in another are flagged, Europe PMC reads allotment* as allotment, and no hits
in one while another has some, No hits in Europe PMC: syntax or coverage?, so a database that reads
the asterisk as nothing is seen before the run. The table stays until you change the plan. Start new
run checks the same way first, each database saying Checking truncation while it is counted, keeps
the table in the run's folder as `dry_run_terms.csv` and lists the flags under the run's Details. A new
run takes its `reasons.csv` from the review folder's own, the one list Sift keeps, and with none
from the plan's exclusion reasons. A BibTeX file, which EBSCO's export carries DOIs in, is read with its braces and
accents undone. The records are merged by DOI, two versions of one item, `.v1` and `.v2`, as one,
and then by title with a year at most one apart, as a thesis and its paper often are, a record with
no year by its title alone when exactly one other record has that title, `sources` names every
database that found each, an abstract a database lacks comes from OpenAlex by DOI, each field is the
best its databases give, the fullest list of authors, since Scopus gives only the first, the title
with its subtitle and not in capitals, the journal's full name, the type that says most, a thesis or
a review over an article, the longest abstract and the year most of them give, the earliest on a
tie, and `log.csv` keeps each search's query, hits and records saved for PRISMA-S.
The authors of a record that names one or none come from OpenAlex by DOI too, in the same request as the abstracts,
when OpenAlex names more, so a record only Scopus found carries its whole list, and a record carried
from an earlier run is never changed. The same request asks for each record's count of citations,
which the screening shows as Cited by with the day OpenAlex gave it, so every record with a DOI is
asked about (12 October). Each run's Details says how many abstracts and how many records' authors
came from OpenAlex, and how many records' citation counts, when it filled any. A year is read from
a date as EBSCO writes it, 20260803, as well as 2026-08-03. A database's line counts a benchmark DOI as found when its record has no DOI but carries
the title of a record that does, and an export with no DOIs that matches none by title says No DOIs
in this export. An OpenAlex key, `OPENALEX_API_KEY`, is optional, saved the same way, and every
OpenAlex request carries it.

**PDFs from earlier runs.** A PDF belongs to the paper, not the run (12 October). When Sift makes a
run, and each time Screening opens one, each record with no PDF takes the PDF an earlier run of the
review holds for the same paper, matched by DOI, or for a record with no DOI, as an EBSCO export's
records have none, by its title and year. A title and year that match two different papers take
nothing, so no PDF is guessed. The PDF is copied into the run's `pdfs/` folder, never over a PDF
already there, so a PDF you add to an older run later still reaches the newer run the next time you
open it. A PDF found this way is never counted as work on the screening.

**Keep the decisions from.** A later run follows an earlier one when you choose it: its screening holds every record
of the earlier run, with its decisions and your fields, and adds this run's new records, to screen,
so no record is screened twice. Keep the decisions from, beside Start new run, offers each earlier
run with decisions, the newest first, each by its name as the runs list gives it, an earlier run of
the same day among them, and No earlier run. A record found again keeps its rec_id and gains this
run's databases, a new one is numbered on from the earlier highest, and Database in the table filters
to New in this run. The earlier run's folder is only read, its PDFs copied. `log.csv` holds both
runs' searches with their dates, and Export PRISMA counts says each search and the records new in
this run, while the PRISMA flow counts this run's own search alone (16 October, see The PRISMA flow). Your own columns come too, with their names, types, choices, order and
whether they show, and their values on every record carried, a record found again matched to its
earlier self by DOI, or else by title and year, as a PDF is. A new record holds none of them yet. Your
links of reports as one study come the same way, each record carried in its study (13 October), with
each record's references, and Fill from OpenAlex fills a carried record's columns from OpenAlex and
Crossref where it lacks them.

**With Claude.** Claude reaches the searches through Idiograph's MCP tools: it reads the plan, the
strings and the runs, and runs the newest registered version when you ask, following the newest
earlier run with decisions unless you name another or none. Its dry run says how each database would
go and the truncation check's table, the counts its only requests. No tool registers or edits a plan:
a Claude session that carries your decision on the terms or the strings writes the draft through
Sift's own save, with the reason you gave, and Mark as registered stays yours. It can list your databases and whether each key is saved, and no tool saves, removes or shows
a key.
