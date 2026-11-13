# Translating Idiograph

Idiograph is in English today, British with an American English overlay. A new language is
welcome. Every translation is read by a person who knows the field before it ships, never by AI alone, since a
wrong word for a term of IPA (Interpretative Phenomenological Analysis) changes what a researcher is told to do.

## What you translate

Every word the app shows is in a catalogue of messages, plain JSON files, one object of key and sentence each:

- `family/static/i18n/en/`: the shared words (`page.json`, `shell.json`, `table.json`,
  `errors.json`, `menus.json`)
- `apps/idiograph/static/i18n/en/`: Idiograph's own (`page_idiograph.json`, `distil.json`, `themes.json`,
  `trajectories.json`, `server.json`, `exports.json`, `page_print.json`)
- the long texts beside their English files: `apps/idiograph/guidance.md`, `apps/idiograph/themes_guidance.md`,
  `docs/whats-new.md`

You can start with the family's files alone. Anything not translated shows in English.

## How

1. Copy each `en` folder to one named for your language's tag, `es` for Spanish, `pt-BR` for Brazilian
   Portuguese, beside it: `family/static/i18n/es/`, `apps/idiograph/static/i18n/es/`.
2. Translate the sentence after each colon. Never change a key, the part before the colon.
3. Keep every slot in braces as it is, `{app}`, `{n}`, `{name}`, and move it to where your language puts it.
   Translate whole sentences, never word by word.
4. A count is written in forms, `{"one": "{n} statement", "other": "{n} statements"}`. Give the forms your
   language needs (`zero`, `one`, `two`, `few`, `many`, `other`, as the Unicode CLDR plural rules list them), and
   always `other`.
5. A key ending `_html` holds markup. Translate the words between the tags and leave the tags as they are.
6. A long text is translated as a whole file named with the tag before its suffix, `guidance.es.md`.
7. Leave out any message you are unsure of. It shows in English until someone translates it.
8. The names of the months and days come from your language's own, as the computer writes them. The order of
   day, month and year, the 12- or 24-hour clock and where commas and points go in a number are not the
   translation's: each person chooses them in Settings, Language and formats.

Never translated: the app's name, what a researcher writes (participants' words, statements, notes, the names of
PETs and GETs), the workbook's column headings, the command line and the agents' guides.

## The terms that need an IPA-literate reader

These name the method's own steps and objects. Use the term your language's IPA literature uses (Smith, Flowers
and Larkin's *Interpretative Phenomenological Analysis*, 2nd edition, 2022, in translation where there is one), and
list your choices in the note you send with the translation:

- experiential statement (and its short form, ES)
- exploratory note, and its three kinds: descriptive, linguistic, conceptual
- personal experiential theme (PET), and sub-theme
- group experiential theme (GET)
- longitudinal PET (LPET), timepoint, trajectory
- participant, case, transcript, passage, interviewer
- the hermeneutic circle, idiography, the double hermeneutic, where the guidance names them
- abstraction, subsumption, polarisation, contextualisation, numeration and function, the ways of clustering
- convergence and divergence

## Sending it

The repository is public, github.com/Pharkie/idiograph, so copy the files from it, translate them as set out
under How, and send a pull request there, or attach a zip of the folders to an issue. Name anyone who should
read the translation.

Or by email:

1. Send a note through Send Feedback in the app: the language you would translate, who you are and your
   background in IPA or qualitative research. Put your email in it.
2. The English files come back to you by email, in the folders listed above.
3. Translate them as set out under How, and send the folders back as a zip in a reply to that email.

## Before it ships

A person who knows IPA and reads the language well reads every message in the app itself, not only in the files,
since a word fits or fails in its place. They check the terms above against the literature, then use the app in
the language from a new project to the GETs. Their name goes in About's acknowledgements if they wish. Only then
is the language added to Settings.
