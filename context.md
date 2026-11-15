# ThreadIQ --- Working Context for AI Coding Agents

## Project identity

**Name:** ThreadIQ\
**Full title:** Fashion Commerce Product Intelligence & Operations
Platform\
**Repository slug suggestion:** `threadiq-fashion-commerce-intelligence`

ThreadIQ is an independent portfolio project simulating a fashion
e-commerce product analytics and operations environment. It is intended
to demonstrate the skills expected of a Product Management Intern:
customer empathy, analytical thinking, problem decomposition,
prioritisation, experimentation, stakeholder communication and
execution.

It is inspired by the kinds of product problems found in fashion
commerce, including Myntra's publicly described product areas, but it is
not a Myntra product, internal tool, client engagement or official case
study.

## Scope

Build one coherent platform across:

### 1. Storefront / Customer Experience

-   Event funnel: impression → click/product view → add to cart →
    checkout → purchase.
-   Search quality: zero-result rate, search-to-click rate and search
    conversion when source data supports it.
-   Customer segmentation and cohort analysis.
-   Simple explainable recommendation baseline.
-   Product-page and checkout friction analysis.

### 2. Inbound / Procurement, Catalog, Pricing and Promotions

-   Catalog attribute completeness and product quality flags.
-   SKU/category sales velocity.
-   Inventory availability, stockout rate and days of cover.
-   Pricing, discount depth and promotion analysis.
-   Explainable replenishment indicators.

### 3. Outbound / Inventory, Fulfillment and Delivery

-   Order processing, dispatch and delivery durations.
-   On-time delivery and late-delivery rate.
-   Cancellation and return rates.
-   Delivery performance by geography, carrier and category where
    supported.
-   Return reason analysis and operational root causes.

### 4. Product decision layer

-   Cross-functional executive KPI dashboard.
-   Root-cause analysis.
-   Prioritised opportunity backlog.
-   Experiment design and analysis.
-   Product requirements, prototype, release plan and post-launch
    review.

## Technology constraints

-   Primary language: Python.
-   Data processing: Pandas, NumPy.
-   Database: SQLite for the first working MVP; PostgreSQL is acceptable
    if justified.
-   Analytics: SQL and Python.
-   App: Streamlit.
-   Visualisation: Plotly.
-   Statistical testing: SciPy/statsmodels where appropriate.
-   Testing: pytest.
-   Configuration: environment variables and `.env.example`; never
    commit secrets.
-   Keep the project runnable on a standard laptop. Avoid unnecessary
    cloud infrastructure.

## Data sources and honesty rules

Potential public sources: - Olist Brazilian E-Commerce dataset:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce - Fashion
Product Images dataset:
https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset

Before using a dataset, inspect its licence, provenance, schema and
limitations. Do not assume it contains clickstream, search, inventory
snapshots or a full fashion-commerce journey.

Where needed, create synthetic data for: - sessions and event funnels; -
search queries and zero-result events; - daily inventory snapshots; -
catalog completeness fields; - promotions and experiment assignment.

Synthetic records must be reproducible using a fixed random seed,
clearly marked as synthetic, and documented in
`docs/assumptions_and_limitations.md`. Do not merge synthetic and
observed data without a source/type field.

## Product and analytics standards

-   Define every KPI with numerator, denominator, time window, inclusion
    rules and exclusions.
-   Use correct denominators; distinguish order-level, item-level,
    session-level and customer-level metrics.
-   Handle cancellations, returns, duplicate events, missing timestamps
    and timezone assumptions explicitly.
-   Avoid data leakage in prediction tasks.
-   Do not call observational differences an experiment or causal
    uplift.
-   For A/B tests, document randomisation unit, eligibility, sample size
    assumptions, primary metric, guardrails, duration and decision rule.
-   If experiment data is simulated, explicitly label the results as
    simulated.
-   Separate observed results, estimates, model outputs and assumptions.
-   Never invent business results or claim that a feature improved
    conversion unless a valid experiment supports it.

## Product management standards

For each major opportunity, document: 1. User segment and customer
problem. 2. Evidence and severity/frequency. 3. Business impact and
affected KPI. 4. Root-cause hypothesis and alternative explanations. 5.
Proposed intervention. 6. Scope and non-goals. 7. Success metric and
guardrail metrics. 8. Dependencies, risks and rollout plan. 9.
Measurement and post-launch review.

Prioritise opportunities with a transparent framework such as RICE.
Explain score assumptions and avoid false precision.

## Engineering standards

-   Prefer small, testable modules over one large script.
-   Keep raw data immutable; write processed outputs separately.
-   Use config-driven paths rather than hard-coded machine paths.
-   Include validation for required columns, data types, duplicates and
    impossible values.
-   Add unit tests for metric calculations and data transformations.
-   Add clear logging and actionable error messages.
-   Keep notebooks for exploration; move reusable logic into
    `src/threadiq/`.
-   Make Streamlit pages readable and decision-oriented, not
    chart-heavy.
-   Provide a README with setup, data acquisition, run commands,
    screenshots and known limitations.

## Expected outputs

-   Working Streamlit application.
-   Reproducible data pipeline and documented schema.
-   Storefront, Inbound and Outbound analysis modules.
-   KPI and data dictionaries.
-   PRD and customer journey map.
-   Product backlog and prioritisation rationale.
-   Experiment plan and analysis.
-   Figma prototype or exported prototype screenshots.
-   Release checklist and post-launch review template.
-   Tests and setup documentation.

## How the coding agent should work

1.  Read `goal.md`, `sofar.md` and this `context.md` before changing
    code.
2.  Inspect the existing repository before creating or overwriting
    files.
3.  Start with a short implementation plan and identify assumptions.
4.  Build incrementally; do not generate the entire system in one
    unreviewable change.
5.  After each stage, run tests and report exact commands and outcomes.
6.  Update `sofar.md` with completed work, evidence, changed decisions
    and next steps.
7.  Keep `goal.md` stable unless the product goal is deliberately
    changed.
8.  If requirements conflict, preserve data integrity, honesty and the
    project's product-management learning goals.
9.  Ask the user only when a decision materially blocks implementation;
    otherwise choose a sensible, documented default.
10. Never claim deployment, test success, data validity or measured
    uplift without verification.
