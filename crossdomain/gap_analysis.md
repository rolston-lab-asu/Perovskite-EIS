# Literature Gap Analysis — Cross-Domain Impedance Transfer (AI4X 2026)

Compiled 2026-06-11 from web search + local reference libraries
(`Perovskite EIS/References/`, `NIMS EIS Dataset/references/`).

**Claim to defend:** no published work jointly trains a degradation model across an
optoelectronic and an electrochemical device class via a shared impedance representation,
or quantifies transfer gain between them. Phrase as "to our knowledge."

---

## Lane 1 — Battery EIS → ML (mature; transfer exists but only within Li-ion)

- Zhang et al., *Nat. Commun.* 2020 — GPR on raw EIS → capacity/RUL (our battery baseline).
- Jones et al., *Nat. Commun.* 2022 — EIS forecasting under uneven usage (local: NIMS refs).
- **Transfer learning to estimate Li-ion SOH with EIS**, *J. Energy Storage* 2025 —
  DNN transfer from reference button cell → target batteries.
  https://www.sciencedirect.com/science/article/abs/pii/S2352152X25000581
- **SKDAN**, arXiv 2304.05084 — self-attention domain adaptation, SOH under shallow cycles.
- Review: transfer-learning-based EIS SOH estimation, *Ionics* 2025.
  https://link.springer.com/article/10.1007/s11581-025-06065-y
- **Limit:** source and target are always Li-ion batteries (chemistry / form factor /
  condition shifts). Never another device class.

## Lane 2 — Perovskite EIS → ML (emerging; strictly single-domain)

- **Nabil et al., *Adv. Energy Mater.* 2026, 16:e06352** (local: Perovskite EIS/References) —
  DD-synthetic spectra (SETFOS) → GBR inversion of 6 physical params; OC probes
  recombination, SC probes ionic transport; validated on real MAPI devices (15.3–16.5% PCE).
  Self-described as a "physically grounded, **system-specific** framework."
- Almora et al., *Adv. Sci.* 2021 — ML on environment-dependent PSC impedance.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8336513/
- DD-guided autoencoder for carbon-PSC degradation, arXiv 2603.22520 (Mar 2026) —
  **JV-based, not EIS**; single-domain. https://arxiv.org/abs/2603.22520
- US Patent 12,341,472 — predicting solar-cell performance from EIS (per-domain
  EIS→performance is established; supports feasibility, doesn't touch transfer).
- Kirchartz & Das, *J. Phys. Energy* 2023 — inverse-problem review across characterization
  techniques (motivates ML inversion; single technology class).

## Lane 3 — "Universal" EIS analysis tools (shared formalism, no shared learning)

- **Maradesa et al., *Joule* 2024 DRT review** (local: NIMS refs) — explicitly names
  vectorized DRT as ML features across batteries / fuel cells / electrolyzers as a
  **future direction** — proposed, not executed. Quote this as independent motivation.
  https://www.sciencedirect.com/science/article/abs/pii/S0378775323012211
- AgentEIS, *J. Mater. Sci.* 2026 — LLM/ML multi-system EIS database for automated
  equivalent-circuit identification — analysis automation, not degradation transfer.
  https://link.springer.com/article/10.1007/s10853-025-11692-x
- GP-DRT / DNN-DRT (Ciucci group) — better DRT deconvolution, system-agnostic math,
  no cross-class predictive model.
- No impedance "foundation model" / shared cross-class latent space found (searched
  June 2026).

---

## Gap statement (for slide/poster)

> EIS transfer learning exists only *within* the battery domain; physics-grounded EIS
> inversion exists only *per device class*; cross-system impedance learning is named as
> an outlook in DRT reviews but never executed. To our knowledge, no prior work jointly
> trains a degradation model across an optoelectronic and an electrochemical device
> class or measures transfer gain between them. This work proposes exactly that; the
> proof-of-concept supplies the premise evidence (shared arc-growth signature, same DRT
> formalism, degradation-informative descriptor in both domains, across a ~4-decade gap
> in |Z| and tau).

## Anticipated questions & answers

- *"Hasn't this been done?"* — nearest neighbors are within-battery transfer
  (J. Energy Storage 2025, SKDAN) and AgentEIS; name why each falls short (same device
  class; ECM identification not degradation transfer).
- *"Why should transfer work across a 4-decade tau gap?"* — the encoder input is
  normalized / log-tau-aligned features, not raw |Z|; what is shared is the arc topology
  and monotonic growth law (FIG B), per von Hauff & Klotz 2022's explicit PSC↔electrode
  charge-transfer analogy.
- *"Perovskite label is just time"* — acknowledged; May 2026 Marco-sample light JV
  (4 devices, 15.1–16.6% PCE) + same-day EIS will provide true EIS→performance pairs.
