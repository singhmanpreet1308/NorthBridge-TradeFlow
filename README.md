# NorthBridge-TradeFlow

An end-to-end OTC Trade Lifecycle Intelligence platform integrating Business Analysis, Data Engineering, Snowflake, Machine Learning, and Agentic AI to automate trade validation, detect exceptions, predict reporting risks, and deliver actionable operational insights.

![1791482829811](image/README/1791482829811.png)


## Phase 1 — Business & Domain Foundation

### Objective

Establish the business foundation for **NorthBridge TradeFlow**, an end-to-end OTC trade lifecycle solution designed to reduce manual processing errors, improve trade validation, and strengthen operational traceability.

### Business Problem

Manual trade capture and re-keying can introduce incorrect trade details, leading to reconciliation breaks, delayed corrections, and reporting exceptions.

### Scope & Key Activities

- **Business Analysis:** Define stakeholder responsibilities, business requirements (BRD), and product requirements (PRD).
- **Process Mapping:** Document the AS-IS OTC trade lifecycle and identify operational inefficiencies.
- **Data Definition:** Establish a standardised trade data dictionary and synthetic trade dataset.
- **Data Quality:** Define seeded validation defects and expected control outcomes.
- **KPI Framework:** Specify Straight-Through Processing (STP), defect rates, reporting outcomes, and processing latency.
- **Trade Scenario:** Establish T-1001, a 10-year GBP interest rate swap with an incorrect notional amount, as the core demonstration case.

### Tools & Technologies

`Markdown` · `Excel` · `draw.io` · `Git`

### Key Deliverables

- `Foundation.md` — Project charter, BRD, PRD, stakeholder analysis, and domain glossary.
- `AS_IS.drawio` — Current-state business process.
- `Data_Dictionary.xlsx` — Trade data definitions.
- `sample_trades.csv` — 50 synthetic OTC trades.
- `seeded_errors.csv` — Intentional data-quality defects.
- `T1001_Trade_Card.md` — Trade exception and amendment scenario.

### Expected Outcome

A documented business foundation with defined requirements, standardised trade data, measurable KPIs, and a traceable trade scenario to support solution design and implementation in Phase 2.
