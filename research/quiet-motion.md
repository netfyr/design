# Quiet motion adoption

Recorded 2026-10-26 from Josie's supplied *Quiet motion: Natural animations that
enhance rather than interrupt*, dated 2026-10-26.
Original filename: `natural_unobtrusive_animations_report.md`.
SHA-256: `484cc542d14d2bcb3f7192254c325785838647d93f6154350b4c1715a2abebdd`.

The report provides 24 linked references and distinguishes design prescriptions,
practitioner recommendations and visualization experiments. Its timing ranges,
spring values and component recipes are proposed starting points. The adoption
below refines the existing [principles](../principles.md); it does not introduce
runtime changes or describe new application defaults.

## Adopted guidance

| Decision | Application |
| --- | --- |
| Frequent work starts still | Focus, typing, keyboard selection and ordinary refresh respond immediately. Animate a changed region only when it helps explain the change; keep the reading surface, selected object and relevant scroll position stable where the operation permits. Existing freshness policies still apply. |
| Motion spends attention | Moving area, travel, contrast, repetition and concurrent effects are qualitative review factors, not a measured formula. Avoid routine list staggering, repeated entrances and whole-page choreography. Prefer one coherent changed region over independent effects on every child. |
| Input takes precedence | Acknowledgment, focus, accessible state and operation validity cannot depend on an animation-end event. Retarget from the current presentation and invalidate stale completion callbacks, so an old close cannot hide a reopened surface. Transaction safeguards depend on operation state, not a decorative timer. |
| Values remain truthful | Show observed operational numbers immediately. Loading content appears when ready without waiting for a cycle to finish. Do not manufacture intermediate observations or progress to fit an effect (W5, I6). |
| Motion off is a complete path | Preserve information, controls and logical focus with motion disabled. Replace unnecessary spatial movement with an immediate update; a modest fade is optional, not a universal comfort guarantee. Check reduced-motion changes during use as well as at startup (W7, TUI-S2). |
| Timings follow the component | The report's ranges and spring parameters are candidates for a concrete interaction, not adopted tokens or universal thresholds. Prefer existing native behavior or a small CSS transition. Add semantic motion tokens or a controllable animation mechanism only when actual shared usage calls for them. |

For a proposed effect, state its purpose, trigger, affected region, interruption
behavior and motion-off equivalent. Compare the task with a static version,
including repeated use and slow rendering. Check open/close/reopen during motion,
immediate typing, resize, focus return and cancellation. Measure comfort and task
performance separately from visual preference. These are review directions, not
claims that such user studies have already been performed for netfyr.

## Existing motion and ownership

The hover/focus flame is a local identity effect. Optional
terminal artwork, measured traffic lanes and instructional GIF/rate-comparison
galleries have their own purpose; the one-region heuristic is not a limit on
those demonstrations. Their existing static alternatives and playback controls
remain relevant. A traffic marker supplements the displayed observed rate; it
does not authorize easing or inventing the numeric value.

This adoption changes neither current Motion/Eye candy defaults nor application
preferences. The report's suggested System/Reduced/Off selector is not a new
settings requirement. Browser preference handling and the existing terminal
motion controls remain the mechanisms to use. See [web components](../web/README.md)
and [terminal animations](../tui/animations.md) for implemented behavior.

## Evidence and limits

- [Carbon motion](https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview) and
  [Atlassian applying motion](https://atlassian.design/foundations/motion/applying-motion)
  provide professional guidance on purposeful motion, prompt feedback and
  consistent implementation. They support this design direction; their
  prescriptions are not controlled evidence for netfyr's exact durations.
- [Heer and Robertson (2007)](https://idl.uw.edu/papers/animated-transitions)
  studies transitions in statistical graphics. Benefits in its tracking and
  change-perception tasks do not establish an optimal menu/dialog animation.
- [Robertson et al. (2008)](https://www.microsoft.com/en-us/research/publication/effectiveness-of-animation-in-trend-visualization/)
  compares animated trends with static alternatives. Results differ between
  analysis and presentation tasks; enjoyment alone does not establish
  effectiveness. Evaluate the actual task rather than generalizing these
  visualization findings to every interface transition.
- Accessibility and state-truthfulness requirements retain the owners and
  primary references in the [earlier adoption record](responsive-interactions.md).
  Reduced-motion styling alone does not cover arbitrary JavaScript, video or
  snapshot transitions; check the actual rendered behavior and input paths.
