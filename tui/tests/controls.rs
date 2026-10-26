use netfyr_tui_design::{footer, setting_row};
use ratatui::{
    Terminal,
    backend::TestBackend,
    buffer::Buffer,
    layout::Rect,
    style::{Color, Modifier, Style},
    text::Line,
    widgets::Paragraph,
};

fn draw(width: u16, height: u16, render: impl FnOnce(&mut ratatui::Frame)) -> Buffer {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(render).unwrap().buffer.clone()
}

fn setting_style(monochrome: bool) -> setting_row::SettingRowStyle {
    let color = |color| if monochrome { Color::Reset } else { color };
    setting_row::SettingRowStyle {
        base: Style::default()
            .fg(color(Color::White))
            .bg(color(Color::Black)),
        selected: Style::default()
            .bg(color(Color::DarkGray))
            .add_modifier(Modifier::BOLD),
        value: Style::default().fg(color(Color::Gray)),
        selected_value: Style::default().fg(color(Color::Yellow)),
        marker: Style::default(),
    }
}

fn hint_style(monochrome: bool) -> footer::HintStyle {
    let color = |color| if monochrome { Color::Reset } else { color };
    let key = if monochrome {
        Style::default().add_modifier(Modifier::BOLD | Modifier::REVERSED)
    } else {
        Style::default()
            .fg(Color::White)
            .bg(Color::DarkGray)
            .add_modifier(Modifier::BOLD)
    };
    footer::HintStyle {
        text: Style::default().fg(color(Color::White)),
        separator: Style::default().fg(color(Color::Gray)),
        key,
        primary_key: if monochrome {
            key
        } else {
            Style::default()
                .fg(Color::Black)
                .bg(Color::Yellow)
                .add_modifier(Modifier::BOLD)
        },
    }
}

fn row(buffer: &Buffer, y: u16) -> String {
    let mut value = String::new();
    let mut x = buffer.area.x;
    while x < buffer.area.right() {
        let symbol = buffer[(x, y)].symbol();
        value.push_str(symbol);
        x += Line::raw(symbol).width().max(1) as u16;
    }
    value
}

#[test]
fn setting_rows_keep_the_focus_gutter_and_right_edge_across_sizes_and_color_modes() {
    for width in [32, 40, 48, 100] {
        for monochrome in [false, true] {
            let style = setting_style(monochrome);
            let area = Rect::new(2, 1, width - 4, 2);
            let buffer = draw(width, 4, |frame| {
                setting_row::draw(
                    frame,
                    area,
                    setting_row::SettingRow {
                        label: "Motion",
                        value: setting_row::toggle_value(true),
                        selected: true,
                    },
                    style,
                );
                setting_row::draw(
                    frame,
                    Rect::new(area.x, 2, area.width, 1),
                    setting_row::SettingRow {
                        label: "装飾",
                        value: setting_row::toggle_value(false),
                        selected: false,
                    },
                    style,
                );
            });
            assert_eq!(buffer[(area.x, 1)].symbol(), ">");
            assert_eq!(buffer[(area.x, 2)].symbol(), " ");
            assert_eq!(buffer[(area.x + 2, 1)].symbol(), "M");
            assert_eq!(buffer[(area.x + 2, 2)].symbol(), "装");
            assert_eq!(buffer[(area.right() - 2, 1)].symbol(), "]");
            assert_eq!(buffer[(area.right() - 2, 2)].symbol(), "]");
            assert_eq!(buffer[(area.right() - 1, 1)].symbol(), " ");
            assert!(buffer[(area.x, 1)].modifier.contains(Modifier::BOLD));
            assert!(!buffer[(area.x + 2, 2)].modifier.contains(Modifier::BOLD));
            assert_eq!(
                buffer[(area.right() - 5, 1)].fg,
                if monochrome {
                    Color::Reset
                } else {
                    Color::Yellow
                }
            );
            assert_eq!(buffer[(area.x - 1, 1)].bg, Color::Reset);
        }
    }
}

#[test]
fn setting_rows_require_a_gap_between_label_and_value() {
    for (label, value, width) in [("Eye candy", "[On]", 16), ("装飾", "[Off]", 12)] {
        for extra in [0, 1] {
            let buffer = draw(width + extra, 2, |frame| {
                setting_row::draw(
                    frame,
                    frame.area(),
                    setting_row::SettingRow {
                        label,
                        value,
                        selected: true,
                    },
                    setting_style(false),
                );
            });
            let expected = if extra == 0 {
                [format!("> {label}"), format!("  {value}")]
            } else {
                [format!("> {label} {value}"), String::new()]
            };
            assert_eq!(row(&buffer, 0).trim_end(), expected[0]);
            assert_eq!(row(&buffer, 1).trim_end(), expected[1]);
        }
    }
}

#[test]
fn long_setting_content_stacks_inside_the_supplied_area() {
    let area = Rect::new(3, 1, 20, 5);
    let buffer = draw(28, 7, |frame| {
        frame.render_widget(Paragraph::new("outside"), Rect::new(0, 6, 7, 1));
        setting_row::draw(
            frame,
            area,
            setting_row::SettingRow {
                label: "Default network view",
                value: "Interfaces ▾",
                selected: true,
            },
            setting_style(false),
        );
    });
    assert!(row(&buffer, 1).contains("Default network"));
    assert_eq!(buffer[(area.x + 2, 2)].symbol(), "v");
    assert!(row(&buffer, 3).contains("Interfaces ▾"));
    assert!(row(&buffer, 6).contains("outside"));
    for y in area.y..area.bottom() {
        assert_eq!(buffer[(area.x - 1, y)].bg, Color::Reset);
        assert_eq!(buffer[(area.right(), y)].bg, Color::Reset);
    }
}

#[test]
fn footer_fits_whole_unicode_key_action_pairs_without_partial_hints() {
    let hints = [("Enter", "開く"), ("↑↓", "move"), ("Esc", "back")];
    let style = hint_style(false);
    let line = footer::fitting_line(&hints, 20, style, Some("Enter"));
    assert_eq!(line.to_string(), "Enter 開く · ↑↓ move");
    assert_eq!(line.width(), 20);
    assert_eq!(footer::fitting_line(&hints, 3, style, None).to_string(), "");
    let first = footer::line(&[("Enter", "choose")], style, Some("Enter"));
    assert_eq!(first.spans[0].style.bg, Some(Color::Yellow));
    let review = footer::line(&[("y", "approve"), ("n", "cancel")], style, None);
    assert_eq!(review.spans[0].style, review.spans[4].style);
}

#[test]
fn footer_fills_panel_and_keeps_monochrome_keycaps_distinct() {
    for width in [32, 40, 48, 100] {
        for monochrome in [false, true] {
            let base = Style::default().bg(if monochrome {
                Color::Reset
            } else {
                Color::Black
            });
            let style = footer::FooterStyle {
                base,
                border: Style::default().fg(Color::Gray),
            };
            let hints = footer::fitting_line(
                &[("↑↓", "move"), ("Enter", "choose"), ("Esc", "back")],
                width - 4,
                hint_style(monochrome),
                Some("Enter"),
            );
            let area = Rect::new(1, 1, width - 2, 4);
            let buffer = draw(width, 6, |frame| footer::draw(frame, area, &[hints], style));
            assert_eq!(buffer[(area.x, area.y)].symbol(), "┌");
            assert_eq!(buffer[(area.right() - 1, area.bottom() - 1)].symbol(), "┘");
            assert_eq!(buffer[(area.x, 2)].symbol(), "│");
            for y in area.y..area.bottom() {
                for x in area.x..area.right() {
                    if y > area.y || x == area.x || x == area.right() - 1 {
                        assert_eq!(buffer[(x, y)].bg, base.bg.unwrap());
                    }
                }
            }
            let key = &buffer[(area.x + 1, area.y)];
            assert!(key.modifier.contains(Modifier::BOLD));
            assert_eq!(key.modifier.contains(Modifier::REVERSED), monochrome);
            assert!(
                !buffer[(area.x + 4, area.y)]
                    .modifier
                    .contains(Modifier::REVERSED)
            );
            assert_eq!(buffer[(area.x - 1, area.y)].bg, Color::Reset);
        }
    }
}

#[test]
fn shared_controls_bound_empty_and_clipped_rectangles() {
    for area in [
        Rect::default(),
        Rect::new(3, 2, 0, 2),
        Rect::new(3, 2, 1, 1),
        Rect::new(8, 3, 10, 10),
    ] {
        draw(10, 5, |frame| {
            footer::draw(
                frame,
                area,
                &[Line::raw("Example")],
                footer::FooterStyle {
                    base: Style::default(),
                    border: Style::default(),
                },
            );
            setting_row::draw(
                frame,
                area,
                setting_row::SettingRow {
                    label: "Motion",
                    value: "[On]",
                    selected: true,
                },
                setting_style(true),
            );
        });
    }
}
