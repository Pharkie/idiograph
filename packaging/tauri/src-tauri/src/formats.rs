//! The computer's own formats (fmtcore, 28 October 2026): how the Mac or Windows is set to write a date, a
//! time of day and a number, which the page's own `Intl` cannot see, since it knows only the language. The
//! window asks the system to write 28 October 2026, 14:05 and 1234.5 its own way, each as the person has set it
//! (System Settings, General, Language & Region on a Mac, Region's formats on Windows), and hands the three to
//! the server it starts as a small JSON in IDIOGRAPH_COMPUTER_FORMATS, `{"date": "28/10/2026", "time": "14:05",
//! "number": "1,234.50"}`. The server maps each to the nearest of the choices under Settings, Language and
//! formats (`family/i18n.py`, `computer_formats`), and the page writes by it while each is Same as this computer.

/// The variable the server reads them from, `i18n.COMPUTER_FORMATS`.
pub const VARIABLE: &str = "IDIOGRAPH_COMPUTER_FORMATS";

/// The computer's own writing of 28 October 2026, of 14:05 and of 1234.5 as the JSON the server reads, or None
/// where the system says nothing.
pub fn computer() -> Option<String> {
    let (date, time, number) = read()?;
    Some(serde_json::json!({ "date": date, "time": time, "number": number }).to_string())
}

/// On a Mac, Foundation's own formatters in the current locale, which carries the person's own changes: the
/// short date, the short time and the decimal number.
#[cfg(target_os = "macos")]
fn read() -> Option<(String, String, String)> {
    use objc2::runtime::AnyObject;
    use objc2::{class, msg_send};
    use std::ffi::{c_char, CStr};

    unsafe fn said(s: *mut AnyObject) -> String {
        if s.is_null() {
            return String::new();
        }
        let p: *const c_char = msg_send![s, UTF8String];
        if p.is_null() { String::new() } else { CStr::from_ptr(p).to_string_lossy().into_owned() }
    }

    unsafe {
        let locale: *mut AnyObject = msg_send![class!(NSLocale), autoupdatingCurrentLocale];
        let parts: *mut AnyObject = msg_send![class!(NSDateComponents), alloc];
        let parts: *mut AnyObject = msg_send![parts, init];
        let _: () = msg_send![parts, setYear: 2026isize];
        let _: () = msg_send![parts, setMonth: 10isize];
        let _: () = msg_send![parts, setDay: 28isize];
        let _: () = msg_send![parts, setHour: 14isize];
        let _: () = msg_send![parts, setMinute: 5isize];
        let calendar: *mut AnyObject = msg_send![class!(NSCalendar), currentCalendar];
        let when: *mut AnyObject = msg_send![calendar, dateFromComponents: parts];
        if when.is_null() {
            return None;
        }
        // NSDateFormatterNoStyle 0, NSDateFormatterShortStyle 1, NSNumberFormatterDecimalStyle 1
        let dates: *mut AnyObject = msg_send![class!(NSDateFormatter), alloc];
        let dates: *mut AnyObject = msg_send![dates, init];
        let _: () = msg_send![dates, setLocale: locale];
        let _: () = msg_send![dates, setDateStyle: 1usize];
        let _: () = msg_send![dates, setTimeStyle: 0usize];
        let date = said(msg_send![dates, stringFromDate: when]);
        let _: () = msg_send![dates, setDateStyle: 0usize];
        let _: () = msg_send![dates, setTimeStyle: 1usize];
        let time = said(msg_send![dates, stringFromDate: when]);
        let numbers: *mut AnyObject = msg_send![class!(NSNumberFormatter), alloc];
        let numbers: *mut AnyObject = msg_send![numbers, init];
        let _: () = msg_send![numbers, setLocale: locale];
        let _: () = msg_send![numbers, setNumberStyle: 1usize];
        let _: () = msg_send![numbers, setMinimumFractionDigits: 1usize];
        let value: *mut AnyObject = msg_send![class!(NSNumber), numberWithDouble: 1234.5f64];
        let number = said(msg_send![numbers, stringFromNumber: value]);
        Some((date, time, number))
    }
}

/// On Windows, the user's own short date, time without seconds and number, overrides included, from the
/// system's formatting calls for the user's locale.
#[cfg(windows)]
fn read() -> Option<(String, String, String)> {
    use windows_sys::Win32::Foundation::SYSTEMTIME;
    use windows_sys::Win32::Globalization::{
        GetDateFormatEx, GetNumberFormatEx, GetTimeFormatEx, DATE_SHORTDATE, TIME_NOSECONDS,
    };

    // 28 October 2026, a Wednesday, at 14:05
    let when = SYSTEMTIME {
        wYear: 2026, wMonth: 10, wDayOfWeek: 3, wDay: 28, wHour: 14, wMinute: 5, wSecond: 0, wMilliseconds: 0,
    };
    // a null locale name is LOCALE_NAME_USER_DEFAULT, the user's own
    let user = std::ptr::null();
    let text = |buf: &[u16], n: i32| if n > 1 { String::from_utf16_lossy(&buf[..(n - 1) as usize]) } else { String::new() };
    let mut buf = [0u16; 128];
    let size = buf.len() as i32;
    unsafe {
        let n = GetDateFormatEx(user, DATE_SHORTDATE, &when, std::ptr::null(), buf.as_mut_ptr(), size, std::ptr::null());
        let date = text(&buf, n);
        let n = GetTimeFormatEx(user, TIME_NOSECONDS, &when, std::ptr::null(), buf.as_mut_ptr(), size);
        let time = text(&buf, n);
        let value: Vec<u16> = "1234.5".encode_utf16().chain(std::iter::once(0)).collect();
        let n = GetNumberFormatEx(user, 0, value.as_ptr(), std::ptr::null(), buf.as_mut_ptr(), size);
        let number = text(&buf, n);
        Some((date, time, number))
    }
}

/// Elsewhere the window says nothing, and the page writes as its language does.
#[cfg(not(any(target_os = "macos", windows)))]
fn read() -> Option<(String, String, String)> {
    None
}
