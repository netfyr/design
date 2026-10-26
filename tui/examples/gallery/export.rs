use std::io::{self, Write};

use netfyr_tui_design::{flame, glyphs::GlyphSet};
use ratatui::{
    Terminal,
    backend::TestBackend,
    buffer::Buffer,
    style::{Color, Modifier},
    text::Line,
};

use super::samples::{self, Sample, Samples};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Paint {
    fg: (u8, u8, u8),
    bg: (u8, u8, u8),
    bold: bool,
    underline: bool,
}

#[derive(Debug, PartialEq, Eq)]
struct Run {
    x: u16,
    y: u16,
    style: usize,
    text: String,
    width: u16,
}

struct Preview {
    sample: Sample,
    still: Vec<Run>,
    fallback: Option<Vec<Run>>,
    frames: Vec<Vec<Run>>,
}

pub fn write(output: &mut impl Write) -> io::Result<()> {
    let mut styles = Vec::new();
    let mut previews = Vec::new();
    for sample in samples::SAMPLES {
        let (columns, rows) = sample.dimensions();
        let mut terminal = Terminal::new(TestBackend::new(columns, rows)).unwrap();
        let mut render = |tick, motion, glyphs| -> io::Result<Vec<Run>> {
            let state = Samples {
                glyphs,
                ..Samples::default()
            };
            let completed = terminal
                .draw(|frame| {
                    samples::draw(frame, frame.area(), sample, &state, tick, motion, false);
                })
                .unwrap();
            Ok(runs(completed.buffer, &mut styles))
        };
        previews.push(Preview {
            sample,
            still: render(
                0,
                false,
                if sample == Sample::Glyphs {
                    GlyphSet::Netfyr
                } else {
                    GlyphSet::Standard
                },
            )?,
            fallback: if sample == Sample::Glyphs {
                Some(render(0, false, GlyphSet::Standard)?)
            } else {
                None
            },
            frames: (0..sample.frame_count())
                .map(|tick| render(tick, true, GlyphSet::Standard))
                .collect::<io::Result<_>>()?,
        });
    }
    write!(output, "{{\"version\":1,\"styles\":[")?;
    for (index, paint) in styles.iter().enumerate() {
        if index > 0 {
            write!(output, ",")?;
        }
        write!(
            output,
            "{{\"fg\":\"#{:02x}{:02x}{:02x}\",\"bg\":\"#{:02x}{:02x}{:02x}\",\"bold\":{},\"underline\":{}}}",
            paint.fg.0,
            paint.fg.1,
            paint.fg.2,
            paint.bg.0,
            paint.bg.1,
            paint.bg.2,
            paint.bold,
            paint.underline
        )?;
    }
    write!(output, "],\"previews\":[")?;
    for (index, preview) in previews.iter().enumerate() {
        if index > 0 {
            write!(output, ",")?;
        }
        let (columns, rows) = preview.sample.dimensions();
        write!(output, "{{\"id\":")?;
        string(output, preview.sample.id())?;
        write!(
            output,
            ",\"columns\":{columns},\"rows\":{rows},\"intervalMs\":{},\"still\":",
            flame::FRAME_INTERVAL.as_secs_f64() * 1000.0
        )?;
        frame(output, &preview.still)?;
        if let Some(fallback) = &preview.fallback {
            write!(output, ",\"fallback\":")?;
            frame(output, fallback)?;
        }
        write!(output, ",\"frames\":[")?;
        for (index, data) in preview.frames.iter().enumerate() {
            if index > 0 {
                write!(output, ",")?;
            }
            frame(output, data)?;
        }
        write!(output, "]}}")?;
    }
    writeln!(output, "]}}")
}

fn runs(buffer: &Buffer, styles: &mut Vec<Paint>) -> Vec<Run> {
    let mut result: Vec<Run> = Vec::new();
    for y in buffer.area.y..buffer.area.bottom() {
        let mut x = buffer.area.x;
        while x < buffer.area.right() {
            let cell = &buffer[(x, y)];
            let width = Line::raw(cell.symbol()).width().max(1) as u16;
            let supported = Modifier::BOLD | Modifier::UNDERLINED;
            assert!(
                supported.contains(cell.modifier),
                "Unsupported exported cell modifier: {:?}",
                cell.modifier
            );
            let paint = Paint {
                fg: rgb(cell.fg, (247, 242, 234)),
                bg: rgb(cell.bg, (41, 36, 32)),
                bold: cell.modifier.contains(Modifier::BOLD),
                underline: cell.modifier.contains(Modifier::UNDERLINED),
            };
            let style = styles
                .iter()
                .position(|existing| *existing == paint)
                .unwrap_or_else(|| {
                    styles.push(paint);
                    styles.len() - 1
                });
            let ascii = cell.symbol().is_ascii();
            if ascii
                && let Some(previous) = result.last_mut()
                && previous.y == y
                && previous.x + previous.width == x
                && previous.style == style
                && previous.text.is_ascii()
            {
                previous.text.push_str(cell.symbol());
                previous.width += width;
            } else {
                result.push(Run {
                    x,
                    y,
                    style,
                    text: cell.symbol().into(),
                    width,
                });
            }
            x += width;
        }
    }
    result
}

fn rgb(color: Color, fallback: (u8, u8, u8)) -> (u8, u8, u8) {
    match color {
        Color::Reset => fallback,
        Color::Rgb(r, g, b) => (r, g, b),
        _ => panic!("Gallery export requires explicit RGB colors: {color:?}"),
    }
}

fn frame(output: &mut impl Write, data: &[Run]) -> io::Result<()> {
    write!(output, "[")?;
    for (index, run) in data.iter().enumerate() {
        if index > 0 {
            write!(output, ",")?;
        }
        write!(output, "[{},{},{},", run.x, run.y, run.style)?;
        string(output, &run.text)?;
        write!(output, ",{}]", run.width)?;
    }
    write!(output, "]")
}

fn string(output: &mut impl Write, value: &str) -> io::Result<()> {
    write!(output, "\"")?;
    for character in value.chars() {
        match character {
            '"' => write!(output, "\\\"")?,
            '\\' => write!(output, "\\\\")?,
            '\0'..='\u{1f}' => write!(output, "\\u{:04x}", character as u32)?,
            _ => write!(output, "{character}")?,
        }
    }
    write!(output, "\"")
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::{layout::Rect, style::Style, widgets::Paragraph};

    #[test]
    fn json_strings_escape_controls_quotes_and_backslashes() {
        let mut output = Vec::new();
        string(&mut output, "\"\\\n\0\u{1f}é界").unwrap();
        assert_eq!(
            String::from_utf8(output).unwrap(),
            "\"\\\"\\\\\\u000a\\u0000\\u001fé界\""
        );
    }

    #[test]
    fn glyph_export_includes_explicit_custom_and_standard_frames() {
        let mut output = Vec::new();
        write(&mut output).unwrap();
        let json = String::from_utf8(output).unwrap();
        assert_eq!(json.matches("\"fallback\":").count(), 1);
        let (_, glyphs) = json.split_once("\"id\":\"glyphs\"").unwrap();
        let (custom, fallback) = glyphs.split_once("\"fallback\":").unwrap();
        assert!(custom.contains("netfyr symbols"));
        for character in [
            '\u{100000}',
            '\u{100001}',
            '\u{100002}',
            '\u{100003}',
            '\u{100004}',
        ] {
            assert!(custom.contains(character));
            assert!(!fallback.contains(character));
        }
        assert!(fallback.contains("Standard characters"));
        assert!(fallback.contains("\"frames\":[]"));
        for label in [
            "Flame",
            "Right solid",
            "Right outline",
            "Left solid",
            "Left outline",
        ] {
            assert!(custom.contains(label) && fallback.contains(label));
        }
    }

    #[test]
    fn runs_preserve_wide_cells_styles_and_blank_backgrounds() {
        let mut terminal = Terminal::new(TestBackend::new(8, 1)).unwrap();
        let completed = terminal
            .draw(|frame| {
                frame.render_widget(
                    Paragraph::new("界e\u{301}")
                        .style(Style::new().add_modifier(Modifier::UNDERLINED)),
                    frame.area(),
                );
                frame.render_widget(
                    Paragraph::new(" ").style(Style::new().bg(Color::Rgb(1, 2, 3))),
                    Rect::new(6, 0, 1, 1),
                );
            })
            .unwrap();
        let mut styles = Vec::new();
        let data = runs(completed.buffer, &mut styles);
        assert_eq!(data[0].text, "界");
        assert_eq!((data[0].x, data[0].width), (0, 2));
        assert_eq!(data[1].text, "e\u{301}");
        assert_eq!((data[1].x, data[1].width), (2, 1));
        assert!(styles[data[0].style].underline);
        assert!(
            data.iter()
                .any(|run| run.x == 6 && styles[run.style].bg == (1, 2, 3))
        );
        assert_eq!(data.iter().map(|run| run.width).sum::<u16>(), 8);
    }

    fn traffic_frame(terminal: &mut Terminal<TestBackend>, tick: u64, motion: bool) -> Buffer {
        terminal
            .draw(|frame| {
                samples::draw(
                    frame,
                    frame.area(),
                    Sample::Traffic,
                    &Samples::default(),
                    tick,
                    motion,
                    false,
                );
            })
            .unwrap()
            .buffer
            .clone()
    }

    #[test]
    fn transfer_rates_have_distinct_speeds_without_moving_the_idle_lane() {
        let mut terminal = Terminal::new(TestBackend::new(40, 11)).unwrap();
        let first = traffic_frame(&mut terminal, 0, true);
        let marker = |buffer: &Buffer, y| {
            (13..38)
                .find(|&x| buffer[(x, y)].symbol() == "o")
                .expect("active transfer must retain its marker")
        };
        let mut positions = [4, 5, 6, 7].map(|y| marker(&first, y));
        let mut distance = [0; 4];
        for tick in 1..=Sample::Traffic.frame_count() {
            let buffer = traffic_frame(&mut terminal, tick, true);
            for x in 0..40 {
                assert_eq!(buffer[(x, 3)], first[(x, 3)], "idle lane moved");
            }
            for (index, y) in [4, 5, 6, 7].into_iter().enumerate() {
                let current = marker(&buffer, y);
                let previous = positions[index];
                if current != previous {
                    assert!(
                        current == previous + 1 || (previous == 36 && current == 14),
                        "rate row {y} skipped or reversed a cell at tick {tick}"
                    );
                    distance[index] += 1;
                }
                positions[index] = current;
            }
        }
        assert_eq!(distance, [23, 115, 207, 299]);
    }

    #[test]
    fn transfer_rate_labels_and_lanes_keep_their_columns_on_narrow_grids() {
        let labels = ["0 B/s", "1 B/s", "1 KiB/s", "1 MiB/s", "1 GiB/s"];
        for (width, arrow) in [(32, 31), (40, 37), (48, 37), (100, 37)] {
            let mut terminal = Terminal::new(TestBackend::new(width, 9)).unwrap();
            for motion in [false, true] {
                let buffer = traffic_frame(&mut terminal, 117, motion);
                for (index, label) in labels.into_iter().enumerate() {
                    let y = 3 + index as u16;
                    let field: String = (2..11).map(|x| buffer[(x, y)].symbol()).collect();
                    assert_eq!(field.trim_start(), label);
                    assert_eq!(buffer[(10, y)].symbol(), "s");
                    for x in [0, 1, 11, 12] {
                        assert_eq!(buffer[(x, y)].symbol(), " ");
                    }
                    assert_eq!(buffer[(13, y)].symbol(), "-");
                    assert_eq!(buffer[(arrow, y)].symbol(), ">");
                    let markers = (13..arrow)
                        .filter(|&x| buffer[(x, y)].symbol() == "o")
                        .count();
                    assert_eq!(markers, usize::from(index > 0));
                    for x in arrow + 1..width {
                        assert_eq!(buffer[(x, y)].symbol(), " ");
                    }
                }
            }
        }
    }

    #[test]
    fn sample_frames_change_only_when_motion_is_enabled() {
        for sample in samples::SAMPLES {
            let (width, height) = sample.dimensions();
            let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
            let mut draw = |tick, motion, monochrome| {
                terminal
                    .draw(|frame| {
                        samples::draw(
                            frame,
                            frame.area(),
                            sample,
                            &Samples::default(),
                            tick,
                            motion,
                            monochrome,
                        )
                    })
                    .unwrap()
                    .buffer
                    .clone()
            };
            assert_eq!(draw(0, false, false), draw(400, false, false));
            if sample.animated() {
                let initial = draw(0, true, false);
                assert!(
                    (1..sample.frame_count()).any(|tick| draw(tick, true, false) != initial),
                    "{} did not move",
                    sample.id()
                );
                assert_eq!(
                    initial,
                    draw(sample.frame_count(), true, false),
                    "{} has a discontinuous loop",
                    sample.id()
                );
            }
            let buffer = draw(8, true, true);
            assert!(
                buffer
                    .content
                    .iter()
                    .all(|cell| cell.fg == Color::Reset && cell.bg == Color::Reset)
            );
        }
    }
}
