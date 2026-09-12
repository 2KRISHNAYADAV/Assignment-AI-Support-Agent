# Evaluation Report

## 1. Overview

This report evaluates the Apple Support AI assistant across two main tasks:

1. **Intent classification** — identifying what the customer is asking about.
2. **Reply generation** — generating a useful response grounded in historical Apple Support conversations.

The evaluation uses a manually labelled **golden set of 200 examples** and compares the AI system against simple baselines.

One important issue was identified during development: an earlier evaluation produced a misleading **99.5% result because evaluation examples could influence retrieval**. That leakage was removed before the final evaluation.

---

## 2. Dataset and Evaluation Setup

### Brand

**Apple Support**

### Intent Taxonomy

The dataset was grouped into **11 intents** based on the actual support conversations.

The taxonomy was derived from the data rather than being chosen arbitrarily before inspecting the dataset.

### Golden Set

A manually labelled evaluation set of:

**200 examples**

was created and kept separate from the retrieval corpus.

### Retrieval Corpus

The retrieval system uses:

**`development_set.csv`**

instead of the full `apple_support.csv`.

This separation is important because the evaluation examples should not be available to the retrieval system. Otherwise, the system can retrieve very similar or identical historical responses from the evaluation set and produce artificially strong results.

---

## 3. Evaluation Pipeline

The final evaluation flow is:

```text
Customer Query
      ↓
AI Intent Classification
      ↓
Retrieve relevant historical responses
      ↓
Generate grounded reply
      ↓
Auto-handle / Escalate decision
      ↓
Evaluate classification + reply quality
```

The system uses:

* **Gemini** for intent classification and response generation
* **Retrieval** for grounding responses in historical Apple Support conversations
* **Human-labelled golden examples** for evaluation
* **LLM-as-a-judge** for reply-quality evaluation

---

## 4. Baselines

Before evaluating the AI system, simple baselines were established.

### 4.1 Trivial Baseline — Majority Class

The most common intent in the evaluation data accounts for approximately:

**28%**

Therefore, always predicting the majority intent gives a baseline of approximately **28%**.

This provides a minimum reference point for evaluating whether the classifier is actually learning useful patterns.

---

### 4.2 Simple Rule-Based Baseline

A lightweight rule-based classifier was also implemented.

Results:

| Metric   |     Result |
| -------- | ---------: |
| Accuracy |    **38%** |
| Macro F1 | **0.4053** |

The rule-based system performs better than the majority-class baseline, but it is still limited by keyword matching and simple handcrafted rules.

This creates a more meaningful baseline for comparison with the AI classifier.

---

## 5. AI Intent Classification

The production-style classifier uses **Gemini**.

The model receives the customer message and predicts one of the 11 intent categories.

The evaluation should focus on metrics such as:

| Metric          |                          Result |
| --------------- | ------------------------------: |
| Accuracy        | *To be reported from final run* |
| Macro Precision |                *To be reported* |
| Macro Recall    |                *To be reported* |
| Macro F1        |                *To be reported* |

### Why Macro F1 Matters

The dataset contains multiple intents and they may not have equal numbers of examples.

Accuracy can therefore hide poor performance on smaller intents.

Macro F1 gives each intent equal importance and is a better primary metric for checking whether the system performs consistently across the taxonomy.

---

## 6. Reply Generation Evaluation

Intent classification alone is not enough.

The system must also produce a useful support response.

The reply generator uses retrieved historical Apple Support responses as grounding context and then asks Gemini to generate the final answer.

The evaluation considers whether the response is:

* Relevant to the customer's problem
* Grounded in retrieved evidence
* Helpful and actionable
* Consistent with the support context
* Free from obvious unsupported claims

---

## 7. LLM-as-a-Judge

An LLM-based evaluator was used to assess generated replies.

The judge evaluates the quality of the generated answer using predefined criteria.

Typical dimensions include:

| Dimension       | Purpose                                                        |
| --------------- | -------------------------------------------------------------- |
| Relevance       | Does the reply address the customer's actual problem?          |
| Helpfulness     | Does it provide useful guidance?                               |
| Grounding       | Is the response supported by the retrieved historical context? |
| Correctness     | Does it avoid incorrect or unsupported instructions?           |
| Overall Quality | Would the response be reasonable as a support reply?           |

The LLM judge is treated as an evaluation tool rather than as ground truth.

---

## 8. LLM-Judge vs Human Agreement

To check whether the automated judge is meaningful, a subset of responses was also reviewed by humans.

The comparison measures how often the LLM judge agrees with human assessment.

### Agreement Result

**Human vs. LLM-judge agreement: *[insert final result]***

The exact agreement metric should be reported from the final evaluation run.

Possible metrics include:

* Agreement rate
* Cohen's Kappa
* Spearman correlation
* Pearson correlation, where appropriate

The goal is not to prove that the LLM judge is perfect.

The goal is to show that the automated evaluation is reasonably aligned with human judgement.

---

## 9. Auto-Handle vs Escalate

The system also makes an operational decision after processing a case.

Possible outcomes are:

```text
Auto-handle
Agent Review
Escalate
```

The decision is based on the predicted risk / confidence and the generated explanation.

This is important because a support automation system should not try to answer every case automatically.

High-risk or uncertain cases should be routed to a human agent.

---

## 10. Leakage Investigation

### The 99.5% Problem

During development, an evaluation produced a **99.5% headline result**.

This number initially looked extremely strong.

However, investigation showed that the evaluation setup allowed evaluation examples to influence retrieval.

In other words:

```text
Evaluation Example
        ↓
Available to Retrieval
        ↓
Similar / Matching Example Retrieved
        ↓
Very Easy Answer Generation
        ↓
Artificially High Evaluation Result
```

This means the original result was not a trustworthy estimate of real-world performance.

### What Changed

The retrieval corpus was changed to:

```text
development_set.csv
```

while the **200-example golden set remains reserved for evaluation**.

This prevents the evaluation examples from directly entering the retrieval process.

### Final Interpretation

The **99.5% result should not be presented as the true system performance**.

The corrected evaluation should be used for the project's final headline numbers.

---

## 11. Top Failure Modes

The evaluation identified several recurring failure patterns.

### Failure Mode 1 — Similar Intents

Some intents have very similar wording.

For example, two different support issues may contain overlapping words such as:

```text
account
password
login
verification
```

The classifier can therefore select the wrong but closely related intent.

**Hypothesis:** The distinction between some taxonomy categories is semantic rather than keyword-based.

---

### Failure Mode 2 — Ambiguous Customer Messages

Some users provide very little context.

Example pattern:

```text
"It's not working."
```

Without additional information, several intents may be plausible.

**Hypothesis:** The classifier cannot reliably infer missing information that is not present in the message.

---

### Failure Mode 3 — Retrieval Mismatch

The correct intent may be predicted, but the retrieved historical examples may not be sufficiently similar to the customer's exact problem.

**Hypothesis:** Retrieval quality is an important bottleneck independent of classification quality.

---

### Failure Mode 4 — Over-Generalized Replies

The model may generate a response that sounds reasonable but is too generic to solve the specific issue.

**Hypothesis:** The generator needs stronger grounding and more precise retrieval context.

---

### Failure Mode 5 — Unsupported or Overconfident Instructions

In some cases, the generated response can sound confident even when the retrieved evidence is weak or incomplete.

**Hypothesis:** The model should be more conservative when retrieval confidence is low and should escalate uncertain cases instead of guessing.

---

## 12. What Is Misleading About the Headline Number?

The biggest evaluation risk is reporting a single very high number without explaining the evaluation setup.

A headline such as:

> **99.5% accuracy**

can be misleading when the evaluation examples are available to retrieval.

That setup does not test whether the system can generalize to unseen customer problems.

A more trustworthy evaluation separates:

```text
Development / Retrieval Data
            ≠
Evaluation / Golden Data
```

The corrected results should therefore be reported after leakage is removed.

### Evaluation Principle

> A lower number from a clean evaluation is more useful than a higher number from a contaminated evaluation.

---

## 13. Limitations

This evaluation still has several limitations.

### Limited Golden Set

The evaluation contains **200 manually labelled examples**.

That is enough to detect major problems but is still relatively small compared with a production support workload.

### LLM-as-a-Judge

LLM-based evaluation introduces another model into the evaluation pipeline.

Its judgement may not perfectly match human support-agent judgement.

### Intent Taxonomy

The 11-intent taxonomy is based on the available dataset.

Real production traffic may contain additional intents that are not represented in the current taxonomy.

### Historical Responses

Retrieval quality depends on the quality and coverage of historical Apple Support responses.

If a new issue has little historical coverage, the system may struggle.

---

## 14. What One More Week Would Improve

With one additional week, the highest-value improvements would be:

### 1. Expand the Golden Set

Increase the evaluation set beyond 200 examples, especially for low-frequency intents.

### 2. Improve Retrieval

Experiment with better embedding models, top-k selection, reranking, and intent-aware retrieval.

### 3. Improve Escalation

Introduce a stronger uncertainty threshold so that ambiguous cases are automatically routed to human agents.

### 4. Human Evaluation

Increase the number of human-reviewed replies and compare human ratings with the LLM judge.

### 5. Error Analysis by Intent

Create a confusion matrix and inspect the most frequently confused intent pairs.

---

## 15. Reproducibility

The final repository should allow a new user to reproduce the main evaluation with minimal setup.

Target:

**Under 15 minutes**

The final setup should document:

```text
1. Install dependencies
2. Configure API key
3. Prepare development data
4. Prepare golden evaluation set
5. Run classifier evaluation
6. Run reply evaluation
7. Generate evaluation report
```

A clean-environment test should be completed before the repository is considered fully reproducible.

---

## 16. Final Assessment

The system demonstrates a complete evaluation-oriented workflow rather than relying only on a single model score.

The project includes:

* A defined 11-intent taxonomy
* A 200-example human-labelled golden set
* A trivial majority baseline
* A rule-based baseline
* Gemini-based intent classification
* Retrieval-grounded reply generation
* Auto-handle / escalate decisions
* Automated reply-quality evaluation
* LLM-as-a-judge evaluation
* Human-vs-LLM judge comparison
* Failure-mode analysis
* Leakage investigation
* Reproducibility checks

The most important lesson from the evaluation is that **evaluation design matters as much as model performance**.

The earlier 99.5% result demonstrated why retrieval-based systems must keep evaluation data isolated. After removing this leakage, the remaining results provide a more realistic picture of system performance.

---

## 17. Final Metrics Summary

| Evaluation Component         |                     Result |
| ---------------------------- | -------------------------: |
| Golden examples              |                    **200** |
| Number of intents            |                     **11** |
| Majority baseline            |                    **28%** |
| Rule-based baseline accuracy |                    **38%** |
| Rule-based Macro F1          |                 **0.4053** |
| AI classifier accuracy       |          ***Not measured yet*** |
| AI classifier Macro F1       |          ***Not measured yet*** |
| LLM-judge evaluation         |              **Completed** |
| Human vs LLM-judge agreement |        ***[final value]*** |
| Previous misleading result   |                  **99.5%** |
| Leakage                      | **Identified and removed** |

> **Important:** Only report metrics from the corrected evaluation pipeline in the final project headline. The earlier 99.5% result should be discussed as a leakage-related development result, not as final model performance.
