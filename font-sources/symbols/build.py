#!/usr/bin/env python3
# SPDX-License-Identifier: OFL-1.1
"""Build the netfyr symbols companion from the published Mono Regular font."""

import argparse
import hashlib
import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import fontTools
from fontTools import subset
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable


SOURCE_FILE = "netfyrmono-Regular.ttf"
SOURCE_SHA256 = "242ae4bb9d29636c4105ac1c745421fdf73f181f5803bab3cc5861cf059a892f"
LICENSE_SHA256 = "90761d8cea97cbc8fe1f7c7d7454212c83164ab38a30802ea5b8a78e426777b4"
FAMILY = "netfyr symbols"
STEM = "netfyrsymbols-Regular"
VERSION = "1.000"
MAPPINGS = (
    (0x100000, 0xE000, "Flame"),
    (0x100001, 0xE0B0, "Right solid"),
    (0x100002, 0xE0B1, "Right outline"),
    (0x100003, 0xE0B2, "Left solid"),
    (0x100004, 0xE0B3, "Left outline"),
)
NOTICE = """netfyr symbols 1.000

Derived from the five original symbols in netfyr mono Regular 0.507.
The glyph outlines and 640-unit advances are unchanged. New character mappings
use U+100000 through U+100004. The original font release remains unchanged.

This font and its build source use the SIL Open Font License 1.1; see OFL.txt.
The license covers every glyph, including the flame. Standalone netfyr artwork
and the netfyr marks have separate rights. Font licensing does not grant
trademark permission or permission to use netfyr as another project's identity.
"""
INSTALL = """netfyr symbols

Install netfyrsymbols-Regular.ttf using your system's font installer or user
font directory. On Linux, a user font directory is ~/.local/share/fonts/.
Reopen the terminal if it caches the fonts available before installation.

The companion contains five symbols and no ordinary text characters. Terminals
with font fallback can use it for those symbols while retaining their text font.
The font must be installed on the computer displaying the terminal; installing
it only on a remote SSH host does not provide the client with the glyphs.

Fallback behavior depends on the terminal. These private-use character values
avoid known Nerd Font and Powerline ranges but are not globally reserved.
See OFL.txt for the font license and NOTICE.txt for its source.
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_source(directory):
    data = (directory / SOURCE_FILE).read_bytes()
    license_data = (directory / "OFL.txt").read_bytes()
    if sha(data) != SOURCE_SHA256:
        raise ValueError("Source font differs from the published 0.507 Mono Regular")
    if sha(license_data) != LICENSE_SHA256:
        raise ValueError("OFL.txt differs from the source font's published license")
    font = TTFont(BytesIO(data), recalcTimestamp=False)
    licenses = [n.toUnicode() for n in font["name"].names if n.nameID == 13]
    if not licenses or any(text != license_data.decode("utf-8") for text in licenses):
        raise ValueError("Embedded font license differs from OFL.txt")
    return data, license_data


def license_records(font):
    return sorted(
        (r.platformID, r.platEncID, r.langID, r.nameID, bytes(r.string))
        for r in font["name"].names
        if r.nameID in (0, 13, 14)
    )


def outline(font, glyph):
    glyphs = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyphs)
    glyphs[glyph].draw(pen)
    return pen.value


def build_ttf(source):
    font = TTFont(BytesIO(source), recalcTimestamp=False)
    original_cmap = font.getBestCmap()
    glyphs = [original_cmap[old] for _, old, _ in MAPPINGS]
    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.name_legacy = True
    options.glyph_names = True
    options.notdef_outline = True
    options.layout_features = []
    options.drop_tables += ["GDEF", "GPOS", "GSUB"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=glyphs)
    subsetter.subset(font)

    cmap = {new: original_cmap[old] for new, old, _ in MAPPINGS}
    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = []
    for platform, encoding in ((0, 4), (3, 10)):
        table = CmapSubtable.newSubtable(12)
        table.platformID = platform
        table.platEncID = encoding
        table.language = 0
        table.cmap = dict(cmap)
        font["cmap"].tables.append(table)

    names = {
        1: FAMILY,
        2: "Regular",
        3: f"{VERSION};netfyr;{STEM}",
        4: f"{FAMILY} Regular",
        5: f"Version {VERSION}",
        6: STEM,
        10: "Five original netfyr mono symbols with supplementary private-use mappings.",
        16: FAMILY,
        17: "Regular",
    }
    for name_id, text in names.items():
        font["name"].removeNames(nameID=name_id)
        for platform, encoding, language in ((0, 3, 0), (3, 1, 0x409)):
            font["name"].setName(text, name_id, platform, encoding, language)
    font["head"].fontRevision = float(VERSION)
    font["OS/2"].recalcUnicodeRanges(font)
    font["OS/2"].usFirstCharIndex = 0xFFFF
    font["OS/2"].usLastCharIndex = 0xFFFF
    font["OS/2"].ulCodePageRange1 = 0
    font["OS/2"].ulCodePageRange2 = 0
    stream = BytesIO()
    font.save(stream, reorderTables=True)
    return stream.getvalue()


def verify_font(source, result):
    before = TTFont(BytesIO(source), recalcTimestamp=False)
    after = TTFont(BytesIO(result), recalcTimestamp=False)
    expected = {new: before.getBestCmap()[old] for new, old, _ in MAPPINGS}
    if after.getBestCmap() != expected:
        raise ValueError("Companion cmap does not contain exactly the five new mappings")
    if {(t.platformID, t.platEncID, t.format) for t in after["cmap"].tables} != {
        (0, 4, 12), (3, 10, 12)
    } or any(t.cmap != expected for t in after["cmap"].tables):
        raise ValueError("Both supplementary Unicode cmap subtables must agree")
    if set(after.getGlyphOrder()) != {".notdef", *expected.values()}:
        raise ValueError("Unexpected glyphs in the companion")
    for glyph in after.getGlyphOrder():
        if outline(before, glyph) != outline(after, glyph):
            raise ValueError(f"Source outline changed: {glyph}")
        if before["hmtx"][glyph] != after["hmtx"][glyph]:
            raise ValueError(f"Source advance or bearing changed: {glyph}")
    for table, fields in {
        "head": ("unitsPerEm",),
        "hhea": ("ascent", "descent", "lineGap"),
        "OS/2": ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"),
        "post": ("isFixedPitch",),
    }.items():
        if any(getattr(before[table], key) != getattr(after[table], key) for key in fields):
            raise ValueError(f"Source cell metrics changed: {table}")
    if license_records(before) != license_records(after) or after["OS/2"].fsType != 0:
        raise ValueError("Source licensing or embedding permissions changed")
    if after["head"].fontRevision != 1.0:
        raise ValueError("Incorrect companion font revision")
    for name_id, text in ((1, FAMILY), (16, FAMILY), (6, STEM), (5, f"Version {VERSION}")):
        records = [r.toUnicode() for r in after["name"].names if r.nameID == name_id]
        if not records or any(value != text for value in records):
            raise ValueError(f"Incorrect companion name record: {name_id}")


def web_font(ttf):
    font = TTFont(BytesIO(ttf), recalcTimestamp=False)
    font.flavor = "woff2"
    output = BytesIO()
    font.save(output)
    return output.getvalue()


def download(files):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for filename in (f"{STEM}.ttf", "OFL.txt", "NOTICE.txt", "README.txt"):
            info = zipfile.ZipInfo(filename, date_time=(2026, 10, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[filename])
    return output.getvalue()


def outputs(source, license_data, ttf_only):
    ttf = build_ttf(source)
    verify_font(source, ttf)
    files = {
        f"{STEM}.ttf": ttf,
        "OFL.txt": license_data,
        "NOTICE.txt": NOTICE.encode("utf-8"),
        "README.txt": INSTALL.encode("utf-8"),
    }
    if not ttf_only:
        woff2 = web_font(ttf)
        verify_font(source, woff2)
        files[f"{STEM}.woff2"] = woff2
        files["netfyr-symbols.zip"] = download(files)
    manifest = {
        "schema": "netfyr-symbols/v1",
        "family": FAMILY,
        "version": VERSION,
        "license": "OFL-1.1",
        "source": {"file": SOURCE_FILE, "version": "0.507", "sha256": SOURCE_SHA256},
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "fonttools": fontTools.__version__,
        "glyphs": [
            {"codepoint": f"U+{new:06X}", "source_codepoint": f"U+{old:04X}", "name": name, "advance": 640}
            for new, old, name in MAPPINGS
        ],
        "verification": {
            "source_outlines_and_metrics_preserved": True,
            "license_records_preserved": True,
            "only_declared_mappings": True,
            "scope": "Exact derivation checks against the published source; no new visual review or terminal compatibility certification.",
        },
        "files": {name: {"sha256": sha(data), "bytes": len(data)} for name, data in sorted(files.items())},
    }
    files["symbols-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Published 0.507 fonts directory")
    parser.add_argument("--output", required=True, type=Path, help="Companion output directory")
    parser.add_argument("--ttf-only", action="store_true", help="Omit WOFF2 and ZIP; does not require Brotli")
    parser.add_argument("--verify", action="store_true", help="Rebuild in memory and compare existing outputs without writing")
    args = parser.parse_args()
    source, license_data = read_source(args.source)
    files = outputs(source, license_data, args.ttf_only)
    if args.verify:
        for filename, expected in files.items():
            if (args.output / filename).read_bytes() != expected:
                raise ValueError(f"Companion output differs from a fresh build: {filename}")
        print(f"Verified {len(files)} companion files, mappings, source geometry, metrics and OFL")
        return
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, data in files.items():
        with tempfile.NamedTemporaryFile(dir=args.output, prefix=f".{filename}-", delete=False) as temp:
            temp.write(data)
            path = Path(temp.name)
        try:
            path.chmod(0o644)
            path.replace(args.output / filename)
        finally:
            path.unlink(missing_ok=True)
    print(f"Built {len(files)} companion files in {args.output}")


if __name__ == "__main__":
    main()
