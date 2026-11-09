# **Velox Databricks Assessment & Discovery Accelerator: PoC plan**

## **1\. Objective**

Show that Velox can run **AI-assisted discovery and assessment** of a legacy data platform. From the repo, the docs and a live Databricks workspace, it should produce structured findings, dependencies, risks, recommendations and MIGRATION scope in hours instead of days. EuroStream is the sample customer.

## **2\. Success criteria**

| \# | Criterion | Target |
| ----- | ----- | ----- |
| 1 | Known issues found (the baseline) | ≥ 80% |
| 2 | False positives | ≤ 20% |
| 3 | Dependency graph: all topics → tables → consumers covered | 100% |
| 4 | Discovery questionnaire: each question answered from evidence or flagged as open | ≥ 90% |
| 5 | Every workload gets a migration complexity score (L/M/H) with a rationale | 100% |
| 6 | Each finding cites evidence and a best-practice reference | 100% |
| 7 | Full run time | \< 1.5 h (manual: 1–2 weeks) |
| 8 | Addepto rates it "usable as a first draft" | Yes |

## **3\. PoC architecture**

```
Inputs → Knowledge Hub: EuroStream repo + docs site · README/paper · mock stakeholder notes
Databricks Security Best Practices (Azure) · Well-Architected Framework · Azure trial workspace
STAGE 1 — DISCOVERY
  A1  Business & Requirements  → business context, use cases, NFRs/SLAs, target-state requirements,stakeholder questionnaire (pre-filled + open questions)
  A2  Landscape & Architecture → component inventory, tech stack, current-state architecture diagram
  A3  Workloads & Dependencies → workload catalogue, data lineage/dependency graph, external dependencieste
STAGE 2 — ASSESSMENT
  A4  Governance, PII & GDPR   → PII register & gaps, secrets, erasure vs Delta retention, DQ/consent mapping
  A5  Platform Security Posture→ scored checklist from live read-only checks
  A6  Debt, Complexity & Report→ tech-debt register, complexity scoring, migration scope & waves,target mapping, recommendations, roadmap, cost, risks → full report (.docx)
```

A1 extends the **existing Velox BA agent** and its code-reading and document-comparison skills. That reuse is what keeps Discovery affordable.

## **4\. WBS**

| ID | Work package | Output | Effort |
| ----- | ----- | ----- | ----- |
| **1.0** | **Setup** |  | **2 d** |
| 1.1 | Velox project, harness and model pinned; Knowledge Hub loaded | Configured project | 0.25 d |
| 1.2 | Report template (12 sections, each mapped to an agent) | Template | 0.25 d |
| 1.3 | Mock business inputs: stakeholder interview notes and business goals, simulating the customer | Inputs | 0.25 d |
| 1.4 | Baseline list of expected findings (discovery \+ assessment) | Ground truth | 0.5 d |
| 1.5 | Azure trial workspace with planted misconfigs, read-only service principal, and a mocked config as fallback | Test workspace | 0.75 d |
| **2.0** | **Stage 1: Discovery agents** |  | **2.5 d** |
| 2.1 | A1 Business & Requirements (extends the BA agent) | §2 | 0.75 d |
| 2.2 | A2 Landscape & Architecture, including a Mermaid diagram | §3 | 0.75 d |
| 2.3 | A3 Workloads & Dependencies, including a lineage graph | §4–5 | 1 d |
| **3.0** | **Stage 2: Assessment agents** |  | **5 d** |
| 3.1 | A4 Governance, PII & GDPR | §6 | 1.5 d |
| 3.2 | A5 Platform Security Posture | §7 | 1.5 d |
| 3.3 | A6 Debt, Complexity & Report: scoring rubric, migration waves, roadmap, cost, risks, exec summary, .docx | §1, 8–12 | 2 d |
| **4.0** | **Validation** |  | **4 d** |
| 4.1 | End-to-end run \#1 and metrics | Metrics | 1 d |
| 4.2 | Tuning, run \#2, lessons captured in the Knowledge Hub | Final report | 1 d |
| 4.3 | Addepto review (send Thu AM; 60-min call at 15:00 VN) and adjust  | Feedback | 2 d |
| **5.0** | **Demo readiness** |  | **1.5 d** |
| 5.1 | Deck (7 slides) and demo script | Deck | 0.25 d |
| 5.2 | Backup recording and dry run | Video | 0.5 d |

## **5\. Timeline**

| Day | Task |  |  | Gate |
| ----- | ----- | :---- | :---- | ----- |
| **Fri 25 Sep** | Scope note to Edwin; book Addepto for Thu | Confirm availability | Request the Azure subscription | Team and access confirmed |
| **Mon 28 Sep** | 1.1, 1.2 → start A1 | 1.3, 1.4 → start A3 | 1.5 workspace | **M1: setup done by 17:00** |
| **Tue 29 Sep** | A1 ✔, A2 ✔ | A3 ✔ (AM) → start A4 | A5 | **M2: Discovery output ready** |
| **Wed 30 Sep** | A6 | A4 ✔ → run \#1 at 16:00 | A5 ✔ (AM), support the run | **M3: first full report** |
| **Thu 1 Oct** | AM: tuning / PM: Addepto review, deck | AM: run \#2 | PM: recording and dry run | **Freeze 12:00 · demo-ready 18:00** |
| **2-5 Oct** | Adjust solution needed based on Addepto discussion |  |  |  |
| **6-7 Oct** | **Demo to Guy/Edwin/Phong** |  |  |  |

## **6\. Updated report structure (what the PoC generates)**

**Part A: Discovery**

1. Executive summary: overall readiness score, top 5 risks, recommendation  
2. Business context and target-state requirements (use cases, NFRs, SLAs, residency, open questions)  
3. Data landscape and current-state architecture  
4. Workload catalogue: type, frequency, volume, owner  
5. Data dependencies and lineage, including external services

**Part B: Assessment**

6. Governance, PII and GDPR gaps  
7. Databricks security posture (scored)  
8. Technical debt register  
9. Migration complexity and scope: L/M/H per workload, in and out of scope, migration waves  
10. Target architecture and component mapping  
11. Recommendations, phased roadmap and cost estimate  
12. Risk register, assumptions and open decisions

**Appendix:** evidence links, best-practice references and the stakeholder questionnaire

## **7\. Demo (25 min)**

1. The problem: discovery and assessment take 1–2 weeks per engagement (2 min)  
2. **Stage 1 live:** requirements, architecture diagram and dependency graph appear (6 min)  
3. **Stage 2** (recorded): posture score, PII gaps, complexity heatmap (5 min)  
4. Report walkthrough: exec summary, migration waves, top 3 findings (5 min)  
5. Metrics against the baseline (3 min)  
6. Knowledge Hub reuse, then the roadmap and ask: a pilot with an Addepto customer, AWS/GCP, continuous compliance (4 min)

## **8\. Risks**

| Risk | Trigger | Fallback |
| ----- | ----- | ----- |
| Business analysis looks shallow (no real customer) | A1 output is generic | Use richer mock stakeholder notes; present A1 as "pre-filled questionnaire \+ open questions", which is realistic for day 1 of an engagement |
| Addepto pushes back on BA framing (data teams have no BAs) | Review feedback | Position A1 as a tool for the multi-hat engineer, which is Marcin's point, not as a BA role |
| Workspace not ready | Not live by Mon 17:00 | A5 runs against the mocked config |
| A5 or A6 overrun | Not done Wed 12:00 | A5: top 15 controls. A6: drop the cost estimate first |
