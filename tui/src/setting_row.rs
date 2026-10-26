use ratatui::{
    Frame,
    layout::Rect,
    style::Style,
    text::{Line, Span, Text},
    widgets::{Clear, Paragraph, Wrap},
};

#[derive(Clone, Copy, Debug)]
pub struct SettingRow<'a> {
    pub label: &'a str,
    pub value: &'a str,
    pub selected: bool,
}

#[derive(Clone, Copy, Debug)]
pub struct SettingRowStyle {
    pub base: Style,
    pub selected: Style,
    pub value: Style,
    pub selected_value: Style,
    pub marker: Style,
}

pub fn toggle_value(enabled: bool) -> &'static str {
    if enabled { "[On]" } else { "[Off]" }
}

/// Draw one setting with a stable two-cell focus gutter. Labels and values that
/// do not fit beside each other stack and wrap in the supplied area.
pub fn draw(frame: &mut Frame, area: Rect, row: SettingRow<'_>, style: SettingRowStyle) {
    let area = area.intersection(frame.area());
    if area.is_empty() {
        return;
    }
    let text_style = if row.selected {
        style.base.patch(style.selected)
    } else {
        style.base
    };
    let value_style = text_style.patch(if row.selected {
        style.selected_value
    } else {
        style.value
    });
    let label_width = Line::raw(row.label).width();
    let value_width = Line::raw(row.value).width();
    let available = usize::from(area.width.saturating_sub(3));
    frame.render_widget(Clear, area);
    frame.buffer_mut().set_style(area, style.base);
    if label_width + value_width < available
        && !row.label.contains('\n')
        && !row.value.contains('\n')
        && area.width >= 3
    {
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(
                    if row.selected { "> " } else { "  " },
                    text_style.patch(style.marker),
                ),
                Span::styled(
                    format!(
                        "{}{}",
                        row.label,
                        " ".repeat(available - label_width - value_width)
                    ),
                    text_style,
                ),
                Span::styled(row.value, value_style),
            ]))
            .style(style.base),
            Rect::new(area.x, area.y, area.width, 1),
        );
    } else {
        frame.render_widget(
            Paragraph::new(if row.selected { ">" } else { " " })
                .style(text_style.patch(style.marker)),
            Rect::new(area.x, area.y, 1, 1),
        );
        let content = Rect::new(
            area.x.saturating_add(2).min(area.right()),
            area.y,
            area.width.saturating_sub(3),
            area.height,
        );
        let lines = row
            .label
            .lines()
            .map(|line| Line::styled(line, text_style))
            .chain(
                row.value
                    .lines()
                    .map(|line| Line::styled(line, value_style)),
            )
            .collect::<Vec<_>>();
        frame.render_widget(
            Paragraph::new(Text::from(lines)).wrap(Wrap { trim: false }),
            content,
        );
    }
}
