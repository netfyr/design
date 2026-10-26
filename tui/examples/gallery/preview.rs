use netfyr_tui_design::dropdown::{self, Dropdown, DropdownLayout, DropdownOption, DropdownStyle};
use ratatui::{
    Frame,
    crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers},
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Text},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap},
};

pub const EXAMPLES: [&str; 5] = [
    "Finite choice",
    "Interface: ready",
    "Interface: empty",
    "Interface: loading",
    "Interface: failed",
];
const PALETTES: [&str; 7] = [
    "Standard",
    "Accessible",
    "Custom — high contrast twilight",
    "Dusk",
    "Dawn",
    "明るい",
    "Éclair",
];
const INTERFACES: [&str; 7] = [
    "eth0",
    "wlan0",
    "br0",
    "veth-workstation",
    "enp6s0",
    "wg0",
    "測試0",
];

#[derive(Default)]
struct Field {
    value: String,
    query: String,
    cursor: usize,
    selected: usize,
    filtering: bool,
    refreshed: bool,
}

pub struct Gallery {
    pub quit: bool,
    selected: usize,
    preview: bool,
    expanded: bool,
    fields: [Field; 5],
    layout: DropdownLayout,
    limited: bool,
    monochrome: bool,
}

impl Gallery {
    pub fn new(monochrome: bool) -> Self {
        Self {
            quit: false,
            selected: 0,
            preview: false,
            expanded: false,
            fields: std::array::from_fn(|index| Field {
                value: if index == 0 { "Standard" } else { "eth0" }.into(),
                ..Field::default()
            }),
            layout: DropdownLayout::default(),
            limited: false,
            monochrome,
        }
    }

    pub fn open(&mut self, index: usize) {
        self.selected = index;
        self.preview = true;
        self.fields[index].refreshed = false;
        self.expand();
    }

    pub fn showing_preview(&self) -> bool {
        self.preview
    }

    fn expand(&mut self) {
        let editable = self.selected != 0;
        let field = &mut self.fields[self.selected];
        field.query = if editable {
            field.value.clone()
        } else {
            String::new()
        };
        field.cursor = field.query.len();
        field.filtering = false;
        field.selected = 0;
        self.expanded = true;
        self.select_value();
    }

    fn options(&self) -> Vec<&'static str> {
        let field = &self.fields[self.selected];
        let source: &[&str] = match self.selected {
            0 => &PALETTES,
            1 => &INTERFACES,
            _ if field.refreshed => &INTERFACES,
            _ => &[],
        };
        let query = field.query.to_lowercase();
        source
            .iter()
            .copied()
            .filter(|option| !field.filtering || option.to_lowercase().contains(&query))
            .collect()
    }

    fn select_value(&mut self) {
        let field = &self.fields[self.selected];
        let selected = self
            .options()
            .iter()
            .position(|option| *option == field.value)
            .unwrap_or(0);
        self.fields[self.selected].selected = selected;
    }

    fn choose(&mut self) -> bool {
        let options = self.options();
        let field = &mut self.fields[self.selected];
        if let Some(option) = options.get(field.selected) {
            field.value = (*option).into();
        } else if self.selected == 0 || field.value.trim().is_empty() {
            return false;
        }
        self.expanded = false;
        true
    }

    pub fn key(&mut self, key: KeyEvent) {
        if key.kind != KeyEventKind::Press {
            return;
        }
        if key.modifiers == KeyModifiers::CONTROL && key.code == KeyCode::Char('c') {
            self.quit = true;
            return;
        }
        let plain = key.modifiers == KeyModifiers::NONE;
        if plain && key.code == KeyCode::Esc {
            if self.expanded {
                self.expanded = false;
            } else if self.preview {
                self.preview = false;
            } else {
                self.quit = true;
            }
            return;
        }
        if plain && key.code == KeyCode::F(4) && self.expanded {
            self.expanded = false;
            return;
        }
        if self.limited {
            return;
        }
        if !self.preview {
            if !plain {
                return;
            }
            match key.code {
                KeyCode::Up | KeyCode::Char('k') => self.selected = self.selected.saturating_sub(1),
                KeyCode::Down | KeyCode::Char('j') => {
                    self.selected = (self.selected + 1).min(EXAMPLES.len() - 1)
                }
                KeyCode::Home => self.selected = 0,
                KeyCode::End => self.selected = EXAMPLES.len() - 1,
                KeyCode::Enter => self.open(self.selected),
                KeyCode::Char('q') => self.quit = true,
                _ => {}
            }
            return;
        }
        if plain && key.code == KeyCode::F(4) {
            self.expand();
            return;
        }
        if key.modifiers == KeyModifiers::ALT && key.code == KeyCode::Down {
            if !self.expanded {
                self.expand();
            }
            return;
        }
        if key.modifiers == KeyModifiers::CONTROL
            && key.code == KeyCode::Char('r')
            && self.selected != 0
        {
            self.fields[self.selected].refreshed = true;
            self.select_value();
            return;
        }
        let tab = (plain && key.code == KeyCode::Tab)
            || (key.modifiers == KeyModifiers::SHIFT && key.code == KeyCode::BackTab);
        if tab {
            if self.expanded {
                self.choose();
            }
            self.expanded = false;
            self.preview = false;
            return;
        }
        if !self.expanded {
            if plain {
                match key.code {
                    KeyCode::Enter => self.expand(),
                    KeyCode::Down if self.selected != 0 => self.expand(),
                    KeyCode::Char('q') => self.quit = true,
                    _ => {}
                }
            }
            return;
        }
        let options = self.options();
        if plain {
            match key.code {
                KeyCode::Enter => {
                    self.choose();
                    return;
                }
                KeyCode::Down | KeyCode::PageDown => {
                    let step = if key.code == KeyCode::PageDown {
                        self.layout.page_down.max(1)
                    } else {
                        1
                    };
                    let field = &mut self.fields[self.selected];
                    field.selected = field
                        .selected
                        .saturating_add(usize::from(step))
                        .min(options.len().saturating_sub(1));
                    return;
                }
                KeyCode::Up | KeyCode::PageUp => {
                    let step = if key.code == KeyCode::PageUp {
                        self.layout.page_up.max(1)
                    } else {
                        1
                    };
                    let field = &mut self.fields[self.selected];
                    field.selected = field.selected.saturating_sub(usize::from(step));
                    return;
                }
                _ => {}
            }
        }
        let field = &mut self.fields[self.selected];
        if edit(&mut field.query, &mut field.cursor, key) {
            field.filtering = true;
            if self.selected != 0 {
                field.value.clone_from(&field.query);
            }
            self.select_value();
        }
    }

    pub fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        self.limited = area.width < 32 || area.height < 12;
        let colour = |rgb| if self.monochrome { Color::Reset } else { rgb };
        let foreground = colour(Color::Rgb(247, 242, 234));
        let surface = colour(Color::Rgb(41, 36, 32));
        let border = colour(Color::Rgb(140, 122, 107));
        let accent = colour(Color::Rgb(255, 122, 26));
        let selected = colour(Color::Rgb(60, 49, 40));
        let base = Style::default().fg(foreground).bg(surface);
        frame.render_widget(Block::default().style(base), area);
        if self.limited {
            frame.render_widget(
                Paragraph::new("Resize to at least 32×12.\nCtrl+C quit · Esc back")
                    .wrap(Wrap { trim: false }),
                area,
            );
            self.layout = DropdownLayout::default();
            return;
        }
        let content = Rect::new(area.x + 1, area.y, area.width - 2, area.height - 4);
        let header = if self.preview {
            EXAMPLES[self.selected]
        } else {
            "Dropdown examples"
        };
        frame.render_widget(
            Paragraph::new(header).style(base.fg(accent).add_modifier(Modifier::BOLD)),
            Rect::new(content.x + 2, content.y, content.width - 2, 1),
        );
        if !self.preview {
            let items: Vec<_> = EXAMPLES.into_iter().map(ListItem::new).collect();
            let mut state = ListState::default().with_selected(Some(self.selected));
            frame.render_stateful_widget(
                List::new(items)
                    .highlight_symbol("▎ ")
                    .highlight_style(base.bg(selected).add_modifier(Modifier::BOLD)),
                Rect::new(content.x, content.y + 2, content.width, content.height - 2),
                &mut state,
            );
        } else {
            let label = if self.selected == 0 {
                "Colour palette"
            } else {
                "Interface name"
            };
            frame.render_widget(
                Paragraph::new(label),
                Rect::new(content.x + 2, content.y + 1, content.width - 2, 1),
            );
            let field = &self.fields[self.selected];
            if self.expanded {
                let input = Rect::new(content.x + 2, content.y + 2, content.width - 2, 1);
                let (query, cursor) = window(&field.query, field.cursor, input.width);
                let text = if field.query.is_empty() {
                    if self.selected == 0 {
                        "Filter choices".into()
                    } else {
                        "Type interface name".into()
                    }
                } else {
                    query
                };
                frame.render_widget(Paragraph::new(text).style(base.bg(selected)), input);
                frame.set_cursor_position((input.x + cursor, input.y));
                let options = self.options();
                let message = if self.selected == 0 {
                    "No matching choices."
                } else if self.selected == 2 && !field.refreshed {
                    "No interfaces found."
                } else if self.selected == 3 && !field.refreshed {
                    "Loading interfaces..."
                } else if self.selected == 4 && !field.refreshed {
                    "Interface list unavailable\nFixture: namespace could not be read."
                } else {
                    "No matching interfaces."
                };
                let list = Rect::new(content.x, content.y + 3, content.width, content.height - 3);
                let label = if self.selected == 0 {
                    "Choices"
                } else {
                    "Interfaces"
                };
                let title = if options.is_empty() {
                    label.into()
                } else {
                    format!("{label} {}/{}", field.selected + 1, options.len())
                };
                self.layout = dropdown::draw(
                    frame,
                    list,
                    Dropdown {
                        title: title.into(),
                        options: options
                            .into_iter()
                            .map(|value| DropdownOption {
                                text: wrapped(value, dropdown::content_width(list.width)),
                                committed: value == field.value,
                            })
                            .collect(),
                        selected: field.selected,
                        message: message.into(),
                    },
                    DropdownStyle::new(foreground, surface, border, accent, selected),
                );
            } else {
                frame.render_widget(
                    Paragraph::new(field.value.as_str())
                        .style(base.fg(accent))
                        .wrap(Wrap { trim: false }),
                    Rect::new(
                        content.x + 2,
                        content.y + 2,
                        content.width - 2,
                        content.height - 2,
                    ),
                );
            }
        }
        let footer = Rect::new(area.x, area.bottom() - 4, area.width, 4);
        frame.render_widget(
            Block::default()
                .borders(Borders::TOP)
                .border_style(Style::default().fg(border))
                .style(base),
            footer,
        );
        let hints = if !self.preview {
            ["↑↓ select · Enter open", "q quit · Ctrl+C quit", ""]
        } else if self.expanded {
            let available = !self.options().is_empty();
            let manual = self.selected != 0 && !self.fields[self.selected].value.trim().is_empty();
            [
                if available {
                    "↑↓ move · Enter choose"
                } else if manual {
                    "Type name · Enter keep"
                } else {
                    "Type to filter"
                },
                if available {
                    "Esc close · Tab choose/back"
                } else if manual {
                    "Esc close · Tab keep/back"
                } else {
                    "Esc close · Tab examples"
                },
                if self.selected == 0 {
                    "Ctrl+U clear · Ctrl+C quit"
                } else {
                    "Ctrl+U clear · Ctrl+R refresh"
                },
            ]
        } else {
            [
                "Enter/F4 choices · Esc back",
                "Tab examples · q quit",
                "Ctrl+C quit",
            ]
        };
        frame.render_widget(
            Paragraph::new(hints.join("\n")),
            Rect::new(footer.x + 2, footer.y + 1, footer.width - 2, 3),
        );
    }
}

fn edit(text: &mut String, cursor: &mut usize, key: KeyEvent) -> bool {
    let plain = key.modifiers == KeyModifiers::NONE;
    if key.modifiers == KeyModifiers::CONTROL && key.code == KeyCode::Char('u') {
        let changed = !text.is_empty();
        text.clear();
        *cursor = 0;
        return changed;
    }
    if !plain && !(key.modifiers == KeyModifiers::SHIFT && matches!(key.code, KeyCode::Char(_))) {
        return false;
    }
    let previous = text[..*cursor]
        .char_indices()
        .next_back()
        .map_or(0, |(index, _)| index);
    let next = text[*cursor..]
        .chars()
        .next()
        .map_or(*cursor, |character| *cursor + character.len_utf8());
    match key.code {
        KeyCode::Left => *cursor = previous,
        KeyCode::Right => *cursor = next,
        KeyCode::Home => *cursor = 0,
        KeyCode::End => *cursor = text.len(),
        KeyCode::Backspace if *cursor > 0 => {
            text.drain(previous..*cursor);
            *cursor = previous;
            return true;
        }
        KeyCode::Delete if *cursor < text.len() => {
            text.drain(*cursor..next);
            return true;
        }
        KeyCode::Char(character)
            if !character.is_control() && text.len() + character.len_utf8() <= 4096 =>
        {
            text.insert(*cursor, character);
            *cursor += character.len_utf8();
            return true;
        }
        _ => {}
    }
    false
}

fn window(text: &str, cursor: usize, width: u16) -> (String, u16) {
    let mut start = 0;
    while Line::raw(&text[start..cursor]).width() >= usize::from(width) {
        start += text[start..].chars().next().unwrap().len_utf8();
    }
    let before = Line::raw(&text[start..cursor]).width() as u16;
    let mut shown = String::new();
    for character in text[start..].chars() {
        if Line::raw(format!("{shown}{character}")).width() > usize::from(width) {
            break;
        }
        shown.push(character);
    }
    (shown, before)
}

fn wrapped(text: &str, width: u16) -> Text<'static> {
    let mut lines = Vec::new();
    let mut line = String::new();
    for character in text.chars() {
        if !line.is_empty() && Line::raw(format!("{line}{character}")).width() > usize::from(width)
        {
            lines.push(Line::raw(std::mem::take(&mut line)));
        }
        line.push(character);
    }
    lines.push(Line::raw(line));
    Text::from(lines)
}

#[cfg(test)]
#[path = "tests.rs"]
mod tests;
