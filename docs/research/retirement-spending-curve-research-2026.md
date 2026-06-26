# Retirement Spending Curve — Research & Modelling Glidepath (2026)

*Prepared June 2026. For an example couple; all figures AUD unless flagged. Conversion rates used where sources are foreign: 1 GBP ≈ 2.0 AUD, 1 USD ≈ 1.5 AUD — every conversion is flagged inline. Feeds the model's spending glidepath (illustrated here against an example flat **$X/yr real** need).*

---

## Executive summary

The evidence is strong and consistent across US (RAND/HRS, Blanchett) and **Australian (Milliman, Productivity Commission, ASFA)** data that **real, inflation-adjusted retirement spending falls** through the active years — roughly **1% per year early, ~2%/year through the mid-70s–80s**, with a cumulative real fall of **~25–37%** from the early-60s peak to the mid-80s. The "spending smile" (a late-life upturn) is real but, in the Australian data, the **late-life ASFA budget is actually ~7% *lower*, not higher** — because lost mobility removes travel/transport faster than routine health costs rise. The genuine end-of-life spike is **residential aged care**, which is a separate, lumpy, **largely self-funded** cost for a high-net-worth couple: roughly **$71k/yr in recurrent fees plus accommodation** (a refundable lump-sum RAD of ~$400k–$1m+, *or* a DAP of ~$40–80k/yr), for a **median ~20-month stay** (with a real chance of 3–5 years). The correct modelling treatment is **not** a flat real spend for ~36 years: use a **declining real glidepath** for everyday spending **plus a ring-fenced late-life aged-care reserve** (logically the family home). On balance this makes the plan **easier**, not harder, to fund — the long, cheap middle outweighs the spike, and the spike is mostly covered by an asset (the home) that the flat-line model already implicitly holds in reserve.

---

## 1. The retirement spending smile / U-shape

### 1.1 Blanchett — the foundational work
David Blanchett, *"Exploring the Retirement Consumption Puzzle"* (Journal of Financial Planning, May 2014), with the underlying model in the Morningstar working paper *"Estimating the True Cost of Retirement"* (5 Nov 2013, US data: RAND HRS + CAMS + CEX).

- **Average real spending change ≈ −1%/yr**, but it is **not constant** — it traces a smile. Decomposed by decade (Kitces' read of Blanchett's Figure 5): **≈ −1%/yr in the first decade, ≈ −2%/yr in the second, then ≈ −1%/yr again** in the final decade, with the late upturn forming the smile.
- **The U-shape in dollars (US example):** a household spending **US$100k/yr** (≈ **A$150k** ×1.5) sees real spending decline to a **trough of US$74,146 at age 84 — a ~26% real fall** — and does not climb back above the starting level until the **mid-90s**.
- **Crucially, the decline depends on spend level and wealth.** Blanchett splits households four ways:
  - *Low-spend* households (high or low net worth) tend to **increase** real spend through 65–75.
  - *High-spend* households (especially high-spend / low-net-worth) **decline fastest** (~2%/yr+).
  - His fitted model adds **+0.5%/yr** for households spending **>US$85k/yr** (≈ A$128k ×1.5) to proxy higher health exposure. **A high-spend self-funded couple sits squarely in the "high-spend, declines fastest" band** — Blanchett's curve would predict a steeper-than-average real decline for them.
- **Planning impact Blanchett reports:** using the smile instead of constant-real spending lifts the sustainable initial withdrawal rate from **4.03% → 4.73%** (~17% higher), i.e. retirees may need **~20% less capital** than a flat-real assumption implies.

*Honest caveat:* Blanchett never states a single headline "−X%/yr" — his result is a curve (Figure 5). The −1/−2/−1 decade split is Kitces' interpretation of that curve, not a sentence in Blanchett's paper.

### 1.2 Go-go / slow-go / no-go (Michael Stein, *The Prosperous Retirement*, 1998)
The framework is Stein's; the age bands and percentages below are advisor-source characterisations layered onto Stein's qualitative phases via Blanchett's curve (Stein's 1998 book does not, per available sources, state the percentages):

| Phase | Approx age | Character | Real spend trend |
|---|---|---|---|
| **Go-Go** | ~65–75 (first decade) | Active: travel, hobbies, high discretionary | declines ~1%/yr |
| **Slow-Go** | ~75–85 | Activity tapers, travel winds down | declines ~2%/yr |
| **No-Go** | ~85+ | Low mobility; discretionary collapses, health rises | discretionary falls sharply; health rises (smile upturn) |

### 1.3 How much does real spending actually fall? (the numbers)

| Magnitude | Window | Source | Year | Region |
|---|---|---|---|---|
| **~26% real fall** (total, $100k household) | 65 → trough at 84 | Blanchett | 2013/14 | US |
| **~2%/yr, across *all* wealth quartiles** | 65+ | RAND/HRS (Hurd & Rohwedder) | 2022 | US |
| **15–20% less real at 90 than at 70** | 70 → 90 | Productivity Commission / Grattan | ~2015 | **AUS** |
| **36.7%** median couple total-spend fall | 65–69 → 85+ | **Milliman Australia ESP** | 2018 | **AUS** |
| **6–8% per 4-year age band**, accelerating after 80 | 65 → 85+ | **Milliman Australia ESP** | 2018 | **AUS** |
| **~7% lower** (comfortable couple) at 85+ vs 65–84 | around 85 | **ASFA Standard** | Dec 2025 | **AUS** |

The single most relevant Australian anchor is **Milliman Australia's Retirement Expectations and Spending Profiles (ESP), 23 April 2018**, built from the **actual transaction data of 300,000+ Australian retirees** (not surveys): median retired-couple spending falls **36.7%** from its 65–69 peak to 85+, at **6–8% per four-year band**, accelerating after 80. Milliman also found the decline is **behavioural (reduced activity), not income-constrained** — retirees who *could* spend more simply don't. "All discretionary expenditure, such as travel and leisure, declines throughout retirement."

### 1.4 The notable counter-case — UK
The UK IFS (*"How does spending change through retirement?"*, Report R209, Sept 2022) found the **opposite for higher-income retirees**: real spend **rose ~7%** from age 67→75 (£245→£263/wk, ≈ **A$490→A$526/wk** ×2), driven by holidays (+£430/yr ≈ +A$860) and household bills, falling only in the 80s. Lower-income UK retirees were roughly flat. This is a genuine caveat: the smile/decline is robust in **US and Australian** data but **not universal** — a high-income, healthy, travel-keen couple could hold or grow real discretionary spend through their 60s. For a couple retiring in their late 50s/early 60s in good health, **front-loading the go-go years rather than declining immediately is defensible** (see glidepath).

---

## 2. Australian baseline retirement budgets (ASFA) — for calibration

ASFA Retirement Standard, homeowners aged 65–84, latest published quarters:

| Quarter | Comfortable COUPLE | Comfortable SINGLE | Modest COUPLE |
|---|---|---|---|
| **March 2026** (latest, live ASFA page) | **$78,566** | $55,923 | $52,473 |
| December 2025 | $77,375 | $54,840 | $51,299 |
| September 2025 | $76,505 | $54,240 | $50,866 |
| March 2025 (primary PDF, verified) | $73,875 | $52,383 | $48,184 |

**Lump sum ASFA says a couple needs (homeowner, from 67, revised Feb 2026):** comfortable **$730,000**, modest $120,000 (assumes drawdown of capital + part Age Pension). *Note: a high-net-worth self-funded couple is far above this and will receive no Age Pension — ASFA's "comfortable" is a floor, not a target, for them.*

### The over-85 band — *budgets go DOWN, not up*
This directly contradicts the original hypothesis that 85+ is a higher-cost band. ASFA maintains a separate older-retiree standard (launched 2015). For the **December 2025 quarter**:

| Cohort | Comfortable COUPLE | Modest COUPLE |
|---|---|---|
| Aged 65–84 | $77,375 | $51,299 |
| **Aged 85+** | **$72,093** (−6.8%) | $47,999 (−6.4%) |

**Why it falls:** transport (running a car) effectively drops out, overseas holidays fall to **$0**, general leisure reduces with mobility — and these outweigh the rise in out-of-pocket health, chemist, and in-home help (cleaning, meals). Net **~7% lower** for a comfortable couple.

**The critical limitation:** the ASFA Standard **assumes the person stays in their own home**. It explicitly **excludes residential aged-care accommodation costs (RAD/DAP)**. So the 85+ ASFA budget is the *everyday-living* number; if residential care is later needed it is a **separate, much larger cost line** — which is §3 and is exactly where the real late-life spike lives.

---

## 3. The end-of-life / aged-care spike (Australia)

**Lens:** a self-funded couple with a high net worth is **fully means-tested**, receives **effectively no means-tested subsidy** on accommodation or non-clinical care, and pays **every capped contribution at its maximum**. The one universal new benefit (from 1 Nov 2025): **clinical care is 100% government-funded for everyone, regardless of wealth.**

*Dating note:* fees index **20 March / 20 September**. Two parallel systems run: residents who entered **before 1 Nov 2025** stay on the old "means-tested care fee" rules; entrants **on/after 1 Nov 2025** are on the new Aged Care Act 2024 system. A couple entering care in the 2030s+ will be on the **new system**. Figures below are the current 20 March 2026 indexed values where available.

### 3.1 The four cost components (new system, entrant after 1 Nov 2025)

**(a) Accommodation — RAD / DAP**
- **RAD (Refundable Accommodation Deposit):** lump sum, **refundable** on leaving (subject to new retention below). National median ≈ **$400,000**; national average **>$570,000** (mid-2025); major metro typically **$350k–$550k**, premium metro **$1,000,000+**; regional $200k–$350k. **A desirable coastal area would plausibly sit ~$450k–$750k+.**
- **Max RAD without IHACPA approval:** ~**$750,000** (set 1 Jan 2025), indexed to ~**$758,627** (1 Jul 2025). *(Old cap was ~$550k — lifted in the reforms.)*
- **DAP (Daily Accommodation Payment):** non-refundable daily alternative. **DAP = unpaid-RAD × MPIR ÷ 365.** MPIR = **7.65%** (Jan–Mar 2026), **7.96%** (Apr–Jun 2026). Worked example: a **$500k room at 7.65% ≈ $38,247/yr** DAP; at 7.96% ≈ $39,800/yr. Can split part-RAD/part-DAP.
- **NEW RAD retention (entrants from 1 Nov 2025):** provider retains **2% of RAD per year for up to 5 years (max 10%)**, non-refundable. On a $750k RAD, up to **$75,000** is permanently consumed over 5 years.

**(b) Basic Daily Fee** — 85% of single basic Age Pension, paid by everyone: **$65.55/day (~$23,926/yr)** early 2026, rising to **$66.80/day from 20 Mar 2026**.

**(c) Hotelling Contribution (HSC)** — new; everyday living (meals/cleaning/laundry/utilities). **Daily cap $22.15/day (~$8,085/yr), no annual or lifetime cap.** A high-net-worth couple pays the **full cap indefinitely**.

**(d) Non-Clinical Care Contribution (NCCC)** — new; replaces the old means-tested care fee (clinical care now free to all). **Daily cap $107.32/day (~$39,170/yr)** at 20 Mar 2026. Reaches the cap at assets ≥ ~$1.023M, so a high-net-worth couple pays the **maximum**. **Lifetime cap** (figure conflicted across sources): legislated **$130,000**, indexed to **~$135,319** (Sep 2025), **~$137,917** (Mar 2026). **4-year rule:** NCCC stops at the lifetime cap **or after 4 years**, whichever first.

*Old system, for reference (entrants before Nov 2025):* means-tested care fee **annual cap $35,910**, **lifetime cap $86,185** (20 Mar 2026).

### 3.2 Home care — Support at Home (from 1 Nov 2025)
Replaces Home Care Packages. **8 classification levels**, 2026 annual funding:

| Class | Annual | Class | Annual |
|---|---|---|---|
| 1 | $10,698 | 5 | $39,535 |
| 2 | $15,982 | 6 | $47,957 |
| 3 | $21,920 | 7 | $58,122 |
| 4 | $29,545 | 8 | $78,106 |

(Old HCP levels for reference: L1 ~$10k, L2 ~$18k, L3 ~$40k, L4 ~$61k/yr.) Clinical services free; self-funded participants pay **income-tested contributions** on non-clinical services (adviser-cited ~$38.72/day above threshold ≈ $14,095/yr). A high-net-worth couple pays the **higher tier**. This is the cheaper, earlier-stage path that typically *precedes* residential care.

### 3.3 Total annual cost & length of stay

**Recurrent residential fees, self-funded (2026):** basic daily ~$23,900 + full hotelling ~$8,085 + capped NCCC ~$39,170 = **~$71,000/yr**, **plus accommodation** (a RAD lump sum ~$450k–$1m+ tying up capital, *or* a DAP ~$40–80k/yr). All-DAP self-funded residents land around **$110,000–$150,000/yr** all-in; RAD-funded residents pay **~$71k/yr recurrent** while the RAD sits as a (largely) refundable asset.

**Length of stay (GEN Aged Care Data / AIHW, 2024–25):** **median 20.1 months** in permanent residential care (up from 18.5 months in 2017–18). Women stay ~8 months longer than men (historically ~23 vs ~14 months). Mean is longer (~35 months historically) due to a long right tail. **Plan on ~1.7 years median, with material probability of 3–5+ years.** Where there is an age gap between partners, the likely pattern is the **older partner enters care first and alone**, then potentially the younger — i.e. **two separate, non-overlapping single-occupancy episodes**, not one couple episode.

### 3.4 Confirmation: a high-net-worth couple pays near-maximum
At assessable assets ≥ ~**$1.023M**, residents pay the **maximum daily-capped HSC and NCCC**; pay the **full room price** (no accommodation supplement); receive **no Age Pension**; and pay the **higher Support at Home contribution tier**. Their only universal benefit is fully-funded clinical care.

---

## 4. Modelling implications — synthesis

### 4.1 Why a flat real spending line is wrong in both directions
A flat real spend for ~36 years **over-states** everyday spending in the long slow-go/no-go middle (the data says it should fall ~25–37% real), while **under-stating** the lumpy aged-care tail (residential care + accommodation can run $110–150k/yr all-in for 1–5 years, *on top of* a home that may be sold). The fix is to **split the spend into two streams**: a declining everyday-living glidepath, plus a separate, ring-fenced late-life care reserve.

### 4.2 Suggested everyday-living glidepath (multipliers of base)
Express everyday spend as a multiplier of a **base "go-go" spend**. Anchoring to the plan's flat assumption, treat the **base spend as the go-go base** (for a high-net-worth self-funded couple this typically sits well above the ASFA comfortable-couple figure). Apply per-person mortality/aged-care transition separately (any age gap matters).

| Phase | Ages (older partner) | Multiplier | Basis |
|---|---|---|---|
| **Go-Go** | ~59–70 | **1.00×** (optionally 1.05× peak early travel) | Active years; UK/IFS supports holding flat-to-up early for healthy high-income |
| **Slow-Go** | ~70–80 | **0.85× → declining ~2%/yr** | Blanchett 2nd-decade −2%/yr; Milliman 6–8%/band |
| **No-Go** | ~80+ | **0.75×** baseline everyday | ASFA 85+ is ~7% below 65–84; Milliman cumulative −37%; PC −15–20% by 90 |

A simple, defensible implementation: **hold real flat (1.0×) to age ~70, then decline real everyday spending ~1.5–2%/yr, floored at ~0.75× of base** for the survivor-adjusted no-go years. This brackets the AU evidence (Milliman's steeper −37% and PC's milder −15–20% sit either side of it).

### 4.3 Suggested aged-care reserve / spike (separate stream)
**Do not blend this into the everyday line — ring-fence it.** Concrete reserve for the model:

- **Recurrent care fees:** ~**$71k/yr** (basic + capped hotelling + capped NCCC) per person in residential care, indexed.
- **Accommodation:** a **RAD of ~$550k–$750k** (desirable-area estimate) — *capital tied up, largely refundable* (less ~2%/yr retention, max 10% ≈ up to $75k consumed) — **or** a **DAP ~$42–60k/yr** if not lump-summed.
- **Duration:** model **~2 years median per episode**, with a stress branch at **4–5 years**. Where there is an age gap, allow **two separate single episodes** (older partner, then younger), not one.
- **Home-care precursor:** optionally a 1–3 year Support at Home phase before residential care at ~$14–40k/yr out-of-pocket.

**Order-of-magnitude reserve:** two single episodes × (~$71k/yr recurrent × ~2 yrs) ≈ **$285k recurrent**, plus accommodation funded by RAD (refundable, so largely capital-neutral) or ~$100–240k of DAP. **A reserve of roughly $300k–$500k of *spendable* funds, plus the family home earmarked to fund the RAD(s), comfortably covers the central case**, with the home being the natural RAD source.

### 4.4 Is it sound to ring-fence the family home as the aged-care reserve?
**Yes — this is the standard and economically correct treatment.** The RAD is explicitly the mechanism by which **the family home is converted into aged-care accommodation funding**: residents very commonly sell (or borrow against) the home to pay the RAD, and the RAD is itself **largely refundable** to the estate. So:
- The home is **not** consumed by everyday spending and shouldn't sit in the spendable pool funding a flat everyday line;
- It is the **right-sized, naturally-timed asset** for the late-life accommodation spike;
- Ring-fencing it (excluding it from drawdown projections, then releasing it as the aged-care reserve) is **more accurate**, not a fudge.
This argues for modelling net worth in **two pools**: a **drawdown pool** (super, pensions, investments) funding the declining everyday glidepath, and a **reserve pool** (the home + a modest cash buffer) for the aged-care tail.

### 4.5 Net effect: easier or harder to fund?
**On balance, EASIER.** The literature is consistent (Blanchett: ~20% less capital needed under the smile; RAND: ~2%/yr real decline across all wealth; Milliman: −37% by 85+) that **the long, cheap slow-go/no-go middle outweighs the end spike** for a self-funded household. Three reasons it's easier for a high-net-worth couple specifically:
1. The everyday real decline runs for **~15–25 years** (a large cumulative saving), while the care spike is **~2–5 years** and partly **capital-neutral** (RAD refundable).
2. The spike is **funded by an asset (the home) the flat-line model already holds in reserve** — it isn't new money, it's re-purposed money.
3. **Clinical care is now free to all**, capping the genuinely uninsurable medical risk; non-clinical and accommodation costs are **bounded by lifetime caps and a 4-year rule**.

**The one risk that makes it harder:** a **long-tail care stay (4–5+ years for one partner)** combined with a **high RAD that erodes via retention** and full recurrent fees — this is the scenario the ring-fenced reserve and the 4–5 year stress branch are there to size. But it is a **bounded, insurable-by-asset tail risk**, not a reason to carry a flat real spend for ~36 years.

**Bottom line for the Monte Carlo:** replace the flat real spend with (a) a **declining real everyday glidepath** (1.0× to 70, taper ~1.5–2%/yr, floor ~0.75×) drawn from the investment pool, plus (b) a **separate aged-care reserve** (~$300–500k spendable + the home earmarked for RAD), modelled as **two single episodes of ~$71k/yr recurrent for ~2 years (stress 4–5)**. This is both more realistic and, net, **more affordable** than the flat assumption.

---

## Sources

**Spending smile / decline**
- Blanchett, *Estimating the True Cost of Retirement*, Morningstar Working Paper, 5 Nov 2013 — https://www.morningstar.com/content/dam/marketing/shared/research/foundational/677785-EstimatingTrueCostRetirement.pdf [US]
- Blanchett, *Exploring the Retirement Consumption Puzzle*, J. Financial Planning, May 2014 — https://www.financialplanningassociation.org/article/journal/MAY14-exploring-retirement-consumption-puzzle [US]
- Kitces, *How Total Spending Declines Over Time In Retirement* — https://www.kitces.com/blog/estimating-changes-in-retirement-expenditures-and-the-retirement-spending-smile/ [US]
- McLean AM, *What is the Retirement Spending Smile?* — https://www.mcleanam.com/what-is-the-retirement-spending-smile/ [US]
- Stein, *The Prosperous Retirement* (1998) framework via Pranawealth — https://www.pranawealth.com/three-phases-of-retirement-how-your-spending-changes/ and https://www.financialfreedomwmg.com/blog/go-go-slow-go-no-go-retirement-phases [US]
- RAND/HRS (Hurd & Rohwedder), 2022 — https://www.rand.org/news/press/2022/12/07/index1.html ; report RR-A2355-1 https://www.rand.org/pubs/research_reports/RRA2355-1.html [US]
- IFS Report R209, *How does spending change through retirement?*, Sept 2022 — https://ifs.org.uk/publications/how-does-spending-change-through-retirement-0 [UK]
- **Milliman Australia ESP, 23 Apr 2018** — https://au.milliman.com/en/insight/Analysis-Retirees-spending-falls-faster-than-expected-into-old-age and https://au.milliman.com/en/insight/research-falling-retirement-spend-driven-by-behaviour-not-declining-income [AUS]
- Productivity Commission / Grattan — https://grattan.edu.au/news/how-much-do-you-need-to-retire/ ; https://www.pc.gov.au/research/completed/housing-decisions-older-australians [AUS]

**ASFA Retirement Standard**
- ASFA consumer page (March 2026 qtr) — https://www.superannuation.asn.au/consumers/retirement-standard/ [AUS]
- ASFA detailed budgets, March 2025 (PDF) — https://www.superannuation.asn.au/wp-content/uploads/2025/06/ASFA_Retirement_Standard_Budgets_Mar_25_quarter.pdf [AUS]
- ASFA summary / lump sums (Feb 2026 PDF) — https://www.superannuation.asn.au/wp-content/uploads/2026/02/260223-ASFA-Retirement_Standard-Summary.pdf [AUS]
- SuperGuide (Dec 2025 qtr incl. 85+ band) — https://www.superguide.com.au/retirement-planning/how-much-cost-live-in-retirement [AUS]
- ASFA older-retiree standard (85+) — https://www.superannuation.asn.au/wp-content/uploads/2023/09/ASFA-RetirementStandardOlder-Sep2014.pdf [AUS]
- Actuaries Institute, re-evaluating the ASFA Standard — https://www.actuaries.asn.au/research-analysis/re-evaluating-the-asfa-standard-how-to-afford-a-comfortable-retirement-with-less-super [AUS]

**Aged care costs & reforms**
- GEN Aged Care Data, *People leaving aged care* (length of stay) — https://www.gen-agedcaredata.gov.au [AUS]
- Aged Care Act 2024 (Federal Register) — C2024A00104; Dept of Health & Aged Care "new arrangements from 1 Nov 2025" [AUS]
- Challenger adviser hub — 1 Nov 2025 reforms / HSC / NCCC / self-funded retirees [AUS]
- Services Australia — annual & lifetime caps for aged care costs [AUS]
- My Aged Care — aged care home costs and fees [AUS]
- Adviser fee guides (2026): Sensible Care, Superior Care, Aged Care Decisions, Tonkin Law, Best Aged Care Australia [AUS]

## Data gaps & cautions (flagged honestly)
1. Blanchett states a curve, not a single "−X%/yr"; the −1/−2/−1 decade split is Kitces' read.
2. RAND's exact per-wealth-quartile decline %s were behind an access block — confirmed "~2%/yr across all quartiles" only.
3. Stein's original age bands/percentages are advisor paraphrase, not his 1998 book.
4. NCCC lifetime cap conflicted: $130k legislated vs ~$135,319 (Sep 2025) vs ~$137,917 (Mar 2026) — verify against Services Australia primary.
5. Max RAD: $750k (Jan 2025) vs ~$758,627 (Jul 2025) — not primary-verified.
6. HSC/NCCC asset thresholds ($252k/$355k/$532k/$1.023M) are adviser-sourced, medium confidence; couple thresholds differ from singles.
7. Govt primary pages (health.gov.au, servicesaustralia.gov.au, myagedcare) could not be loaded directly — figures sourced from search snippets + adviser sites. Re-verify 4–6 before relying on them in a binding way.
