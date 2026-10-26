//! Measured activity and RTT replay presentation. Hosts retain sampling,
//! freshness, rate-to-phase mapping and whether the evidence permits motion.

use crate::flame::FRAME_INTERVAL;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Direction {
    Left,
    Right,
}

/// Exactly `width` cells, with a direction marker and an optional activity marker.
/// Invalid or negative phases start at zero; motion off centers the activity.
pub fn traffic(
    width: u16,
    direction: Direction,
    active: bool,
    motion: bool,
    position: f64,
) -> String {
    let width = usize::from(width);
    if width == 0 {
        return String::new();
    }
    let mut cells = vec![b'-'; width];
    let arrow = match direction {
        Direction::Left => {
            cells[0] = b'<';
            0
        }
        Direction::Right => {
            cells[width - 1] = b'>';
            width - 1
        }
    };
    if active && width > 1 {
        let position = if width == 2 {
            1 - arrow
        } else {
            let span = width - 2;
            let phase = if !motion {
                span / 2
            } else if position.is_finite() && position >= 0.0 {
                (position % span as f64) as usize
            } else {
                0
            };
            match direction {
                Direction::Left => width - 2 - phase,
                Direction::Right => 1 + phase,
            }
        };
        cells[position] = b'o';
    }
    String::from_utf8(cells).expect("ASCII traffic lane")
}

/// A bounded logarithmic replay duration, stretched so no cell is skipped.
/// Invalid RTTs use the minimum duration; `replay` displays them as unknown.
pub fn cycle_ticks(rtt_ms: f64, span: u16) -> u64 {
    let rtt = if rtt_ms.is_finite() && rtt_ms >= 0.0 {
        rtt_ms.min(1000.0)
    } else {
        0.0
    };
    let seconds = 0.8 + 3.2 * (1.0 + rtt).ln() / 1001.0_f64.ln();
    ((seconds / FRAME_INTERVAL.as_secs_f64()).ceil() as u64).max(u64::from(span) * 2)
}

/// Bracketed RTT replay with `width` interior cells. Missing or invalid RTTs use
/// a static `?`; known RTTs use a static `o` when motion is disabled.
pub fn replay(width: u16, rtt_ms: Option<f64>, tick: u64, motion: bool) -> String {
    if width == 0 {
        return "[]".into();
    }
    let mut cells = vec![b'-'; usize::from(width)];
    match rtt_ms.filter(|rtt| rtt.is_finite() && *rtt >= 0.0) {
        Some(rtt) if motion && width > 1 => {
            let span = u64::from(width - 1);
            let period = cycle_ticks(rtt, width - 1);
            let step = (tick % period) * (span * 2) / period;
            let position = if step <= span { step } else { span * 2 - step };
            cells[position as usize] = if step < span { b'>' } else { b'<' };
        }
        Some(_) => cells[usize::from(width / 2)] = b'o',
        None => cells[usize::from(width / 2)] = b'?',
    }
    format!("[{}]", String::from_utf8(cells).expect("ASCII replay lane"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn traffic_preserves_direction_activity_and_requested_width() {
        assert_eq!(traffic(9, Direction::Left, false, true, 0.0), "<--------");
        assert_eq!(traffic(9, Direction::Right, false, true, 0.0), "-------->");
        assert_eq!(traffic(9, Direction::Left, true, true, 0.0), "<------o-");
        assert_eq!(traffic(9, Direction::Right, true, true, 2.0), "---o---->");
        for direction in [Direction::Left, Direction::Right] {
            for width in [0, 1, 2, 3, 22, u16::MAX] {
                for active in [false, true] {
                    for motion in [false, true] {
                        for phase in [0.0, 1.5, 20.0, -1.0, f64::NAN, f64::INFINITY, f64::MAX] {
                            let lane = traffic(width, direction, active, motion, phase);
                            assert_eq!(lane.len(), usize::from(width));
                            if width > 0 {
                                match direction {
                                    Direction::Left => assert!(lane.starts_with('<')),
                                    Direction::Right => assert!(lane.ends_with('>')),
                                }
                            }
                            if !active || !motion {
                                assert_eq!(lane, traffic(width, direction, active, motion, 0.0));
                            }
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn replay_reverses_direction_without_skipping_cells() {
        for width in [2, 5, 9] {
            let period = cycle_ticks(1.2, width - 1);
            assert!(period >= 2 * u64::from(width - 1));
            assert!(period < cycle_ticks(1000.0, width - 1));
            assert!(replay(width, Some(1.2), 0, true).contains('>'));
            assert!(replay(width, Some(1.2), period.div_ceil(2), true).contains('<'));
            assert_eq!(
                replay(width, Some(1.2), 0, true),
                replay(width, Some(1.2), period, true)
            );
            let positions: Vec<_> = (0..=period)
                .map(|tick| {
                    replay(width, Some(1.2), tick, true)
                        .find(['<', '>'])
                        .unwrap()
                })
                .collect();
            assert!(
                positions
                    .windows(2)
                    .all(|pair| pair[0].abs_diff(pair[1]) <= 1)
            );
        }
    }

    #[test]
    fn unknown_and_static_replays_retain_their_meaning_at_small_widths() {
        for width in [0, 1, 2, 3, 9, u16::MAX] {
            for rtt in [
                None,
                Some(-1.0),
                Some(f64::NAN),
                Some(f64::INFINITY),
                Some(1.2),
            ] {
                for tick in [0, 17, u64::MAX] {
                    assert_eq!(replay(width, rtt, tick, true).len(), usize::from(width) + 2);
                    assert_eq!(
                        replay(width, rtt, tick, false),
                        replay(width, rtt, 0, false)
                    );
                    if rtt.is_none_or(|value| !value.is_finite() || value < 0.0) {
                        assert_eq!(replay(width, rtt, tick, true), replay(width, None, 0, true));
                    }
                }
            }
        }
        assert_eq!(replay(0, Some(1.2), u64::MAX, true), "[]");
        assert_eq!(replay(1, Some(1.2), u64::MAX, true), "[o]");
        assert_eq!(replay(5, None, u64::MAX, true), "[--?--]");
        assert_eq!(replay(5, Some(1.2), u64::MAX, false), "[--o--]");
    }
}
