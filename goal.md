# ThreadIQ --- Fashion Commerce Product Intelligence & Operations Platform

## Product vision

Build **ThreadIQ**, an end-to-end product intelligence platform for a
simulated fashion e-commerce marketplace. ThreadIQ helps product
managers understand customer behaviour, diagnose commerce and
operational problems, prioritise product opportunities, and evaluate
proposed improvements using measurable evidence.

ThreadIQ is an independent portfolio project inspired by common
fashion-commerce problems. It is **not affiliated with Myntra and does
not use Myntra internal data**.

## Primary goal

Demonstrate the work of an analytical Product Manager across three
connected product areas:

1.  **Storefront / Customer Experience** --- search and discovery,
    product-page engagement, conversion funnel, personalisation,
    customer retention.
2.  **Inbound / Supply and Catalog** --- product catalog quality,
    inventory availability, stockout risk, pricing and promotion
    analysis, replenishment signals.
3.  **Outbound / Fulfillment and Delivery** --- order processing,
    dispatch and delivery performance, cancellations, returns and
    exchanges.

## Users

-   Product managers who need a clear view of product and operational
    health.
-   Analytics and operations teams investigating root causes.
-   Engineering, design and QA partners who need prioritised
    requirements and release criteria.
-   Interviewers evaluating product sense, analytical thinking,
    communication and execution.

## Core product capabilities

### A. Unified commerce data model

Bring together customers, products, sessions/events, orders, order
items, inventory snapshots, shipments, returns and promotions. Define
clear primary keys, timestamps, metric definitions and data-quality
checks.

### B. Storefront intelligence

-   Build an event funnel: impression → product click/view → add to cart
    → checkout start → purchase.
-   Analyse conversion and drop-off by device, category, traffic source,
    customer cohort and price band.
-   Analyse search queries, zero-result searches, click-through and
    search-to-purchase behaviour where data exists.
-   Create a transparent baseline recommendation approach
    (e.g. popularity or category affinity); do not claim
    production-grade personalisation.
-   Identify high-impact customer friction points and propose product
    changes.

### C. Inbound intelligence

-   Track stock-on-hand, stockout rate, days of cover and inventory
    availability.
-   Analyse demand and sales velocity by SKU/category.
-   Identify catalog completeness issues (missing size, colour, images,
    descriptions or category attributes).
-   Analyse price bands, discount depth and promotion performance.
-   Create explainable replenishment and catalog-quality flags; label
    forecasts as estimates.

### D. Outbound intelligence

-   Track order-to-dispatch and dispatch-to-delivery time.
-   Measure on-time delivery, late delivery, cancellation and return
    rates.
-   Segment performance by region, carrier, category, fulfilment mode
    and promised delivery window where fields exist.
-   Identify operational bottlenecks and estimate their commercial
    impact.
-   Analyse return reasons, especially size/fit, quality, description
    mismatch and damaged item where available.

### E. Product decision layer

-   Executive KPI overview across all three product areas.
-   Root-cause investigation pages.
-   Prioritised opportunity backlog using RICE or an explicitly
    explained scoring framework.
-   Experiment design workspace with hypothesis, primary metric,
    guardrails, target population, sample-size assumptions and decision
    rule.
-   PRD, customer journey, prototype, release checklist and post-launch
    review templates.

## Success criteria for the portfolio project

The project is successful when: - A user can run the application locally
from documented instructions. - Data sources and synthetic data are
clearly distinguished. - KPI definitions are documented and reproducible
in SQL/Python. - Each product area has at least one evidence-backed
problem statement and recommendation. - At least one experiment is
designed and analysed using either real experiment data or clearly
labelled simulated data. - The dashboard supports drill-downs rather
than only displaying decorative charts. - The repository includes a
concise PRD, metric dictionary, data dictionary, prioritised backlog,
prototype link/screenshots and release plan. - All quantified business
impacts are labelled as observed, estimated, modelled or simulated.

## Non-goals

-   Do not represent this as an actual Myntra product or internal case
    study.
-   Do not imply access to Myntra customer, order or operational data.
-   Do not claim causal uplift from observational data.
-   Do not fabricate results, experiments, customer interviews or
    deployments.
-   Do not build a complex machine-learning model before establishing
    reliable baseline metrics.

## Product principles

1.  Start with customer and business problems, not features.
2.  Prefer simple, explainable baselines.
3.  Define metric denominators and exclusions.
4.  Separate correlation from causation.
5.  Make assumptions visible.
6.  Prioritise decisions and usability over chart quantity.
7.  Design for a product review: every insight should lead to a decision
    or a question.
