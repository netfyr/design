#!/usr/bin/env python3
"""Capture the real interactive gallery through isolated Kitty instances."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "web/tui/screenshots"
COLUMNS, ROWS = 48, 16
FONT = "Noto Sans Mono"
FIXTURES = (
    ("dropdown-choice", "Finite choice", "Choices 2/7", "明るい"),
    ("dropdown-interfaces", "Interface: ready", "Interfaces 1/7", "測試0"),
    ("dropdown-empty", "Interface: empty", "No interfaces found."),
    ("dropdown-loading", "Interface: loading", "Loading interfaces..."),
    ("dropdown-failed", "Interface: failed", "Interface list unavailable", "Fixture: namespace could not be read."),
)


@dataclass(frozen=True)
class Step:
    keys: tuple = ()
    contains: tuple = ()
    excludes: tuple = ()
    patterns: tuple = ()
    delay: int = 80


def interaction_steps(fixture):
    if fixture == "dropdown-choice":
        return (
            Step(contains=("Finite choice", "Choices 1/7"), delay=120),
            Step(("down",), ("Choices 2/7",)),
            Step(("d",), ("Choices 1/3",), delay=60),
            Step(("z",), ("No matching choices.",), delay=110),
            Step(("ctrl+u",), ("Choices 1/7",)),
            Step(("d",), ("Choices 1/3",), delay=50),
            Step(("u",), ("Choices 1/1", "Dusk")),
            Step(("enter",), ("Dusk", "Enter/F4 choices"), delay=110),
            Step(("f4",), ("Choices 4/7",)),
            Step(("down",), ("Choices 5/7",)),
            Step(("escape",), ("Dusk", "Enter/F4 choices"), ("Dawn",), delay=110),
            Step(("f4",), ("Choices 4/7",)),
            Step(("up", "up", "up"), ("Choices 1/7",)),
            Step(("enter",), ("Standard", "Enter/F4 choices")),
            Step(("f4",), ("Choices 1/7",), delay=100),
        )
    if fixture == "dropdown-interfaces":
        return (
            Step(contains=("Interface: ready", "Interfaces 1/7", "eth0"), delay=120),
            Step(("ctrl+u",), ("Type interface name", "Interfaces 1/7")),
            Step(("w",), ("Interfaces 1/3",), delay=60),
            Step(("g",), ("Interfaces 1/1", "wg0")),
            Step(("enter",), ("wg0", "Enter/F4 choices"), delay=110),
            Step(("f4",), ("Interfaces 6/7",)),
            Step(("ctrl+u", "m"), ("No matching interfaces.",), delay=60),
            Step(tuple("anual0"), ("manual0", "No matching interfaces.")),
            Step(("enter",), ("manual0", "Enter/F4 choices"), delay=110),
            Step(("f4",), ("manual0", "Interfaces 1/7")),
            Step(("down",), ("Interfaces 2/7",)),
            Step(("enter",), ("wlan0", "Enter/F4 choices"), delay=110),
            Step(("f4", "up"), ("Interfaces 1/7",)),
            Step(("enter",), ("eth0", "Enter/F4 choices")),
            Step(("f4",), ("Interfaces 1/7", "eth0"), delay=100),
        )
    if fixture.startswith("dropdown-"):
        _, title, *messages = next(item for item in FIXTURES if item[0] == fixture)
        return (
            Step(contains=(title, "eth0", *messages), delay=140),
            Step(("ctrl+u",), ("Type interface name", *messages)),
            Step(("w",), tuple(messages), delay=60),
            Step(("g",), ("wg", *messages)),
            Step(("ctrl+r",), ("Interfaces 1/1", "wg0"), tuple(messages), delay=140),
            Step(("enter",), ("wg0", "Enter/F4 choices"), delay=110),
            Step(("f4",), ("Interfaces 6/7",)),
            Step(("up", "up", "up", "up", "up", "enter", "escape", "enter"),
                 (title, "eth0", *messages), delay=100),
        )
    if fixture == "settings":
        def settings(keys=(), selected="Motion", motion="On", candy="On", delay=90):
            return Step(keys, ("Settings rows",), patterns=(
                rf"(?m)^\s*>\s+{re.escape(selected)}\s+\[",
                rf"Motion\s+\[{motion}\]", rf"Eye candy\s+\[{candy}\]",
            ), delay=delay)
        return (
            settings(delay=120),
            settings(("enter",), motion="Off"),
            settings(("down",), selected="Eye candy", motion="Off"),
            settings(("enter",), selected="Eye candy", motion="Off", candy="Off", delay=120),
            settings(("up",), motion="Off", candy="Off"),
            settings(("right",), candy="Off"),
            settings(("down",), selected="Eye candy", candy="Off"),
            settings(("right",), selected="Eye candy"),
            settings(("up",), delay=100),
        )
    raise ValueError(f"Unknown fixture: {fixture}")


def run(*arguments, **kwargs):
    return subprocess.run(arguments, check=True, text=True, capture_output=True, **kwargs).stdout


def png_dimensions(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise RuntimeError(f"Invalid PNG: {path}")
    return struct.unpack(">II", header[16:24])


class GalleryCapture:
    def __init__(self, executable, fixture, directory):
        self.directory = directory
        self.address = f"unix:{directory / 'kitty.sock'}"
        self.window_id = None
        self.dimensions = None
        self.process = None
        self.log = None
        self.executable = executable
        self.fixture = fixture

    def remote(self, *arguments):
        return run("kitty", "@", "--to", self.address, "--use-password", "never", *arguments, timeout=10)

    def key(self, name):
        self.remote("send-key", "--match", f"id:{self.window_id}", name)

    def wait_for(self, step):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            text = self.remote("get-text", "--match", f"id:{self.window_id}")
            if (all(fragment in text for fragment in step.contains)
                    and not any(fragment in text for fragment in step.excludes)
                    and all(re.search(pattern, text) for pattern in step.patterns)):
                return
            time.sleep(0.05)
        raise RuntimeError(f"Gallery did not reach expected state: {step}\n{text}")

    def screenshot(self, destination):
        self.remote("screenshot", "--match", f"id:{self.window_id}", str(destination))
        size = png_dimensions(destination)
        if self.dimensions is None:
            self.dimensions = size
        if size != self.dimensions or size[0] % COLUMNS or size[1] % ROWS:
            raise RuntimeError(f"Inconsistent terminal screenshot dimensions: {size}")

    def __enter__(self):
        options = {
            "allow_remote_control": "socket-only", "font_family": FONT,
            "bold_font": f"{FONT} Bold", "font_size": "16",
            "initial_window_width": f"{COLUMNS}c", "initial_window_height": f"{ROWS}c",
            "remember_window_size": "no", "window_padding_width": "0",
            "window_margin_width": "0", "hide_window_decorations": "yes",
            "cursor_blink_interval": "0", "cursor_shape": "beam",
            "background": "#292420", "foreground": "#f7f2ea",
            "background_opacity": "1", "sync_to_monitor": "no",
        }
        command = ["kitty", "--config", "NONE", "--session", "none", "--start-as=hidden",
                   "--listen-on", self.address]
        for name, value in options.items():
            command.extend(("--override", f"{name}={value}"))
        command.extend((self.executable, "--fixture", self.fixture))
        environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith("KITTY_") and key not in ("NO_COLOR", "TERM", "COLORTERM", "WINDOWID")
        }
        self.directory.mkdir()
        self.log = (self.directory / "kitty.log").open("w+")
        try:
            self.process = subprocess.Popen(command, env=environment, stdout=self.log, stderr=self.log)
            deadline = time.monotonic() + 10
            while not (self.directory / "kitty.sock").exists():
                if self.process.poll() is not None or time.monotonic() > deadline:
                    self.log.seek(0)
                    raise RuntimeError(f"Kitty did not start: {self.log.read()}")
                time.sleep(0.05)
            windows = [window for os_window in json.loads(self.remote("ls"))
                       for tab in os_window["tabs"] for window in tab["windows"]]
            if len(windows) != 1 or windows[0]["cmdline"] != command[-3:]:
                raise RuntimeError("The capture instance must contain exactly its own gallery window.")
            window = windows[0]
            self.window_id = window["id"]
            if (window["columns"], window["lines"]) != (COLUMNS, ROWS):
                raise RuntimeError(f"Kitty did not create the requested {COLUMNS}×{ROWS} terminal.")
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.process is not None and self.process.poll() is None:
            if self.window_id is not None:
                try:
                    self.key("ctrl+c")
                    self.process.wait(timeout=2)
                except (subprocess.SubprocessError, OSError):
                    pass
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
        if self.log is not None:
            self.log.close()

    def __exit__(self, *_):
        self.close()


def encode_gif(frames, destination):
    palette = destination.with_suffix(".palette.png")
    run("magick", *(str(path) for path, _ in frames), "-append", "+dither", "-colors", "256",
        "-unique-colors", str(palette), timeout=60)
    arguments = ["magick", "-loop", "0", "-dispose", "None"]
    for path, delay in frames:
        arguments.extend(("-delay", str(delay), str(path)))
    arguments.extend(("+dither", "-remap", str(palette), "-layers", "Optimize", str(destination)))
    run(*arguments, timeout=60)
    hashes = run("magick", str(destination), "-coalesce", "-format", "%#\n", "info:", timeout=60).splitlines()
    if len(hashes) < 2 or len(set(hashes)) < 2:
        raise RuntimeError(f"Recording does not contain changing frames: {destination}")
    if hashes[0] != hashes[-1]:
        raise RuntimeError(f"Recording does not return to its initial screen: {destination}")
    delays = run("magick", "identify", "-format", "%T\n", str(destination), timeout=30).splitlines()
    if sum(map(int, delays)) != sum(delay for _, delay in frames):
        raise RuntimeError(f"GIF encoding changed interaction pacing: {destination}")


def capture(gifs=False):
    for command in ("cargo", "kitty", "fc-match", *(("magick",) if gifs else ())):
        if not shutil.which(command):
            raise RuntimeError(f"Required command is missing: {command}")
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        raise RuntimeError("Kitty capture requires an available X11 or Wayland display.")
    family = run("fc-match", "-f", "%{family}", FONT).strip()
    if FONT not in family.split(","):
        raise RuntimeError(f"Install {FONT}; fontconfig currently substitutes {family}.")
    run("kitty", "@", "screenshot", "--help")
    build = run("cargo", "build", "--locked", "--manifest-path", str(ROOT / "tui/Cargo.toml"),
                "--example", "gallery", "--message-format=json", cwd=ROOT)
    executable = next(artifact["executable"] for line in build.splitlines()
                      if (artifact := json.loads(line)).get("reason") == "compiler-artifact"
                      and artifact.get("target", {}).get("name") == "gallery" and artifact.get("executable"))
    with tempfile.TemporaryDirectory(prefix="netfyr-gallery-") as directory:
        temporary = Path(directory)
        completed = []
        fixtures = [item[0] for item in FIXTURES] + (["settings"] if gifs else [])
        dimensions = None
        for fixture in fixtures:
            with GalleryCapture(executable, fixture, temporary / fixture) as gallery:
                if gifs:
                    frames = []
                    for index, step in enumerate(interaction_steps(fixture)):
                        for key in step.keys:
                            gallery.key(key)
                        gallery.wait_for(step)
                        path = gallery.directory / f"{index:02d}.png"
                        gallery.screenshot(path)
                        frames.append((path, step.delay))
                    destination = temporary / f"{fixture}.gif"
                    encode_gif(frames, destination)
                    completed.append(destination)
                    if fixture == "settings":
                        poster = temporary / "settings.png"
                        shutil.copyfile(frames[0][0], poster)
                        completed.append(poster)
                else:
                    if fixture == "dropdown-choice":
                        gallery.key("down")
                    expected = next(item[1:] for item in FIXTURES if item[0] == fixture)
                    gallery.wait_for(Step(contains=expected))
                    destination = temporary / f"{fixture}.png"
                    gallery.screenshot(destination)
                    completed.append(destination)
                if dimensions is None:
                    dimensions = gallery.dimensions
                if dimensions != gallery.dimensions:
                    raise RuntimeError("Fixture dimensions differ between terminal windows.")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for source in completed:
            destination = OUTPUT / source.name
            shutil.copyfile(source, destination)
            print(f"{destination.relative_to(ROOT)}: {dimensions[0]}×{dimensions[1]}, {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gifs", action="store_true",
                        help="Record dropdown and settings interactions; keep existing PNG screenshots unchanged.")
    capture(parser.parse_args().gifs)
