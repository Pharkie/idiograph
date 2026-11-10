# Trace manual

Trace is an app of its own since 20 October 2026, on Idiograph's code, with its own window, icon and
installer. Its Home holds your Trace projects under Projects, and ends with Idiograph and Sift. Its
settings are its own, Appearance and the AI features among them, once its first start has copied what
it shares from Idiograph's. How to install it is in the [README](../README.md), and how it works
underneath in [docs/internals.md](internals.md).

Trace (15 October) holds each claim a
manuscript makes of a reference against the reference itself, so you check with your own eyes that the
source says what the manuscript says it does. It is no part of a literature review, so it stands on its
own: a review protocol first, and any paper after it. It grew out of Sift's Check references of 14
October, which it replaces.

**A project.** Home's Projects section holds a card for each Trace project, newest
first, with one line on where it stands, the folder named in its tooltip alone: its newest manuscript and how many
of its claims you have judged, "protocol.md, 12 of 40 claims judged", or its reference list alone, or
No document yet. New project, under the cards, takes a folder through the Mac's folder dialog, or off a
Mac its typed path, then the project's name, and Create project makes the project there and opens it.
A folder that holds anything gets a new folder inside it, named for the project, and one that holds a
Trace project already is refused. The project's folder holds `trace-project.json`, its name and the
reference list you loaded. Open project folder takes a project that stands, writing nothing into it.
In Trace's Projects category in Settings, which the cog in Trace's title bar opens, each project has its
name, saved with Save into the app's own list and never its folder, the folder it is in, and Remove from
Trace, which asks first and takes the project off Home, its folder and every file in it
left as they are. The title bar holds Trace's mark, which is Home, and the project's name with a chevron,
and at its right Search (`Cmd + F`), Shortcuts, Feedback and Settings, each with its word where the bar has the
room (see One title bar and Search).

**A project's menu (6 November).** Each project's card on Home has a "…" at its top right, and on a project's
screen its name opens the same menu: Show in Finder (Show in Explorer on Windows, in Trace's own window
alone), Project settings, which opens Settings on Projects with this project in front, and Remove from
Trace…, which asks first and, from inside the project, leaves the screen and ends on Home. A project whose
folder has gone has Remove alone. Trace keeps no History of a project and makes no shared copy, so neither is there.
The mark goes Home, and the name no longer does.

**What goes in.** Add file, over the table or on an empty project, takes a manuscript or a
reference list through the Mac's file dialog, or off a Mac its typed path, in a field beside it that
says "Path to a manuscript or reference list" and shows only off a Mac. On an empty project the field
is as wide as the one over the table and as tall as Add file beside it, and on a phone it takes the
row (15 October, later). A manuscript is a Markdown or
Word file, read afresh each time you open it and never written, so the table follows it as you revise
it. Trace finds its reference list under a heading named References, Reference list or Bibliography,
and every citation in the text in APA's author and year forms: Smith (2020), (Smith, 2020), two authors
with and or an ampersand, et al., several in one bracket parted by semicolons, a run of years, e.g. and
see before a name, a page after the year, and a group's name with its abbreviation in square brackets,
which a later citation may give alone. Each citation is matched to its reference by the first author's
surname and the year with its letter, 2020a, a two-author citation's second author too. A reference
list alone is a CSV, with whatever columns your reference manager's export holds, a column of whole
references or Author, Year and Title, with a DOI and Zotero's Key where there are any, or an RIS or
BibTeX export. Works of the same authors in the same year are lettered by their titles, as APA letters
them. A list alone shows its references, each with its PDF, and one line over them, "No manuscript
yet." A manuscript with no reference list of its own is matched to the project's list,
and one with its own takes a DOI and a Zotero item from the list where its own entry has none. A
project may hold several manuscripts, chosen from the list over the table, which says "References from"
and the list's name when they come from it.

**The claim.** Each row is a claim: a reference a sentence cites, with that sentence whole, the
heading of the section it stands in, and the forms it cites the reference in. Where the citation closes
a sentence that leans on the one before, one that opens This, These, It, Such, However, For example or
the like, the claim is the two together, the sentence before it shown first in the faint ink. A
sentence that cites three references is three claims, and one that cites a reference twice is one.

**The table.** The same table and filters as Sift's: Claim, Reference, Judgement, PDF, Section and your note, a
claim in the manuscript's order, a citation no reference answers in its place, its claim in the ink and
No reference in grey with the form it was cited in, Zeller et al., 2015, which has nothing to judge against, and each
reference never cited at the foot, Never cited in the same grey in its Reference column. A reference's
label after either keeps to one line, under the grey where the column is narrow. The headings sort, Shift adding a second key, and the filters at the
left take Judged and Not judged, each judgement, PDF and No PDF, Cited and listed, No reference and
Never cited, each section and each reference, each with its live count, as Sift's filters do. This browser keeps the
filters for each manuscript. Below about 600 pixels the table keeps the claim, its judgement and its
PDF, the reference under the claim, and Section and Note stand on the record alone, with nothing
scrolling sideways.

**Your judgement.** Supports, Y, in the screening's green, Question, Q, in its amber, or Doesn't support,
N, in its red, on the row chosen, the arrows choosing it, or on a claim open. Every claim starts with
none, its cell blank and no line over it until you judge it. Each goes to the project's log at once with
the day, and Undo at the foot, U or Cmd + Z, takes back the last judgement or note. The foot counts the
claims at each judgement.

**A claim.** Enter or a click opens it: your judgement and the day you gave it, the section, the
sentence before it where it leans on one, the claim in the transcript's serif and the forms it cites
in where they say more than the author and year, a page or every author's name, then the reference with
its DOI as a link, Open PDF, which opens the PDF in your computer's own app
for it, Show in Zotero where Zotero's item is known, and how many of that reference's claims you have
judged, "Judged: 1 of 3 claims citing it". The PDF stands beside it, as on a screening's record, fitted to the pane's width, and P folds
it away. Under the claim are Supports, Question and Doesn't support, each key in its word's own colour as on a screening's
record (17 October), then your note, the three on one
line on a phone, where they leave out their keys. A reference never cited opens with "The manuscript
never cites this reference." in the claim's place, wrapping on a phone as a claim does (15 October,
later), then the reference and its PDF. The arrows go to the claim before or after, and Esc
back to the table. A small link before the project's name, "Claims" with a left chevron, also goes back to the table, and shows
only on a claim. The name itself opens the project's menu.

**PDFs.** Trace finds a reference's PDF and never fetches one: in the project's `pdfs/` folder, a file
named for the reference, `page2021.pdf`, or carrying its DOI in its name or on its first page, or else
the PDF of a screening record with the same DOI or title in any of your Sift projects, those Sift lists
under Projects, with that record's Zotero item. Trace only reads Sift's list and its screenings. Add
PDF, where a reference has none, keeps one you choose in that folder under the reference's name, never
over a file there. Every path Trace shows is written with forward slashes, on Windows too.

**AI find passages.** With the AI switch on, AI find passages on a claim asks the AI for the passages
in its reference's PDF on each claim the manuscript makes of it, and AI find passages for the rows
shown, over the table, asks for each reference shown with a PDF and no passages yet, saying first how
many and that Trace asks the model once for each, a second press leaving the rest not asked, and at the
end how many references it asked and how many came back with no passage. The AI sees the claims and
the PDF's text and answers with a passage and its page for each claim, or none, and a claim with none
says the model gave no passage for it. Trace looks for every passage in the PDF's own text before it
shows it, and shows it in the PDF's words with its page, which shows that page in the pane. A passage that is not in the PDF is never
shown as a quote: the claim says the model gave a passage Trace could not find. The passages name
their model and their day. They never judge a claim: that is yours alone, and the log records each
judgement as the researcher's, saying whether the AI's passages were shown and what they found.

**The files.** Kept in the project's folder, never beside the manuscript: for each manuscript a log of
every judgement, note, undo and the AI's passages, one line an act, and a plain JSON file written afresh
from it, the manuscript's path and each claim with its reference, section and sentence, your judgement
in words, the day and your note, the AI's passages with their model, and the counts its card shows.

**Sift's Check references.** A Sift project that used Check references on 14 October keeps its
`reference_check/` folder, and Open project folder under Trace, given the Sift project's folder or that
folder itself, opens it in place as a Trace project named for the Sift project. Its documents, its PDFs
and its log are read as they are. Its old Checked lines, set on a whole reference, stay in its log and
its history and are never read as a judgement of a claim.

**With Claude.** Claude reads Trace through Idiograph's MCP tools and the command line, each manuscript's
claims with your judgements, your notes and the AI's passages, to help you check. No tool judges a claim
or writes a note.
