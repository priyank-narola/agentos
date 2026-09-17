# Customer Discovery Interview Guide V1

## Purpose

Learn which real-world AI action companies want to automate but do not yet trust an agent to perform. This is not a sales call and it is not a product demo. The objective is evidence for selecting a market wedge.

## Interview target

Conduct 15 interviews across three groups:

- Five customer operations or support leaders.
- Five finance operations, controller, treasury, or payments leaders.
- Five engineering, platform, DevOps, or SRE leaders.

Prefer people at companies that are actively using AI agents, AI support systems, coding agents, automation, or workflow tools. A person who has a current manual approval process is more useful than a person who only has general interest in AI.

## Interview rules

1. Listen more than speak.
2. Do not present the current product until the final five minutes, and only if the interviewee asks.
3. Do not claim that a product solves a problem before the interviewee explains the problem.
4. Ask about past or current behaviour, not hypothetical future enthusiasm.
5. Record notes only with permission. Never record a call without explicit consent.
6. Do not send outreach, share contact details, promise a pilot, or state pricing without founder approval.

## Opening script

> Thank you for speaking with me. I am researching how companies decide which business actions AI agents can safely perform. I am not selling software in this conversation. I want to understand your current workflow, where human approval is still needed, and what makes certain actions too risky to automate. Is it okay if I take notes?

## Interview flow

| Time | Topic | Goal |
| --- | --- | --- |
| 0 to 3 minutes | Context and role | Understand the interviewee, their team, and their responsibility |
| 3 to 10 minutes | Current workflow | Learn how the work is performed today and where AI is involved |
| 10 to 18 minutes | Unsafe or blocked action | Identify one action the team does not trust an agent to perform |
| 18 to 23 minutes | Current controls and alternatives | Learn the manual process, existing tools, and why they are insufficient |
| 23 to 27 minutes | Cost, urgency, and ownership | Measure impact, timing, buyer, and pilot feasibility |
| 27 to 30 minutes | Close | Confirm notes, ask for a relevant referral, and thank them |

## Core questions

### Current workflow

1. Please walk me through a recent customer, finance, or production operation that changed data, money, access, or a live system.
2. Where does AI currently help in this workflow, if at all?
3. What systems are involved from request to final execution?
4. Which person is accountable if the result is wrong?

### The blocked action

5. What is one action you would like an AI agent to perform but currently do not allow it to perform alone?
6. Tell me about the last time that action needed a human review.
7. What could go wrong if the agent performed it incorrectly?
8. Is the concern about money, security, customer trust, compliance, technical downtime, or something else?
9. Can the action be reversed, compensated, or only prevented before it happens?

### Existing process and alternatives

10. What happens today when this action needs approval?
11. Which tools, internal systems, or manual checks do you use today?
12. What part of the current process is slow, expensive, risky, or frustrating?
13. Have you evaluated a product or built an internal solution to solve this? Why did it succeed or fail?

### Business value and pilot fit

14. How often does this action occur?
15. What would improve if you could automate it safely?
16. Who would own the decision to buy or pilot a solution?
17. Is solving this a current priority, a planned project, or only an interesting idea?
18. What would a safe 30-day pilot need to prove before you would consider continuing?

## Wedge-specific prompts

### Customer operations

- Which refund, credit, account change, or order action currently requires a human?
- Are your support platform controls sufficient, or do different systems create inconsistent policy and evidence?
- What is the financial and customer-experience impact of a wrong action?

### Finance operations

- Which payment, vendor, invoice, refund, or payout action cannot be delegated to automation today?
- What dollar value, context, or exception triggers an additional approval?
- What must an auditor be able to prove about the action later?

### IT and cloud operations

- Which production change do you refuse to let a coding or operations agent execute?
- Do pull requests, CI/CD approvals, and cloud policies solve the problem? If not, where do they fail?
- What rollback or compensation path must exist before the agent can act?

## Evidence capture

For each interview, create a separate record with these fields:

| Field | Record |
| --- | --- |
| Interviewee role and company type | No unnecessary personal data |
| Candidate wedge | Customer operations, finance operations, or IT/cloud operations |
| Exact blocked action | Use the interviewee's language |
| Current workflow | Request, approval, execution, and evidence path |
| Consequence of error | Money, customer impact, downtime, compliance, or security |
| Existing alternative | Product, in-house process, or manual control |
| Repeated quote | Verbatim where possible |
| Frequency and urgency | Observed statement, not an inferred score |
| Buyer and pilot condition | Who decides and what a pilot must prove |
| Evidence type | Fact, direct quote, opinion, inference, or assumption |

## Wedge selection threshold

Do not select a market until one wedge meets all of these conditions:

- At least three interviewees independently describe a comparable blocked action.
- The action has a clear business consequence and occurs often enough to matter.
- Existing tools or manual controls have a specific, evidenced limitation.
- A named buyer can see a reason to pilot or pay.
- The action can be integrated safely using a limited scope and test environment.

## What to do after five interviews

Summarise findings without choosing a winner prematurely:

1. List repeated actions and direct quotes.
2. Separate facts from assumptions.
3. Identify where interviewees disagree.
4. Score each wedge using the master-plan criteria.
5. Decide whether to continue interviews, change the candidate set, or prepare a pilot specification.
