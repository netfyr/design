//! The netfyr mark, sampled into terminal cells. Artwork rights and
//! source provenance are recorded in `assets/flame-NOTICE.txt` and
//! `assets/flame-provenance.json`; the software license does not license the mark.

use std::time::Duration;

pub const WIDTH: u16 = 24;
pub const HEIGHT: u16 = 12;
pub const FRAME_COUNT: u64 = 12;
pub const FRAME_INTERVAL: Duration = Duration::from_nanos(1_150_000_000 / FRAME_COUNT);

const ARTWORK: &str = include_str!("../assets/flame.txt");

pub fn frame(tick: u64, motion: bool) -> &'static str {
    let index = if motion { 1 + tick % FRAME_COUNT } else { 0 };
    ARTWORK
        .split("\n\x0c\n")
        .nth(index as usize)
        .expect("generated flame asset contains the master and all animation frames")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn artwork_fits_fixed_ascii_cells() {
        assert_eq!(ARTWORK.split("\n\x0c\n").count(), FRAME_COUNT as usize + 1);
        for frame in ARTWORK.split("\n\x0c\n") {
            let rows: Vec<_> = frame.lines().collect();
            assert_eq!(rows.len(), usize::from(HEIGHT));
            for row in rows {
                assert_eq!(row.len(), usize::from(WIDTH));
                assert!(row.bytes().all(|byte| b" .:+*#@".contains(&byte)));
            }
        }
    }

    #[test]
    fn reduced_motion_uses_master_and_animation_loops() {
        assert_eq!(frame(0, false), frame(u64::MAX, false));
        assert_ne!(frame(0, false), frame(0, true));
        assert_ne!(frame(0, true), frame(FRAME_COUNT / 2, true));
        assert_eq!(frame(0, true), frame(FRAME_COUNT, true));
    }
}
