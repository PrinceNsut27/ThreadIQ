# ThreadIQ — Product Roadmap & Execution Plan

> [!NOTE]
> **ESTIMATION NOTICE:**
> All milestone timelines, sprint durations, and completion target dates presented below are planning estimates based on standard team velocity and current technical dependencies. They are subject to iteration based on A/B experiment outcomes and operational capacity.

---

## 1. High-Level Product Horizon (Now / Next / Later)

```mermaid
gantt
    title ThreadIQ Product Execution Roadmap (Estimated Horizons)
    dateFormat  YYYY-MM-DD
    section Phase 1 (NOW)
    Analytics & Decision Engine (M1-M5)       :done,    des1, 2026-10-01, 2026-11-15
    PRD-01: Fit & Sizing Intelligence Engine   :active,  des2, 2026-11-16, 2026-12-15
    PRD-02: 1-Click Express Checkout & Wallets :active,  des3, 2026-11-20, 2026-12-20
    PRD-03: Semantic Search & Synonym Engine   :active,  des4, 2026-11-16, 2026-12-05
    section Phase 2 (NEXT)
    Dynamic Days of Cover Replenishment Alerts:         des5, 2026-12-21, 2027-01-20
    Dynamic Multi-Carrier Routing Engine      :         des6, 2027-01-05, 2027-02-15
    Catalog Ingestion Schema Validator        :         des7, 2027-01-10, 2027-02-01
    section Phase 3 (LATER)
    Algorithmic Clearance Markdown Engine     :         des8, 2027-02-16, 2027-03-31
    Merchant Fulfillment SLA Portal           :         des9, 2027-03-01, 2027-04-15
    AR Virtual Try-On Engine (PDP 3D)         :         des10, 2027-04-01, 2027-05-30
```

---

## 2. Milestone Breakdown & Backlog Tasks

### Phase 1: Tier 1 (NOW — Current Sprint Horizon: Q4 2026)

#### Milestone 5.1: Core Discovery & Search Optimization
- **Lead Owner**: Senior Search PM / Tech Lead
- **Key Deliverable**: PRD-03 (Semantic Search & Dynamic Synonym Expansion).
- **Backlog Tasks**:
  - [x] Ingest and tokenize search query streams (`fct_search_queries`).
  - [x] Build synonym dictionary table (`dim_search_synonyms`).
  - [x] Implement fuzzy Levenshtein typo tolerance.
  - [ ] Deploy A/B trial (`EXP-03`).
- **Success Criteria**: Zero-result searches $< 15.0\%$; Search CTR $\ge 35.0\%$.

#### Milestone 5.2: Checkout Friction Elimination
- **Lead Owner**: Growth PM / Full-Stack Engineer
- **Key Deliverable**: PRD-02 (1-Click Express Checkout & Digital Wallets).
- **Backlog Tasks**:
  - [ ] Gateway partner integration (Pix instant payment & mobile wallets).
  - [ ] CEP / Postal Code address autofill API integration.
  - [ ] Single-page accordion checkout component.
  - [ ] Deploy A/B trial (`EXP-02`).
- **Success Criteria**: Checkout completion rate $\ge 25.0\%$; Cart abandonment $\le 75.0\%$.

#### Milestone 5.3: Reverse Logistics Sizing Mitigation
- **Lead Owner**: Operations PM / Machine Learning Engineer
- **Key Deliverable**: PRD-01 (Digital Fit & Sizing Intelligence Engine).
- **Backlog Tasks**:
  - [ ] Ingest garment measurement specifications.
  - [ ] Build biometric recommendation scoring endpoint.
  - [ ] Embed "Find Your Size" widget on apparel PDPs.
  - [ ] Deploy A/B trial (`EXP-01`).
- **Success Criteria**: Apparel item return rate $\le 15.0\%$; Size/fit share $< 20.0\%$.

---

### Phase 2: Tier 2 (NEXT — Upcoming Quarter: Q1 2027)

#### Milestone 6.1: Supply Chain Inbound Resilience
- **Key Deliverable**: Dynamic Days of Cover Replenishment Alerts & Catalog Validator (`OPT-04`, `OPT-06`).
- **Backlog Tasks**:
  - [ ] Automated PO generation when SKU DoC drops below lead time buffer.
  - [ ] Ingestion schema gating rejecting listings with null season/usage.
- **Success Criteria**: $100\%$ catalog completeness; zero stockouts on core fashion SKUs.

#### Milestone 6.2: Outbound Carrier Intelligence
- **Key Deliverable**: Dynamic Multi-Carrier Routing (`OPT-05`).
- **Backlog Tasks**:
  - [ ] Carrier API integration for multi-carrier dispatch allocation.
  - [ ] Machine-learning estimated delivery date (EDD) prediction.
- **Success Criteria**: On-Time Delivery Rate (OTD%) $\ge 92.0\%$.

---

### Phase 3: Tier 3 (LATER — Strategic Horizon: Q2 2027)
- **Initiatives**: Algorithmic Clearance Markdown Rules (`OPT-07`), Merchant SLA Portal (`OPT-09`), AR Virtual Try-On (`OPT-10`).
- **Objective**: Automate end-of-season liquidation and explore next-generation computer vision try-on technologies.
