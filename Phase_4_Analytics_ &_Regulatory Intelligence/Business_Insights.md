
# NorthBridge TradeFlow — Business Insights

## 1. Objective

Analyse trade operations, validation outcomes and portfolio concentration using the NorthBridge TradeFlow synthetic GBP interest rate swap dataset.

**Data sources:** Snowflake dbt analytics views, Phase 3 validation audit, quarantine evidence and Power BI.

**Scope:** 50 current trades. Results demonstrate operational controls using synthetic data rather than production trading activity.

## 2. Key Findings

### Finding 1 — Early Validation Prevented a Significant Notional Error

**Evidence**

- Initial trades evaluated: 50
- Accepted trades: 49
- Quarantined trades: 1
- Initial quarantine rate: 2%
- T-1001 original notional: GBP 100,000,000
- Independent confirmation: GBP 10,000,000
- Detected rule: DEMO_NOTIONAL_MISMATCH

**Business interpretation**

The reconciliation control identified a GBP 90 million difference between the captured trade and the independent confirmation.

The trade was blocked before entering the curated dataset, demonstrating how early validation can prevent incorrect information from propagating downstream.

**Recommendation**

Keep independent confirmation reconciliation as a mandatory pre-reporting control. Prioritise investigation of notional mismatches and monitor the frequency of these exceptions.

**Traceability:** BN-001 / FR-OMS-014 / DEMO_NOTIONAL_MISMATCH, subject to confirmation against the requirements traceability matrix.

### Finding 2 — Controlled Amendments Improve Data Integrity and Traceability

**Evidence**

- T-1001 v1 retained in quarantine
- Human approval documented
- T-1001 v2 created with a corrected GBP 10 million notional
- Corrected version passed validation
- Snowflake current-trade count increased from 49 to 50
- Duplicate trade/version combinations: 0
- Current validation pass rate: 100%

**Business interpretation**

The amendment workflow demonstrates how an incorrect trade can be corrected without overwriting the original exception evidence.

This supports investigation, accountability and reliable current-trade analytics.

**Recommendation**

Extend the reusable amendment process to other supported trade corrections. Retain approval, validation and version records and test replay protection for each amendment batch.

**Traceability:** Human-approved amendment requirement and trade-version preservation requirement; exact requirement IDs to be verified against Phase 2.

### Finding 3 — Counterparty Notional Concentration Requires Monitoring

**Evidence**

- Total current GBP notional: GBP 664.5 million
- CP-009 notional: GBP 169 million
- CP-009 share of total: approximately 25.4%

**Business interpretation**

CP-009 represents the largest notional concentration displayed in the current portfolio dashboard.

This does not establish an equivalent credit exposure or financial loss. It provides an operational indicator for identifying counterparties requiring closer review.

**Recommendation**

Monitor notional concentration by counterparty and investigate unusual changes over time. Add appropriate risk and exposure measures if supported data becomes available.

**Traceability:** Portfolio monitoring and counterparty exposure requirements; exact requirement IDs to be verified against Phase 2.

## 3. Limitations

- The dataset is synthetic and contains only 50 current trades.
- Historical exception analysis currently covers the original validation batch.
- Current validation success is not equivalent to straight-through processing.
- Counterparty notional is not a measure of credit exposure.
- Simulated reporting rejection and resubmission outcomes have not yet been executed.
- Operational processing latency has not been reliably measured.
- No findings establish real-world predictive performance or regulatory compliance.

## 4. Conclusion

NorthBridge TradeFlow demonstrates how trade validation, controlled amendments and operational analytics can improve the visibility and traceability of trade-processing issues.

The strongest demonstrated result is the T-1001 lifecycle: an incorrect captured notional was identified, quarantined, approved for correction, revalidated and made available to downstream analytics while preserving its original exception evidence.

Further work is required to implement simulated reporting outcomes, measure processing efficiency and complete end-to-end testing.
