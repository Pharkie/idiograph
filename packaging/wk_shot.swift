// Shots in the Mac's own window engine (zoomsweep, 30 October 2026, from fbcard's harness of 29 October): the
// system WebKit, a WKWebView as the Tauri window holds on a Mac, at a page zoom (pageZoom, which is what
// Cmd+plus and Settings' Text size set there), light or dark, at a window size, with legacy scroll bars
// (always shown, as with a mouse plugged in) for this process alone, never a system setting. Chrome's headless
// shots cannot show a fault that only WebKit lays out, or a scroll bar only a zoom brings: fbcard's sideways
// bar on Send feedback's note box was one.
//
//   swiftc -O packaging/wk_shot.swift -o <scratch>/wk_shot
//   <scratch>/wk_shot --url http://127.0.0.1:<PORT>/ --out <dir> --steps <steps.json> [--width 1280] [--height 800]
//       [--zoom 1.25] [--scheme light|dark] [--scale 2] [--shot-box packaging/shot_box.js] [--init <js>]
//       [--timeout 120] [--overlay-bars] [--no-still]
//
// The steps are a JSON list run in order, each an object whose keys are done in this order:
//   "size": [w, h]       the window's new size in points
//   "zoom": 1.5          the page zoom (Small 0.9, Medium 1, Large 1.25)
//   "scheme": "dark"     the appearance, which the page reads as prefers-color-scheme
//   "load": "<url>"      a new page, waited for
//   "js": "<expr>"       run in the page and awaited (an async function's call or a promise is waited for),
//                        its value printed as `js <n>: <json>`
//   "waitFor": "<sel>"   until an element matching it is drawn, at most 10 seconds
//   "wait": 300          milliseconds before the shot (300 when left out)
//   "shot": "<name>"     <out>/<name>.png: the whole window, or "clip": {x, y, w, h} in CSS pixels, or "plan":
//                        [selectors] with "planOptions": {...}, which runs shot_box.js's shotPlan in the page,
//                        shoots its crop and writes the plan beside the PNG as <name>.shot.json
//   "scale": 2           this shot's pixels a point, in place of --scale, or "perCss": 2, its pixels a CSS
//                        pixel at any zoom (2 at Large is 1.6 a point), as Chrome's shots at device scale 2
//   "native": true       the shot through the window server, the way the screen shows the window, at the
//                        screen's own scale (see below)
// A shot is a WebKit snapshot at --scale pixels a point (2 by default, a Retina screen's), so at a page zoom z
// one CSS pixel is scale times z pixels, and the sidecar's `scale` says so, which is what review_shot.js reads.
// WebKit keeps a Mac's scroll bars out of its snapshots, so the tool turns off its async scrolling, which draws
// them in the page again where a snapshot holds them, the layout unchanged, all but the window's own bar at the
// right of a page that scrolls as Home does. A native shot is the window server's
// own picture, at the screen's scale and never more (1 on a screen that is not Retina): the check that a
// snapshot's scroll bars are the ones the window shows. Each run starts with no cookies or storage kept from any
// other, every animation, transition and caret stilled on each page (--no-still keeps them), and `--init` run at
// the start of each page before its own scripts. It ends `WK: done <n> shots` and exit 0, or exit 1 with the reason.
import Cocoa
import WebKit

// the window server's own picture of this process's window, reached by its C name since the SDK hides it
@_silgen_name("CGWindowListCreateImage")
func cgWindowImage(_ rect: CGRect, _ option: UInt32, _ id: UInt32, _ imageOption: UInt32) -> Unmanaged<CGImage>?

let usage = """
wk_shot --url <url> --out <dir> --steps <steps.json> [--width 1280] [--height 800] [--zoom 1] [--scheme light|dark]
        [--scale 2] [--shot-box packaging/shot_box.js] [--init <js>] [--timeout 120] [--overlay-bars] [--no-still]
"""

func fail(_ why: String, _ code: Int32 = 1) -> Never {
  FileHandle.standardError.write(("WK: " + why + "\n").data(using: .utf8)!)
  exit(code)
}

struct Options {
  var url = "", out = "", steps = "", scheme = "light", shotBox = "", initJs = ""
  var width = 1280.0, height = 800.0, zoom = 1.0, scale = 2.0, timeout = 120.0
  var overlayBars = false, still = true
}

func readOptions() -> Options {
  var o = Options()
  var argv = Array(CommandLine.arguments.dropFirst())
  while !argv.isEmpty {
    let a = argv.removeFirst()
    if a == "-h" || a == "--help" { print(usage); exit(0) }
    if a == "--overlay-bars" { o.overlayBars = true; continue }
    if a == "--no-still" { o.still = false; continue }
    guard a.hasPrefix("--"), !argv.isEmpty else { fail("not an option, or no value: \(a)\n\(usage)", 2) }
    let v = argv.removeFirst()
    let n = Double(v)
    switch a {
    case "--url": o.url = v
    case "--out": o.out = v
    case "--steps": o.steps = v
    case "--scheme": o.scheme = v
    case "--shot-box": o.shotBox = v
    case "--init": o.initJs = v
    case "--width": o.width = n ?? -1
    case "--height": o.height = n ?? -1
    case "--zoom": o.zoom = n ?? -1
    case "--scale": o.scale = n ?? -1
    case "--timeout": o.timeout = n ?? -1
    default: fail("unknown option \(a)\n\(usage)", 2)
    }
  }
  if o.url.isEmpty || o.out.isEmpty || o.steps.isEmpty { fail(usage, 2) }
  if URL(string: o.url)?.port == 8765 { fail("port 8765 is the running app's own: start a smoke server on another port", 2) }
  if !(o.width > 0 && o.height > 0 && o.zoom > 0 && o.scale > 0 && o.timeout > 0) { fail("width, height, zoom, scale and timeout are numbers above 0", 2) }
  if o.scheme != "light" && o.scheme != "dark" { fail("--scheme is light or dark", 2) }
  return o
}

let opt = readOptions()

// Legacy scroll bars for this process alone, read by AppKit and handed to WebKit's own processes as they start:
// the argument domain, as `-AppleShowScrollBars Always` on the command line would set it, so no setting is written
if !opt.overlayBars {
  UserDefaults.standard.setVolatileDomain(["AppleShowScrollBars": "Always"], forName: UserDefaults.argumentDomain)
}

let stepsList: [[String: Any]] = {
  guard let data = FileManager.default.contents(atPath: opt.steps),
        let list = (try? JSONSerialization.jsonObject(with: data)) as? [[String: Any]] else { fail("\(opt.steps) is not a JSON list of steps", 2) }
  return list
}()
let shotBoxText: String = {
  if opt.shotBox.isEmpty { return "" }
  guard let s = try? String(contentsOfFile: opt.shotBox, encoding: .utf8) else { fail("cannot read \(opt.shotBox)", 2) }
  return s
}()
try? FileManager.default.createDirectory(atPath: opt.out, withIntermediateDirectories: true)

let STILL = "*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }"

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)

func appearance(_ scheme: String) -> NSAppearance? { NSAppearance(named: scheme == "dark" ? .darkAqua : .aqua) }

func json(_ v: Any?) -> String {
  guard let v = v, !(v is NSNull) else { return "null" }
  if JSONSerialization.isValidJSONObject([v]), let d = try? JSONSerialization.data(withJSONObject: [v], options: [.fragmentsAllowed]),
     let s = String(data: d, encoding: .utf8) { return String(s.dropFirst().dropLast()) }
  return "\"\(v)\""
}

final class Runner: NSObject, WKNavigationDelegate {
  let web: WKWebView
  let win: NSWindow
  var i = 0, shots = 0
  var loaded: (() -> Void)?
  var size: NSSize

  override init() {
    size = NSSize(width: opt.width, height: opt.height)
    let cfg = WKWebViewConfiguration()
    cfg.websiteDataStore = .nonPersistent()
    // Since 2023 WebKit draws a Mac's scroll bars outside the page, so a snapshot leaves them out. With its
    // scrolling on the page's own thread they are drawn in the page again, the same bars in the same places,
    // the layout as it was, and a snapshot holds them
    let off = ["AsyncOverflowScrollingEnabled", "AsyncFrameScrollingEnabled"]
    let setEnabled = NSSelectorFromString("_setEnabled:forFeature:")
    if let features = (WKPreferences.self as AnyObject).perform(NSSelectorFromString("_features"))?.takeUnretainedValue() as? [NSObject],
       cfg.preferences.responds(to: setEnabled) {
      typealias SetEnabled = @convention(c) (AnyObject, Selector, Bool, AnyObject) -> Void
      let call = unsafeBitCast(cfg.preferences.method(for: setEnabled), to: SetEnabled.self)
      for f in features where off.contains((f.value(forKey: "key") as? String) ?? "") { call(cfg.preferences, setEnabled, false, f) }
    } else { print("WK: this WebKit keeps its scroll bars out of snapshots: shoot with \"native\": true to see them") }
    var start = ""
    if opt.still { start += "addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = \(json(STILL)); document.head.appendChild(s); });" }
    if !opt.initJs.isEmpty { start += opt.initJs }
    if !start.isEmpty { cfg.userContentController.addUserScript(WKUserScript(source: start, injectionTime: .atDocumentStart, forMainFrameOnly: true)) }
    web = WKWebView(frame: NSRect(origin: .zero, size: size), configuration: cfg)
    // off the screens, so nobody sees it, and never counted hidden, so the page's timers and frames keep running
    win = NSWindow(contentRect: NSRect(x: -20000, y: -20000, width: opt.width, height: opt.height), styleMask: [.borderless], backing: .buffered, defer: false)
    super.init()
    let occlusion = NSSelectorFromString("_setWindowOcclusionDetectionEnabled:")
    if web.responds(to: occlusion) { web.perform(occlusion, with: false) }
    web.appearance = appearance(opt.scheme)
    win.appearance = appearance(opt.scheme)
    win.contentView = web
    web.navigationDelegate = self
    web.pageZoom = CGFloat(opt.zoom)
    win.orderFront(nil)
  }

  func load(_ s: String, then: @escaping () -> Void) {
    guard let u = URL(string: s) else { fail("not a URL: \(s)", 2) }
    if u.port == 8765 { fail("port 8765 is the running app's own", 2) }
    loaded = then
    web.load(URLRequest(url: u))
  }
  func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    let f = loaded; loaded = nil
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { f?() }
  }
  func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { fail("the page did not load: \(error.localizedDescription)") }
  func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { fail("the page did not load: \(error.localizedDescription)") }

  func run(_ js: String, _ done: @escaping (Any?, String?) -> Void) {
    web.callAsyncJavaScript("return await (\(js));", arguments: [:], in: nil, in: .page) { r in
      switch r {
      case .success(let v): done(v, nil)
      case .failure(let e):
        let info = (e as NSError).userInfo
        done(nil, (info["WKJavaScriptExceptionMessage"] as? String) ?? e.localizedDescription)
      }
    }
  }

  func next() {
    if i >= stepsList.count { print("WK: done \(shots) shots"); exit(0) }
    let s = stepsList[i], n = i
    i += 1
    if let wh = s["size"] as? [Double], wh.count == 2 {
      size = NSSize(width: wh[0], height: wh[1])
      win.setContentSize(size)
      web.frame = NSRect(origin: .zero, size: size)
    }
    if let z = s["zoom"] as? Double { web.pageZoom = CGFloat(z) }
    if let sc = s["scheme"] as? String { web.appearance = appearance(sc); win.appearance = appearance(sc) }
    let afterLoad = {
      let afterJs = {
        self.waitFor(s["waitFor"] as? String, n, tries: 0) {
          let wait = (s["wait"] as? Double ?? 300) / 1000
          DispatchQueue.main.asyncAfter(deadline: .now() + wait) {
            if let name = s["shot"] as? String { self.shoot(name, s) } else { self.next() }
          }
        }
      }
      if let js = s["js"] as? String {
        self.run(js) { v, err in
          if let err = err { print("js \(n): error: \(err)") } else { print("js \(n): \(json(v))") }
          afterJs()
        }
      } else { afterJs() }
    }
    if let u = s["load"] as? String { load(u, then: afterLoad) } else { afterLoad() }
  }

  func waitFor(_ sel: String?, _ n: Int, tries: Int, then: @escaping () -> Void) {
    guard let sel = sel else { then(); return }
    let probe = "(() => { const e = document.querySelector(\(json(sel))); return !!(e && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden'); })()"
    run(probe) { v, _ in
      if (v as? Bool) == true { then() }
      else if tries >= 100 { print("step \(n): \(sel) never showed"); then() }
      else { DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { self.waitFor(sel, n, tries: tries + 1, then: then) } }
    }
  }

  // the part of the window to shoot, in CSS pixels, and the plan to write beside it
  func shoot(_ name: String, _ s: [String: Any]) {
    if let targets = s["plan"] {
      if shotBoxText.isEmpty { fail("step \(i - 1) asks for a plan: give --shot-box packaging/shot_box.js", 2) }
      let o = s["planOptions"] ?? [String: Any]()
      run("(() => { \(shotBoxText)\n; return JSON.stringify(shotPlan(\(json(targets)), \(json(o)))); })()") { v, err in
        guard let str = v as? String, let data = str.data(using: .utf8),
              var plan = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let crop = plan["crop"] as? [String: Any] else { print("plan \(name) failed: \(err ?? "no plan")"); self.next(); return }
        let rect = CGRect(x: crop["x"] as? Double ?? 0, y: crop["y"] as? Double ?? 0, width: crop["w"] as? Double ?? 0, height: crop["h"] as? Double ?? 0)
        if rect.width < 1 || rect.height < 1 {
          print("plan \(name) has nothing to shoot: \(json(plan["problems"]))"); self.next(); return
        }
        self.capture(name, rect, s) { scale in
          plan["scale"] = scale
          plan["engine"] = "WKWebView"
          plan["zoom"] = Double(self.web.pageZoom)
          if let d = try? JSONSerialization.data(withJSONObject: plan, options: [.sortedKeys]) {
            try? d.write(to: URL(fileURLWithPath: "\(opt.out)/\(name).shot.json"))
          }
          if let p = plan["problems"] as? [Any], !p.isEmpty { print("plan \(name) problems: \(json(p))") }
        }
      }
      return
    }
    var rect = CGRect.null
    if let c = s["clip"] as? [String: Double] { rect = CGRect(x: c["x"] ?? 0, y: c["y"] ?? 0, width: c["w"] ?? 0, height: c["h"] ?? 0) }
    capture(name, rect, s) { _ in }
  }

  // `rect` in CSS pixels (null for the whole window), shot at the step's `scale` or --scale pixels a point, or at
  // `perCss` pixels a CSS pixel whatever the zoom, or with `native` the window server's picture at the screen's
  // own scale. `wrote` gets the pixels a CSS pixel came out at
  func capture(_ name: String, _ css: CGRect, _ s: [String: Any], wrote: @escaping (Double) -> Void) {
    let z = Double(web.pageZoom)
    let native = s["native"] as? Bool == true
    let scale = (s["perCss"] as? Double).map { $0 / z } ?? (s["scale"] as? Double ?? opt.scale)
    let pts = css.isNull ? CGRect(origin: .zero, size: size) : CGRect(x: css.minX * z, y: css.minY * z, width: css.width * z, height: css.height * z)
    let path = "\(opt.out)/\(name).png"
    func save(_ cg: CGImage, _ how: String) {
      let rep = NSBitmapImageRep(cgImage: cg)
      guard let png = rep.representation(using: .png, properties: [:]) else { fail("could not write \(path)") }
      do { try png.write(to: URL(fileURLWithPath: path)) } catch { fail("could not write \(path): \(error.localizedDescription)") }
      let perCss = Double(cg.width) / (pts.width / z)
      shots += 1
      print("shot \(name): \(cg.width)x\(cg.height) \(how), \(Int(pts.width / z))x\(Int(pts.height / z)) CSS px at zoom \(z), \((perCss * 100).rounded() / 100) px a CSS px")
      wrote((perCss * 100).rounded() / 100)
      next()
    }
    if native {
      let back = Double(win.backingScaleFactor)
      guard let img = cgWindowImage(CGRect.null, 8, UInt32(win.windowNumber), 1 | 8)?.takeRetainedValue(),
            let part = img.cropping(to: CGRect(x: pts.minX * back, y: pts.minY * back, width: pts.width * back, height: pts.height * back))
      else { fail("the window server gave no picture of the window") }
      save(part, "native")
      return
    }
    let c = WKSnapshotConfiguration()
    c.rect = pts
    c.afterScreenUpdates = true
    // snapshotWidth is in points: the screen's backing scale multiplies it, so ask for scale over that
    c.snapshotWidth = NSNumber(value: Double(pts.width) * scale / Double(win.backingScaleFactor))
    web.takeSnapshot(with: c) { image, err in
      guard let image = image, let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fail("the snapshot failed: \(err?.localizedDescription ?? "no picture")")
      }
      save(cg, "snapshot")
    }
  }
}

let runner = Runner()
runner.load(opt.url) { runner.next() }
DispatchQueue.main.asyncAfter(deadline: .now() + opt.timeout) { fail("out of time after \(Int(opt.timeout)) s at step \(runner.i)") }
app.run()
