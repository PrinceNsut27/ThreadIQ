# ThreadIQ — System Architecture & Technical Design

## 1. System Overview

**ThreadIQ** is an integrated fashion commerce product intelligence and operational decision platform. It bridges the gap between digital consumer behavior and physical supply chain execution by providing real-time diagnostic intelligence, algorithmic decision support, and closed-loop experimentation.

---

## 2. Multi-Tier Architecture

ThreadIQ is organized into a modular five-tier architecture designed for separation of concerns, testability, and operational resilience:

```mermaid
flowchart TD
    subgraph Tier 1: Data Ingestion & Storage
        S1["Observed E-Commerce Transactions (Olist)"]
        S2["Fashion Catalog Metadata (Kaggle Fashion)"]
        S3["Stochastic Behavioral Clickstream (fct_sessions, fct_events)"]
        S4["Warehouse Inventory Time-Series (fct_inventory_snapshots)"]
        DB[("Relational Database Store (data/threadiq.db)")]
        S1 & S2 & S3 & S4 --> DB
    end

    subgraph Tier 2: Validation, Cleaning & ETL
        V1["Multi-Encoding CSV Ingestion (src/threadiq/data/ingestion.py)"]
        V2["7-Point Quality Gates & Quarantine (src/threadiq/data/validation.py)"]
        V3["Star-Schema Transformations (src/threadiq/data/transformations.py)"]
        V1 --> V2 --> V3 --> DB
    end

    subgraph Tier 3: Core Domain Analytics Engines
        A1["Storefront Analytics (Funnel, Search, Merchandising, RFM)"]
        A2["Inbound Analytics (Catalog Completeness, Stockouts, DoC, Replenishment)"]
        A3["Outbound Analytics (Fulfillment Funnel, OTD% SLA, Return Decomposition)"]
        DB --> A1 & A2 & A3
    end

    subgraph Tier 4: Product Decision & Experimentation Layer
        E1["Statistical Calculator (Sample Size, Z-Test, Welch T-Test, SRM)"]
        E2["RICE Prioritization Engine (Ranked Now/Next/Later Backlog)"]
        E3["PRDs & Operational Governance SOPs"]
        A1 & A2 & A3 --> E1 & E2 --> E3
    end

    subgraph Tier 5: Presentation & Dashboard
        UI["Interactive Streamlit Web Application (app.py)"]
        UI1["Executive Overview"]
        UI2["Storefront Intelligence"]
        UI3["Inbound Intelligence"]
        UI4["Outbound Intelligence"]
        UI5["A/B Experimentation"]
        UI6["Product Roadmap & RICE"]
        UI7["Strategic Insights & PRDs"]
        UI --> UI1 & UI2 & UI3 & UI4 & UI5 & UI6 & UI7
        A1 & A2 & A3 & E1 & E2 --> UI
    end
```

---

## 3. Technology Stack & Rationale

| Layer | Component | Technology Selection | Rationale |
| :--- | :--- | :--- | :--- |
| **Language** | Runtime | **Python 3.13** | Core language for data engineering, scientific computing, and rapid web prototyping. |
| **Data Processing** | Numerical & Tabular | **Pandas, NumPy** | High-performance vectorized tabular transformations and aggregations. |
| **Statistics** | Statistical Testing | **SciPy 1.15.3, Statsmodels 0.14.4** | Exact two-proportion z-tests, Welch's t-tests, power analysis, and Chi-square goodness-of-fit. |
| **Database** | Relational Store | **SQLite 3 via SQLAlchemy 2.0** | Serverless, zero-configuration local embedded database with standard ANSI SQL and star-schema support. |
| **Presentation** | Interactive Web UI | **Streamlit 1.45.1, Plotly 5.24.1** | Native Python web framework for reactive data applications; eliminates frontend/backend overhead. |
| **Quality** | Testing Suite | **Pytest 8.3.4, AppTest** | Comprehensive unit testing and native headless Streamlit integration smoke testing. |

---

## 4. Key Architectural Patterns

1. **Explicit Data Provenance Tagging**:
   - `[OBSERVED]`: Real-world transactions from the Olist Brazilian E-Commerce dataset.
   - `[SYNTHETIC]`: Simulated clickstream events, search queries, and daily warehouse inventory snapshots.
   - `[RECONCILED]`: Cross-layer metrics reconciling behavioral engagement with verified financial transactions.
2. **Defensive Programming & Zero-Division Protection**:
   - All analytics calculations inherit from `BaseAnalytics` and utilize `calc_rate(numerator, denominator)` with `NULLIF` and `try/except` safeguards.
3. **Decoupled Analytics and Presentation**:
   - Dashboard view scripts do not execute raw calculations or embedded business logic; they consume domain analytics methods returning structured `MetricResult` dataclasses or validated DataFrames.
