use ratatui::{
    Frame,
    layout::Rect,
    style::Style,
    text::{Line, Span},
    widgets::{Clear, Paragraph},
};

pub type Hint<'a> = (&'a str, &'a str);

#[derive(Clone, Copy, Debug)]
pub struct HintStyle {
    pub text: Style,
    pub separator: Style,
    pub key: Style,
    pub primary_key: Style,
}

#[derive(Clone, Copy, Debug)]
pub struct FooterStyle {
    pub base: Style,
    pub border: Style,
}

pub fn line<'a>(hints: &[Hint<'a>], style: HintStyle, primary: Option<&str>) -> Line<'a> {
    let mut spans = Vec::new();
    for (index, &(key, label)) in hints.iter().enumerate() {
        if index != 0 {
            spans.push(Span::styled(" · ", style.separator));
        }
        if !key.is_empty() {
            spans.push(Span::styled(
                key,
                if primary == Some(key) {
                    style.primary_key
                } else {
                    style.key
                },
            ));
            spans.push(Span::raw(" "));
        }
        spans.push(Span::styled(label, style.text));
    }
    Line::from(spans)
}

/// Keep complete key/action pairs in the caller's priority order.
pub fn fitting_line<'a>(
    hints: &[Hint<'a>],
    width: u16,
    style: HintStyle,
    primary: Option<&str>,
) -> Line<'a> {
    let mut fitting = Vec::new();
    for &hint in hints {
        fitting.push(hint);
        if line(&fitting, style, primary).width() > usize::from(width) {
            fitting.pop();
        }
    }
    line(&fitting, style, primary)
}

pub fn boundary<'a>(mut line: Line<'a>, width: u16, style: Style) -> Line<'a> {
    let remaining = usize::from(width).saturating_sub(line.width());
    if remaining > 1 {
        if !line.spans.is_empty() {
            line.spans.push(Span::raw(" "));
        }
        let remaining = usize::from(width).saturating_sub(line.width());
        line.spans.push(Span::styled("─".repeat(remaining), style));
    }
    line
}

/// The area includes both side borders. Hosts prepare complete hint rows and
/// own contextual actions, ordering, overflow and consent behavior.
pub fn draw(frame: &mut Frame, area: Rect, rows: &[Line<'_>], style: FooterStyle) {
    let area = area.intersection(frame.area());
    if area.is_empty() {
        return;
    }
    frame.render_widget(Clear, area);
    frame.buffer_mut().set_style(area, style.base);
    for y in area.y..area.bottom() {
        let (left, right) = if y == area.y {
            ("┌", "┐")
        } else if y + 1 == area.bottom() {
            ("└", "┘")
        } else {
            ("│", "│")
        };
        frame.render_widget(
            Paragraph::new(left).style(style.border),
            Rect::new(area.x, y, 1, 1),
        );
        if area.width > 1 {
            frame.render_widget(
                Paragraph::new(right).style(style.border),
                Rect::new(area.right() - 1, y, 1, 1),
            );
        }
    }
    let width = area.width.saturating_sub(2);
    if width == 0 {
        return;
    }
    for (index, line) in rows.iter().take(usize::from(area.height)).enumerate() {
        frame.render_widget(
            Paragraph::new(if index == 0 {
                boundary(line.clone(), width, style.border)
            } else {
                line.clone()
            })
            .style(style.base),
            Rect::new(area.x + 1, area.y + index as u16, width, 1),
        );
    }
}
