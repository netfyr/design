# Animations

The shared renderers accept a tick, phase or measured value; they do not own
clocks, network sampling, preferences or redraw scheduling. One tick is
`flame::FRAME_INTERVAL` (one twelfth of 1.15 seconds).

| Module | Inputs and output |
| --- | --- |
| `flame::frame(tick, motion)` | 24×12 character mark. Twelve animated frames; motion off returns the static master. |
| `animation::spinner(tick, motion)` | Quarter-circle busy indicator; motion off uses `●`. |
| `animation::dots(tick, motion)` | Three-cell cycling dots; motion off keeps `...`. |
| `animation::pulse(width, tick, motion)` | Travelling pulse; motion off centers it. Always exactly `width` cells. |
| `lanes::traffic(width, direction, active, motion, phase)` | Direction/activity lane. The host supplies phase from observed throughput and stops stale data. Always exactly `width` cells. |
| `lanes::replay(width, rtt_ms, tick, motion)` | RTT replay with `width` interior cells and two brackets. Missing/invalid timing uses `?`; motion off preserves a static marker. |

Label the pending work beside a waiting indicator (W5). Dots and pulses do not
measure progress or completion. The application uses the spinner.

Traffic motion supplements the displayed rate. The application retains its
bounded logarithmic rate-to-phase mapping and freshness checks. RTT movement is
a replay of measured round-trip time, not a packet trace or adjacent-hop latency.
The gallery uses explicit synthetic fixtures (I6).

The traffic example compares idle, 1 B/s, 1 KiB/s, 1 MiB/s and 1 GiB/s together.
Its fixed speeds match the application's logarithmic scale: 0, 0.5, 2.5, 4.5
and 6.5 cells per second. The numeric labels carry the rates; marker speed is
supplementary, not a linear throughput gauge. The browser export spans their
complete 46-second common cycle; narrow terminals shorten the lanes while
preserving cell velocity and aligned rate labels (TUI-A2, TUI-S2).

Set `motion` to false when motion is disabled. All data and state cues remain
available (TUI-S2); `NO_COLOR` is a separate style choice. Render only when the
component is visible and has changed. The browser gallery also pauses offscreen
and hidden-page playback and honors reduced-motion preferences.

Handle new input, cancellation and resize without waiting for a decorative frame
or animation completion. After work has been dispatched, cancelling local
orchestration does not establish rollback (W5). The [shared principles](../principles.md)
apply without changing the host's operation or cancellation policy.

For frequent editing and selection, use immediate updates and keep the reading
surface stable. The [quiet-motion guidance](../research/quiet-motion.md) permits
purposeful artwork and measured lanes while avoiding decorative entrances on
every refresh. Display observed numbers directly; marker motion supplements
them.

The flame is reserved artwork; see its [notice](assets/flame-NOTICE.txt).
Rendering code uses the crate's MIT license.
