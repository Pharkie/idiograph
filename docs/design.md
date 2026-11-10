# Idiograph design

How Idiograph looks, for whoever builds it: the tokens, the rules and the components, and the one
place a rule about the look is written down. The reference page at `/design` on a running server,
`family/static/design.html`, shows every component here in a light panel and a dark one side by side, from
the app's own stylesheets. No menu leads to it. Open it at 1280 and 720 wide before a merge and look
for anything that moved. The suite's area 147, `colour_problems`, holds the app to this file.

## The principles, as they bear on the look

1. **Human first, AI assisted.** Nothing looks like the AI's but what is the AI's. The sparkles mark
   an AI control and nothing else, and every AI part goes with the AI features switch.
2. **Your files, your machine.** Nothing is downloaded and no font file ships. The faces are the
   system's own, and the page fetches nothing at runtime.
3. **IPA by the book.** The colours carry the method's meanings, the crux orange a crux as the
   researcher marks one in Excel and a quote where it stands in its passage, and never a
   decoration. The participants' colours mark a participant on the boards and every other screen,
   and on the statements screen, which holds one participant, the same colours mark her statements:
   statement 1's quotes keep the crux orange and the others take their statement's colour (18
   October, Adam's ruling).

## Tokens

Every value that means something is a token in `family/static/tokens.css`, linked first on every page the
app serves that links its stylesheets, and nothing else writes a colour. Light sits on the root and
on any element marked `data-theme="light"`, dark on any element marked `data-theme="dark"`, and the
system's dark on `data-theme="auto"` and `data-theme="system"` while the page follows macOS. The two
dark blocks are written alike, and area 147 fails when they differ, when a colour is written outside
a token block, when a `var(--name)` names nothing, and when a row below disagrees with the file.

### In light and dark

| Token | Light | Dark | Its one meaning, and who uses it |
|---|---|---|---|
| `--paper` | `#FBF7EF` | `#16130E` | The page's ground, every screen |
| `--paper-sunk` | `#F3EDE1` | `#100E0A` | Sidebars, wells, a row under the pointer, a passage under the pointer among them since 17 October, later, and the current passage's band with Larger current passage off |
| `--card` | `#FFFDF8` | `#1E1A14` | Cards, fields and popovers |
| `--ink` | `#1F1B16` | `#EFE7D9` | Words, and the current passage's name and rule in the transcript (17 October) |
| `--ink-soft` | `#554C41` | `#B6AC9B` | Quieter words, labels and controls at rest |
| `--ink-faint` | `#756A5C` | `#8B8272` | Small print, counts and timecodes, 4.5 to 1 or more on paper, card and sunk paper |
| `--rule` | `#E3D9C7` | `#2E2820` | Lines between things |
| `--rule-firm` | `#CBBFA8` | `#463E32` | Borders of controls and cards |
| `--field-edge` | `#8F8473` | `#6F6758` | The edge of a text field, a note box or a chooser, 3.1 to 1 or more on paper, card and sunk paper (8 November), where the rules stand at 1.2 to 1.8 to 1 |
| `--scroll-thumb` | `#8F8473` | `#6F6758` | A scrollbar's thumb, 3 to 1 or more on paper, card and sunk paper (17 October, the third Tauri build) |
| `--dim` | `#FFFDF859` | `#1E1A1440` | The card's paper laid over what stands outside a view to dim it, the minimap's column outside its box, 35% in light and a little less in dark, 25% (18 October) |
| `--crux` | `#B04E00` | `#F79646` | A crux, a quote marked in its passage (16 October), and the app's one accent: the filled button, the focus ring's edge, the selected tab, the selected row's bar |
| `--crux-wash` | `#F7964622` | `#F7964626` | A crux's wash, a quote's in its passage |
| `--mark-dot` | `#F26B1D` | `#F26B1D` | The dot of Idiograph's mark wherever the mark is drawn, the launch film's orange, a graphic and never words, about 2.9 to 1 on the light paper and 6 to 1 on the dark (22 October) |
| `--hold-yes`, `--hold-yes-ink` | `#B04E00`, `#FBF7EF` | `#B04E00`, `#FBF7EF` | Approve on the card where an agent's action waits for his yes, the light crux and its paper in both themes, so the yes reads in dark as he approved it in light (27 October) |
| `--es-wash` | `12.5%` | `14.5%` | How much of its statement's bright tint a quote's wash takes in its passage, statements 2 to 6, the words on it reading at least as well as on the crux's wash in the same theme (18 October) |
| `--es-lit` | `34%` | `22%` | The same wash lit, under the pointer or while its quote holds the caret, at least as readable as the crux's lit wash (18 October) |
| `--accent` | `#786850` | `#B4A588` | The playhead, a quote being built, the demo tag, the days and a link to a page outside the app, never the crux orange |
| `--good` | `#4C6B45` | `#8FB183` | Supports, Include, saved, a phase complete, a passage decided in the transcript's margin and in the minimap's track, and the case's line and the round's short bar, which count decided passages (16 October) |
| `--amber` | `#936000` | `#E3B45E` | The one warning tint: Question, Maybe, a card's failure line, a statement past its length, a run still waiting |
| `--danger` | `#A8402F` | `#E58A78` | Doesn't support, Exclude, every Remove and Delete |
| `--find-wash` | `#F7D84A70` | `#E9D65A3D` | What the find or a search has found, never written anywhere |
| `--find-on` | `#F4C81FD9` | `#E9D65A66` | The find's one in focus, its ink 4.8 to 1 or more on it in dark, where at half its yellow it read at 3.6 to 3.9 (17 October, the cards' sweep) |
| `--find-edge` | `#B38F00` | `#E9D65A` | The edge of the find's one in focus |
| `--excerpt` | `#2E6AA6` | `#8FBCEB` | A key excerpt in Sift |
| `--pdf` | `#D7261E` | `#D21C12` | A PDF, Acrobat's red |
| `--part-sift` | `#8F2C7A` | `#B297A8` | Sift's mark and its chosen tab's rule, never a judgement |
| `--part-distil` | `#27539C` | `#7AA0DD` | Idiograph's mark and its chosen tab's rule, never a judgement |
| `--part-trace` | `#3A5A62` | `#55AAC0` | Trace's mark and its chosen tab's rule, never a judgement |
| `--rest` | `0 1px 2px rgba(31,27,22,.06)` | `0 1px 2px rgba(0,0,0,.4)` | A card at rest on the PETs canvas, a tip |
| `--lift-low` | `0 6px 18px rgba(31,27,22,.10)` | `0 6px 18px rgba(0,0,0,.35)` | A card chosen on the canvas |
| `--lift` | `0 1px 2px rgba(31,27,22,.05), 0 8px 28px rgba(31,27,22,.07)` | `0 1px 2px rgba(0,0,0,.4), 0 10px 30px rgba(0,0,0,.35)` | A dialog, a popover, a menu, a toast |
| `--lift-high` | `0 2px 4px rgba(31,27,22,.08), 0 14px 36px rgba(31,27,22,.18)` | `0 2px 4px rgba(0,0,0,.45), 0 16px 40px rgba(0,0,0,.5)` | What is picked up on the canvas |

### In either theme

| Token | Value | What for |
|---|---|---|
| `--focus` | `0 0 0 3px var(--crux)` | The focus ring, the solid crux, 3 to 1 or more on paper, card and sunk paper in both themes (WCAG 1.4.11, 8 November) |
| `--focus-small` | `0 0 0 2px var(--crux)` | The focus ring on a small control |
| `--tick-wash` | `color-mix(in srgb, var(--ink) 7%, transparent)` | The wash under a tick's row |
| `--sf-reject` | `var(--danger)` | The old name of `--danger`, until its last use goes |
| `--sf-excerpt` | `var(--excerpt)` | The old name of `--excerpt` |
| `--sf-pdf` | `var(--pdf)` | The old name of `--pdf` |
| `--crux-excel` | `#F79646` | The crux orange as Excel draws it, for the confetti |
| `--es-tint1` | `#3FBEFF` | Statement 2's wash in the transcript, Blue's hue at the lightness and strength of Excel's orange (18 October) |
| `--es-tint2` | `#EF89CF` | Statement 3's wash, Plum's hue so (18 October) |
| `--es-tint3` | `#CEB020` | Statement 4's wash, Brown's hue so (18 October) |
| `--es-tint4` | `#A5A7FF` | Statement 5's wash, Indigo's hue so (18 October) |
| `--es-tint5` | `#00CDB1` | Statement 6's wash, Teal's hue so (18 October) |
| `--on-pdf` | `#FFFFFF` | The word on a PDF's pill |
| `--rest-control` | `0 1px 2px rgba(0,0,0,.15)` | A small control at rest, the range filter's knobs |
| `--serif` | `"Iowan Old Style", "Charter", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif` | The transcript, names and titles |
| `--sans` | `"Avenir Next", "Avenir", "Gill Sans", "Gill Sans MT", "Segoe UI", system-ui, sans-serif` | Everything else |
| `--mono` | `"SF Mono", ui-monospace, Menlo, Consolas, monospace` | Timecodes, keys and counts |
| `--hand` | `"Bradley Hand", "Noteworthy", "Segoe Print", "Segoe Script", "Comic Sans MS", cursive` | A sticky note's words |
| `--fs-label` | `10.5px` | A tracked capital label |
| `--fs-small` | `11.5px` | Small print |
| `--fs-ui` | `12.5px` | Controls and bars |
| `--fs-body` | `13.5px` | Cards and panels |
| `--fs-read` | `15px` | Reading |
| `--fs-field` | `17px` | A field he writes in |
| `--fs-name` | `19px` | A name |
| `--fs-title` | `24px` | A card's title |
| `--fs-lede` | `27px` | The first screen's line |
| `--label-track` | `.12em` | A capital label's tracking |
| `--sp-1` | `2px` | Spacing, the smallest step |
| `--sp-2` | `4px` | Spacing |
| `--sp-3` | `6px` | Spacing |
| `--sp-4` | `8px` | Spacing |
| `--sp-5` | `10px` | Spacing |
| `--sp-6` | `12px` | Spacing |
| `--sp-7` | `14px` | Spacing |
| `--sp-8` | `16px` | Spacing |
| `--sp-9` | `18px` | Spacing |
| `--sp-10` | `22px` | Spacing |
| `--sp-11` | `26px` | Spacing |
| `--sp-12` | `34px` | Spacing, the largest step |
| `--r-tag` | `2px` | A tag's corners |
| `--r-control` | `3px` | A button's or a field's |
| `--r-box` | `4px` | A box's or a row's |
| `--r-card` | `5px` | A card's |
| `--r-pill` | `10px` | A pill's |
| `--r-round` | `50%` | A dot |
| `--quick` | `.16s` | A transition, off under reduced motion |
| `--ease` | `cubic-bezier(.2,.7,.3,1)` | A rise, off under reduced motion |
| `--z-bar` | `30` | The title bar |
| `--z-find` | `40` | The find and the tips over the bar |
| `--z-overlay` | `60` | An overlay and its card |
| `--z-confetti` | `70` | The confetti |
| `--z-toast` | `80` | The line at the foot |
| `--z-gone` | `200` | Restarting, over everything |
| `--gutter` | `16px` | The page's side gutter |
| `--band` | `0px` | The research question band's height, measured by the page |

The type and spacing scales stand where today's sizes cluster. A rule takes its nearest step when
it is next touched for its own sake, never in a sweep, since a size moved is a layout moved. Two
counts may only fall, the distinct font sizes and the distinct radii across the stylesheets, and a
builder who brings one onto the scale lowers its number in area 147.

### Palettes

The categorical sets stay beside the part that reads them, in light and dark as the tokens are:
the eight PETs tints `--th-h0` to `--th-h7`, `--th-grey`, the sticky note's four papers, its ink,
shadow and edge, and the cases' eight colours on the GETs board in `themes.css`, and Sift's grounds' and excerpts' washes, the databases' colours
`--db-*` and the map's `--sf-map-*` in `sift.css`. None of them is the crux orange, and no database
is red.

| Palette | Light | Dark | What for |
|---|---|---|---|
| The cases' colours, `--th-case0` to `--th-case7` (16 October) | `#0D6ABB` `#706D06` `#774E6D` `#5B4315` `#2841B9` `#02544C` `#851286` `#616491` | `#7DD0FA` `#ABBD3E` `#D3A9C4` `#A08237` `#5B8BFF` `#019D7E` `#BD65BE` `#838593` | A participant on the GETs board, Blue, Olive, Plum, Brown, Indigo, Teal, Purple and Slate, a case's place in case order by default, through `.case-0` to `.case-7`, which set `--case`, and on the statements screen, which holds one participant, statements 2 to 6 by their place in the passage's list, Blue, Plum, Brown, Indigo and Teal, the board's order with Olive left out since it reads as the orange under colour blindness, through `[data-es-colour="1"]` to `"5"`, which set `--es` and the wash's tint, statement 1 keeping the crux orange through `[data-es-colour="0"]` and a seventh starting the round again (18 October) |

Each of the cases' colours is a badge's ground under a letter in the card's colour, so it reads at 4.5
to 1 or more on paper, card and sunk paper. Any two stand apart by `CASE_APART`, light and dark each their own
since 16 October, later, when the dark set, apart by the first rules, read as one pale lilac in Blue,
Indigo, Purple and Slate: in light a colour distance of 14.9 or more, 7.5 or more under protanopia,
deuteranopia and tritanopia and 1.45 or more as small marks, in dark 20, 10.5 and 2.65. A small mark's
distance is in noticeable differences for a mark a quarter of a degree across, a badge's disc on the
canvas at 59%, after Stone, Szafir and Setlur (2014), where hue counts for less beside lightness. Each
stands 15 or more from every judgement's colour, the crux orange among them, and none takes a hue from
red to amber. Area 147 holds them to it through `case_palette_problems`, and area 157 holds a GET's
title on the GETs board in the ink, 20 or more from every case's colour, so a GET never reads as a
participant's, and with it the left edge of each card in a GET, the stripe of a GET's head in the
Table and the underline of its title in the audit trail (17 October).

## Rules, and what holds each

- **The sparkles mark AI controls and nothing else**, drawn in the button icon's box and stroke.
  Areas 104, 109, 110 and 118 fail on a sparkle anywhere else.
- **Every AI part follows the AI features switch, off on a new install.** Markup carries `data-ai`,
  and `body.ai-off [data-ai]` hides it. Scripts ask `aiOn` and `thAiOn()`.
- **Every checkbox and radio ticks from its whole row**, inside its `<label>` or in a row marked
  `data-tick-row`. Area 127, `tick_problems`, fails on a tick outside a label.
- **Every Remove and Delete is red with a bin**, `button.btn-remove`, `--danger` in both themes.
- **A card that applies its changes as you go ends with Done at its foot right**, in
  `.card-actions.card-done`. A card with its own Save or confirm never has one.
- **Each colour has one meaning**, the tokens' table above, and orange means crux, and in the
  transcript a quote, the crux of a statement, since Highlight went on 16 October, statement 1's since
  18 October, when every other statement's quotes took that statement's own colour. Theme tints,
  sticky papers, the playhead, a pending quote, a passage's done bar, the case's line and the round's
  short bar, the minimap, the current passage's name and rule, the round
  that holds it and the margin's hovers (17 October) and the ticks stay off it, and a warning is amber.
  A card's kicker, Participant on Rename and Audit trail among them, is a label in `--ink-soft` and
  stays off it too, as does a line that only says a row holds nothing (17 October, later), and the time
  on Back to where I was, a timecode on a button in the faint ink as every other (17 October, later). So do the counts,
  the statements left on PETs and GETs and the place in the round on Experiential statements, in the ink with
  their word fainter, Sift's Year chart and its slider, the bars in range and the stretch between the knobs in the
  soft ink and the knobs ringed in the ink, the funnel of Filters, Active on a search run in the ink on a firm
  border, a database's word while it runs in the ink, and a nudge's mark, in the amber (17 October, later). On paper a
  case not complete, with no PETs yet or changed since it came in, and an item no longer in its file, stand
  in the light amber, `PRINT_AMBER` in `themes_print.py`, as the GETs table on screen sets them, where the
  GETs print set them in an orange brown no token carries.
  So do, since 17 October, later, where each stood in it: a case's tag that its workbook is still to make, in
  the soft ink on its own border, today among the days, outlined in the ink, the dot by Exploratory notes folded,
  in the soft ink, the place in the round's tick, from the faint ink up to the ink, the player's play button and
  track and the canvas's play button under the pointer, in the ink as any control, the canvas's play button while
  it plays, in the accent as the playhead, and in Sift a sorted column's arrow, the bar that marks where a column
  goes and the flow's stage under way, in the ink, the last by `!important` over Mermaid's own rule, which names
  the drawing by its id and kept the firm rule's colour on screen until 18 October, and the place a file drops
  under the pointer, the sunk paper.
  The filled button keeps it as the app's one accent, Skip and Next among them, its paper word 5 to 1
  on it in light and its dark paper word 8.3 to 1 in dark.
  A case's colour on the GETs board says whose a card is and nothing else, along a card's top edge,
  where the GET's edge in the ink keeps the left and its tint the wash, and in its badge, never a
  judgement. On the statements screen, which holds one participant, the same colours say which
  statement a quote's mark, a number's dot and a quote's stripe belong to, statements 2 to 6 by
  their place in the passage's list, statement 1 keeping the crux orange (18 October, Adam's ruling),
  each wash its colour's bright tint at the lightness and strength of Excel's orange, as statement 1's
  wash is Excel's orange under the deeper crux rule.
  Each mark's rule reads at 4.5 to 1 or more on paper and sunk paper, each dot's number in the card's
  paper at 4.7 or more, and the words on every statement's wash at least as well as on the crux's in
  the same theme. Words two statements share keep the first's wash and take both rules, the second's
  under the first's past a gap of the passage's ground.
- **Three appearances**, Light, Dark and Same as this computer, on `html[data-theme]`, the last
  following macOS with no reload, chosen under Settings, General and never on a bar. Area 147 holds
  the two dark blocks equal.
- **Small type reads.** The inks, the meanings that colour words and the parts' colours reach 4.5 to
  1 or more on paper, card and sunk paper in both themes, and area 147 computes it from `tokens.css`.
  The light crux is Excel's orange taken down until it does, and the dark crux is Excel's own,
  F79646, which stands clear of the amber, so the selected row's bar never reads as a Maybe.
  A key beside a decision's word stands in the word's own colour, never faded, and Maybe's wash under
  the pointer is a tenth of its amber where the others' are 16 per cent, so its word keeps 4.5 to 1. A
  placeholder is in the faint ink and a tick takes a token's colour by `accent-color`, never the browser's
  own grey or blue, which the sweep of 17 October found on fields in Settings, New project and Set
  columns and on ticks in Search strategy and Set columns. Find and replace's ticks and the reference page's
  take the ink, every row of switches with them wherever it stands, and a find field's placeholder the faint
  ink, where the ticks stood in the browser's own blue (17 October). The print views, a printed page being
  always light, set their small print in the light faint ink, `PRINT_FAINT` in `themes_print.py`, 5.3 to 1
  on their white paper, and on the audit trail's card a box's small print is in the soft ink, which keeps
  4.5 to 1 on the box's wash in dark. A key hint on a button stands in the faint ink, or in
  the colour a rule names for it, a decision's key in its word's own (17 October, later), never an opacity.
  An unlit rating star is an outline in the faint ink, past the 3 to 1 a mark takes, beside a lit one's amber
  fill, and every tick is in the ink, the study's cases in Settings and Mark as registered's radios among them,
  and Sift's filters and its Zotero card since 17 October, later, where they kept the crux as Sift's own accent.
  A stage of PRISMA's flow not yet reached is dashed, its words in the ink as every stage's are, never faded,
  where at half their opacity they read at 3.3 to 1 (17 October, later).
  Small type is measured in the shots too, the strongest pixel of its strokes against its ground, since
  the faint ink's thin strokes read under 4.5 to 1 there at 11px: H after Key excerpts stands in the soft
  ink at the decisions' keys' 500, and Discard under the bin in the soft ink at rest (17 October, later).
  Every radio is the app's own, a ring in the faint ink with nothing inside while unchosen, and chosen the
  ring and a dot in the ink, as every tick is, so an unchosen one is plainly empty in both themes, where the
  browser's own filled the dark's with grey (17 October, later).
  Every checkbox is the app's own too since 1 November 2026 (loose01), a square in the faint ink, and ticked
  the square filled with the ink and a check in the card's colour cut into it, the same in Chrome, the Mac's
  window at every text size and dark, where the Mac's engine drew the system's pale grey box whatever the
  `accent-color`.
  On a card in a PET or a GET the timecode and the count of statements stand in the soft ink, which keeps
  4.5 to 1 on every tint's wash, a PET's count on its frame takes its theme's own tint 65 per cent to the
  ink's 35, and the statements margin's interviewer and a round to do stand in the faint ink at full
  strength, told apart by weight and by their word, never an opacity (17 October, later).
  In a passage set in the faint ink, every one but the current, a quote's words take the soft ink, 6.4 to 1 or
  more on its wash and 5.3 on its lit wash, where the faint ink read at 3.8 to 1 in dark, and a passage under the
  pointer takes the sunk paper, on which the faint time and the row's menu read at 4.5 or more, where a tint of
  the ink took them to 4.4 (17 October, later).
- **One focus ring.** Every control takes the app's ring from the keyboard, `--focus`, or `--focus-small`
  on a small one, a bar's tools, its switchers and its steps, every tick, every radio and every field
  among them, never the browser's own blue and never none (17 October, later, where a bar tool given the
  focus back from its menu and a tick drew the blue and Rename's field showed none). Area 166 holds every
  button on a bar to it. A card's close in its corner takes `--focus-small` too, where the guidance's
  close drew the blue (18 October).
- **Keys in capitals**, as keyboards and the Mac's and Windows' menus print them (Adam, 17 October, later):
  G, Q, Cmd + Z, on every shortcuts card, in every tooltip, "Group (G)", and in every line, "press Q.", where
  the statements screen and PETs wrote theirs in lowercase beside Sift's and Trace's capitals. `keyName`
  writes a letter key it is given in its capital, and every key written by hand is written so too. Area 171
  fails on a letter key in lowercase in the app's own words or in the manual. Every part takes a letter key in
  either case, so Caps Lock never stops one, the statements screen's since 18 October, where Q did nothing with
  it on.
- **A part's colour is its mark's and its chosen tab's**, and never a judgement, a decision or a
  wash. The three carry one weight, each within a tenth of 7 to 1 on paper in both themes, at
  the board's hues within six degrees of OKLCH, apart from each other by a colour distance of 12 or more and
  of 6 or more under protanopia, deuteranopia and tritanopia, and 15 or more from every judgement's
  colour. At one weight two parts are told apart under colour blindness by how much colour each
  carries, so in light Sift carries more and Trace less, and in dark Trace more and Sift less.
  Area 148, `identity`, holds the parts, the marks and the icon.
- **The parts stand in the order a study does them**, Sift, Idiograph and Trace, the literature review,
  the analysis, then checking the references, wherever the three stand together: the first screen's
  sections, Settings' list, which its arrow keys walk in the same order, and the reference page's
  colours, marks, title bars and tabs, where Idiograph's name and one of its tabs stand between Sift's
  and Trace's as in Settings. Their ids, keys and routes keep their old names. Area 149,
  `part_order`, holds the order.
- **No font downloaded, none shipped**, and reduced motion turns every animation and transition off.
- **One title bar**, set out in The title bar below. The mark stands 7px from the name at every
  width whatever the bar's gap, which is `--rail-gap` on `.rail`, and the name follows it with its
  ellipsis, never the part's word. Below 760px, where the steps of Sift and its searches wrap under
  their bars, those bars and Trace's keep their first row 11px from the top, where a bar of one row
  centres it, as the PETs and GETs bars do where their names take a row of their own (17 October, later).
  Idiograph's steps never take a row of their own, on PETs and GETs standing on the first row with the way
  back where the names take the second (18 October).
- **A filled button that cannot be pressed loses its fill and its outline**, its word in the faint ink and
  dimmed, in light and dark alike, so it never reads as ready or as a second Cancel (6 November 2026, from
  Share a copy's look of 26 October, when Add boards looked ready in the dark theme).
- **A link to a page outside the app** is underlined in the accent and goes to the ink under the pointer, a
  record's links in Sift, the registries' and the databases' sites on Search strategy and Trace's DOI and Show in
  Zotero alike, never the crux orange or the browser's blue (17 October, later).
- **A word wraps whole, never through a letter.** A column too narrow for its longest word takes the
  room it needs from the others, and where the columns together need more than the window, the table
  scrolls sideways in its own box under its title, as the audit trail does on paper and in its card,
  whose five columns are one grid, `.tr-wide`, with every row a subgrid of it (17 October, later).
  Paper, A4 landscape, never scrolls. The trail on a narrow screen keeps its five columns about 720px together, as
  the GETs table does, and scrolls in its box, where they squeezed to a word or two a line (17 October, later).
- **On paper a quote stands in single curly quotation marks**, once, whatever marks the workbook keeps, in
  every print view, the table of PETs, the GETs table and the trail, as the book's tables and the Word document
  set it (17 October, later). The app's own words on screen keep the straight marks.
- **No strip of cut words beside a card or a sheet.** One that stands over a panel takes the whole
  width where the strip beside it would be narrow, the guidance sheet below 520px and Find and replace,
  at the window's foot, below 700px (17 October, later), and Search, under the bar, below 700px too. A
  card that stands over a screen's words at any width lays a wash of the paper over the rest of the
  screen under the bar, as the guidance sheet does where the columns stack and Search does whenever it
  is open, so a word cut beside it, under it or at its foot reads as under it (17 October, after the
  screenshot check). A box of rows shows whole rows, never one cut through its letters, and says when
  more wait, as Search's filters do below 700px with More.
- **A drag selects words alone.** A drag across the transcript selects the passages' words, in their wash, and
  nothing round them: the title bar, the research question, a round's marker, the margin's names, times and menus
  and the notes beside the words take no selection, where the margin and the notes took the browser's own blue
  (18 October). A field among them keeps its own.
- **The statements screen is the book's three columns** (17 October, Adam's decision, Smith, Flowers and Larkin
  2022, Box 5.4): experiential statements, the transcript and exploratory notes side by side, each passage a row
  across the three, in the book's order on a new install and in any of the six by his hand, every part of a row
  in its own column whatever the order, the margin always at the left of the words. Each column narrows by its own
  least width, the statements 210 pixels, the transcript 300 and the notes 160, down to 801px, the notes go under the
  words up to 800px while the statements stay a column, and only at 600px and below, a phone or a narrow window
  at Text size Large (560px until 30 October), does a passage stack. A cell grows with what it holds and never scrolls inside, the notes field starting about five lines tall
  (18 October, two until then), and the current passage's card is the one place he writes statements, where until
  then a panel at the right held the fields. Area 172 holds the columns. Since 18 October, Adam's drawing of
  four layouts and one menu, Columns shows or hides the statements and the notes, the transcript always shown
  and hidden never deleted, a hidden column hidden at every width, and stacks the notes under the statements
  in one column beside the transcript above 800px, the current passage's two halves each scrolling and the
  divider between them his to move, where until then its menu listed the six orders, the order a grip's
  alone. The transcript alone keeps a reading measure in the middle of the screen. Area 186 holds them.
- **A failure is said in plain words**: which database or service, what happened, did not answer,
  refused the key, refused the request, asked for a break from requests or sent something it could not
  read, and the status in brackets, "PubMed did not answer (HTTP 503).", never an address, a query or
  what a server's answer held, which a run's own log keeps (17 October, later). It is said in one tone
  everywhere, the amber: a card's failure line, a database that failed under its run's row, what stands in
  the way of a plan, under Register and beside its cause, and a line beside a control that says it failed,
  `.said-failed`, as Check under a database's key in Settings does, where Sift's stood in Exclude's red and
  Settings' in the small print's grey (17 October, later). Every line beside a control in Settings takes it when
  it says something failed, Zotero's, the key's, the models', the bench's, the exports' and the projects', as do the
  Zotero card's, the second screener's, the AI's note on Experiential statements, the canvas's note, the trail's,
  a save that failed, the boards menu's line and an AI title's or review's line, where the canvas's stood in the
  crux orange (17 October, later). A restart to finish an update is no failure and stays in the small print.
- **Words**: plain and as untechnical as possible, no helper lines for minor states, no nudges to
  continue work, a break and never a stop, no em dashes or semicolons.

## The title bar

Since 26 October 2026 (Adam's option C of the bars) every title bar reads: the app's lockup, `.bar-brand`, Home, its lockup drawn in from Home's own by `barLockups` in shell.js and its mark alone where the stages take a row of their own (Sift at 760px and below, Idiograph below the app's narrowest window, 720px), then the stages as tabs, `.ds-tabs` in Idiograph and `.sf-steps` drawn as tabs in Sift, every tab alike and always as wide as its name in bold, the words over a hidden bold copy of themselves, `.tab-w` with `data-bold`, so the tab in front, in bold, moves none (6 November 2026), then the screen's own tools, a rule, `.bar-tools-sep`, and Search, Feedback and Settings last. `barFit` takes the tools' words away first where the bar runs short, `.bar-fit-words`, then a tab's long name, `.bar-fit-tabs`. The band under it opens with the path, `.ds-path`: since option D (6 November 2026) no Home, the lockup being Home, but the project's name, `.ds-proj`, a button in the participant chooser's outline with its chevron, no link, its name cut at 22em with its ellipsis and the chevron kept, opening the project's card menu from Home, in Idiograph, Sift and Trace alike (the family's `projectMenuHtml` and `bandMenuOpen`), then the participant's and timepoint's choosers, then `.ds-path-rule` and the question, `.band-unasked` where there is none. The way back below is history: the path took its place. The sidebars' buttons stand at the two ends of `#th-dock`, the board between, its name over its save state in `.th-boardname`, and Canvas and Table after them. The statements screen has its own toolbar under its band, `#es-dock`, the boards' `.th-dock` and `.th-palette` with the boards' code, the same words giving way by the same steps.

Since 19 October (Adam's choice A) the PETs and GETs bars hold no counts and none of the canvas's own tools: the counts and Shortcuts stand on the status bar along the canvas's foot, `#th-status`, and Sticky note, Group, Undo and Redo in the palette floating at its side, `.th-palette`, each in Components. Since 21 October the statements screen's bar follows: the passage's place and Shortcuts stand on its status bar under the player, `#es-status`, with the statements' count, Minimap and Quotes.

Every screen's head is one title bar (16 October, after a tester found Appearance on some screens
and not others), and every bar, the first screen's head, Experiential statements, PETs, GETs, Sift,
its searches and Trace, holds its parts in one order from left to right.

1. On GETs, Cases, the toggle of the sidebar at the canvas's left, at the bar's left end over it.
2. The way back, the part's mark and the name, then the part's steps where it has them, then where the
   screen stands, its sheet and passage or its board. Idiograph's steps, Experiential statements, PETs and
   GETs, stand after the name on each of its three bars in the book's order, one row as Sift's stand
   after its review's name, the screen in front of him marked and the others links to this case's
   screens, both ways, as the book's to-ing and fro-ing goes (18 October, Adam's decision on a tester's
   feedback, Topic A of 17 October). They keep their words at every width, the rest of the bar giving
   way first, and below 1600px Experiential statements reads ES, its whole name in its tooltip and to a
   screen reader. On Experiential statements, the fullest bar, the mark's long words and the round's go
   below 1440px, the shortcuts and the sheet's label below 760px and View below 480px, each still reached
   from its key, its chevron or Settings, so the case name keeps a letter or more. A step goes to its screen for this case, and where the way back goes there already the
   step is the way back, so the screen comes back as he left it. Every bar's way back keeps that one
   rule: the arrow alone, its tooltip naming where it goes, the case list or the screen it was opened
   from, "Back to PETs", since the steps name every screen of Idiograph beside it (18 October, where until
   then the way back named the screen it went back to beside its arrow unless the bar had a tool of that
   name in view, "← PETs" on GETs opened from a case's PETs). Being a place and no tool, the way back on
   PETs and GETs takes no tool's box, at rest or under the pointer, its arrow going to the ink under the
   pointer and the focus ring marking it from the keyboard (17 October).
   The name gives way first, to its first letter and an ellipsis and never through a letter, its
   whole name in its tooltip, and a board's counts keep their width, never cut, dropping the
   discarded where the bar runs short and then going (17 October), and above 740px, where they would go
   with every name whole, the bar takes its two rows instead, so they show (18 October). At any width where a name on the
   PETs or GETs bar is still cut once the counts have gone, the bar takes two rows, the way back, the steps,
   the counts and the tools on the first and the mark, the names and the board on a row of their own under them, so
   each reads whole at its own size, never smaller (17 October, later), and keeps one row wherever everything fits.
   The two bars take one measure. On the second row the names share what the row leaves, each up to its
   whole width, and one still too long there gives way to its ellipsis rather than a third row.
3. After the space, the screen's own tools: what it alone does first, View, its menu ending with
   Minimap, then Guidance, which opens the guidance's sheet (16 October), New sticky note (18 October),
   Group and Undo, then what writes or sends, Export, then the rest, Second screener and the PDF. PETs
   stood among them as the next step until Idiograph's steps took its place on 18 October.
4. The tools every bar ends with, always in this order: Search where the screen has one, Shortcuts
   where it has keys, Send feedback, once the build carries the collector's address, and Settings.
   Search took Find's place on 17 October, on Experiential statements, PETs, GETs and a project's page,
   and Find and replace stays on its key and on Replace in the transcript. Sift's bar, Search strategy's,
   Trace's and the home screen's picker took Search on 18 October, before Shortcuts where a bar has them.
5. On PETs and GETs, Inspector, the toggle of the sidebar at the canvas's right, at the bar's right
   end over it.

A sidebar's toggle carries the standard panel icon, its part filled on its own side, and its one
name, Cases or Inspector, as its word, in its tooltip and in the manual alike. Each tool is an icon
and its word, the words shown from 1280px, and a tool with a key names it in its tooltip, "Group
(G)". On PETs and GETs the board keeps its rule before it at every width, so "PETs" never runs into the
board's name as one phrase (17 October, later). Appearance is a setting, under Settings, General, and never on a bar. Area 155,
`top_bar_problems`, fails on a bar that breaks the order, leaves out Send feedback or Settings,
or carries Appearance.

Three colours stand outside the tokens, each in area 147's allowed list with its reason: the black
of the transcript's mask in `style.css`, an alpha mask and never a colour on screen, `SF_MAP_PAPER`
in `sift.js`, since a saved map is always light, and the sheet of `thCanvasPage` in `themes.js`,
since the canvas's print page is always light.

## Marks

Idiograph's mark is an orange dot between two square brackets: the participant's experience held
where the researcher's hand enters a quotation, and phenomenology's bracketing. Each part has a mark
in the same square stroke, Sift a tray that keeps one record and lets one through, Idiograph three
statements gathered into one theme, and Trace a claim's line rising into the citation that holds its
source. They are symbols on a 24 grid in `family/static/marks.svg`, `#idiograph`, `#sift`, `#distil` and
`#trace`, drawn in `currentColor` and called with `<use href="/marks.svg#distil">` inside an
`svg.mark`, with the part's class, `.part-sift`, `.part-distil` or `.part-trace`, for its colour.
The 24 grid's stroke of 2 falls between pixels at 16, 18 and 20, so each part's mark is drawn again for
those sizes, `#distil-16`, `#distil-18` and `#distil-20` and so on, every edge on a whole pixel. At 16
and 18 each line is one pixel and each record or citation two. At 20 each is two, since a line of one
pixel read faint beside the home screen's section names.
Idiograph's dot is `--mark-dot`, the launch film's orange (22 October), and Sift's record and Trace's citation
stay `--crux`. A mark travels with its part's name, so colour is never the only cue,
and it carries `aria-hidden` beside the name.

| Where | Mark | Size |
|---|---|---|
| The first screen's head | The lockup, Idiograph's mark and the name in tracked capitals drawn as paths in `page.html` | 24px high, 32px in the Preview Edition |
| A part's section on the first screen | The part's 20 pixel drawing, before its name | 20px |
| A title bar | The part's 18 pixel drawing, after the way back and 7px before the case or project name, on Experiential statements, PETs, GETs, Sift, its searches and Trace | 18px at every width |
| Settings | The 16 pixel drawings, Sift's in its tab, Idiograph's beside its name over its three tabs and before its first tab where the tabs make a row, Trace's in its tab, a chosen part tab's rule in the part's colour | 16px |
| The browser tab | `apps/idiograph/static/favicon.svg`, the mark drawn for 16 pixels on its tile, dark under a dark system, and `/favicon.png`, 32 pixels, drawn by the server | 16 and 32 |
| The Mac and Windows icons | `make_app.draw_icon`, the 1024 drawing, and every size up to 32 from the 16 pixel drawing | 16 to 1024 |

The icon's drawing carries its own colours, the paper tile, the ink and the crux orange of the design
board, in `make_app.py`, since an icon is an image and reads no token. Idiograph's `favicon.svg` has
the mark's own dot, `#F26B1D`, in both themes since 22 October, while the Mac and Windows icons' PNGs
keep the design board's orange.

### Clear space

The lockup always has at least its mark's height clear above it and to its left, measured above from the bottom
of the window's title bar (the page's top in the app's window, where the title bar is the system's own), and
nothing else stands inside that space, no tool, rule, edge or word. The mark's height scales with the lockup, so
it is the lockup's own height, whatever size the lockup is drawn at: the space grows and shrinks with it and is
never a fixed number of pixels. A lockup is never used without it (Adam, 6 November 2026, when Home's lockup
stood 14px under the title bar and read as crowded: the logo is never used without the appropriate height
above it).

| Place | Lockup, its mark's height | Clear space | Measured from |
|---|---|---|---|
| Home's head, Idiograph's Preview Edition | `.wordmark`, 32px | 32px above, its top at least 32px under the page's top, and 32px at its left from 560px of page | The bottom of the title bar, the page's top |
| Home's head, Sift, Trace and a plain Idiograph | `.wordmark`, 24px | 24px above, and the page's 32px margin at its left | The same |
| A project's page's head | The same head, `.lib-head`, so the same lockup and the same space | As Home's | The same |
| About | `.about-lockup`, 28px | 35px above and to its left, the card's 34px of padding and its 1px edge, and 29px on a phone's narrow card, whose padding About raises to 28px since the other cards' 26px and 18px left it short | The card's edge, since the card is a dialog standing over the page |
| The bars | `.bar-brand svg.lockup`, 15px | 15px above, exactly its mark's height, by the bar's own rule below | The bottom of the title bar, the bar's top |

On Home the head's top row stands the mark's height less the wordmark's 3px under the page's top, `--mark-h` in
`.lib-head` (24px, and 32px while the Preview Edition's lockup is drawn at 32), and the tools stand with it, level
with the lockup as the head set them. The Preview Edition's stamp hangs under the lockup and is no part of the
space above. To the left, the head and the projects under it keep a margin of 32px at each side from 560px of page (`--home-edge`
on `#library`, Adam, 6 November 2026: margin 32 at every width), which holds the app's smallest window, 720px, at
Large (125%) too, where it is 576px of page. So Home's lockup, the preview box, the title and Projects, and a
project page's way back and name, share one left edge 32px from the window's edge, the Preview Edition's mark
height and more than the 24px lockups need, and a wide window leaves more, the column staying 1048px wide.
Below 560px of page, a browser's phone-width tab, the page's 16px gutter stays and the space to the left is short
of the mark's height, as the app has no window so narrow.

The bar's lockup is the one place the space cannot be a free choice. The bar is 46px high with its rule below
and its lockup, 15px, stands centred in it, so it has 15px above it, exactly its mark's height with no room to
spare, and 16px at its left from the bar's gutter. The bar's own rule is therefore: the lockup is centred, and no
lockup in a bar is taller than 15px, since a taller one has less than its own height above it and a shorter bar
has less room for it. Where the stages take a row of their own, the bar shows the mark alone (Sift at 760px and
below), 18px in the first 46px row and 14px under the page's top. That is a mark and not a lockup, so the rule is
not claimed for it. Area 333 measures every place in the table, Home's head in each app and in the Preview Edition,
above the lockup at 1280, 1050, 720, the first and last again at Large (125%), and 360, and to its left at all but
360, the bar's and About's too.

## Components

| Component | Class | When | Not when | Words |
|---|---|---|---|---|
| Filled button | `button.primary` | The one next step on a screen or a card | A second choice beside it | Done, Next, Save |
| Outlined button | `button.ghost`, `button.ghost.small` | Every other action | The screen's one next step | A verb |
| Remove and Delete | `button.btn-remove` | Anything that takes something away | Undo, which puts back, and a pair's Remove on the statement card, a bin alone in the soft ink since 18 October (see Statement card) | Remove, Delete |
| Quiet text button | `.quiet` | A small action at the edge | A main action | A verb |
| Bar tool | `.rail-btn.bar-tool` with `.bar-word` | A title bar's tools, in the order of The title bar, a typed glyph, Shortcuts' `?`, at the drawn icons' 15px and 600 (17 October) | Inside a card | Its word on the bar, its key in its tooltip |
| AI button | a `button.ghost.small` with the sparkles and `data-ai` | Asking the AI | Anything the AI does not do | AI and a verb |
| Decision buttons | `.sf-act` with `--c` | Include, Maybe, Exclude, and Trace's judgements | Any other choice | The decision's word |
| Tag | `.tag`, `.raw`, `.locked`, `.demo` | A word about a whole thing | A count | One word |
| Pill | `.sf-pill` by `data-decision`, `.sf-pdfpill` | A decision or a PDF in a row | A button | The decision's word |
| Case badge | `.gt-badge` with `.case-0` to `.case-7`, `.gt-swatch` the one that is a button | A participant's initial in its case's colour, before a GETs card's kicker and a name in the GET table and the trail, and the swatch on a case's row of the Cases panel that opens its colour choice, whose rows carry it too | Alone, with no name beside it on the page, or its letter under 9px on the screen: on a card it grows by `--gt-up` as the canvas zooms out and below 54% keeps its disc without the letter | The initial, two letters where two cases share one, `aria-hidden` beside the name |
| Card button | `.home-card`, `.sf-row-open` | A project or a review to open | A list inside a card | Its name |
| Dialog | `.overlay` and `.card`, `.card-close`, `.card-actions` | A task that needs the screen | A note that needs no answer | A kicker, a title, Done |
| Menu | `.row-menu` with ghost buttons and `.row-menu-rule` | A row's or a bar's choices | One choice | Short names |
| Status bar | `#th-status`, the `.th-zoomer` with `.th-status-counts` of `.th-stat`, each a `.th-stat-n`, and `#th-smenu` | Along the PETs and GETs canvas's foot on `--card` under `--rule-firm`, the counts at its left in `--ink-soft`, their numbers in `--mono`, the tools at its right, off leaving the floating zoom bar, at 767px and below In PETs and Not placed with the zoom and Fit all (19 October) | Anything to act on | "3 PETs", "12 in PETs", a right click choosing which |
| Palette | `.th-palette` of `.th-pal-btn`, its `.th-palette-grip` and `.th-palette-rule` | A column 40 wide at the canvas's side on `--card` inside `--rule-firm` with `--lift`, icons alone, settling against the nearer side edge, faint while cards are dragged (19 October) | Words, or a tool that is not the canvas's own | The tooltip, "Group (G)" |
| Toast | `.toast` | The line at the foot after an act, 8px over the canvas's zoom bar and bin wherever it would cover them, as at 360 (18 October) | Anything he must answer | One sentence |
| Update line | `.update-line` holding `.update-words` and `.update-acts` | Idiograph's own updates at the head of the home screen, in the window alone and in its flow so it covers no control, on a card's ground: the question asked once, a newer version, its download and an update ready (18 October) | Anything about his work, or a line that only says all is well | One sentence, two plain buttons |
| Foot line | `.foot-line` with `.foot-close` | What's new once after an update, at the toast's place and on its ground, staying until What's new or Close, a toast standing above it (18 October) | A line that goes by itself, or anything he must answer | One sentence, a plain button and Close |
| Tabs | `.settings-nav`, `.th-tab`, `.sf-steps`, Idiograph's `.sf-steps.ds-steps` (18 October) | Panes, sidebar tabs, a review's steps and Idiograph's three, Experiential statements, PETs and GETs, on each of its bars | Two choices | A name each, Idiograph's first ES below 1600px |
| Title bar | `.rail` | The head of every screen | Anywhere else | The screen's name |
| Ticks | a `<label>` round each checkbox or radio | A setting or a filter | An act | What it turns on |
| Field | `.setting input`, `.find-input` | A value he types | A choice from a few | Its name |
| Failure line | `.warn`, and beside the control that failed `.said-failed` (17 October, later) | What went wrong on a card, or beside a control such as Check, in amber | A note that nothing failed | One sentence saying why |
| Mark | `svg.mark` with `.part-sift`, `.part-distil` or `.part-trace` and a `<use>` of `marks.svg` | Beside a part's name | Alone, or as a button's icon | None, the name beside it |
| Lockup | `.wordmark` holding `svg.lockup`, `.about-lockup` and the bars' `.bar-brand svg.lockup` | The first screen's head and the project page's, About, and the bars, each with its clear space, at least its mark's height above it and to its left, measured from the bottom of the window's title bar (Marks, Clear space, 6 November 2026) | Anywhere else, or nearer the title bar than its mark's height | Idiograph, its label |
| Sheet | `aside.guide` with `.guide.open`, its close button a `.card-close.guide-close`, opened by the bar's `#btn-guide` with `aria-expanded` | Reference to hand beside the work, the statements screen's guidance (16 October): over the right of the screen under the title bar, sliding in from the right edge, with no slide under reduced motion, closed by default and kept open or closed in the browser, taking no width from the columns, its close button, Esc and a click outside it closing it, as its tool does, its left edge a card's `--rule-firm` beside `--lift`, the whole width below 520px, and the keyboard in it, never in a field under it, while it is open (17 October), and since 17 October, later, under the research question at every width, over the last of the three columns whole above 1100px where that column is 300 pixels or more, its left edge at the column's, as `measureColumns` measures it into `--guide-w` and `#work.guide-whole`, where until the three columns it lay over the fields' column whole, and elsewhere 340 pixels with the rest of the screen under a wash of the paper, so no strip of cut words stands beside it at any width | Anything he answers or saves, which is a dialog, or a choice, which is a menu | Its heading, Close in its close button's tooltip with Esc |
| Search card | `.search-card` holding `.search-head`, the field, `.search-in` and `.search-mods`, two `.search-mod` ticks as Find and replace's, Whole word, ticked at first, and Match case, not (6 November), `.search-side` with `.search-filters` of `.search-tick` rows under the `.search-group` headings Kind, Case and Sheet, or with Everything Sift, Idiograph, Trace and Project, and `.search-more`, and `.search-list` of `.search-hit`, its words under `.search-mark`, written once in `index.html`, and `.search-lit` on what a result lands on in Sift, a key excerpt in the list under the note | Finding words across Idiograph from the bar's Search or Cmd + F (17 October), and across Sift, Trace and every project from their bars and the home screen's (18 October): under the bar of the screen in front, its top measured into `--search-top`, a wash of the paper over the rest of the screen under the bar while it is open, the kinds found with their counts at its left under Kind, each ticking from its whole row, and Case and Sheet once wider than a case, the results at its right, the one in focus on the sunk paper with the crux's bar at its left and one under the pointer on a fainter ground, Esc and a click outside closing it, the whole width below 700px with the filters over the results as the Kind heading and three whole rows of ticks and More under them while more wait, the filter column at a desk width fading at its foot while more groups wait below, a row brought in by Tab opening them all, a filter's row under the pointer on the results' fainter ground and never the tick's wash a ticked row keeps, the last result in sight fading at the card's foot while more wait, and on a project's page the card under the project's name | A find inside one passage's words, which stays Find and replace | Search, Search in, Whole word, Match case, This case, This project, This Sift project, This Trace project, Everything, Kind, Sift, Idiograph, Trace, Project, More, Fewer, Nothing found |
| Minimap | `.minimap` holding `.minimap-card`, which holds `.minimap-area`, its `.minimap-map` of `.mm-track`, `.mm-done`, `.mm-block`, `.mm-ask`, `.mm-dash` and `.mm-time` and its `.minimap-views` of one `.minimap-view`, then `.minimap-btn` outside the card and `.minimap-tip`, and on PETs and GETs `.th-map` holding `.th-map-area`, its `.th-map-items` of `.tm-frame`, `.tm-sticky` and `.tm-card` and its `.th-map-view`, with `.th-map-btn` at the zoom bar's end | A corner card at the bottom right of the statements screen's transcript, where until 17 October it was a strip down the column from 621px of window, one card of one size, about 135 by 300, whatever the interview's length, its contents scaled to fit like a measuring jug and the map alone in it: the transcript as one narrow column 62 wide, a block in `--ink-faint` at 80% for each of her passages as tall as its words, joined with its neighbours under 4.5 pixels, finer past an hour to 2.5 at three hours with the gaps from 2.1 to 1.6 (18 October), the interviewer's turns a thin mark in `--rule-firm` at 40% of the width between blocks, a 4 pixel track at its left, its outline `--rule-firm`, holding `--good` beside each passage done and nothing beside one not done, the part in view a box in a solid `--ink` line 2px, at least 12 high, the column outside it dimmed by `--dim`, the card's paper at 35% in light and 25% in dark, the line 3 to 1 or more on the card, the blocks and the dimmed blocks and 5px clear of the green (18 October, Adam's choice of A's line with D's dimming from four looks drawn for him, where it was a box in 18% of `--ink` with no edge), and the time at its right in `--ink-faint` dashes, labelled every 5, 15 or 30 minutes by the interview's length, its labels in minutes, 90:00, never hours, and nothing else, no quote, round or current passage. Auto, On or Off in View and in Settings' View, Auto on a new install, showing it as he scrolls or moves to another passage and fading about two seconds after, On keeping it, Off leaving nothing in the corner. Its map button stands outside the card in the corner, a small card of its own on the card's bottom edge, alone while the map does not show. From 1101px of window, where until 17 October the sheet and the fields stood side by side, the card shows as chosen, and at 1100px and below the button alone, which a press or M opens until what he works on comes under it. The blocks and the green 3 to 1 or more on the card, the card giving way to its button, and both going, while the passage being worked on or a field in focus would stand under them, Back to where I was to its left on one bottom edge, or at the column's head over a strip where its words fade out where the column has no room beside it, and a card opened by his press over the words standing on a band where they fade out (16 October, a corner card since 17 October, drawn to Adam's drawing since 17 October, later). On PETs and GETs since 18 October the board's map, Miro's and tldraw's way: a card above the zoom bar at the canvas's bottom right, the bar's width and 160 high, on the same paper, edge, corners and lift, the board fitted to every card on it, a small board as large as a big one across the card (until 18 October never more than a fifth of its size), each card a rectangle in its PET's tint at `--hue-base` however deep it sits, on GETs in its participant's `--case`, one in no PET in `--ink-faint` at 80%, a discarded one left out, each sticky note on its paper, every frame a 1 pixel outline in its tint, and the view a box in a solid `--ink` line 2px with the map outside it dimmed by `--dim` and 8% of `--ink` under the pointer, as the transcript's (until 18 October a box in 14% of `--ink` with a quiet edge at 35%), its whole size where it reaches past the map and cut at the edge (until 18 October held inside it), and where it would reach past every side, as after Fit all, the board and the view fitted together so the box stands whole inside the card (until 18 October the whole card washed with no edge), and the card giving way while a sidebar lies over it below 900px. A click glides the view there, a drag on the box pans, the wheel over it reaches the canvas, and it is drawn at most once a frame. The same Auto, On and Off rule it, Auto showing it on a pan or a zoom and fading two seconds after, its button and M showing or hiding it until pressed again, the button pressed in on `--paper-sunk` inside `--rule-firm` in `--ink` while the map shows as the zoom bar's pointer and hand are, Off leaving neither map nor button, and at 767px of window and below neither | Any other column, or a choice he has to make | Minimap (M) in the button's tooltip, Minimap over Auto, On and Off in View, Minimap (M) on the zoom bar's button too |
| Column headings | `.cols-head` holding a `.col-head` for each column, `data-col` its name, its grip the shared `.pc-grip` and its name a `.field-label.col-name`, then `#cols-pick`, and `#cols-menu`, a `.row-menu.view-menu` of Show over two ticks, Statements and notes over two radio rows and Order over `#cols-book`, a rule between them (18 October), each tick and choice in a `.view-row` label, a choice not offered `.row-off`, where until then six radio rows listed the orders, the book's marked `.cols-book` | The statements screen's three columns (17 October), each heading over its column in the columns' order, the places `--es-col`, `--tx-col` and `--en-col` and the tracks `--cols` that app.js sets on `#work`, the room the transcript's scrollbar takes left at their right (`--sb`), a drag on a grip marking where it goes with a bar in the ink at a heading's edge and `Alt` and an arrow moving it a place, Columns at the right of the last heading, its word alone at every width and the order in its tooltip and its menu (until 18 October the order beside its word where the heading left the room, at 800px alone), its menu covering the last column's width wherever less than half the menu's width of that column would show beside it, the notes' heading gone from 800px down and every heading at a phone's width | A choice of anything but the columns | The columns' names, Experiential statements, Transcript and Exploratory notes, Columns, the columns shown in words, Show, Statements and notes, Side by side, Stacked, notes under statements, Order, Back to the book's order |
| Statement card | `.es-card` holding `#pairs` of `.pair`, each carrying `data-es-colour` by its place (18 October) and a `.pair-num` in a dot of its colour and a `.pair-body` of `.pair-es`, `.wordcount`, `.nudges`, `.pair-qhead` with `.pair-qlabel` alone, `.pair-kq` with a stripe of its colour at its left and `.pair-remove`, a bin with no word at the pair's top right beside the statement's first line in `--ink-soft`, `--danger` with its wash under the pointer and in focus (18 October, where it stood at the Quote label's right as a `btn-remove`), then `#ai-block` and `.es-foot` with Add another, AI suggest and `#btn-commit`, and beside each other passage `.turn-es` of `.es-list` with `.es-go` buttons, `.es-n` in a dot of its statement's colour and `.es-words` | The current passage's statements in its row of the statements column (17 October), on the card's paper with a card's firm edge and corners at rest, growing with its pairs and never scrolling inside, the one filled button at its foot right, and every other passage's statements read-only in the reading face and the soft ink, each numbered, a statement still to write its quote in the faint ink, a click on one going to it | A panel of fields beside the columns, which it replaced | Experiential statement 1 for a screen reader, Quote, Remove this statement, Add another, Skip or Next, Go to this statement |
| Stacked column | `#stack` in `#cols-body`, `.stack-half` `#stack-es` and `#stack-en` with its `.stack-label`, and `#stack-divider`, a `role="separator"` holding `.stack-grip` | Stacked, notes under statements (18 October): the current passage's card above and its notes field below beside the transcript, on the statements' side, each half scrolling on its own, the card's foot kept at its half's foot, the divider a hairline with a short handle, `row-resize`, its handle in the faint ink under the pointer and the app's ring from the keyboard, its place the statements' share | 800px and below, where the notes go under the words, or with a column hidden | Exploratory notes over its half, Drag to move, Divider between statements and notes for a screen reader |

## Adding something

A new colour needs a meaning no token has, a line in each block of `tokens.css` and a row in the
table above, in the same change. A new component goes on the reference page in the same change that
makes it, written once in its template so both panels show it. A part's colour or mark arrives as a
token and a component here, never as a one-off in a part's stylesheet.
