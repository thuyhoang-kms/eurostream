# Velox × Adepto: Databricks accelerator kickoff, 11 Sep 2026

**Attendees:** Vu Tran and Hieu Ngoc Le (Velox team), Marcin Rawicki and Mateusz Kijewski (Adepto)

**Purpose:** The Velox team introduced the platform and asked Adepto to share its Databricks and data-project experience. This feeds a planned Databricks/data accelerator, starting with the assessment phase.

## 1. Velox demo (Vu and Hieu)

- **What it is:** An AI orchestrator on top of the SDLC. It has two focus areas:
  - The BA workflow, used for modernization (e.g., CETA) and greenfield spec-driven work.
  - The QA workflow, covering test generation, automation scripts and manual test execution.
- **Control Plane (web portal):** Central team governance for connections, users, LLM providers, the Knowledge Hub and memories.
- **Desktop app:** BA skills (read code, generate specs, compare against documents), automation-script generation pushed to GitHub, test generation, and agent-driven manual test execution with reports.
- **Knowledge Hub:** Lessons learned in a session can be reviewed and shared with the whole team. Session memory can be turned on or off.
- **LLM support:** Users can bring their own subscriptions (Claude Code, Codex, Copilot, Google) or providers such as Bedrock.

## 2. Marcin Rawicki: key points

- **Adepto's identity:** Data and AI is Adepto's DNA, not a side line. Nearly all of its engineers and architects have years of deep Databricks experience. Marcin joined about 5–6 weeks ago.
- **Governance of LLMs is critical.** He asked who maintains the allowed-model list and who adds or removes models. Vu said a project admin (TA/SA) does this during onboarding.
- **Why governance matters: Adepto is a consultancy, not a software house.**
  - Adepto usually works inside the client's own infrastructure, with client accounts, environments and tools, and can bring in very little of its own.
  - Clients restrict tooling for legal, compliance and regulatory reasons (EU, California) and for commercial ones. For example, a Microsoft-aligned client won't allow Google or AWS models, even better ones, because of contract terms.
  - Velox must respect each project's restrictions.
- **Fit concern:** Velox's strengths are SDLC acceleration, which fits Adepto's delivery model only partly. The two concepts need to be "married."
- **The assessment happens before the SDLC starts.** It covers two cases:
  - Greenfield: advising how to set up a Databricks environment properly.
  - Existing: getting access to a client's environment and auditing what's wrong, which is the usual case.
- **Scope question:** Putting the assessment into Velox turns it from an SDLC tool into something bigger. Whether that's wanted is a concept decision for Edwin (and Guy), not for Marcin and Mateusz.
- **Use vendor frameworks as the standard.** He shared the Databricks Well-Architected Framework and compared it with the Microsoft Well-Architected and Cloud Adoption Frameworks.
  - Vendor principles aren't argued with by clients, while Adepto or KMS principles would be. They are also maintained by the vendor.
  - Databricks guidance differs per cloud (Azure, AWS, GCP), so the tooling must account for that.
- **Team model is "multi-hatting."** Data projects have no classic BA / PM / architect trio; it collapses to one or two people. Marcin isn't fully convinced this is the best way, but he sees an opportunity: Velox could hold those roles so one person switches hats inside the tool.
- **Adoption risk:**
  - Adepto's data engineers are already "crazy advanced" with GenAI agents (VS Code, CLI, GitHub Actions).
  - A corporate tool that is slower or less capable will meet resistance.
  - Velox's potential is in optimizing their existing flow, but that is a later topic.

## 3. Mateusz Kijewski: key points

- **Harnesses:** Different subscriptions require their own harness binary (Claude Code, Codex, Copilot). A Copilot API key can't be pulled out, and an Anthropic subscription requires Claude Code.
  - Hieu confirmed Velox handles this per configuration; Velox calls these "code agents."
  - This matters because some customers contractually allow only Anthropic / Claude Code.
- **Edwin's direction:** Focus first on the **Mobius accelerator**, which covers policy compliance for Databricks and Azure. Velox could support it with dedicated skills and agents that define checks and scoring.
- **Timing risk:** The audit usually happens in pre-sales or early assessment, before Velox is deployed at the customer or permissions exist.
  - Onboarding Velox may cost more than simply running the audit, possibly with bare Claude Code.
  - The team needs to decide whether it's worth selling Velox that early.
- **How Adepto's Databricks work really runs** (Mateusz has started all of Adepto's Databricks projects):
  1. **Audit.** Customers always already have Databricks workspaces they set up themselves without expertise. These are often exposed to the internet, run unsecured VMs, and have critical security policies disabled. Adepto audits against Databricks' published, cloud-specific security best practices (roughly 20–30 items). This used to be manual; now agents go through the document item by item.
  2. **Remediation.** This is manual work done with the customer. Pipelines run 24/7, so changes need maintenance windows.
  3. **Continuous compliance monitoring.** Enterprises run tens or hundreds of platforms, set up by different lines of business with varying skill levels.
- **Cloud coverage:** Adepto has done this only for Azure customers so far. The Databricks-level logic is common, but the audit needs an Azure/AWS/GCP switch.
  - Example findings: public tokens, publicly accessible workspaces, no service principals used for deployments.
  - Later steps: scheduled audits and stronger remediation.
- **No BAs on data projects.** In 9 years of Databricks work, he has never had a BA, or even an architect.
  - Teams are one or two people (a data engineer plus an AI/ML engineer, sometimes a junior).
  - They do analysis, planning, build, deployment and maintenance themselves.
  - Requirements go directly into the customer's Jira or ADO.
- **Concrete recommendation:**
  - **Short term:** Build the Velox pilot strictly on the **Databricks Security Best Practices and Threat Model** document (now 38 pages), embedded as a spec. It applies to every customer regardless of maturity. He shared this and other Databricks audit links in the chat.
  - **Longer term:** Brainstorm in 1–2 weeks on how Velox could support a data-oriented SDLC. He calls this "a pickle" to work out later.

## 4. Other points

- **Vu:** Research shows assessment and validation/verification are the hardest phases of data projects. The team, with Edwin, chose to start with assessment. Guy wants the **full roadmap**, not just the assessment piece. The executive vision may be a new platform focused 100% on data, not just an add-on to SDLC.
- **Hieu:** Proposed Velox for the requirements/spec step before engineering work. This was pushed back on because data teams have no BA role.

## Action items

- **Velox team:** Get the materials Mateusz shared in the chat and base the assessment accelerator on the Databricks Security Best Practices document. Vu will re-watch the recording because his connection was poor.
- **Marcin and Mateusz:** Discuss the concept and positioning in person in Warsaw next week, then align with Edwin (and possibly Guy) on whether the assessment belongs in Velox and on the overall vision.
- **All:** Regroup in 1–2 weeks. Mateusz will schedule a follow-up for Wednesday or Thursday, since he may be off on Friday.
- **Open question:** Does early-phase use of Velox justify its onboarding cost compared with bare Claude Code?