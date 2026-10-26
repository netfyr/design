use netfyr_tui_design::{
    animation, flame, footer,
    glyphs::{Glyph, GlyphSet},
    lanes, setting_row,
};
use ratatui::{
    Frame,
    layout::Rect,
    style::{Color, Modifier, Style},
    text::Line,
    widgets::{Block, Paragraph},
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Sample {
    Activity,
    Flame,
    Traffic,
    Replay,
    Settings,
    Footer,
    Glyphs,
}

pub const SAMPLES: [Sample; 7] = [
    Sample::Activity,
    Sample::Flame,
    Sample::Traffic,
    Sample::Replay,
    Sample::Settings,
    Sample::Footer,
    Sample::Glyphs,
];

impl Sample {
    pub const fn id(self) -> &'static str {
        match self {
            Self::Activity => "activity",
            Self::Flame => "flame",
            Self::Traffic => "traffic",
            Self::Replay => "replay",
            Self::Settings => "settings",
            Self::Footer => "footer",
            Self::Glyphs => "glyphs",
        }
    }

    pub const fn title(self) -> &'static str {
        match self {
            Self::Activity => "Activity indicators",
            Self::Flame => "Flame",
            Self::Traffic => "Traffic lanes",
            Self::Replay => "Trace replay",
            Self::Settings => "Settings rows",
            Self::Footer => "Action footer",
            Self::Glyphs => "Glyphs",
        }
    }

    pub const fn animated(self) -> bool {
        !matches!(self, Self::Settings | Self::Footer | Self::Glyphs)
    }

    pub fn frame_count(self) -> u64 {
        match self {
            Self::Activity => 72,
            Self::Flame => flame::FRAME_COUNT,
            Self::Traffic => 480,
            Self::Replay => lanes::cycle_ticks(120.0, 15),
            Self::Settings | Self::Footer | Self::Glyphs => 0,
        }
    }

    pub const fn dimensions(self) -> (u16, u16) {
        match self {
            Self::Flame => (32, 14),
            Self::Activity => (40, 11),
            Self::Traffic => (40, 11),
            Self::Replay => (40, 10),
            Self::Settings => (40, 8),
            Self::Footer => (40, 8),
            Self::Glyphs => (40, 11),
        }
    }
}

pub struct Samples {
    pub glyphs: GlyphSet,
    pub motion: bool,
    pub eye_candy: bool,
    pub selected_setting: usize,
}

impl Default for Samples {
    fn default() -> Self {
        Self {
            glyphs: GlyphSet::default(),
            motion: true,
            eye_candy: true,
            selected_setting: 0,
        }
    }
}

#[derive(Clone, Copy)]
pub struct Palette {
    pub base: Style,
    pub border: Style,
    pub accent: Style,
    pub selected: Style,
}

impl Palette {
    pub fn new(monochrome: bool) -> Self {
        let colour = |rgb| if monochrome { Color::Reset } else { rgb };
        Self {
            base: Style::default()
                .fg(colour(Color::Rgb(247, 242, 234)))
                .bg(colour(Color::Rgb(41, 36, 32))),
            border: Style::default().fg(colour(Color::Rgb(140, 122, 107))),
            accent: Style::default().fg(colour(Color::Rgb(255, 122, 26))),
            selected: Style::default().bg(colour(Color::Rgb(60, 49, 40))),
        }
    }

    pub fn hints(self) -> footer::HintStyle {
        footer::HintStyle {
            text: self.base,
            separator: self.border,
            key: self.accent,
            primary_key: self.accent.add_modifier(Modifier::BOLD),
        }
    }
}

pub fn draw(
    frame: &mut Frame,
    area: Rect,
    sample: Sample,
    state: &Samples,
    tick: u64,
    motion: bool,
    monochrome: bool,
) {
    let palette = Palette::new(monochrome);
    frame.render_widget(Block::new().style(palette.base), area);
    if area.is_empty() {
        return;
    }
    if sample == Sample::Flame {
        let show_title = area.height > flame::HEIGHT;
        if show_title {
            line(
                frame,
                area,
                0,
                sample.title(),
                palette.accent.add_modifier(Modifier::BOLD),
            );
        }
        if area.width >= flame::WIDTH && area.height >= flame::HEIGHT {
            frame.render_widget(
                Paragraph::new(flame::frame(tick, motion)).style(palette.accent),
                Rect::new(
                    area.x + (area.width - flame::WIDTH) / 2,
                    area.y + u16::from(show_title),
                    flame::WIDTH,
                    flame::HEIGHT,
                ),
            );
        }
        return;
    }
    line(
        frame,
        area,
        0,
        sample.title(),
        palette.accent.add_modifier(Modifier::BOLD),
    );
    match sample {
        Sample::Glyphs => {
            line(
                frame,
                area,
                1,
                match state.glyphs {
                    GlyphSet::Standard => "Standard characters",
                    GlyphSet::Netfyr => "netfyr symbols",
                },
                palette.base,
            );
            for (index, (glyph, label)) in [
                (Glyph::Flame, "Flame"),
                (Glyph::RightSolid, "Right solid"),
                (Glyph::RightOutline, "Right outline"),
                (Glyph::LeftSolid, "Left solid"),
                (Glyph::LeftOutline, "Left outline"),
            ]
            .into_iter()
            .enumerate()
            {
                line(
                    frame,
                    area,
                    3 + index as u16,
                    format!("{}  {label}", state.glyphs.character(glyph)),
                    palette.base,
                );
            }
        }
        Sample::Activity => {
            line(
                frame,
                area,
                2,
                format!("{} Loading records", animation::spinner(tick, motion)),
                palette.base,
            );
            line(
                frame,
                area,
                4,
                format!("Waiting {}", animation::dots(tick, motion)),
                palette.base,
            );
            line(
                frame,
                area,
                6,
                animation::pulse(19, tick, motion),
                palette.accent,
            );
            line(frame, area, 7, "Working · progress unknown", palette.base);
        }
        Sample::Traffic => {
            line(frame, area, 1, "Transmit · fixture rates", palette.base);
            // App logarithmic scale: 0, 0.5, 2.5, 4.5 and 6.5 cells/s.
            // 480 ticks span 46s; rational phases close the 23-cell loops exactly.
            let phase = tick as f64 / Sample::Traffic.frame_count() as f64 * 23.0;
            for (index, (rate, speed)) in [
                ("0 B/s", 0),
                ("1 B/s", 1),
                ("1 KiB/s", 5),
                ("1 MiB/s", 9),
                ("1 GiB/s", 13),
            ]
            .into_iter()
            .enumerate()
            {
                let y = 3 + index as u16;
                line(frame, area, y, format!("{rate:>9}"), palette.base);
                if y < area.height {
                    frame.render_widget(
                        Paragraph::new(lanes::traffic(
                            area.width.saturating_sub(13).min(25),
                            lanes::Direction::Right,
                            speed > 0,
                            motion,
                            phase * f64::from(speed),
                        ))
                        .style(if speed > 0 {
                            palette.accent
                        } else {
                            palette.base
                        }),
                        Rect::new(
                            area.x + area.width.min(13),
                            area.y + y,
                            area.width.saturating_sub(13).min(25),
                            1,
                        ),
                    );
                }
            }
        }
        Sample::Replay => {
            line(frame, area, 1, "Fixture RTT · not hop timing", palette.base);
            line(frame, area, 3, "Reply 120 ms", palette.base);
            line(
                frame,
                area,
                4,
                lanes::replay(16, Some(120.0), tick, motion),
                palette.accent,
            );
            line(frame, area, 6, "No reply", palette.base);
            line(
                frame,
                area,
                7,
                lanes::replay(16, None, tick, motion),
                palette.base,
            );
        }
        Sample::Settings => {
            for (index, (label, enabled)) in
                [("Motion", state.motion), ("Eye candy", state.eye_candy)]
                    .into_iter()
                    .enumerate()
            {
                let y = 2 + index as u16 * 2;
                if y >= area.height {
                    break;
                }
                setting_row::draw(
                    frame,
                    Rect::new(area.x + 1, area.y + y, area.width.saturating_sub(2), 1),
                    setting_row::SettingRow {
                        label,
                        value: setting_row::toggle_value(enabled),
                        selected: state.selected_setting == index,
                    },
                    setting_row::SettingRowStyle {
                        base: palette.base,
                        selected: palette.selected,
                        value: palette.accent,
                        selected_value: palette.accent.add_modifier(Modifier::UNDERLINED),
                        marker: palette.accent.add_modifier(Modifier::BOLD),
                    },
                );
            }
        }
        Sample::Footer => {
            line(frame, area, 2, "Actions for this preview", palette.base);
            let height = area.height.min(4);
            footer::draw(
                frame,
                Rect::new(area.x, area.bottom() - height, area.width, height),
                &[
                    footer::line(&[("Esc", "examples"), ("q", "quit")], palette.hints(), None),
                    footer::line(&[("Ctrl+C", "quit")], palette.hints(), None),
                ],
                footer::FooterStyle {
                    base: palette.base,
                    border: palette.border,
                },
            );
        }
        Sample::Flame => unreachable!(),
    }
}

fn line(frame: &mut Frame, area: Rect, y: u16, value: impl Into<Line<'static>>, style: Style) {
    if y < area.height && area.width > 2 {
        frame.render_widget(
            Paragraph::new(value.into()).style(style),
            Rect::new(area.x + 2, area.y + y, area.width - 2, 1),
        );
    }
}
