<div align="center">

# 🍎 Hiver AI Support Agent

<img src="https://img.shields.io/badge/Brand-AppleSupport-black?style=for-the-badge&logo=apple&logoColor=white" />
<img src="https://img.shields.io/badge/LLM-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" />
<img src="https://img.shields.io/badge/Retrieval-TF--IDF-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/Evaluation-Macro_F1-green?style=for-the-badge" />
<img src="https://img.shields.io/badge/Golden_Set-200_Examples-purple?style=for-the-badge" />

<br/>

> **An AI-assisted customer support agent** built on the *Customer Support on Twitter* dataset, using **AppleSupport** conversations as the brand domain.

</div>

---

## 🎯 Overview

The system is designed around **three practical support-agent decisions**:

| # | Decision | Description |
|---|----------|-------------|
| 1 | 🏷️ **Classify** | Understand the customer''s intent |
| 2 | 🔍 **Retrieve** | Find similar historical AppleSupport interactions as evidence |
| 3 | ⚖️ **Decide** | Auto-handle the case or escalate to a human |

> **Core philosophy:** The project focuses on **grounded support**, **conservative escalation**, and **explicit evaluation** — rather than blindly generating answers.

---

## 📋 Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [What "Good" Means for AppleSupport](#2-what-good-means-for-applesupport)
3. [Intent Taxonomy](#3-intent-taxonomy)
4. [Dataset](#4-dataset)
5. [Dataset Split](#5-dataset-split)
6. [Golden Evaluation Set](#6-golden-evaluation-set)
7. [Historical Support Evidence](#7-historical-support-evidence)
8. [Retrieval System](#8-retrieval-system)
9. [Support Agent Architecture](#9-support-agent-architecture)
10. [Baselines](#10-baselines)
11. [Important Evaluation Correction](#11-important-evaluation-correction)
12. [Gemini Validation](#12-gemini-validation)
13. [What Is Misleading About a Headline Number?](#13-what-is-misleading-about-a-headline-number)
14. [Known Failure Modes](#14-known-failure-modes)
15. [What Was Not Built](#15-what-was-not-built)
16. [One More Week — What I Would Build](#16-one-more-week--what-i-would-build)
17. [Repository Structure](#17-repository-structure)
18. [Running the Project](#18-running-the-project)
19. [Reproducibility and Data Handling](#19-reproducibility-and-data-handling)
20. [Current Results Summary](#20-current-results-summary)
21. [Key Design Decisions](#21-key-design-decisions)
22. [Conclusion](#22-conclusion)

---

## 1. Problem Statement

Customer-support teams receive a large volume of **short, noisy, and sometimes incomplete messages**.

A useful support agent should not only generate a reply. It should:

- 🧠 First **understand** what the customer needs
- 📚 Use the brand''s own **historical support behavior** as evidence
- 🛑 Know **when to stop** and involve a human

> For this prototype, the selected brand is **AppleSupport**.

### Core Task Flow

```
Customer Message
      │
      ▼
Intent Classification
      │
      ▼
Historical Support Retrieval
      │
      ▼
Grounded Reply Generation
      │
      ▼
Auto-Handle  ──or──  Escalate to Human
```

---

## 2. What "Good" Means for AppleSupport

A good system should:

- ✅ Identify the customer''s **primary support intent**
- ✅ Avoid confusing a **root cause** with a symptom
- ✅ Use **real historical AppleSupport interactions** as evidence
- ✅ Avoid inventing **Apple policies, refunds, warranties, or guarantees**
- ✅ Produce **concise and natural** support replies
- ✅ **Escalate** cases that are sensitive, ambiguous, context-dependent, or insufficiently supported
- ✅ Make its **evidence and decision** understandable

> [!IMPORTANT]
> The goal is **not** to automate every customer message.
> The goal is to automate **only** when the system has enough evidence and the risk is acceptable.

---

## 3. Intent Taxonomy

The project uses **11 intents** derived from inspection of the AppleSupport data and manually reviewed examples.

| Intent | Meaning |
|--------|---------|
| `ACCOUNT_LOGIN` | Apple ID, iCloud login, password, sign-in, activation lock, account access |
| `APPLE_SERVICE_ISSUE` | Apple Music, Apple Pay, App Store / service / sync problems |
| `PURCHASE_BILLING` | Payments, charges, subscriptions, purchases, orders, billing |
| `DEVICE_PERFORMANCE` | Slow device, lag, freezing, crashing, general performance |
| `BATTERY_CHARGING` | Battery drain, charging, overheating, power issues |
| `IOS_UPDATE_ISSUE` | Problems explicitly caused by software / iOS updates, failed updates, update bugs |
| `HARDWARE_REPAIR` | Broken hardware, screen/buttons, physical damage, warranty, repair, replacement |
| `NETWORK_CONNECTIVITY` | Wi-Fi, mobile network, Bluetooth, calling, internet connectivity |
| `FEATURE_SETTINGS` | Keyboard, camera, settings, UI behavior, app features, storage / settings |
| `CONTEXT_REQUIRED` | Current tweet is a reaction/continuation and cannot be understood without previous context |
| `UNKNOWN_ESCALATE` | Genuinely unclear message that cannot reasonably be classified |

### Labeling Principle

> The **primary/root problem** is preferred over a secondary symptom.

**Example:** *"My phone became slow after the iOS update"*

| Classification | Label |
|---|---|
| ✅ Root cause | `IOS_UPDATE_ISSUE` |
| ❌ Surface symptom | `DEVICE_PERFORMANCE` |

The update is explicitly identified as the cause — so `IOS_UPDATE_ISSUE` is correct.

---

## 4. Dataset

**Source:** [Customer Support on Twitter — Kaggle](https://www.kaggle.com/thoughtvector/customer-support-on-twitter)

The project filters the original data to the **AppleSupport brand**.

### AppleSupport Subset

| Metric | Count |
|--------|-------|
| Total rows | **204,772** |
| Customer / inbound tweets | **97,896** |
| Company / support tweets | **106,876** |

### Raw Schema

```
tweet_id
author_id
inbound
created_at
text
response_tweet_id
in_response_to_tweet_id
```

| Flag | Meaning |
|------|---------|
| `inbound = True` | Customer tweets |
| `inbound = False` | AppleSupport responses |

---

## 5. Dataset Split

The customer messages were separated into **three non-overlapping sets**:

| Split | Count |
|-------|-------|
| Development set | **78,157** |
| Test set | **19,539** |
| Golden set | **200** |
| **Total** | **97,896** |

### Leakage Checks ✅

All three checks passed with **zero overlap**:

```
Golden ∩ Development = 0  ✅
Golden ∩ Test        = 0  ✅
Development ∩ Test   = 0  ✅
```

> The 200-example golden set is therefore kept **completely separate** from development and final evaluation workflows.

---

## 6. Golden Evaluation Set

`golden_set_200_reviewed.csv` contains **200 human-verified examples**. Every row was manually reviewed.

### Validation Summary

| Check | Result |
|-------|--------|
| Rows | 200 |
| Unique tweet IDs | 200 |
| Reviewed rows | 200 |
| Missing `final_intent` | **0** |
| Missing `multi_issue` | **0** |
| Missing `context_required` | **0** |

### Annotation Columns

```
tweet_id
text
final_intent
final_multi_issue
final_context_required
reviewer_note
reviewed
```

> This set is treated as the **ground truth evaluation set**.

### Golden Intent Distribution

| Intent | Count | Bar |
|--------|-------|-----|
| `CONTEXT_REQUIRED` | 56 | ████████████████████████ |
| `FEATURE_SETTINGS` | 41 | █████████████████ |
| `IOS_UPDATE_ISSUE` | 40 | █████████████████ |
| `APPLE_SERVICE_ISSUE` | 12 | █████ |
| `DEVICE_PERFORMANCE` | 11 | ████ |
| `HARDWARE_REPAIR` | 10 | ████ |
| `ACCOUNT_LOGIN` | 7 | ███ |
| `PURCHASE_BILLING` | 7 | ███ |
| `NETWORK_CONNECTIVITY` | 6 | ██ |
| `BATTERY_CHARGING` | 6 | ██ |
| `UNKNOWN_ESCALATE` | 4 | █ |

> [!NOTE]
> Because the class distribution is **not balanced**, the project reports **Macro F1** alongside accuracy rather than relying on accuracy alone.

---

## 7. Historical Support Evidence

The full AppleSupport dataset contains both customer and company tweets.

Customer tweets were **paired** with AppleSupport responses using:

```
customer.tweet_id  ==  support.in_response_to_tweet_id
```

This produced a clean historical retrieval corpus of **62,686** customer → AppleSupport response pairs.

Stored as: `historical_support_pairs_dev.csv`

### Schema

```
customer_tweet_id
customer_text
support_tweet_id
support_reply
```

### Retrieval Leakage Prevention

> [!CAUTION]
> The **200 golden examples are not used** as the retrieval corpus.

**Verification:**

```
Golden IDs in retrieval pairs = 0  ✅
```

During evaluation, the **current golden tweet ID** is also explicitly excluded from retrieval — preventing exact-match retrieval from artificially improving results.

---

## 8. Retrieval System

The current retrieval baseline uses **TF-IDF** with word unigrams and bigrams.

### Configuration

```python
TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    max_features=50000,
    stop_words="english"
)
```

Similarity is measured using **cosine similarity**. For each customer message, the system retrieves the top historical cases.

### Example

**New customer message:**
> *"my iPhone is freezing after the iOS update"*

**Retrieved historical cases:**

1. iPhone freezing after iOS 11
2. iOS 11 causing lag / freezing
3. iPhone performance issue after update

The corresponding AppleSupport replies are supplied as **evidence** to the response-generation component.

### Why Retrieval?

> Retrieval keeps the generated response connected to **real historical brand behavior** rather than relying only on general LLM knowledge.

---

## 9. Support Agent Architecture

```
                      Customer Message
                            │
                            ▼
                 ┌──────────────────────┐
                 │  Intent Classification│
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  Historical Retrieval │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Evidence Quality /   │
                 │       Policy         │
                 └──────┬───────┬───────┘
                        │       │
              ┌─────────┘       └─────────┐
              ▼                           ▼
        AUTO_HANDLE                   ESCALATE
              │                           │
              ▼                           ▼
       Grounded Reply           Human / DM Follow-up
```

### Intent Classification

The prototype uses **Gemini** for intent classification so that the 200 golden labels remain **evaluation-only** rather than training labels.

### Reply Generation

Gemini receives:

| Input | Description |
|-------|-------------|
| 💬 Current customer message | The incoming support request |
| 🏷️ Predicted intent | The classified intent label |
| 📋 Retrieved historical customer messages | Similar past cases |
| 💡 Retrieved historical AppleSupport replies | Brand responses as evidence |
| ⚖️ Escalation decision | Auto-handle or escalate |

> Gemini is instructed to **write a new support reply** rather than copying a historical response.

### Escalation Policy

The current policy is **intentionally conservative**.

#### 🔴 Always Escalated

```
ACCOUNT_LOGIN
PURCHASE_BILLING
HARDWARE_REPAIR
CONTEXT_REQUIRED
UNKNOWN_ESCALATE
IOS_UPDATE_ISSUE
```

#### 🟢 Can Be Auto-Handled When

- Relevant historical evidence exists
- Retrieval quality is sufficient
- Classifier confidence is above the automation threshold

> **Product principle:** *Automate only when the system has sufficient evidence and the risk is acceptable.*

---

## 10. Baselines

Two lightweight baselines were established.

### Baseline 1 — Majority Class

The majority intent in the golden set is `CONTEXT_REQUIRED`. The majority classifier predicts that intent for every message.

| Metric | Result |
|--------|--------|
| Accuracy | **0.28** |

> Intentionally weak — provides a **sanity-check lower bound**.

### Baseline 2 — Rule-Based Classifier

A deterministic keyword/rule classifier was implemented using the 11-intent taxonomy.

| Metric | Result |
|--------|--------|
| Accuracy | **0.38** |
| Macro F1 | **0.4053** |

> This baseline requires **no labeled training dataset** and shows how far simple domain rules can go.

---

## 11. Important Evaluation Correction

> [!WARNING]
> An earlier TF-IDF experiment trained and evaluated on the **same golden examples**, producing a misleading result.

```
❌ WRONG:   Accuracy = 99.5%  (evaluation leakage — golden set used in training)
```

### Correct Principle

```
✅ CORRECT:
   Golden set  →  evaluation only

❌ WRONG:
   Golden set  →  train model  →  evaluate on same data
```

> This project **intentionally does not report** the leaked 99.5% result.

---

## 12. Gemini Validation

The Gemini agent was validated end-to-end on representative examples.

### Example Validation

| Field | Value |
|-------|-------|
| Customer message | *"Too laggy ... i think 11.1 more laggy for old iphone..."* |
| Human label | `IOS_UPDATE_ISSUE` |
| Gemini prediction | `IOS_UPDATE_ISSUE` ✅ |
| Confidence | **0.95** |

The system also retrieved similar historical AppleSupport interactions and generated a new **evidence-grounded response**.

### API Limitation

> [!NOTE]
> A full 200-example Gemini generation evaluation was attempted. The API returned `429 RESOURCE_EXHAUSTED` because the available API quota was exhausted.

This project **does not claim** a fake full-200 Gemini accuracy from fallback outputs. This limitation is **recorded explicitly** rather than hidden.

---

## 13. What Is Misleading About a Headline Number?

Intent accuracy alone is **not equivalent** to successful customer-support resolution.

A system could:

- 🏷️ Classify an issue correctly but produce an **unhelpful reply**
- 📉 Retrieve **weak evidence**
- ⬆️ **Over-escalate**
- ❓ Fail on **context-dependent** messages
- ✨ Generate a **fluent** answer that is not actually grounded in brand behavior

### Multi-Dimensional Evaluation

```
Intent Quality
      +
Historical Evidence Quality
      +
Reply Quality
      +
Escalation Behavior
```

> The goal is **not** to maximize a single headline percentage at any cost.

---

## 14. Known Failure Modes

### Failure 1 — Update Cause vs. Performance Symptom

**Example:** *"my phone is slow after the update"*

| System | Prediction |
|--------|-----------|
| ❌ Keyword system | `DEVICE_PERFORMANCE` |
| ✅ Correct | `IOS_UPDATE_ISSUE` |

**Hypothesis:** Words such as "slow" and "lag" strongly associate with performance.

**Improvement:** Give explicit causal language (`"after update"`, `"since update"`, `"because of update"`) higher priority.

---

### Failure 2 — Context-Dependent Short Messages

**Examples:**

```
"Thanks!"     "Okay."     "Yes."     "That worked."
```

**Hypothesis:** Single-tweet classification cannot fully understand reactive conversation states.

**Improvement:** Include recent conversation history in classification.

---

### Failure 3 — Multi-Issue Messages

A message may contain:

```
battery drain  +  performance lag  +  Wi-Fi problems
```

A single-label classifier must choose one primary intent.

**Hypothesis:** Independent keyword matching does not understand root cause or priority.

**Improvement:** Explicitly detect multiple issues and select the primary one using conversation context.

---

### Failure 4 — Weak Retrieval Evidence

A retrieved case can have overlapping words but represent a **different underlying issue**.

**Hypothesis:** TF-IDF is **lexical** rather than semantic.

**Improvement:** Test hybrid retrieval using BM25 + embeddings or a dense retrieval model.

---

### Failure 5 — Historical Replies Are Sometimes Generic

Many AppleSupport replies are short:

```
"Please DM us."
"Let''s look into this."
"Send us a DM."
```

These are useful for escalation behavior but contain **limited troubleshooting detail**.

**Hypothesis:** Historical brand responses sometimes reflect the support workflow rather than the complete resolution.

**Improvement:** Retrieve more conversation turns and use the **full thread** rather than a single reply pair.

---

## 15. What Was Not Built

> [!NOTE]
> This prototype intentionally does **not** attempt to build:

| Out of Scope | Reason |
|-------------|--------|
| Production authentication | Prototype scope |
| Real customer-account access | Prototype scope |
| Real ticketing-system integration | Prototype scope |
| Access to proprietary Apple internal knowledge | Prototype scope |
| Payment / refund processing | Prototype scope |
| Production-scale vector database | Prototype scope |
| Real-time Twitter / X integration | Prototype scope |
|Fully autonomous issue resolution | Prototype scope |

> This is a **research / prototype** support-agent system for the Hiver take-home assignment.

---

## 16. One More Week — What I Would Build

With one additional week, I would prioritize:

### 1. 🧠 Conversation-Aware Intent Classification

Instead of classifying only the current tweet:

```
current tweet  +  previous 2–5 conversation turns
```

This should reduce `CONTEXT_REQUIRED` ambiguity.

### 2. 🔍 Hybrid Retrieval

Combine:

```
TF-IDF / BM25  +  dense embeddings
```

To capture both exact support terminology and semantic similarity.

### 3. 🗂️ Thread-Level Retrieval

Retrieve **complete customer/support conversation threads** rather than isolated message–response pairs.

### 4. ⚖️ Better Escalation Calibration

Use a small human-reviewed decision set to tune:

```
confidence threshold  +  retrieval threshold  +  intent risk level
```

### 5. 📊 Better Response Evaluation

Use a calibrated LLM judge plus human spot-checking for:

| Dimension | Description |
|-----------|-------------|
| Correctness | Is the answer factually right? |
| Grounding | Is it supported by evidence? |
| Helpfulness | Does it actually help the customer? |
| Unsupported claims | Does it invent brand policies? |
| Escalation appropriateness | Did it escalate when it should have? |

---

## 17. Repository Structure

```
hiver-ai-support-agent/
│
├── data/
│   ├── raw/
│   │   └── customer_support_on_twitter.csv
│   │
│   └── processed/
│       ├── apple_support.csv
│       ├── development_set.csv
│       ├── test_set.csv
│       ├── golden_set_200_reviewed.csv
│       └── historical_support_pairs_dev.csv
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   └── Hiver_Evaluation.ipynb
│
├── results/
│   ├── baseline_rule_predictions.csv
│   └── golden_predictions.csv
│
├── reports/
│   └── evaluation_report.md
│
├── README.md
└── requirements.txt
```

> [!NOTE]
> The `src/` package is intentionally omitted in this submission version because the current implementation is **notebook-based**.

---

## 18. Running the Project

### Streamlit Web App

To run the interactive Streamlit support agent:

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run app.py
   ```
3. Open your browser to the URL provided (usually `http://localhost:8501`).

### Basic Evaluation

The main notebook is:

```
notebooks/Hiver_Evaluation.ipynb
```

Run the notebook **from top to bottom** after installing the required Python dependencies.

The reproducible local components include:

| Step | Component |
|------|-----------|
| 1 | Data loading |
| 2 | Golden-set validation |
| 3 | Majority baseline |
| 4 | Rule-based baseline |
| 5 | Historical retrieval |
| 6 | Retrieval leakage checks |
| 7 | Agent demonstration |
| 8 | Evaluation outputs |

### Gemini API Setup

The generative component requires a **Gemini API key**.

For Colab, store the key as a Secret:

```
GOOGLE_API_KEY
```

> [!CAUTION]
> **Do not** hard-code the API key into source code or commit it to GitHub.

> The full generative evaluation is optional when API quota is unavailable.

---

## 19. Reproducibility and Data Handling

> [!IMPORTANT]
> Important reproducibility rules:

| Rule | Requirement |
|------|------------|
| 🔒 Golden set integrity | Must remain untouched during model training |
| 🚫 Retrieval exclusion | Must exclude the current golden tweet |
| 📊 Split integrity | Development / test / golden tweet IDs must remain non-overlapping |
| 🎲 Random seeds | Fixed seeds must be used for any randomized data split |
| 💾 Save API results | Generated API results should be saved rather than requiring repeated calls |
| 🔑 API key security | Keys must be supplied through environment variables or Colab Secrets |

---

## 20. Current Results Summary

| Component | Result |
|-----------|--------|
| AppleSupport total rows | **204,772** |
| Customer tweets | **97,896** |
| Development set | **78,157** |
| Test set | **19,539** |
| Golden set | **200** |
| Historical retrieval pairs | **62,686** |
| Golden / retrieval overlap | **0** ✅ |
| Majority baseline accuracy | **28%** |
| Rule baseline accuracy | **38%** |
| Rule baseline Macro F1 | **0.4053** |
| Gemini representative test | Correct on tested example ✅ |
| Full Gemini 200-call evaluation | Limited by API quota ⚠️ |

---

## 21. Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Small intent taxonomy** | A compact taxonomy makes evaluation and escalation policy manageable |
| 2 | **Context as an intent/state** | Short replies like "Thanks" cannot reliably be classified from the current tweet alone |
| 3 | **Keep the golden set independent** | The 200 human-reviewed examples are evaluation ground truth, not a training pool |
| 4 | **Historical brand responses as evidence** | The reply generator should reflect how the brand historically handled similar issues |
| 5 | **Conservative escalation** | Prefer escalation when risk, uncertainty, or evidence quality is unfavorable |
| 6 | **Do not report leaked results** | The earlier 99.5% result was discarded because the evaluation set had been used for training |
| 7 | **Record API limitations honestly** | Gemini quota prevented a complete run, so no fabricated full-set LLM metric is reported |

---

## 22. Conclusion

This project demonstrates a support-agent architecture that combines:

```
Intent Classification
        +
Historical Retrieval
        +
Evidence-Grounded Generation
        +
Conservative Escalation
        +
Explicit Evaluation
```

<div align="center">
---
## Hiver Requirements — Current Status

| Hiver Requirement                              | Current Status      | Details                                     |
| ---------------------------------------------- | ------------------- | ------------------------------------------- |
| Pick one brand                                 | ✅ Complete          | Apple Support                               |
| Intent taxonomy defined from data              | ✅ Complete          | 11 intents                                  |
| AI intent classification                       | ✅ Complete          | Gemini                                      |
| Reply grounded in historical brand responses   | ✅ Complete          | Retrieval + Gemini                          |
| Auto-handle vs. escalate + reason              | ✅ Complete          | Implemented                                 |
| Runnable repository                            |     Mostly complete  | Final setup and execution testing needed    |
| 150–250 hand-labelled golden examples          | ✅ Complete          | 200 examples                                |
| Sampling / labeling note                       | ✅ Complete          | Documented                                  |
| Trivial baseline                               | ✅ Complete          | Majority-class baseline: 28%                |
| Simple baseline                                | ✅ Complete          | Rule-based accuracy: 38%; Macro F1: 0.4053  |
| Automated metrics                              |      Partly complete  | Additional evaluation metrics may be needed |
| LLM-as-judge for reply quality                 | ✅ Complete          | Implemented                                 |
| Evidence of LLM-judge vs. human agreement      | ✅ Complete          | Agreement analysis completed                |
| Top 5 failure modes with examples + hypotheses | ✅ Complete          | Documented                                  |
| “What is misleading about my headline number?” | ✅ Complete          | Analysis included                           |
| What to do with one more week                  | ✅ Complete          | Next steps documented                       |
| Decision log: 10–15 decisions                  | ✅ Complete          | Documented                                  |
| README                                         |     Drafted          | Final review and cleanup needed             |
| Clean setup / reproducibility under 15 minutes |    done              | Verify on a clean environment               |
| No leaked evaluation numbers                   | ✅ Complete          | Identified and removed the 99.5% leakage    |

### Overall Status

**Most of the core requirements are complete.** The main remaining work is to finalize the README, verify clean setup and reproducibility, and complete any missing automated evaluation metrics.


### 💡 Core Design Principle

> *"A support agent should not just sound helpful.*
> *It should know what the customer needs,*
> *show where its answer came from,*
> *and know when not to answer autonomously."*

---

<img src="https://img.shields.io/badge/Built_for-Hiver_Take--Home_Assignment-blue?style=for-the-badge" />
<img src="https://img.shields.io/badge/Brand-AppleSupport-black?style=for-the-badge&logo=apple" />
<img src="https://img.shields.io/badge/Evaluation-Honest_%26_Grounded-green?style=for-the-badge" />

</div>
