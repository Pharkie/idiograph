# Signing the Windows installers with SignPath

Written 21 November 2026. The signing is built into the repository and switched off. This says what turns it on once the SignPath Foundation has approved the project. What the application needs, and what is still open, is in the harness's `Idiograph_signpath_checklist_21Nov26.md`.

## What is built

- The website's policy page, `site/holding/signing.html`, linked from the home page and the Download page. It carries the line SignPath asks for, the three roles with their members, the approval rule and what Idiograph sends to other computers. When a role changes, change the page.
- The workflow's signing steps, `.github/workflows/windows-installer.yml`, in the `windows` job. Each new step has `if: env.SIGNING == 'true'`, and `SIGNING` is true only on a tag's run where the repository variable `SIGNPATH_ENABLED` is `true`. With the variable unset, the job runs the build step as `--stage all`, the one run it always was, and every added step is skipped. The only change that is not a step is the job's permissions, which gain `actions: read` (SignPath's action reads the artifact it signs) and the timeout, 75 minutes unless signing is on and then 300, since a person approves each of two requests.
- The build in stages, `packaging/build_windows.py --stage`: `freeze` builds the server and compiles the window (Tauri's `build --no-bundle`) and leaves the four programs to sign in `build/signpath/unsigned/` (`server/` holds the windowed program, its console twin and the typesetter, `window/` the window), `pack` puts the signed ones back and has Tauri pack the installer round them (`bundle`), leaving it in `build/signpath/installer-unsigned/`, and `finish` puts the signed installer in `dist/`. Each stage that takes a file back stops unless PowerShell says its signature is Valid. Signing by a local certificate (`--sign-sha1`) is as it was and cannot be combined with a stage.
- The two artifact configurations, `packaging/signpath/artifact-configuration.xml` (the four programs) and `packaging/signpath/installer-artifact-configuration.xml` (the installer). They take the app's name and version as parameters from the workflow, so Sift and Trace sign under their own names.

## What turns it on

1. In SignPath, once approved: add the trusted build system "GitHub.com" to the organisation and link it to the project, set the project's repository URL, paste the two artifact configurations as two configurations of the project, and make a signing policy that uses the release certificate with "Verify origin" on and the allowed branches limited to the tag form. Make a user with submitter rights and an API token.
2. In the repository's settings, under Secrets and variables, Actions:
   - Secret `SIGNPATH_API_TOKEN`, the token.
   - Variables `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_POLICY_SLUG`, `SIGNPATH_CONFIG_SLUG` (the first configuration) and `SIGNPATH_INSTALLER_CONFIG_SLUG` (the second). None of these is secret.
   - Variable `SIGNPATH_ENABLED` set to `true`. Delete it, or set anything else, to switch signing off again.
3. On the next release, approve the two requests in SignPath, the programs and then the installer, each within two hours of its request (`wait-for-completion-timeout-in-seconds: 7200`).
4. Then change the Windows first-open text on the Download page, which says the preview is not signed, and the policy page's sentence that signing is switched on once approved.

## The window's marker

`tauri bundle` writes a marker into the window's exe (the bundle type, `__TAURI_BUNDLE_TYPE`, from unknown to NSIS) by changing its bytes in place, which would break a signature made before it. So `--stage freeze` runs the bundle once, throws that installer away, and sends the exe it patched to SignPath, and `pack`'s own bundle finds nothing left to patch. `pack` then reads the signature of the window and the server's programs again after the bundle and stops the job unless each is Valid.

## Not tried

The stages cannot run on a Mac, so only their dry-run path and the argument checks were run here, not Tauri's `build --no-bundle` followed by `bundle`, the SignPath action, or an NSIS installer being accepted as a PE file by SignPath. The first real tag with signing on is the test. What to look at then:

- Whether Tauri's `bundle` packs the compiled window as it stands, signed, and does not compile it again, and whether the second bundle really finds the marker patched (the check after it fails the job if the signature broke).
- Whether the product versions in the artifact configurations match what each file carries: the server's programs carry four numbers (`0.9.35.0`), the window and the installer the three Tauri is given (`0.9.35`). SignPath names the mismatch if there is one, and `versionThree` and `versionFour` in the configurations are the places to change.
- The publisher: the certificate says SignPath Foundation, and `publisher` in `tauri.conf.json` says Adam Knowles, so no company-name restriction is set.
- Origin verification asks for builds with no reused cache. The job caches pip, and downloads Rust and Tauri's CLI at run time.

The action is pinned to `signpath/github-action-submit-signing-request@v3.2`. Move the pin by hand.
