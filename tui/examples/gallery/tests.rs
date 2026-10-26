use super::*;
use ratatui::{Terminal, backend::TestBackend, buffer::Buffer};

fn press(gallery: &mut Gallery, code: KeyCode) {
    gallery.key(KeyEvent::new(code, KeyModifiers::NONE));
}

fn control(gallery: &mut Gallery, letter: char) {
    gallery.key(KeyEvent::new(KeyCode::Char(letter), KeyModifiers::CONTROL));
}

fn render(gallery: &mut Gallery, width: u16, height: u16) -> Buffer {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(|frame| gallery.draw(frame)).unwrap();
    terminal.backend().buffer().clone()
}

#[test]
fn finite_candidates_commit_only_on_choice_and_unmatched_queries_cannot_commit() {
    let mut gallery = Gallery::new(false);
    gallery.open(0);
    press(&mut gallery, KeyCode::Down);
    assert_eq!(gallery.fields[0].value, "Standard");
    press(&mut gallery, KeyCode::Esc);
    press(&mut gallery, KeyCode::F(4));
    assert_eq!(gallery.fields[0].selected, 0);
    for ch in "missing".chars() {
        press(&mut gallery, KeyCode::Char(ch));
    }
    press(&mut gallery, KeyCode::Enter);
    assert!(gallery.expanded);
    assert_eq!(gallery.fields[0].value, "Standard");
    press(&mut gallery, KeyCode::Tab);
    assert!(!gallery.preview);
    gallery.open(0);
    press(&mut gallery, KeyCode::Down);
    let buffer = render(&mut gallery, 32, 12);
    let footer: String = (0..32).map(|x| buffer[(x, 10)].symbol()).collect();
    assert!(footer.contains("Tab choose/back"));
    press(&mut gallery, KeyCode::Tab);
    assert_eq!(gallery.fields[0].value, "Accessible");
    assert!(!gallery.preview);
    gallery.open(0);
    press(&mut gallery, KeyCode::Down);
    press(&mut gallery, KeyCode::Enter);
    assert_eq!(gallery.fields[0].value, PALETTES[2]);
    assert!(!gallery.expanded);
}

#[test]
fn manual_names_survive_closing_and_failed_lists_can_retry_without_replacing_input() {
    let mut gallery = Gallery::new(false);
    for index in 1..EXAMPLES.len() {
        gallery.open(index);
        control(&mut gallery, 'u');
        for character in "橋é0".chars() {
            press(&mut gallery, KeyCode::Char(character));
        }
        press(&mut gallery, KeyCode::Left);
        press(&mut gallery, KeyCode::Backspace);
        assert_eq!(gallery.fields[index].value, "橋0");
        press(&mut gallery, KeyCode::Home);
        press(&mut gallery, KeyCode::Delete);
        assert_eq!(gallery.fields[index].value, "0");
        press(&mut gallery, KeyCode::Esc);
        assert_eq!(gallery.fields[index].value, "0");
        press(&mut gallery, KeyCode::F(4));
        control(&mut gallery, 'r');
        assert_eq!(gallery.fields[index].value, "0");
        assert_eq!(gallery.options().len(), INTERFACES.len());
        control(&mut gallery, 'u');
        for character in "manual0".chars() {
            press(&mut gallery, KeyCode::Char(character));
        }
        press(&mut gallery, KeyCode::Enter);
        assert!(!gallery.expanded);
        assert_eq!(gallery.fields[index].value, "manual0");
    }
}

#[test]
fn text_owns_shortcuts_and_modifiers_do_not_activate_controls() {
    let mut gallery = Gallery::new(false);
    gallery.open(0);
    for character in "qjk?".chars() {
        press(&mut gallery, KeyCode::Char(character));
    }
    assert_eq!(gallery.fields[0].query, "qjk?");
    assert!(!gallery.quit);
    for modifiers in [
        KeyModifiers::CONTROL,
        KeyModifiers::ALT,
        KeyModifiers::SUPER,
    ] {
        gallery.key(KeyEvent::new(KeyCode::Enter, modifiers));
        gallery.key(KeyEvent::new(KeyCode::Esc, modifiers));
        gallery.key(KeyEvent::new(KeyCode::Char('q'), modifiers));
    }
    gallery.key(KeyEvent::new_with_kind(
        KeyCode::Esc,
        KeyModifiers::NONE,
        KeyEventKind::Release,
    ));
    gallery.key(KeyEvent::new_with_kind(
        KeyCode::Enter,
        KeyModifiers::NONE,
        KeyEventKind::Repeat,
    ));
    assert!(gallery.expanded);
    assert_eq!(gallery.fields[0].query, "qjk?");
    assert!(!gallery.quit);
    control(&mut gallery, 'c');
    assert!(gallery.quit);
}

#[test]
fn compact_buffers_keep_origins_markers_full_error_and_footer_in_monochrome() {
    for (width, height) in [(32, 12), (40, 12), (48, 14), (100, 32)] {
        let mut gallery = Gallery::new(true);
        gallery.open(0);
        press(&mut gallery, KeyCode::Down);
        let buffer = render(&mut gallery, width, height);
        assert_eq!(buffer[(3, 3)].symbol(), "C");
        assert_eq!(buffer[(3, 4)].symbol(), "S");
        assert_eq!(buffer[(1, 5)].symbol(), "▎");
        assert!(buffer[(3, 4)].modifier.contains(Modifier::UNDERLINED));
        assert!(!buffer[(3, 5)].modifier.contains(Modifier::UNDERLINED));
        assert_eq!(buffer[(2, height - 3)].symbol(), "↑");
        assert!(
            buffer
                .content
                .iter()
                .all(|cell| cell.fg == Color::Reset && cell.bg == Color::Reset)
        );
        gallery.open(4);
        let buffer = render(&mut gallery, width, height);
        let body: String = buffer.content.iter().map(|cell| cell.symbol()).collect();
        assert!(body.contains("read."));
        for index in [2, 3] {
            gallery.open(index);
            let buffer = render(&mut gallery, width, height);
            assert_eq!(buffer[(3, 4)].symbol(), if index == 2 { "N" } else { "L" });
        }
    }
}

#[test]
fn paging_uses_widget_steps_and_resize_blocks_hidden_choices() {
    let mut gallery = Gallery::new(false);
    gallery.open(0);
    render(&mut gallery, 32, 12);
    let expected = usize::from(gallery.layout.page_down);
    press(&mut gallery, KeyCode::PageDown);
    assert_eq!(gallery.fields[0].selected, expected);
    render(&mut gallery, 20, 8);
    press(&mut gallery, KeyCode::Enter);
    press(&mut gallery, KeyCode::Tab);
    assert_eq!(gallery.fields[0].value, "Standard");
    assert!(gallery.preview && gallery.expanded);
    render(&mut gallery, 100, 32);
    press(&mut gallery, KeyCode::Enter);
    assert_eq!(gallery.fields[0].value, PALETTES[expected]);
    press(&mut gallery, KeyCode::F(4));
    render(&mut gallery, 20, 8);
    press(&mut gallery, KeyCode::F(4));
    assert!(
        !gallery.expanded,
        "closing stays available below the minimum"
    );
}

#[test]
fn unicode_query_window_keeps_the_cursor_inside_and_on_a_char_boundary() {
    let mut gallery = Gallery::new(false);
    gallery.open(1);
    control(&mut gallery, 'u');
    for character in "界é".repeat(40).chars() {
        press(&mut gallery, KeyCode::Char(character));
    }
    for width in [1, 2, 29, 80] {
        let field = &gallery.fields[1];
        let (text, caret) = window(&field.query, field.cursor, width);
        assert!(Line::raw(text).width() <= usize::from(width));
        assert!(caret < width);
    }
    render(&mut gallery, 32, 12);
}

#[test]
fn snapshots_preserve_wide_labels_and_clear_previous_frame_contents() {
    let mut gallery = Gallery::new(true);
    let mut terminal = Terminal::new(TestBackend::new(64, 16)).unwrap();
    for index in [0, 1, 2] {
        gallery.open(index);
        let completed = terminal.draw(|frame| gallery.draw(frame)).unwrap();
        let mut output = Vec::new();
        super::super::write_frame(completed.buffer, &mut output).unwrap();
        let snapshot = String::from_utf8(output).unwrap();
        match index {
            0 => assert!(snapshot.contains("明るい")),
            1 => assert!(snapshot.contains("測試0")),
            _ => {
                assert!(snapshot.contains("No interfaces found."));
                for row in snapshot.lines().skip(5).take(7) {
                    assert_eq!(row.trim(), "│", "previous labels leaked: {row:?}");
                }
            }
        }
    }
}
