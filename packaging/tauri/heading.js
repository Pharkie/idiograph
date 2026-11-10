// A heading baked into a picture above it, for a check's shots on a Mac (17 October 2026, the third Tauri
// build): what the picture shows and what to check in it, drawn by AppKit offscreen, so no screen is read.
//
//     osascript -l JavaScript packaging/tauri/heading.js <in.png> <out.png> <what it shows> <what to check>
ObjC.import('AppKit');

function run(argv) {
  var rep = $.NSBitmapImageRep.imageRepWithData($.NSData.dataWithContentsOfFile(argv[0]));
  if (!rep || rep.isNil()) return 'no picture at ' + argv[0];
  var w = Number(rep.pixelsWide), h = Number(rep.pixelsHigh);
  var scale = w > 2000 ? 2 : 1;
  var band = 92 * scale;
  var out = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
    null, w, h + band, 8, 4, true, false, $.NSCalibratedRGBColorSpace, 0, 0);
  var ctx = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(out);
  $.NSGraphicsContext.saveGraphicsState;
  $.NSGraphicsContext.setCurrentContext(ctx);
  $.NSColor.colorWithCalibratedRedGreenBlueAlpha(251 / 255, 247 / 255, 239 / 255, 1).setFill;
  $.NSRectFill($.NSMakeRect(0, 0, w, h + band));
  rep.drawInRect($.NSMakeRect(0, 0, w, h));
  var ink = $.NSColor.colorWithCalibratedRedGreenBlueAlpha(31 / 255, 27 / 255, 22 / 255, 1);
  var big = $.NSDictionary.dictionaryWithObjectsForKeys(
    $([$.NSFont.boldSystemFontOfSize(24 * scale), ink]), $([$.NSFontAttributeName, $.NSForegroundColorAttributeName]));
  var small = $.NSDictionary.dictionaryWithObjectsForKeys(
    $([$.NSFont.systemFontOfSize(19 * scale), ink]), $([$.NSFontAttributeName, $.NSForegroundColorAttributeName]));
  $(argv[2]).drawAtPointWithAttributes($.NSMakePoint(20 * scale, h + band - 44 * scale), big);
  $('Check: ' + argv[3]).drawAtPointWithAttributes($.NSMakePoint(20 * scale, h + band - 80 * scale), small);
  $.NSGraphicsContext.restoreGraphicsState;
  var png = out.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  return png.writeToFileAtomically(argv[1], true) ? 'baked ' + argv[1] : 'not written';
}
