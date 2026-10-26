# Interaction principles

Use these principles when choosing or changing a component. The
[responsiveness](research/responsive-interactions.md) and
[quiet-motion](research/quiet-motion.md) research records explain the adopted
guidance and its limits.

These are library design decisions. They apply the existing
[wording](../specs/wording.md), [interaction](../specs/interaction.md) and
[identity](../specs/identity.md) references without changing their approval status
or an application's operation, freshness or confirmation contracts.

1. **Acknowledge intent promptly; report outcomes from evidence.** Separate input
   feedback, usable content and confirmed completion. Identify pending work,
   failure and uncertainty. A spinner cannot imply progress that was not measured;
   a local preview cannot establish that a network change was applied. Show
   operational values directly, without decorative counting through unobserved
   numbers. W5, I6.
2. **Keep frequent work quiet and responsive.** Start routine task interactions
   with still, immediate feedback. Add local motion when it explains a change or
   supports direct manipulation. Focus, typing and keyboard selection must not
   trail the input; refresh must not replay entrances. Correction, cancellation
   and navigation must not wait for decoration. Retarget or stop motion from its
   current state. Motion off retains information and controls; reduced motion
   replaces unnecessary travel rather than accelerating it. Cancelling
   local work after dispatch does not establish rollback. W5, W7; TUI-K4, TUI-S2.
3. **Preserve context and make recovery usable.** Retain the relevant object,
   entered values and logical focus through correction and return. Keep unresolved
   failures and unknown outcomes reachable. Offer undo only when the operation can
   actually be reversed, with recovery available independently of a timed toast.
   Cached observations require an explicit freshness policy. U2-U3, W6, W9.
4. **Use the platform's ordinary controls.** Keep keyboard operation, visible
   focus and meaningful labels. Gestures also need a clickable alternative;
   hover, shortcuts and motion supplement discoverable actions. Hints describe
   implemented keys in the active context. Preserve browser/system Back and
   native dismissal behavior. W4, W7; TUI-K1-K5, TUI-D2/D4.
5. **Keep layout stable and information complete.** Reserve known content
   geometry, keep numeric columns and units aligned, and allow short headings to
   wrap with their available width. Use tabular digits where changing numbers
   need them, checking the actual font. Terminal layouts measure display cells.
   Preserve meaning at narrow widths, larger text sizes and without color or
   motion. W7; TUI-A1-A4, TUI-S2.
6. **Add a mechanism for a demonstrated problem.** Address avoidable latency
   before adding a loader. Choose caching, prefetching, command search or extra
   motion only when the task benefits and its failure path is defined. Use the
   smallest sufficient feedback; routine success does not need another notice.
   Judge motion by its area, distance, repetition and competing effects as well
   as duration. Reduce its scope before tuning the curve. U4-U5, W9.

## Applying the principles

Start with the user's task and the existing shared component. Describe what
happens while waiting, after failure, on cancellation and when newer input
arrives. Keep domain state and authority in the application; a renderer should
not invent them.

For the changed interaction, check actual keyboard/pointer input, focus return,
resize and motion-off behavior. Measure the relevant problem: input-to-feedback,
time to usable content, time to confirmed outcome, ignored input or layout
movement. Record failures and recovery alongside the successful path; these
checks do not establish usability gains. For proposed motion, compare with the
static interaction and check repeated use, comfort and task success separately.
