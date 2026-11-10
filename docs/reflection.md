# Reflection — BJT DC Bias Web App

What I learned: separating frontend from backend makes each part testable on its own.
The engineering module has no Flask in it, so I could verify the DC math with plain
unit tests before touching the web layer at all. The registry idea means next week's
bias types will not break this week's screen.

What was hard: deciding what to show when the device is cut off or saturated. The
equations still run and print negative currents, which looks like a bug until you
realise the point is to warn that the assumption failed. We chose to show the raw
numbers de-emphasised with a warning rather than hide them.

Limitation of this model: fixed β and fixed VBE mean it is only accurate near the
design point. Real transistors vary with temperature and current, so this is a
teaching tool, not a design-signoff simulator.
