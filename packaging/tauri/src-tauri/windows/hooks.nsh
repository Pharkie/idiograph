; Idiograph's own steps in the installer Tauri's bundler makes for Windows (tauri.conf.json names this
; file as installerHooks), 17 October 2026, the third Tauri build.
;
; Before it puts a file down, the installer stops a running Idiograph as its own Stop stops it, through
; the console twin beside the server, so no window flashes up and anything in hand is written first.
; Then it removes the version testers had before the window, 0.9.0, which Inno Setup installed in a
; folder of its own: its own uninstaller, run quietly, stops its server first and takes its Start menu
; entry, its shortcut and its folder with it. Every setting and every case stays, since they live in
; %APPDATA%\Idiograph and neither installer touches that folder. The uninstaller stops a running
; Idiograph the same way before it removes the app's own files.

; The first page's words, the Welcome page's, where NSIS's own spoke of closing other programs to update
; system files without a restart, none of it true of an install for one user (17 October, the third
; build's screenshots), and the uninstaller's first page, which says what goes and what stays: its tick,
; English.nsh's deleteAppData, clears only what the window remembers, never a case. Each is taken by the
; page it belongs to, which this file comes before (18 October, the fourth build). Since the fifth build
; (18 October, Adam's words) the Welcome page says no administrator's password, and the last page's tick
; says Open Idiograph, where NSIS's own said Run.
!define MUI_WELCOMEPAGE_TEXT "Setup installs $(^NameDA) for you alone on this computer. It needs no administrator's password and no restart.$\r$\n$\r$\nAn open $(^NameDA) is closed first, and your cases and settings stay as they are.$\r$\n$\r$\n$_CLICK"
!define MUI_UNCONFIRMPAGE_TEXT_TOP "$(^NameDA) will be removed from the folder below. Your cases, transcripts and projects stay where they are, whether or not you tick the box."
!define MUI_FINISHPAGE_RUN_TEXT "Open $(^NameDA)"

; The installer's own version resource names its publisher, tauri.conf.json's, as the window's and the
; server's do (22 October 2026, after Windows Defender's false finding on 0.9.3). Tauri's NSIS script
; gives it the product, description, copyright and version but no company. One publisher for all three
; apps, so it is written here once.
VIAddVersionKey "CompanyName" "Adam Knowles"

; Inno Setup's key for the Idiograph it installed, its AppId as packaging/build_windows.py wrote it
!define IDIOGRAPH_INNO_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\{C7E7DA37-1EC0-4980-B693-28D0962DA65C}_is1"

; Since the three-app split's build 6 (20 October) this file serves Sift's and Trace's installers too.
; Each app installs in a folder of its own named for it, Sift's beside Idiograph's, its server named
; for it too, so the stop below finds the one server its folder holds and stops that app alone,
; and the Inno Setup install, which was Idiograph's, is removed by Idiograph's Setup alone.
!macro IDIOGRAPH_STOP
  Push $0
  ${If} ${FileExists} "$INSTDIR\server\Idiograph-console.exe"
    DetailPrint "Stopping Idiograph"
    nsExec::Exec '"$INSTDIR\server\Idiograph-console.exe" stop'
    Pop $0
    Sleep 1500
  ${EndIf}
  ${If} ${FileExists} "$INSTDIR\server\Sift-console.exe"
    DetailPrint "Stopping Sift"
    nsExec::Exec '"$INSTDIR\server\Sift-console.exe" stop'
    Pop $0
    Sleep 1500
  ${EndIf}
  ${If} ${FileExists} "$INSTDIR\server\Trace-console.exe"
    DetailPrint "Stopping Trace"
    nsExec::Exec '"$INSTDIR\server\Trace-console.exe" stop'
    Pop $0
    Sleep 1500
  ${EndIf}
  Pop $0
!macroend

!macro NSIS_HOOK_PREINSTALL
  Push $R0
  Push $R1
  !insertmacro IDIOGRAPH_STOP
  ; the Inno Setup install was Idiograph's, so only Idiograph's Setup (and Idiograph Test's) looks for it
  StrCpy $R1 "${PRODUCTNAME}" 9
  StrCpy $R0 ""
  ${If} $R1 == "Idiograph"
    ReadRegStr $R0 HKCU "${IDIOGRAPH_INNO_KEY}" "UninstallString"
  ${EndIf}
  ${If} $R0 != ""
    DetailPrint "Removing the earlier Idiograph, its settings and cases kept"
    ExecWait '$R0 /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
    ; Inno's uninstaller hands over to a copy of itself and returns at once, so its key going is what
    ; says it has finished, waited for up to a minute
    StrCpy $R1 0
    ${Do}
      ReadRegStr $R0 HKCU "${IDIOGRAPH_INNO_KEY}" "UninstallString"
      ${If} $R0 == ""
      ${OrIf} $R1 >= 120
        ${ExitDo}
      ${EndIf}
      Sleep 500
      IntOp $R1 $R1 + 1
    ${Loop}
  ${EndIf}
  Pop $R1
  Pop $R0
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro IDIOGRAPH_STOP
!macroend
