use netfyr_tui_design::dropdown::{self, Dropdown, DropdownOption, DropdownStyle};
use ratatui::{
    Terminal,
    backend::TestBackend,
    buffer::Buffer,
    layout::Rect,
    style::{Color, Modifier},
    text::Text,
};

fn draw(width: u16, height: u16, selected: usize, monochrome: bool) -> Buffer {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    let color = |value| if monochrome { Color::Reset } else { value };
    terminal
        .draw(|frame| {
            let layout = dropdown::draw(
                frame,
                frame.area(),
                Dropdown {
                    title: "Choices".into(),
                    options: vec![
                        DropdownOption {
                            text: "é界 current value".into(),
                            committed: true,
                        },
                        DropdownOption {
                            text: "Candidate".into(),
                            committed: false,
                        },
                    ],
                    selected,
                    message: Text::default(),
                },
                DropdownStyle::new(
                    color(Color::White),
                    color(Color::Black),
                    color(Color::Gray),
                    color(Color::Yellow),
                    color(Color::DarkGray),
                ),
            );
            assert_eq!(layout.rows.x, 0);
            assert_eq!(layout.page_rows, height.saturating_sub(1).max(1));
        })
        .unwrap();
    terminal.backend().buffer().clone()
}

#[test]
fn committed_and_keyboard_candidate_are_distinct_without_colour_or_suffixes() {
    for width in [30, 38, 46, 96, 136] {
        for monochrome in [false, true] {
            for selected in [0, 1] {
                let buffer = draw(width, 4, selected, monochrome);
                assert_eq!(buffer[(0, selected as u16 + 1)].symbol(), "▎");
                assert_eq!(buffer[(2, 0)].symbol(), "C");
                assert_eq!(buffer[(2, 1)].symbol(), "é");
                assert_eq!(buffer[(6, 1)].symbol(), "c");
                assert_eq!(buffer[(2, 2)].symbol(), "C");
                assert!(buffer[(2, 1)].modifier.contains(Modifier::UNDERLINED));
                assert!(!buffer[(2, 2)].modifier.contains(Modifier::UNDERLINED));
                assert!(
                    buffer[(2, selected as u16 + 1)]
                        .modifier
                        .contains(Modifier::BOLD)
                );
                assert_eq!(buffer[(width - 1, 0)].symbol(), "┐");
                assert_eq!(buffer[(width - 1, 1)].symbol(), "│");
                if monochrome {
                    for cell in &buffer.content {
                        assert_eq!(cell.fg, Color::Reset);
                        assert_eq!(cell.bg, Color::Reset);
                    }
                }
            }
        }
    }
}

#[test]
fn a_single_available_row_keeps_the_selected_option_visible() {
    let buffer = draw(30, 1, 1, true);
    assert_eq!(buffer[(0, 0)].symbol(), "▎");
    assert_eq!(buffer[(2, 0)].symbol(), "C");
}

#[test]
fn empty_loading_and_error_messages_share_the_option_content_origin() {
    for message in [
        "No matching choices.",
        "Loading interfaces...",
        "Interface list unavailable",
    ] {
        let mut terminal = Terminal::new(TestBackend::new(32, 12)).unwrap();
        terminal
            .draw(|frame| {
                dropdown::draw(
                    frame,
                    Rect::new(1, 3, 30, 4),
                    Dropdown {
                        title: "Choices".into(),
                        options: Vec::new(),
                        selected: 0,
                        message: message.into(),
                    },
                    DropdownStyle::new(
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                    ),
                );
            })
            .unwrap();
        let buffer = terminal.backend().buffer();
        assert_eq!(buffer[(3, 3)].symbol(), "C");
        assert_eq!(buffer[(3, 4)].symbol(), &message[..1]);
        assert_eq!(buffer[(30, 3)].symbol(), "┐");
    }
}

#[test]
fn paging_steps_follow_rendered_item_heights_in_both_directions() {
    let heights = [1, 1, 1, 1, 4, 2, 3, 3, 3];
    let render = |selected| {
        let mut terminal = Terminal::new(TestBackend::new(30, 7)).unwrap();
        let mut layout = dropdown::DropdownLayout::default();
        terminal
            .draw(|frame| {
                layout = dropdown::draw(
                    frame,
                    frame.area(),
                    Dropdown {
                        title: "Choices".into(),
                        options: heights
                            .iter()
                            .enumerate()
                            .map(|(index, height)| DropdownOption {
                                text: (0..*height)
                                    .map(|row| format!("Choice {index} row {row}"))
                                    .collect::<Vec<_>>()
                                    .join("\n")
                                    .into(),
                                committed: false,
                            })
                            .collect(),
                        selected,
                        message: Text::default(),
                    },
                    DropdownStyle::new(
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                        Color::Reset,
                    ),
                );
            })
            .unwrap();
        (layout, terminal.backend().buffer().clone())
    };
    let (layout, buffer) = render(5);
    assert_eq!(layout.page_rows, 6);
    assert_eq!(buffer[(2, 1)].symbol(), "C");
    assert_eq!(buffer[(9, 1)].symbol(), "4");
    assert_eq!(
        layout.page_up, 2,
        "the preceding page must include Choice 3"
    );
    assert_eq!(
        layout.page_down, 2,
        "two three-row options fit the next page"
    );
    let (previous, buffer) = render(5 - usize::from(layout.page_up));
    assert_eq!(buffer[(9, 4)].symbol(), "3");
    assert_eq!(
        previous.page_down, 2,
        "the next four-row and two-row options fit"
    );
}
