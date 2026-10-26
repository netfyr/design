#!/usr/bin/env python3
# SPDX-License-Identifier: OFL-1.1
"""Check real Fontconfig fallback without changing installed fonts or caches."""

import argparse
import ctypes as C
import ctypes.util
from contextlib import contextmanager
from pathlib import Path
from xml.sax.saxutils import escape


class FontSet(C.Structure):
    _fields_ = [("nfont", C.c_int), ("sfont", C.c_int), ("fonts", C.POINTER(C.c_void_p))]


def bind(library, name, result, *arguments):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = arguments
    return function


library = ctypes.util.find_library("fontconfig")
if not library:
    raise SystemExit("Fontconfig is required for this check")
fc = C.CDLL(library)
create = bind(fc, "FcConfigCreate", C.c_void_p)
destroy = bind(fc, "FcConfigDestroy", None, C.c_void_p)
load = bind(fc, "FcConfigParseAndLoadFromMemory", C.c_int, C.c_void_p, C.c_char_p, C.c_int)
build = bind(fc, "FcConfigBuildFonts", C.c_int, C.c_void_p)
add_file = bind(fc, "FcConfigAppFontAddFile", C.c_int, C.c_void_p, C.c_char_p)
parse = bind(fc, "FcNameParse", C.c_void_p, C.c_char_p)
substitute = bind(fc, "FcConfigSubstitute", C.c_int, C.c_void_p, C.c_void_p, C.c_int)
defaults = bind(fc, "FcDefaultSubstitute", None, C.c_void_p)
pattern_destroy = bind(fc, "FcPatternDestroy", None, C.c_void_p)
sort = bind(
    fc, "FcFontSort", C.POINTER(FontSet), C.c_void_p, C.c_void_p, C.c_int,
    C.c_void_p, C.POINTER(C.c_int),
)
set_destroy = bind(fc, "FcFontSetDestroy", None, C.POINTER(FontSet))
get_string = bind(
    fc, "FcPatternGetString", C.c_int, C.c_void_p, C.c_char_p, C.c_int,
    C.POINTER(C.c_char_p),
)
get_charset = bind(
    fc, "FcPatternGetCharSet", C.c_int, C.c_void_p, C.c_char_p, C.c_int,
    C.POINTER(C.c_void_p),
)
has_char = bind(fc, "FcCharSetHasChar", C.c_int, C.c_void_p, C.c_uint32)

CODEPOINTS = range(0x100000, 0x100005)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


@contextmanager
def config(fonts, rule=None):
    configuration = create()
    require(configuration, "Could not create Fontconfig configuration")
    try:
        additions = f"<include>{escape(str(rule))}</include>" if rule else ""
        xml = (
            "<fontconfig><include>/etc/fonts/fonts.conf</include>"
            "<reset-dirs/>" + additions + "</fontconfig>"
        )
        require(load(configuration, xml.encode(), 1), "Could not load Fontconfig rules")
        require(build(configuration), "Could not initialize empty font set")
        for font in fonts:
            require(font.is_file(), f"Missing fixture font: {font}")
            require(add_file(configuration, str(font).encode()), f"Could not load {font}")
        yield configuration
    finally:
        destroy(configuration)


def fallback(configuration, query):
    pattern = parse(query.encode())
    require(pattern, f"Could not parse {query}")
    font_set = None
    try:
        require(substitute(configuration, pattern, 0), f"Could not substitute {query}")
        defaults(pattern)
        result = C.c_int()
        font_set = sort(configuration, pattern, 1, None, C.byref(result))
        require(font_set and result.value == 0, f"No fonts returned for {query}")
        output = []
        for index in range(font_set.contents.nfont):
            font = font_set.contents.fonts[index]
            strings = {}
            for field in (b"family", b"file"):
                value = C.c_char_p()
                require(get_string(font, field, 0, C.byref(value)) == 0, f"Missing {field}")
                strings[field.decode()] = value.value.decode()
            charset = C.c_void_p()
            require(get_charset(font, b"charset", 0, C.byref(charset)) == 0, "Missing charset")
            strings["coverage"] = {code for code in CODEPOINTS if has_char(charset, code)}
            strings["latin"] = bool(has_char(charset, ord("A")))
            output.append(strings)
        return output
    finally:
        if font_set:
            set_destroy(font_set)
        pattern_destroy(pattern)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--original-fonts", required=True, type=Path)
    parser.add_argument("--text-font", required=True, type=Path, action="append")
    parser.add_argument("--text-family", default="JetBrainsMono Nerd Font")
    parser.add_argument("--rule", type=Path, default=Path(__file__).with_name("70-netfyr-symbols.conf"))
    args = parser.parse_args()
    fonts = sorted(args.original_fonts.resolve().glob("*.ttf")) + [p.resolve() for p in args.text_font]
    require(fonts and args.rule.is_file(), "Original fonts and fallback rule are required")
    symbols = args.symbols.resolve()
    queries = [args.text_family, "monospace", "serif", "sans-serif", "missing-netfyr-test-family"]
    with config(fonts) as baseline, config(fonts, args.rule.resolve()) as absent:
        with config(fonts + [symbols], args.rule.resolve()) as present:
            for query in queries:
                original = fallback(baseline, query)
                missing = fallback(absent, query)
                available = fallback(present, query)
                require(original[0]["file"] == missing[0]["file"] == available[0]["file"],
                        f"Primary font changed for {query}")
                require(not any(font["coverage"] for font in missing),
                        "Old fonts unexpectedly provide the new symbols")
                for code in CODEPOINTS:
                    chosen = next((font for font in available if code in font["coverage"]), None)
                    require(chosen and Path(chosen["file"]) == symbols,
                            f"Wrong fallback for {query}, U+{code:06X}")
                    require(not chosen["latin"], "Symbols font unexpectedly covers Latin text")
                print(f"{query}: text unchanged; all five symbols use netfyr symbols")
            for configuration, expected in ((absent, False), (present, True)):
                matches = fallback(configuration, "netfyr symbols:charset=100000-100004")
                detected = any(font["family"] == "netfyr symbols" and
                               font["coverage"] == set(CODEPOINTS) for font in matches)
                require(detected == expected, "Companion coverage detection is incorrect")
    print("Missing companion stays undetected; no installed font or cache was changed")


if __name__ == "__main__":
    main()
