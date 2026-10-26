use ratatui::{
    Frame,
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Text},
    widgets::{Block, Borders, Clear, List, ListItem, ListState, Paragraph, Wrap},
};

/// Prepared option text; adapters retain domain formatting and input values.
#[derive(Clone, Debug)]
pub struct DropdownOption<'a> {
    pub text: Text<'a>,
    pub committed: bool,
}

/// A presentation snapshot, independent of the application's input and lookup state.
#[derive(Clone, Debug)]
pub struct Dropdown<'a> {
    pub title: Line<'a>,
    pub options: Vec<DropdownOption<'a>>,
    pub selected: usize,
    pub message: Text<'a>,
}

#[derive(Clone, Copy, Debug)]
pub struct DropdownStyle {
    pub base: Style,
    pub border: Style,
    pub title: Style,
    pub committed: Style,
    pub candidate: Style,
}

impl DropdownStyle {
    pub fn new(
        foreground: Color,
        surface: Color,
        border: Color,
        accent: Color,
        selected: Color,
    ) -> Self {
        Self {
            base: Style::default().fg(foreground).bg(surface),
            border: Style::default().fg(border),
            title: Style::default().fg(accent).add_modifier(Modifier::BOLD),
            committed: Style::default()
                .fg(accent)
                .add_modifier(Modifier::UNDERLINED),
            candidate: Style::default().bg(selected).add_modifier(Modifier::BOLD),
        }
    }
}

/// List geometry after reserving the rule and right edge. Text starts two cells
/// after `rows.x`; the marker occupies the first of those cells.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DropdownLayout {
    pub rows: Rect,
    pub page_rows: u16,
    pub page_up: u16,
    pub page_down: u16,
}

pub fn content_width(width: u16) -> u16 {
    width.saturating_sub(3)
}

pub fn draw(
    frame: &mut Frame,
    area: Rect,
    dropdown: Dropdown<'_>,
    style: DropdownStyle,
) -> DropdownLayout {
    if area.is_empty() {
        return DropdownLayout::default();
    }
    let heading_height = u16::from(area.height > 1);
    let rows = Rect::new(
        area.x,
        area.y + heading_height,
        area.width.saturating_sub(1),
        area.height.saturating_sub(heading_height),
    );
    frame.render_widget(Clear, area);
    frame.render_widget(
        Block::new()
            .borders(if heading_height == 0 {
                Borders::RIGHT
            } else {
                Borders::TOP | Borders::RIGHT
            })
            .border_style(style.border)
            .style(style.base),
        area,
    );
    if heading_height > 0 {
        let title_width = dropdown
            .title
            .width()
            .min(usize::from(content_width(area.width)));
        frame.render_widget(
            Paragraph::new(dropdown.title).style(style.title),
            Rect::new(area.x + 2, area.y, title_width as u16, 1),
        );
    }
    let mut page_up = 1;
    let mut page_down = 1;
    if dropdown.options.is_empty() {
        frame.render_widget(
            Paragraph::new(dropdown.message).wrap(Wrap { trim: false }),
            Rect::new(rows.x + 2, rows.y, content_width(area.width), rows.height),
        );
    } else {
        let selected = dropdown.selected.min(dropdown.options.len() - 1);
        let mut used_rows = 0;
        let mut next_options = 0;
        for option in dropdown.options.iter().skip(selected + 1) {
            let height = option.text.lines.len().max(1);
            if used_rows + height > usize::from(rows.height) {
                break;
            }
            used_rows += height;
            next_options += 1;
        }
        page_down = next_options.max(1);
        let items = dropdown.options.into_iter().map(|mut option| {
            if option.committed {
                for line in &mut option.text.lines {
                    for span in &mut line.spans {
                        span.style = span.style.patch(style.committed);
                    }
                }
            }
            ListItem::new(option.text)
        });
        let mut state = ListState::default().with_selected(Some(selected));
        frame.render_stateful_widget(
            List::new(items.collect::<Vec<_>>())
                .highlight_symbol("▎ ")
                .highlight_style(style.candidate),
            rows,
            &mut state,
        );
        page_up = selected
            .saturating_sub(state.offset())
            .saturating_add(1)
            .min(u16::MAX as usize) as u16;
    }
    DropdownLayout {
        rows,
        page_rows: rows.height.max(1),
        page_up,
        page_down,
    }
}
