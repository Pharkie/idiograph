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

The twenty-four pictures a participant can be given on the Trajectories screen, `static/faces/face01.svg` to `face24.svg`, are line portraits drawn for Idiograph by `packaging/make_faces.py`, part of Idiograph under the same licence. No outside set is used.

The demo case is an invented interview with a participant called Juno about sharing a home with a dog. Nobody real is in it.
