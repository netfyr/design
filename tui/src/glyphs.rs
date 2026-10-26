//! Optional single-cell symbols from the netfyr symbols companion font.
//! Hosts choose the set and retain standard fallbacks when font fallback is unavailable.

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum GlyphSet {
    #[default]
    Standard,
    Netfyr,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Glyph {
    Flame,
    RightSolid,
    RightOutline,
    LeftSolid,
    LeftOutline,
}

impl GlyphSet {
    pub const fn character(self, glyph: Glyph) -> char {
        match (self, glyph) {
            (Self::Standard, Glyph::Flame) => '*',
            (Self::Standard, Glyph::RightSolid | Glyph::RightOutline) => '>',
            (Self::Standard, Glyph::LeftSolid | Glyph::LeftOutline) => '<',
            (Self::Netfyr, Glyph::Flame) => '\u{100000}',
            (Self::Netfyr, Glyph::RightSolid) => '\u{100001}',
            (Self::Netfyr, Glyph::RightOutline) => '\u{100002}',
            (Self::Netfyr, Glyph::LeftSolid) => '\u{100003}',
            (Self::Netfyr, Glyph::LeftOutline) => '\u{100004}',
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::text::Line;

    #[test]
    fn glyphs_default_to_ascii_and_keep_one_cell_when_opted_in() {
        for glyph in [
            Glyph::Flame,
            Glyph::RightSolid,
            Glyph::RightOutline,
            Glyph::LeftSolid,
            Glyph::LeftOutline,
        ] {
            assert!(GlyphSet::default().character(glyph).is_ascii());
            for set in [GlyphSet::Standard, GlyphSet::Netfyr] {
                assert_eq!(Line::raw(set.character(glyph).to_string()).width(), 1);
            }
        }
        assert_eq!(GlyphSet::default().character(Glyph::Flame), '*');
        assert_eq!(GlyphSet::Netfyr.character(Glyph::Flame), '\u{100000}');
        for (glyph, codepoint, fallback) in [
            (Glyph::RightSolid, 0x100001, '>'),
            (Glyph::RightOutline, 0x100002, '>'),
            (Glyph::LeftSolid, 0x100003, '<'),
            (Glyph::LeftOutline, 0x100004, '<'),
        ] {
            assert_eq!(GlyphSet::Netfyr.character(glyph) as u32, codepoint);
            assert_eq!(GlyphSet::Standard.character(glyph), fallback);
        }
    }
}
