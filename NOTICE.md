# Licence

Copyright Adam Knowles. Idiograph, Sift and Trace are free software under the GNU Affero General Public License version 3 (SPDX `AGPL-3.0-only`), in `LICENSE`. Section 7 of that licence allows additional terms, and these two apply.

- Section 7(b), credit. A work based on Idiograph, Sift or Trace must keep the notice "Based on Idiograph by Adam Knowles", or Sift or Trace in place of Idiograph, with the address https://github.com/Pharkie/idiograph. It goes in the work's Appropriate Legal Notices, which in an interactive version means its About screen, and in its documentation.
- Section 7(e), names. The licence grants no right to use the names Idiograph, Sift or Trace, or their marks and icons.

# Third-party software

Idiograph is written in Python and runs in a browser. Beyond Python's standard library it uses:

- openpyxl, by Eric Gazoni and Charlie Clark, under the MIT License, to read and write Excel workbooks.
- Natural Earth 5.1.2's admin 0 countries, in the public domain, for the outlines and label points of the map Sift's Country filter draws. `make_world.py` projects them into `static/world.json`.
- Mermaid 11.14.0, by Knut Sveidqvist and its contributors, under the MIT License, to draw Sift's PRISMA flow. It ships in `static/vendor/` with its licence beside it, and the libraries it bundles keep their own notices in its comments.
- Quicksand Bold, by Andrew Paglinawan and the Quicksand Project Authors, under the SIL Open Font License 1.1, for the words on the Ko-fi button on each Home. Its Latin file ships in `static/vendor/quicksand/` with the licence beside it.
- Typst 0.15.1, by Typst GmbH and its contributors, under the Apache License 2.0, to typeset every PDF and picture of a print view. The installed app carries it built into a small program of its own beside the server, and a run from source uses typst-py, by messense, under the Apache License 2.0, which carries the same version.
- Charis SIL, by SIL International, and Nunito Sans, by the Nunito Sans Project Authors, both under the SIL Open Font License 1.1, the fonts of every print view and PDF. Their Latin files ship in `static/fonts/` with each licence beside them, `OFL-CharisSIL.txt` and `OFL-NunitoSans.txt`.
- The REFI-QDA project schema, `Project.xsd` of QDA-XML 1.0 (18 March 2019), by the REFI-QDA working group, as the openqda project's refi-tools publish it under the GNU Affero General Public License version 3. A copy in `tests/refi-qda/` checks the REFI-QDA projects Idiograph writes. The app itself does not ship it.
- The Ko-fi cup, Ko-fi's own artwork for its button, the cup with a heart, kept in `static/vendor/kofi/` so the button on each Home is Ko-fi's without loading anything from Ko-fi. The Ko-fi name and cup are Ko-fi Labs' and are not under this licence.

The pictures a participant can be given, in `static/faces/`, are three sets, each drawn again in black and white by a script in `packaging/` that fetched them once:

- Open Peeps, `peep01.svg` to `peep80.svg`, by Pablo Stanley (https://www.openpeeps.com), dedicated to the public domain under CC0 1.0 Universal. Each was put together from Open Peeps' parts through DiceBear's `open-peeps` style (https://www.dicebear.com) by `make_peeps.py`.
- Notionists, `notion01.svg` to `notion40.svg`, by Zoish (https://heyzoish.gumroad.com/l/notionists), dedicated to the public domain under CC0 1.0 Universal. Each was put together from Notionists' parts through DiceBear's `notionists` style by `make_notionists.py`.
- Fluent Emoji, `fluent01.svg` to `fluent20.svg`, by Microsoft (https://github.com/microsoft/fluentui-emoji), under the MIT License, each a person's High Contrast drawing recoloured by `make_fluent.py`. The licence ships beside them as `LICENSE-fluent-emoji.txt`, and reads:

  > MIT License
  >
  > Copyright (c) Microsoft Corporation.
  >
  > Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
  >
  > The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
  >
  > THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

CC0 asks for no credit, which is given here all the same. Neither DiceBear, Zoish, Pablo Stanley nor Microsoft endorses Idiograph.

The demo's three interviews, Juno's, Rowan's and Mabel's, are invented, about sharing a home with a dog. Nobody real is in them. Their recordings, in `packaging/recording/`, are AI-generated speech made with Google's Gemini in four synthetic voices designed for the demo. They are not under the GNU Affero General Public License but under their own licence beside them, `LICENSE-audio.md`, which allows copying and sharing them only unchanged and only as part of Idiograph or a modified version of it, and grants no right to use them to train, fine-tune or evaluate any AI or machine-learning model. Google does not endorse Idiograph.
