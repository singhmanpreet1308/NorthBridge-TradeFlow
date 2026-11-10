# Requirements Traceability Matrix

Generated 2026-11-10 15:23 UTC by `python -m nbit.traceability` from saved test results.

- Must requirements: **15**; with at least one linked test: **15**
- Verified: **4** · Implemented with stated gaps: **9** · In progress (core criterion missing): **2** · Failed tests: **0**

| Req | Title | BN | Story | Test cases | Passed | Test status | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FR-001 | Trade Capture | BN-001, BN-004 | US-001 | TC-GT-001, TC-CAP-001, TC-CAP-002, TC-CAP-003, TC-CAP-004, TC-CAP-005 | 6/6 | Passed | **Implemented** | Gap: Conflicting trade IDs abort the batch rather than being held for review |
| FR-002 | Automated Trade Validation | BN-002, BN-005 | US-002 | TC-GT-001, TC-CAP-002, TC-VAL-001, TC-VAL-004 | 4/4 | Passed | **Verified** |  |
| FR-003 | Independent Confirmation Validation | BN-002, BN-001, BN-005 | US-003 | TC-GT-001, TC-CAP-005, TC-VAL-002, TC-VAL-003 | 4/4 | Passed | **Verified** |  |
| FR-004 | Exception Management | BN-003, BN-005 | US-004 | TC-GT-001, TC-EXC-001, TC-EXC-002 | 3/3 | Passed | **Implemented** | Gap: No exception entity with reviewer assignment; quarantine record + approval stand in |
| FR-005 | Human Approval Workflow | BN-004, BN-003 | US-005 | TC-GT-001, TC-AMD-001, TC-AMD-002, TC-AMD-003, TC-AMD-008 | 4/5 | Passed | **In Progress** | Gap: No role-based authorisation; cancellation not implemented | Not run: TC-AMD-003 |
| FR-006 | Trade Versioning and Audit History | BN-004 | US-006 | TC-GT-001, TC-CAP-003, TC-AMD-001, TC-AMD-003, TC-AMD-004, TC-AMD-005, TC-AMD-007 | 6/7 | Passed | **Implemented** | Not run: TC-AMD-003 |
| FR-007 | Amendment Revalidation | BN-002, BN-005 | US-007 | TC-GT-001, TC-AMD-006, TC-AMD-009 | 3/3 | Passed | **Verified** |  |
| FR-008 | Simulated Regulatory Reporting | BN-005 | US-008 | TC-GT-001, TC-EXC-002, TC-RPT-001, TC-RPT-002, TC-RPT-003, TC-RPT-004 | 6/6 | Passed | **Implemented** | Gap: Simulated outcomes are positional not rule-based |
| FR-009 | Operational Analytics | BN-006 | US-009 | TC-GT-001, TC-BI-001, TC-BI-002, TC-BI-003, UAT-BI-001 | 4/5 | Passed | **Implemented** | Gap: Processing-latency KPI is not on the dashboard; .pbix walkthrough is manual | Not run: UAT-BI-001 |
| FR-010 | Predictive Intelligence and AI Investigation | BN-002, BN-003, BN-006 | US-010 | TC-GT-001, TC-AI-001, TC-AI-002, TC-AI-003, TC-AI-004, TC-AI-005, TC-AI-006, UAT-AI-001, TC-OPS-002 | 8/9 | Passed | **Implemented** | Gap: Live LLM answer quality is a manual UAT (UAT-AI-001) | Not run: UAT-AI-001 |
| NFR-001 | Processing Performance |  |  | TC-NFR-001 | 1/1 | Passed | **Implemented** | Gap: Timed on local storage only |
| NFR-002 | Reliability and Idempotency |  |  | TC-NFR-002 | 1/1 | Passed | **Verified** |  |
| NFR-003 | Security and Access Control |  |  | TC-AI-005, TC-NFR-003 | 2/2 | Passed | **In Progress** | Gap: RBAC and denied-attempt logging not implemented |
| NFR-004 | Auditability and Traceability |  |  | TC-VAL-004, TC-NFR-004 | 2/2 | Passed | **Implemented** | Gap: Audit trail reconstructed from component artefacts; no unified event store |
| NFR-005 | Safe Failure and Recoverability |  |  | TC-NFR-005, TC-OPS-001 | 2/2 | Passed | **Implemented** | Gap: Bounded retry not exercised outside Airflow |
