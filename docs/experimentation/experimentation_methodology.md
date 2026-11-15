# ThreadIQ — A/B Experimentation Methodology & Statistical Framework

## 1. Principles of Experimentation

At ThreadIQ, product decisions are governed by randomized controlled experimentation rather than intuition. To establish causal inference, all digital interventions undergo rigorous statistical evaluation:

1. **Explicit Pre-Registration**: Hypotheses, primary metrics, secondary metrics, guardrails, sample sizes, and decision rules must be documented before experiment deployment.
2. **Strict Randomization Unit**: Randomization is conducted at the stable identifier level (e.g. `customer_unique_id` for logged-in users, persistent `session_id` for anonymous storefront visitors).
3. **No Peeking / Sequential Testing Control**: Decision evaluation occurs strictly upon reaching the pre-calculated sample size to prevent inflated false positive rates ($\alpha$-inflation).
4. **Data Lineage Transparency**: Real-world observed data and synthetic experimental simulations are never conflated. All simulated evaluations are tagged with `source_type = 'simulated_experiment'`.

---

## 2. Statistical Mechanics & Formulas

### 2.1 Two-Sample Proportion Test (Conversion Rates)
Used for binary conversion events (e.g., checkout completion, cart addition, return incidence).

- **Null Hypothesis ($H_0$)**: $p_{\text{treatment}} = p_{\text{control}}$
- **Alternative Hypothesis ($H_1$)**: $p_{\text{treatment}} \ne p_{\text{control}}$ (two-tailed)

**Pooled Proportion ($\hat{p}$)**:
$$\hat{p} = \frac{x_{\text{ctrl}} + x_{\text{trt}}}{n_{\text{ctrl}} + n_{\text{trt}}}$$

**Pooled Standard Error ($SE_{\text{pooled}}$)**:
$$SE_{\text{pooled}} = \sqrt{\hat{p}(1 - \hat{p}) \left( \frac{1}{n_{\text{ctrl}}} + \frac{1}{n_{\text{trt}}} \right)}$$

**Z-Statistic**:
$$Z = \frac{p_{\text{trt}} - p_{\text{ctrl}}}{SE_{\text{pooled}}}$$

**Confidence Interval for Absolute Difference ($p_{\text{trt}} - p_{\text{ctrl}}$)**:
$$CI_{1-\alpha} = (p_{\text{trt}} - p_{\text{ctrl}}) \pm Z_{\alpha/2} \sqrt{\frac{p_{\text{ctrl}}(1 - p_{\text{ctrl}})}{n_{\text{ctrl}}} + \frac{p_{\text{trt}}(1 - p_{\text{trt}})}{n_{\text{trt}}}}$$

---

### 2.2 Welch's Independent T-Test (Continuous Metrics: AOV & Lead Time)
Used for monetary spend and time-duration metrics where variances between Control and Treatment cannot be assumed equal ($\sigma_{\text{ctrl}}^2 \ne \sigma_{\text{trt}}^2$).

- **Test Statistic**:
  $$t = \frac{\bar{X}_{\text{trt}} - \bar{X}_{\text{ctrl}}}{\sqrt{\frac{s_{\text{ctrl}}^2}{n_{\text{ctrl}}} + \frac{s_{\text{trt}}^2}{n_{\text{trt}}}}}$$
- **Welch-Satterthwaite Degrees of Freedom ($\nu$)**:
  $$\nu \approx \frac{\left( \frac{s_{\text{ctrl}}^2}{n_{\text{ctrl}}} + \frac{s_{\text{trt}}^2}{n_{\text{trt}}} \right)^2}{\frac{(s_{\text{ctrl}}^2 / n_{\text{ctrl}})^2}{n_{\text{ctrl}} - 1} + \frac{(s_{\text{trt}}^2 / n_{\text{trt}})^2}{n_{\text{trt}} - 1}}$$

---

### 2.3 Sample Size Determination Formulas

#### For Proportions:
$$n = \frac{\left( Z_{\alpha/2}\sqrt{2\bar{p}(1 - \bar{p})} + Z_{\beta}\sqrt{p_1(1 - p_1) + p_2(1 - p_2)} \right)^2}{(p_2 - p_1)^2}$$
where $\bar{p} = \frac{p_1 + p_2}{2}$, $Z_{\alpha/2} = 1.96$ (for $\alpha = 0.05$), and $Z_{\beta} = 0.84$ (for $80\%$ power).

#### For Continuous Variables (e.g., AOV):
$$n = \frac{2 \left( Z_{\alpha/2} + Z_{\beta} \right)^2 \sigma^2}{\Delta^2}$$
where $\sigma$ is the historical standard deviation, and $\Delta$ is the minimum absolute difference to detect.

---

## 3. Sample Ratio Mismatch (SRM) Quality Gate

A **Sample Ratio Mismatch (SRM)** occurs when the observed ratio of visitors assigned to Control vs Treatment deviates significantly from the planned design (e.g. 50/50). SRM indicates upstream engineering bugs (e.g. redirect latency, device bias, or caching failures) that invalidate statistical inference.

The verification uses a Pearson Chi-Square Goodness-of-Fit test with a stringent significance threshold ($\alpha = 0.001$):
$$\chi^2 = \sum_{k \in \{\text{ctrl}, \text{trt}\}} \frac{(O_k - E_k)^2}{E_k} \quad (\text{df} = 1)$$

If $p < 0.001$, the experiment is automatically flagged as **COMPROMISED**, and decision rollout is blocked until the root cause is resolved.

---

## 4. Guardrail Metrics & Stopping Protocol

To protect customer experience and revenue integrity, every experiment designates mandatory guardrails:
1. **Commercial Guardrail**: Total revenue per visitor must not decline by $> 1.0\%$ ($p < 0.05$).
2. **Customer Satisfaction Guardrail**: Support ticket volume must not increase by $> 10.0\%$.
3. **Logistics Guardrail**: Outbound order cancellation rate must not exceed historical baseline $+ 1.5\%$.

**Emergency Abort Rule**: If a treatment branch causes a statistically significant drop in revenue or order completion with $p < 0.01$ at any point after $25\%$ of sample collection, the feature flag is automatically dialed to $0\%$ traffic.

---

## 5. Decision Rules Matrix

| Statistical Outcome | Primary KPI Lift | Guardrail Status | Product Decision |
| :--- | :--- | :--- | :--- |
| $p < 0.05$, $CI_{\text{lower}} > 0$ | Positive & $\ge \text{MDE}$ | All Guardrails Neutral/Green | **Full Rollout (100% Traffic)** |
| $p < 0.05$, $CI_{\text{lower}} > 0$ | Positive & $\ge \text{MDE}$ | 1+ Guardrails Breached | **Block Rollout; Investigate Trade-off** |
| $p \ge 0.05$ | Flat / Inconclusive | All Guardrails Neutral | **Deprecate Feature or Iterate Design** |
| $p < 0.05$, $CI_{\text{upper}} < 0$ | Negative | Any | **Immediate Rollback** |
