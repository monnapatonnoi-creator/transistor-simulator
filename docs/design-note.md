# Design note — BJT DC Bias Web App (student summary)

This app separates the calculation from the screen. `dc_bias.py` does the math with
the equations the lab gave (VTH, RTH, IB, IC, IE, VB, VE, VC, VCE) and returns one
result object. `app.py` only reads the form and shows that object in the HTML template.
Numbers are never typed into the HTML — the backend computes them every time.

I chose the "registry" approach because next week we will add Fixed Bias and Emitter
Bias. With this design, adding a new bias type means writing one new function and one
line in the registry — we do not need to touch the Flask route or the HTML page at
all. The same idea will let us swap in ngspice later without rebuilding the screen.

The forward-active model has limits: if the device is actually cut off or saturated,
the equations still print numbers, but they are physically wrong. I decided to keep
showing the raw numbers, mark the region, and add a warning so the user knows not to
trust them. That is better than hiding numbers or silently correcting them.
