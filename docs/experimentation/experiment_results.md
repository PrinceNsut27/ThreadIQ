# ThreadIQ — A/B Experiment Simulation Results & Decision Audit

> [!WARNING]
> **SIMULATION NOTICE & DATA PROVENANCE:**
> The experimental results documented below were generated using the ThreadIQ statistical experimentation simulation engine (`src/threadiq/experimentation/simulation.py`). All records carry the data lineage tag `source_type = 'simulated_experiment'`. These trials demonstrate the end-to-end mathematical methodology, power analysis, sample ratio mismatch detection, and decision rules. They do **not** represent real-world causal proof prior to live production deployment.

---

## 1. Summary of Simulated Experiments

| Experiment ID | Initiative Name | Primary KPI | Baseline Rate | Treatment Rate | Relative Lift | P-Value | Stat. Sig.? | SRM Check | Decision |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`EXP-01`** | Fit & Sizing Intelligence Widget | Apparel Item Return Rate | $24.33\%$ | $15.13\%$ | **$-37.81\%$** | $< 10^{-6}$ | **YES** | PASS ($p=1.0$) | **SHIP (100% Rollout)** |
| **`EXP-02`** | 1-Click Express Checkout & Wallets | Checkout Completion Rate | $9.75\%$ | $17.10\%$ | **$+75.38\%$** | $< 10^{-6}$ | **YES** | PASS ($p=1.0$) | **SHIP (100% Rollout)** |
| **`EXP-03`** | Semantic Search & Synonym Expansion | Search Click-Through Rate | $15.00\%$ | $31.08\%$ | **$+107.22\%$** | $< 10^{-6}$ | **YES** | PASS ($p=1.0$) | **SHIP (100% Rollout)** |

---

## 2. Detailed Experiment Analyses

### Experiment EXP-01: Fit & Sizing Intelligence Widget
- **Problem Statement**: The analytics audit established that **23.21% of ordered apparel items are returned**, with **Size & Fit causing 38.46% of returns** ($349.39 refund exposure) and **Activewear returns reaching 60.00%**.
- **Hypothesis**: Providing an interactive size recommendation widget on fashion Product Detail Pages (PDPs) will guide customers to optimal garment sizes, reducing the item return rate by at least $20\%$ without depressing add-to-cart rates.
- **Control Group (A)**: Standard PDP with static sizing table image.
- **Treatment Group (B)**: PDP with interactive Fit Advisor collecting height, weight, and fit preference with algorithmic size recommendations.
- **Randomization Unit**: `session_id` (cookie-level persistent across visits).
- **Target Population**: All visitors viewing apparel category PDPs.
- **Statistical Results**:
  - Control Sample ($n_A$): $1,500$ apparel orders, $365$ returned items ($24.33\%$).
  - Treatment Sample ($n_B$): $1,500$ apparel orders, $227$ returned items ($15.13\%$).
  - **Absolute Lift**: $-9.20$ percentage points.
  - **Relative Lift**: **$-37.81\%$** return reduction.
  - **Z-Statistic**: $-6.3307$.
  - **P-Value**: $< 0.000001$ ($p < 0.05$, statistically significant).
  - **95% Confidence Interval**: $[-12.03\%, -6.37\%]$.
  - **Sample Ratio Mismatch**: None detected ($\chi^2 = 0.0, p = 1.0$).
- **Guardrail Metrics**:
  - PDP Add-to-Cart Rate: Control $14.2\%$ vs Treatment $14.5\%$ (Neutral/Positive).
  - Customer Service Sizing Tickets: $-42\%$ decrease in treatment branch.
- **Decision Recommendation**: **SHIP (100% Rollout)**. Roll out to all apparel categories, beginning with Activewear and Dresses.

---

### Experiment EXP-02: 1-Click Express Checkout & Digital Wallets
- **Problem Statement**: Conversion funnel analysis revealed that **89.02% of users drop off between checkout start and payment authorization**, depressing overall conversion from $26.54\%$ down to $2.91\%$.
- **Hypothesis**: Embedding express 1-click digital wallet buttons (Pix, Apple Pay, Google Pay) and address autofill will eliminate form fatigue, increasing the checkout completion rate by at least $30\%$.
- **Control Group (A)**: Traditional multi-step checkout form requiring manual shipping and credit card entry.
- **Treatment Group (B)**: Express checkout accordion with 1-click Apple Pay, Google Pay, and Pix instant payment options.
- **Randomization Unit**: `customer_unique_id` (or anonymous checkout session).
- **Target Population**: All sessions initiating checkout (`checkout_started`).
- **Statistical Results**:
  - Control Sample ($n_A$): $2,000$ checkout sessions, $195$ completed purchases ($9.75\%$).
  - Treatment Sample ($n_B$): $2,000$ checkout sessions, $342$ completed purchases ($17.10\%$).
  - **Absolute Lift**: $+7.35$ percentage points.
  - **Relative Lift**: **$+75.38\%$** conversion lift.
  - **Z-Statistic**: $+6.8176$.
  - **P-Value**: $< 0.000001$ ($p < 0.05$, statistically significant).
  - **95% Confidence Interval**: $[+5.25\%, +9.45\%]$.
  - **Sample Ratio Mismatch**: None detected ($\chi^2 = 0.0, p = 1.0$).
- **Guardrail Metrics**:
  - Payment Gateway Chargeback Rate: $< 0.05\%$ (within compliance tolerance).
  - Average Order Value: Control $\$152.40$ vs Treatment $\$154.10$ (No dilution).
- **Decision Recommendation**: **SHIP (100% Rollout)**. Proceed with full release across mobile and desktop storefronts.

---

### Experiment EXP-03: Semantic Search & Dynamic Synonym Expansion
- **Problem Statement**: Storefront search analytics documented an **85.96% Zero-Result Search Rate** across queries such as *"vintage velvet kimono"*, *"gold sequin sneakers"*, and *"titanium trenchcoat"*, yielding a low search CTR of **14.04%**.
- **Hypothesis**: Deploying fuzzy token matching, fashion synonym dictionaries (e.g. sneakers $\to$ casual shoes), and a top-trending fallback recommendation module will lower zero-result searches to $< 20\%$ and increase search CTR by $\ge 50\%$.
- **Control Group (A)**: Legacy exact-string keyword search engine.
- **Treatment Group (B)**: Semantic search engine with synonym normalization and zero-result fallback recommendations.
- **Randomization Unit**: `session_id`.
- **Target Population**: All user sessions submitting a search query.
- **Statistical Results**:
  - Control Sample ($n_A$): $1,200$ search sessions, $180$ product clicks ($15.00\%$).
  - Treatment Sample ($n_B$): $1,200$ search sessions, $373$ product clicks ($31.08\%$).
  - **Absolute Lift**: $+16.08$ percentage points.
  - **Relative Lift**: **$+107.22\%$** CTR lift.
  - **Z-Statistic**: $+9.3555$.
  - **P-Value**: $< 0.000001$ ($p < 0.05$, statistically significant).
  - **95% Confidence Interval**: $[+12.78\%, +19.39\%]$.
  - **Sample Ratio Mismatch**: None detected ($\chi^2 = 0.0, p = 1.0$).
- **Guardrail Metrics**:
  - Search Query Latency: Control $42\text{ms}$ vs Treatment $68\text{ms}$ ($< 100\text{ms}$ SLA preserved).
  - Search Exit / Bounce Rate: Decreased from $64.2\%$ to $28.1\%$.
- **Decision Recommendation**: **SHIP (100% Rollout)**. Promote to production search cluster.
