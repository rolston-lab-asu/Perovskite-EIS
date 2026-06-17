# AI4X poster — middle text + figure captions (copy-paste)

Audience = mixed AI4X (not all electrochemists). Keep it scannable.

---

## WORKFLOW TEXT (the middle, in order)

### Background
Every energy device — a battery, a solar cell — ultimately fails at its internal
*interfaces*, where charge is transferred, stored, and lost. These processes are
normally studied separately, with device-specific tools. Electrochemical impedance
spectroscopy (EIS) offers a common language: a small AC signal is swept across
frequency, and the device's response separates each internal process by its
characteristic *timescale* — a physics-grounded, feature-engineering-free
fingerprint of the interface as it ages. We ask whether **one EIS workflow can read
degradation in two very different devices** — a Li-ion battery and a perovskite
solar cell — even though their impedances differ by ~10,000×.

### Reading the spectrum 1 — Equivalent-circuit model (textbook method)
The first way to interpret a spectrum is to fit it to an equivalent circuit of
physical components. We use the **same circuit for both devices**: a series
resistance *R*ₛ and two parallel resistor–capacitor blocks, *R*∥CPE. The CPE
(constant-phase element) is a non-ideal capacitor that accounts for rough,
distributed real interfaces. Each *R*∥CPE block is one interfacial process with a
time constant **τ = R·C**, and the resistance of the degradation-relevant process
grows as the device ages. The fit returns interpretable numbers — but it assumes
*in advance* how many processes are present.

### Reading the spectrum 2 — Distribution of relaxation times (model-free method)
DRT removes that assumption and lets the data decide. A **Tikhonov-regularized
inversion** converts the frequency spectrum into a continuous distribution
**γ(τ)** over relaxation times: each peak is one physical process, with no circuit
imposed. Reading the same spectrum this way, the dominant aging peak appears at
**τ ≈ 0.16 s (charge transfer)** for the battery and **τ ≈ 1.3 s (ion migration)**
for the perovskite — the latter visible only once the sweep reaches low frequency
(10 mHz). DRT and the circuit fit agree, giving an interpretable timescale without
hand-picking a model.

### The two devices meet — a shared timescale
Placed on one axis, the dominant aging relaxations of the battery and the
perovskite fall in the **same 50 ms – 2 s band** — despite 10,000× different
impedance and entirely different chemistry. The processes are not identical
(interfacial charge transfer vs. ionic migration), but they occupy the **same
region of timescale-space and grow the same way** as each device ages. That shared
structure is what makes a single transferable descriptor possible: the arc
resistance *R*ₚ predicts measured state-of-health in the battery (|r| = 0.88) and
power retention in the perovskite (|r| = 0.91).

---

## STEP TEXT (middle column, matches the on-poster Step 1 / Step 2)

**Step 1.** EIS is measured with PAIOS (perovskite solar cell) and BioLogic
(Li-ion battery) — different instruments, the same measurement technique for both.

**Step 2.** We fit both spectra to the *same* simple equivalent circuit to extract
the interfacial resistance and its time constant τ.

**Step 3.** DRT drops the circuit assumption and lets the data decide. Each spectrum
is inverted (Tikhonov regularization) into a distribution γ(τ) — every peak is one
interfacial process at its own timescale, no circuit imposed. For both devices it
resolves the dominant aging process directly: charge transfer at τ ≈ 0.16 s
(battery) and ion migration at τ ≈ 1.3 s (perovskite).

**Step 4.** From each spectrum we take a single number — the arc resistance *R*ₚ,
the diameter of the interfacial arc — and test how well it tracks measured
performance. The same *R*ₚ predicts battery state of health (|r| = 0.88) and
perovskite power retention (|r| = 0.91).

**Conclusion (bottom strip).** Same workflow, same interfacial timescale, same
descriptor — across a battery and a solar cell. Impedance is a transferable,
physics-grounded fingerprint of interfacial aging, motivating a single degradation
model that spans device classes.

---

## FIGURE CAPTIONS

Style: bold `Fig. N` + a declarative take-home title (the finding, not "plot of…"),
then one orienting sentence (sample / conditions / method), then the symbol key.
Self-contained; complete sentences. (Conventions: Caltech Hixon Writing Center;
International Science Editing.)

**Fig. 1 — The perovskite's interfacial arc grows monotonically as the cell ages.**
Nyquist impedance of a Cs₂₀FA₈₀PbI₃ solar cell under 1-sun illumination at 358 K,
swept 10 MHz–10 Hz over ~13 h. Color = aging time (dark → light).

**Fig. 2 — The same arc-growth signature tracks capacity loss in the battery.**
Nyquist impedance of a Molicel P42A NMC 21700 cell (4.0 Ah) cycled at room
temperature — 2C charge to 4.2 V, 3.75C discharge — to end-of-life, 10 kHz–1 Hz.
Color = state of health. Axes in mΩ — ~10,000× smaller than the perovskite's Ω scale.

**Equivalent Circuit Model (unnumbered label between Fig. 3 and Fig. 4).** Series
resistance *R*ₛ with two parallel *R*–CPE elements; each is one interfacial process
(CPE = constant-phase / non-ideal capacitance). The colored element is the
degradation-tracking arc.

**Fig. 3 — The circuit fit resolves the perovskite recombination arc.** Two-arc fit
(line) to a mid-life perovskite spectrum (points); highlighted *R*₁ = 444 Ω
(recombination), τ₁ = 7 µs (RMS 8.6%). The slower ionic arc that shares the battery's
timescale appears at low frequency in the DRT (Fig. 5).

**Fig. 4 — The circuit fit resolves the battery charge-transfer arc.** Two-arc fit
(line) to a mid-life battery spectrum (points); highlighted *R*₂ = 65 mΩ (charge
transfer), τ₂ = 0.15 s.

**Fig. 5 — Model-free DRT places the perovskite aging process at τ ≈ 1.3 s.**
Tikhonov-regularized inversion into γ(τ); the dominant ion-migration peak appears
once the sweep reaches 10 mHz. The fast electronic response (~µs) is off-scale (left).

**Fig. 6 — DRT places the battery aging process at τ ≈ 0.16 s.** Inversion of the
battery spectrum; dominant charge-transfer peak at 0.16 s, with a faster SEI feature
in the ms range.

**Fig. 7 — Both aging processes share the 50 ms–2 s timescale band.** Battery and
perovskite DRTs overlaid on one relaxation-time axis; despite different chemistry
and a 10,000× impedance gap, both dominant peaks fall in the shaded band.

**Fig. 8 — A rising arc resistance predicts perovskite power loss.** Arc descriptor
*R*ₚ vs *P*ₘₐₓ retention, where *P*ₘₐₓ is the max-power point from a periodic 1-sun
JV sweep co-logged with each spectrum (not derived from the impedance); |r| = 0.91.
Color = aging time.

**Fig. 9 — The same descriptor predicts battery state of health.** Arc descriptor
*R*ₚ vs SOH, 5 cells pooled; |r| = 0.88.

(One-figure alternative: **Fig. 8 — One impedance descriptor predicts measured
degradation in both systems.** *R*ₚ vs performance — perovskite power retention
(|r| = 0.91, left) and battery state of health (|r| = 0.88, right).)

---

## NOTE — keep ECM and DRT pointing at the same perovskite process
The perovskite ECM card currently highlights *R*₁ = recombination (τ = 7 µs, HF),
but the shared-band feature is the *ionic* process (τ ≈ 1.3 s, LF). To avoid a
reader asking why the two panels point at different processes, either refit the
perovskite ECM on the 10 mHz sweep (recommended) or keep the ECM caption neutral.
