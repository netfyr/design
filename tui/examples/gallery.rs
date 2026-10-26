#[path = "gallery/catalogue.rs"]
mod catalogue;
#[path = "gallery/export.rs"]
mod export;
#[path = "gallery/preview.rs"]
mod preview;
#[path = "gallery/samples.rs"]
mod samples;

use std::io::{self, IsTerminal, Write};
use std::time::{Duration, Instant};

use netfyr_tui_design::{flame, glyphs::GlyphSet};
use ratatui::{
    Terminal,
    backend::TestBackend,
    buffer::Buffer,
    crossterm::event::{self, Event},
    text::Line,
};

use catalogue::Catalogue;

fn main() -> io::Result<()> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let options = parse_args(args.iter().map(String::as_str))?;
    match options.command {
        Command::Interactive => interactive(options.fixture, options.glyphs),
        Command::Snapshot => snapshot(options.glyphs),
        Command::ExportPreviews => export::write(&mut io::stdout().lock()),
        Command::Help => {
            println!(
                "Component gallery\n\ncargo run --example gallery\ncargo run --example gallery -- --fixture flame\ncargo run --example gallery -- --fixture glyphs --glyphs netfyr\ncargo run --example gallery -- --snapshot\ncargo run --example gallery -- --export-previews\n\nChoose a fixture with arrows and Enter. Esc returns; q or Ctrl+C quits.\nAnimations: Space pauses/plays; m toggles motion.\nSettings rows: arrows select, Enter/Space toggles, Left/Right sets Off/On.\nDropdowns: type to filter; Enter chooses; Esc closes before returning.\nTab chooses and returns. F4 or Alt+Down opens choices.\nCtrl+R refreshes the synthetic interface list.\nLeft/Right, Home/End, Backspace/Delete and Ctrl+U edit the query.\nPgUp/PgDown moves through choices. Printable shortcuts remain text in inputs.\n\n--snapshot prints deterministic plain text without terminal interaction.\n--glyphs standard|netfyr selects glyphs for the gallery or snapshot; standard is the default.\nInstall netfyr symbols for terminals with font fallback before choosing netfyr glyphs.\n--export-previews writes deterministic styled terminal frames as JSON.\nNO_COLOR preserves underline and selection markers without colours.\nAt 32×12 the flame uses all rows; its keys remain available without hints.\nAll examples use in-memory fixtures; no network or settings are accessed."
            );
            println!("\nFixture IDs:");
            for (id, _) in catalogue::FIXTURES {
                println!("  {id}");
            }
            Ok(())
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
enum Command {
    #[default]
    Interactive,
    Snapshot,
    ExportPreviews,
    Help,
}

#[derive(Debug, PartialEq, Eq)]
struct Options<'a> {
    command: Command,
    fixture: Option<&'a str>,
    glyphs: GlyphSet,
}

fn parse_args<'a>(args: impl IntoIterator<Item = &'a str>) -> io::Result<Options<'a>> {
    let invalid = |message| io::Error::new(io::ErrorKind::InvalidInput, message);
    let mut args = args.into_iter();
    let mut command = None;
    let mut fixture = None;
    let mut glyphs = None;
    while let Some(argument) = args.next() {
        match argument {
            "--fixture" if fixture.is_none() => {
                let id = args.next().ok_or_else(|| invalid("Missing fixture ID."))?;
                if !catalogue::FIXTURES.iter().any(|(known, _)| *known == id) {
                    return Err(invalid("Unknown fixture; use --help for IDs."));
                }
                fixture = Some(id);
            }
            "--glyphs" if glyphs.is_none() => {
                glyphs = Some(match args.next() {
                    Some("standard") => GlyphSet::Standard,
                    Some("netfyr") => GlyphSet::Netfyr,
                    _ => return Err(invalid("Use --glyphs standard or --glyphs netfyr.")),
                });
            }
            "--snapshot" | "--export-previews" | "--help" | "-h" if command.is_none() => {
                command = Some(match argument {
                    "--snapshot" => Command::Snapshot,
                    "--export-previews" => Command::ExportPreviews,
                    _ => Command::Help,
                });
            }
            _ => {
                return Err(invalid(
                    "Unknown or repeated option; use --help for gallery options.",
                ));
            }
        }
    }
    let command = command.unwrap_or_default();
    if (fixture.is_some() && command != Command::Interactive)
        || (glyphs.is_some() && matches!(command, Command::ExportPreviews | Command::Help))
    {
        return Err(invalid(
            "These options cannot be combined; use --help for gallery options.",
        ));
    }
    Ok(Options {
        command,
        fixture,
        glyphs: glyphs.unwrap_or_default(),
    })
}

fn interactive(fixture: Option<&str>, glyphs: GlyphSet) -> io::Result<()> {
    let mut gallery = Catalogue::new(std::env::var_os("NO_COLOR").is_some());
    gallery.set_glyphs(glyphs);
    if let Some(id) = fixture
        && !gallery.open(id)
    {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "Unknown fixture; use --help for IDs.",
        ));
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "The gallery needs an interactive terminal. Use --snapshot for plain text.",
        ));
    }
    let mut terminal = match ratatui::try_init() {
        Ok(terminal) => terminal,
        Err(error) => {
            ratatui::restore();
            return Err(error);
        }
    };
    let result = (|| {
        let mut previous = Instant::now();
        loop {
            terminal.draw(|frame| gallery.draw(frame))?;
            let animated = gallery.animating();
            let timeout = if animated {
                flame::FRAME_INTERVAL.saturating_sub(previous.elapsed())
            } else {
                Duration::from_secs(60)
            };
            if event::poll(timeout)?
                && let Event::Key(key) = event::read()?
            {
                gallery.key(key);
                if gallery.quit {
                    break;
                }
            }
            if !animated {
                previous = Instant::now();
            } else if previous.elapsed() >= flame::FRAME_INTERVAL {
                gallery.advance();
                previous = Instant::now();
            }
        }
        Ok(())
    })();
    ratatui::restore();
    result
}

fn snapshot(glyphs: GlyphSet) -> io::Result<()> {
    let mut terminal = Terminal::new(TestBackend::new(64, 16)).unwrap();
    let mut gallery = Catalogue::new(true);
    gallery.set_glyphs(glyphs);
    let mut output = io::stdout().lock();
    for (id, _) in catalogue::FIXTURES {
        gallery.open(id);
        let completed = terminal.draw(|frame| gallery.draw(frame)).unwrap();
        write_frame(completed.buffer, &mut output)?;
        writeln!(output)?;
    }
    Ok(())
}

fn write_frame(buffer: &Buffer, output: &mut impl Write) -> io::Result<()> {
    for y in buffer.area.y..buffer.area.bottom() {
        let mut row = String::new();
        let mut x = buffer.area.x;
        while x < buffer.area.right() {
            let symbol = buffer[(x, y)].symbol();
            row.push_str(symbol);
            x += Line::raw(symbol).width().max(1) as u16;
        }
        writeln!(output, "{}", row.trim_end())?;
    }
    Ok(())
}

#[cfg(test)]
mod argument_tests {
    use super::*;

    #[test]
    fn glyphs_require_explicit_selection_and_work_with_fixture_or_snapshot() {
        assert_eq!(parse_args([]).unwrap().glyphs, GlyphSet::Standard);
        for args in [
            ["--fixture", "glyphs", "--glyphs", "netfyr"],
            ["--glyphs", "netfyr", "--fixture", "glyphs"],
        ] {
            assert_eq!(
                parse_args(args).unwrap(),
                Options {
                    command: Command::Interactive,
                    fixture: Some("glyphs"),
                    glyphs: GlyphSet::Netfyr,
                }
            );
        }
        for args in [
            ["--snapshot", "--glyphs", "netfyr"],
            ["--glyphs", "netfyr", "--snapshot"],
        ] {
            let options = parse_args(args).unwrap();
            assert_eq!(options.command, Command::Snapshot);
            assert_eq!(options.glyphs, GlyphSet::Netfyr);
        }
        for flag in ["--snapshot", "--export-previews", "--help", "-h"] {
            assert_eq!(parse_args([flag]).unwrap().glyphs, GlyphSet::Standard);
        }
        assert_eq!(
            parse_args(["--glyphs", "standard"]).unwrap().glyphs,
            GlyphSet::Standard
        );
    }

    #[test]
    fn malformed_or_conflicting_gallery_options_fail() {
        for args in [
            vec!["--glyphs"],
            vec!["--glyphs", "auto"],
            vec!["--glyphs", "netfyr", "--glyphs", "standard"],
            vec!["--fixture"],
            vec!["--fixture", "unknown"],
            vec!["--fixture", "glyphs", "--fixture", "flame"],
            vec!["--snapshot", "--fixture", "glyphs"],
            vec!["--snapshot", "--export-previews"],
            vec!["--export-previews", "--glyphs", "netfyr"],
            vec!["--help", "--glyphs", "netfyr"],
            vec!["--help", "--help"],
            vec!["--unknown"],
            vec!["glyphs"],
        ] {
            assert_eq!(
                parse_args(args).unwrap_err().kind(),
                io::ErrorKind::InvalidInput
            );
        }
    }
}
