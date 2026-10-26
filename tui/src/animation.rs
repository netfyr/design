//! Indeterminate activity indicators. Hosts supply a tick and label the pending work.
//! One tick uses the same interval as [`crate::flame::FRAME_INTERVAL`].

pub fn spinner(tick: u64, motion: bool) -> &'static str {
    if motion {
        ["◜", "◝", "◞", "◟"][(tick / 2 % 4) as usize]
    } else {
        "●"
    }
}

/// Three-cell activity indicator.
pub fn dots(tick: u64, motion: bool) -> &'static str {
    if motion {
        [".  ", ".. ", "..."][(tick / 3 % 3) as usize]
    } else {
        "..."
    }
}

/// A pulse that moves within exactly `width` cells. Motion off centers the pulse.
pub fn pulse(width: u16, tick: u64, motion: bool) -> String {
    let width = usize::from(width);
    if width == 0 {
        return String::new();
    }
    let position = if motion && width > 1 {
        let span = (width - 1) as u64;
        let step = (tick / 2) % (span * 2);
        (if step <= span { step } else { span * 2 - step }) as usize
    } else {
        width / 2
    };
    let mut cells = vec![b' '; width];
    cells[position] = b'o';
    if position > 0 {
        cells[position - 1] = b'.';
    }
    if position + 1 < width {
        cells[position + 1] = b'.';
    }
    String::from_utf8(cells).expect("ASCII activity pulse")
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::text::Line;

    #[test]
    fn indicators_keep_their_width_and_static_state() {
        for tick in [0, 1, 2, 3, 8, 24, u64::MAX] {
            assert_eq!(Line::raw(spinner(tick, true)).width(), 1);
            assert_eq!(dots(tick, true).len(), 3);
            assert_eq!(spinner(tick, false), "●");
            assert_eq!(dots(tick, false), "...");
            for width in [0, 1, 2, 3, 32, u16::MAX] {
                assert_eq!(pulse(width, tick, true).len(), usize::from(width));
                assert_eq!(pulse(width, tick, false), pulse(width, 0, false));
            }
        }
        assert_eq!(spinner(0, true), spinner(8, true));
        assert_ne!(spinner(0, true), spinner(2, true));
        assert_eq!(dots(0, true), dots(9, true));
        assert_ne!(dots(0, true), dots(3, true));
    }

    #[test]
    fn pulse_reverses_without_skipping_cells_or_resembling_a_filled_bar() {
        let positions: Vec<_> = (0..18)
            .map(|tick| {
                let frame = pulse(5, tick, true);
                assert_eq!(frame.bytes().filter(|cell| *cell == b'o').count(), 1);
                assert!(frame.bytes().filter(|cell| *cell != b' ').count() <= 3);
                frame.find('o').unwrap()
            })
            .collect();
        assert_eq!(positions[0], 0);
        assert_eq!(positions[8], 4);
        assert_eq!(positions[16], 0);
        assert!(
            positions
                .windows(2)
                .all(|pair| pair[0].abs_diff(pair[1]) <= 1)
        );
        assert_eq!(pulse(0, u64::MAX, true), "");
        assert_eq!(pulse(1, u64::MAX, true), "o");
    }
}
