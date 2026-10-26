use netfyr_tui_design::{flame, footer, glyphs::GlyphSet};
use ratatui::{
    Frame,
    crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers},
    layout::Rect,
    style::Modifier,
    widgets::{Block, List, ListItem, ListState, Paragraph, Wrap},
};

use super::{
    preview,
    samples::{self, Palette, Sample, Samples},
};

#[derive(Clone, Copy)]
enum Fixture {
    Dropdown(usize),
    Sample(Sample),
}

pub const FIXTURES: [(&str, &str); 12] = [
    ("footer", "Action footer"),
    ("activity", "Activity indicators"),
    ("dropdown-choice", "Dropdown: choices"),
    ("dropdown-empty", "Dropdown: empty"),
    ("dropdown-failed", "Dropdown: failed"),
    ("dropdown-interfaces", "Dropdown: interfaces"),
    ("dropdown-loading", "Dropdown: loading"),
    ("flame", "Flame"),
    ("glyphs", "Glyphs"),
    ("settings", "Settings rows"),
    ("replay", "Trace replay"),
    ("traffic", "Traffic lanes"),
];

pub struct Catalogue {
    pub quit: bool,
    selected: usize,
    active: Option<Fixture>,
    dropdown: preview::Gallery,
    samples: Samples,
    monochrome: bool,
    limited: bool,
    paused: bool,
    tick: u64,
    menu_rows: u16,
}

impl Catalogue {
    pub fn new(monochrome: bool) -> Self {
        Self {
            quit: false,
            selected: 0,
            active: None,
            dropdown: preview::Gallery::new(monochrome),
            samples: Samples::default(),
            monochrome,
            limited: false,
            paused: false,
            tick: 0,
            menu_rows: 1,
        }
    }

    pub fn set_glyphs(&mut self, glyphs: GlyphSet) {
        self.samples.glyphs = glyphs;
    }

    pub fn open(&mut self, id: &str) -> bool {
        let Some(index) = FIXTURES.iter().position(|fixture| fixture.0 == id) else {
            return false;
        };
        let fixture = match id {
            "dropdown-choice" => Fixture::Dropdown(0),
            "dropdown-interfaces" => Fixture::Dropdown(1),
            "dropdown-empty" => Fixture::Dropdown(2),
            "dropdown-loading" => Fixture::Dropdown(3),
            "dropdown-failed" => Fixture::Dropdown(4),
            _ => Fixture::Sample(
                *samples::SAMPLES
                    .iter()
                    .find(|sample| sample.id() == id)
                    .unwrap(),
            ),
        };
        self.selected = index;
        self.active = Some(fixture);
        self.tick = 0;
        self.paused = false;
        if let Fixture::Dropdown(index) = fixture {
            self.dropdown.open(index);
        }
        true
    }

    pub fn animating(&self) -> bool {
        !self.limited
            && !self.paused
            && self.samples.motion
            && matches!(self.active, Some(Fixture::Sample(sample)) if sample.animated())
    }

    pub fn advance(&mut self) {
        if self.animating() {
            self.tick = self.tick.wrapping_add(1);
        }
    }

    pub fn key(&mut self, key: KeyEvent) {
        if key.kind != KeyEventKind::Press {
            return;
        }
        if key.modifiers == KeyModifiers::CONTROL && key.code == KeyCode::Char('c') {
            self.quit = true;
            return;
        }
        if let Some(Fixture::Dropdown(_)) = self.active {
            self.dropdown.key(key);
            self.quit = self.dropdown.quit;
            if !self.dropdown.showing_preview() {
                self.active = None;
            }
            return;
        }
        if key.modifiers != KeyModifiers::NONE {
            return;
        }
        if key.code == KeyCode::Esc {
            if self.active.take().is_none() {
                self.quit = true;
            }
            return;
        }
        if key.code == KeyCode::Char('q') {
            self.quit = true;
            return;
        }
        if self.limited {
            return;
        }
        if let Some(Fixture::Sample(sample)) = self.active {
            if key.code == KeyCode::Char('m') {
                self.samples.motion = !self.samples.motion;
            } else if sample.animated() && key.code == KeyCode::Char(' ') {
                self.paused = !self.paused;
            } else if sample == Sample::Settings {
                match key.code {
                    KeyCode::Up | KeyCode::Char('k') => self.samples.selected_setting = 0,
                    KeyCode::Down | KeyCode::Char('j') => self.samples.selected_setting = 1,
                    KeyCode::Tab => {
                        self.samples.selected_setting = 1 - self.samples.selected_setting
                    }
                    KeyCode::Enter | KeyCode::Char(' ') | KeyCode::Left | KeyCode::Right => {
                        let value = if self.samples.selected_setting == 0 {
                            &mut self.samples.motion
                        } else {
                            &mut self.samples.eye_candy
                        };
                        *value = match key.code {
                            KeyCode::Left => false,
                            KeyCode::Right => true,
                            _ => !*value,
                        };
                    }
                    _ => {}
                }
            }
            return;
        }
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => self.selected = self.selected.saturating_sub(1),
            KeyCode::Down | KeyCode::Char('j') => {
                self.selected = (self.selected + 1).min(FIXTURES.len() - 1)
            }
            KeyCode::Home => self.selected = 0,
            KeyCode::End => self.selected = FIXTURES.len() - 1,
            KeyCode::PageUp => {
                self.selected = self.selected.saturating_sub(usize::from(self.menu_rows))
            }
            KeyCode::PageDown => {
                self.selected =
                    (self.selected + usize::from(self.menu_rows)).min(FIXTURES.len() - 1)
            }
            KeyCode::Enter => {
                self.open(FIXTURES[self.selected].0);
            }
            _ => {}
        }
    }

    pub fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        self.limited = area.width < 32 || area.height < 12;
        let palette = Palette::new(self.monochrome);
        frame.render_widget(Block::new().style(palette.base), area);
        if let Some(Fixture::Dropdown(_)) = self.active {
            self.dropdown.draw(frame);
            return;
        }
        if self.limited {
            frame.render_widget(
                Paragraph::new("Resize to at least 32×12.\nCtrl+C quit · Esc back")
                    .wrap(Wrap { trim: false }),
                area,
            );
            return;
        }
        if let Some(Fixture::Sample(sample)) = self.active {
            let has_footer = sample != Sample::Footer
                && (sample != Sample::Flame || area.height >= flame::HEIGHT + 4);
            let body = Rect::new(
                area.x,
                area.y,
                area.width,
                area.height - if has_footer { 3 } else { 0 },
            );
            samples::draw(
                frame,
                body,
                sample,
                &self.samples,
                self.tick,
                self.samples.motion,
                self.monochrome,
            );
            if has_footer {
                let first = if sample.animated() {
                    vec![
                        ("Space", if self.paused { "play" } else { "pause" }),
                        ("Esc", "examples"),
                    ]
                } else if sample == Sample::Settings {
                    vec![("↑↓", "select"), ("Enter", "toggle")]
                } else {
                    vec![("Esc", "examples"), ("q", "quit")]
                };
                let second = if sample.animated() {
                    vec![("m", "motion"), ("q", "quit")]
                } else if sample == Sample::Settings {
                    vec![("Esc", "examples"), ("q", "quit")]
                } else {
                    vec![("Ctrl+C", "quit")]
                };
                footer::draw(
                    frame,
                    Rect::new(area.x, area.bottom() - 3, area.width, 3),
                    &[
                        footer::fitting_line(&first, area.width - 2, palette.hints(), None),
                        footer::fitting_line(&second, area.width - 2, palette.hints(), None),
                    ],
                    footer::FooterStyle {
                        base: palette.base,
                        border: palette.border,
                    },
                );
            }
            return;
        }
        frame.render_widget(
            Paragraph::new("Component examples").style(palette.accent.add_modifier(Modifier::BOLD)),
            Rect::new(area.x + 2, area.y, area.width - 2, 1),
        );
        self.menu_rows = area.height - 5;
        let mut selected = ListState::default().with_selected(Some(self.selected));
        frame.render_stateful_widget(
            List::new(FIXTURES.map(|(_, title)| ListItem::new(title)))
                .highlight_symbol("▎ ")
                .highlight_style(palette.selected.add_modifier(Modifier::BOLD)),
            Rect::new(area.x, area.y + 2, area.width, self.menu_rows),
            &mut selected,
        );
        footer::draw(
            frame,
            Rect::new(area.x, area.bottom() - 3, area.width, 3),
            &[
                footer::line(
                    &[("↑↓", "select"), ("Enter", "open")],
                    palette.hints(),
                    Some("Enter"),
                ),
                footer::line(&[("q", "quit"), ("Ctrl+C", "quit")], palette.hints(), None),
            ],
            footer::FooterStyle {
                base: palette.base,
                border: palette.border,
            },
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::{Terminal, backend::TestBackend, buffer::Buffer};

    fn press(gallery: &mut Catalogue, key: KeyCode) {
        gallery.key(KeyEvent::new(key, KeyModifiers::NONE));
    }

    fn render(gallery: &mut Catalogue, width: u16, height: u16) -> Buffer {
        let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
        terminal
            .draw(|frame| gallery.draw(frame))
            .unwrap()
            .buffer
            .clone()
    }

    #[test]
    fn fixture_ids_are_stable_and_menu_is_alphabetical() {
        let labels: Vec<_> = FIXTURES.iter().map(|(_, title)| *title).collect();
        let mut ordered = labels.clone();
        ordered.sort();
        assert_eq!(labels, ordered);
        let mut gallery = Catalogue::new(false);
        for (id, _) in FIXTURES {
            assert!(gallery.open(id));
        }
        assert!(!gallery.open("unknown"));
        gallery.open("dropdown-choice");
        press(&mut gallery, KeyCode::Char(' '));
        press(&mut gallery, KeyCode::Char('m'));
        assert!(!gallery.paused);
        assert!(gallery.samples.motion);
        press(&mut gallery, KeyCode::Esc);
        assert!(gallery.active.is_some());
        press(&mut gallery, KeyCode::Esc);
        assert!(gallery.active.is_none());
    }

    #[test]
    fn animation_pauses_without_advancing_and_settings_control_motion() {
        let mut gallery = Catalogue::new(false);
        gallery.open("activity");
        gallery.advance();
        assert_eq!(gallery.tick, 1);
        press(&mut gallery, KeyCode::Char(' '));
        let before = render(&mut gallery, 40, 16);
        for _ in 0..20 {
            gallery.advance();
        }
        assert_eq!(before, render(&mut gallery, 40, 16));
        press(&mut gallery, KeyCode::Char(' '));
        gallery.advance();
        assert_eq!(gallery.tick, 2);
        gallery.open("settings");
        press(&mut gallery, KeyCode::Left);
        gallery.open("flame");
        assert!(!gallery.animating());
        press(&mut gallery, KeyCode::Char('m'));
        assert!(gallery.animating());
    }

    #[test]
    fn glyphs_keep_complete_labels_and_navigation_with_both_character_sets() {
        let labels = [
            "Flame",
            "Right solid",
            "Right outline",
            "Left solid",
            "Left outline",
        ];
        for monochrome in [false, true] {
            let mut gallery = Catalogue::new(monochrome);
            gallery.open("glyphs");
            assert_eq!(gallery.samples.glyphs, GlyphSet::Standard);
            assert!(!gallery.animating());
            for (set, symbols, mode) in [
                (
                    GlyphSet::Standard,
                    ['*', '>', '>', '<', '<'],
                    "Standard characters",
                ),
                (
                    GlyphSet::Netfyr,
                    [
                        '\u{100000}',
                        '\u{100001}',
                        '\u{100002}',
                        '\u{100003}',
                        '\u{100004}',
                    ],
                    "netfyr symbols",
                ),
            ] {
                gallery.set_glyphs(set);
                for (width, height) in [(32, 12), (40, 12), (48, 14), (100, 32)] {
                    let buffer = render(&mut gallery, width, height);
                    let mode_row: String = (2..width).map(|x| buffer[(x, 1)].symbol()).collect();
                    assert_eq!(mode_row.trim_end(), mode);
                    for (index, (symbol, label)) in symbols.into_iter().zip(labels).enumerate() {
                        let y = 3 + index as u16;
                        assert_eq!(buffer[(2, y)].symbol(), symbol.to_string());
                        for x in [0, 1, 3, 4] {
                            assert_eq!(buffer[(x, y)].symbol(), " ");
                        }
                        let text: String = (5..width).map(|x| buffer[(x, y)].symbol()).collect();
                        assert_eq!(text.trim_end(), label);
                    }
                    let footer: String = (height - 3..height)
                        .flat_map(|y| (0..width).map(move |x| (x, y)))
                        .map(|point| buffer[point].symbol())
                        .collect();
                    assert!(footer.contains("Esc examples") && footer.contains("q quit"));
                    assert!(!footer.contains("select") && !footer.contains("toggle"));
                    if monochrome {
                        assert!(buffer.content.iter().all(|cell| {
                            cell.fg == ratatui::style::Color::Reset
                                && cell.bg == ratatui::style::Color::Reset
                        }));
                    }
                    press(&mut gallery, KeyCode::Enter);
                    press(&mut gallery, KeyCode::Char(' '));
                    gallery.advance();
                    assert_eq!(buffer, render(&mut gallery, width, height));
                }
            }
            press(&mut gallery, KeyCode::Esc);
            assert!(gallery.active.is_none());
        }
    }

    #[test]
    fn compact_flame_preserves_artwork_and_resize_blocks_hidden_actions() {
        let mut gallery = Catalogue::new(true);
        gallery.open("flame");
        let buffer = render(&mut gallery, 32, 12);
        let expected: Vec<_> = flame::frame(0, true).lines().collect();
        for y in 0..12 {
            let row: String = (4..28).map(|x| buffer[(x, y)].symbol()).collect();
            assert_eq!(row, expected[usize::from(y)]);
        }
        assert!(
            buffer
                .content
                .iter()
                .all(|cell| cell.fg == ratatui::style::Color::Reset
                    && cell.bg == ratatui::style::Color::Reset)
        );
        gallery.open("settings");
        render(&mut gallery, 20, 8);
        press(&mut gallery, KeyCode::Enter);
        assert!(gallery.samples.motion);
        press(&mut gallery, KeyCode::Esc);
        assert!(gallery.active.is_none());
        for (width, height) in [(32, 12), (40, 12), (48, 14), (100, 32)] {
            for (id, _) in FIXTURES {
                gallery.open(id);
                render(&mut gallery, width, height);
            }
        }
    }
}
