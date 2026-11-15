# Product Decision Log (Product Decision Records — PDR)

This log records major strategic, product, and technical architecture trade-offs agreed upon by the ThreadIQ product and engineering leadership.

---

## PDR-001: Separation of Observed Historical Transactions and Synthetic Behavioral Events
- **Date**: 2026-11-15
- **Status**: **APPROVED & IMPLEMENTED**
- **Deciders**: Product Lead, Principal Data Architect
- **Context**: The observed Olist e-commerce dataset provides verified real-world order lifecycles, delivery dates, and customer entities, but completely lacks top-of-funnel clickstream sessions and daily inventory snapshots.
- **Decision**: Architect a dedicated synthetic event generator (`src/threadiq/data/synthetic.py`) to simulate realistic customer journeys and daily warehouse inventory logs. Strictly tag every database row and metric output with its exact provenance (`observed`, `synthetic`, or `reconciled`).
- **Consequences**: Enables full-funnel analytics without fabricating transaction records. Guarantees complete data lineage and analytical credibility.

---

## PDR-002: Modular Python Analytics Package vs. Embedded Dashboard Logic
- **Date**: 2026-11-15
- **Status**: **APPROVED & IMPLEMENTED**
- **Deciders**: Senior Product Manager, Lead Full-Stack Engineer
- **Context**: Dashboard applications often embed SQL queries and calculations directly inside Streamlit view scripts, making automated testing and headless execution impossible.
- **Decision**: Encapsulate all business metrics, formulas, and aggregations in dedicated Python analytics classes (`src/threadiq/analytics/storefront/`, `inbound/`, `outbound/`). Streamlit pages act strictly as presentation consumers.
- **Consequences**: 100% pytest testability, zero calculation duplication, clean separation of presentation and domain logic.

---

## PDR-003: RICE Framework for Prioritization & Backlog Governance
- **Date**: 2026-11-15
- **Status**: **APPROVED & IMPLEMENTED**
- **Deciders**: VP of Product, Head of Engineering
- **Context**: Competing demands across storefront conversion, warehouse inventory, and carrier logistics require objective, evidence-based prioritization.
- **Decision**: Adopt RICE scoring with explicit rubrics for Reach, Impact, Confidence, and Effort. Require all proposed PRDs to demonstrate positive RICE rank before entering sprint planning.
- **Consequences**: Engineering effort is strictly allocated to high-yield initiatives (`OPT-01: Fit Advisor`, `OPT-02: Express Checkout`, `OPT-03: Semantic Search`).

---

## PDR-004: Pre-Registration & Sample Ratio Mismatch Gating for A/B Experiments
- **Date**: 2026-11-15
- **Status**: **APPROVED & IMPLEMENTED**
- **Deciders**: Data Science Lead, Product Manager
- **Context**: A/B testing can suffer from early stopping (peeking) and allocation biases that produce false positive wins.
- **Decision**: Implement automated Chi-square Sample Ratio Mismatch (SRM) checks ($\alpha = 0.001$) and fixed-sample power analysis before declaring experiment success.
- **Consequences**: Protects against shipping biased treatments; establishes institutional credibility in experiment reporting.
