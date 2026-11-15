# Metric provenance and interpretation

This note distinguishes public transactional source data from generated demonstration data. A metric should not be described as observed customer behaviour unless its numerator and denominator come from observed records.

## Provenance rules

| Data domain | Source in this project | Interpretation |
|---|---|---|
| Orders, payments, order timestamps and delivery timestamps | Olist public Brazilian e-commerce dataset | Observed within that dataset and its population; not representative of Myntra |
| Product attributes | Public fashion catalog dataset and/or Olist product data | Catalog attributes only; source depends on pipeline input |
| Sessions, impressions, product views, cart events and search queries | ThreadIQ synthetic generator | Simulated behaviour; not actual web analytics |
| Inventory snapshots and promotions | ThreadIQ synthetic generator | Simulated operational data |
| Fashion return reason codes | ThreadIQ-generated proxy labels | Not a directly observed return-reason field in the public Olist source |
| A/B experiment cohorts | ThreadIQ experiment simulator | Simulated Bernoulli samples; not live randomized experiments |

## Important interpretation cautions

1. **Search zero-result rate:** the generator assigns zero results to a designated non-converting search archetype. Other generated search records are assigned positive result counts. The resulting percentage depends on the mixture of session archetypes and query-generation logic. It is not a measured real-storefront rate and should not be called an industry benchmark.
2. **Returns:** a generated return-reason code is a synthetic label. A low review score, cancellation, or proxy assignment does not independently prove that a physical item was returned. Call this a *simulated return-reason proxy* unless an actual return/refund source field is available.
3. **Delivery:** Olist delivery timestamps are observed source fields for the Olist dataset. They describe the Olist sample and historical period, not current carrier SLAs or another retailer's delivery performance.
4. **A/B testing:** simulated treatment/control outcomes are generated from configured probabilities. Their p-values describe the generated samples only. They cannot justify shipping a feature or establish causal impact in production.
5. **Mixed denominators:** session-level, order-level and item-level metrics must not be compared as if they shared a denominator. Always display numerator, denominator, unit and provenance alongside a KPI.
6. **Currency and market:** Olist is a Brazilian dataset. Preserve the source currency and market context; do not present its financial totals as INR or Indian fashion-commerce results without an explicit, documented conversion and market caveat.

## Reporting template

For each headline KPI, document:

- Metric name and business definition.
- Numerator and denominator.
- Grain: session, customer, order, order item, seller or SKU-day.
- Source tables and source type.
- Date range and filters.
- Formula and treatment of null/cancelled records.
- Whether the result is observed, synthetic, or a derived metric combining both.

## Safe portfolio wording

Use wording such as: “In this synthetic demonstration dataset, the funnel calculation identifies…” or “Within the Olist public sample, the observed delivery timestamp analysis shows…”. Avoid claiming that the figures describe Myntra, the Indian market, or real customers.
