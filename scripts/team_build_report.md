# Catalog build report (team repos)

## Summary

| Metric | Count |
|--------|------:|
| Total skills | 204 |
| Ready | 191 |
| Stub | 9 |
| Broken | 4 |

## ⚠ Duplicate skill_id rejections

The following skills were **rejected** because their `skill_id` was already claimed by another repo. First-claimer wins; the rejected team must rename their skill or coordinate with the first claimant.

| Rejected team / repo | `skill_id` | First claimed by |
|---|---|---|
| `asian_am-225-skills` | `example-skill` | `cs-348-skills` |
| `poli_sci-210-skills` | `counter-example` | `asian_am-225-skills` |
| `poli_sci-210-skills` | `skill-name` | `jour-201-1-skills` |
| `cs-214-skills` | `example-skill` | `cs-348-skills` |

## Skills needing attention

| Team / Repo | Skill | Status | Error |
|-------------|-------|--------|-------|
| `ASIAN_AM 225` | `skills/example-skill/skills.md` | broken | skill_id 'example-skill' is already claimed by repo 'cs-348-skills'. Repo 'asian_am-225-skills' is rejected. Rename this skill or coordinate with the 'cs-348-skills' team. |
| `CS-214` | `skills/example-skill/skills.md` | broken | skill_id 'example-skill' is already claimed by repo 'cs-348-skills'. Repo 'cs-214-skills' is rejected. Rename this skill or coordinate with the 'cs-348-skills' team. |
| `JOUR-201-1` | `skills/ask-for-example/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `JOUR-201-1` | `skills/depth-of-interviewing/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `JOUR-201-1` | `skills/example-skill/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `JOUR-201-1` | `skills/give-structural-hint/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `JOUR-201-1` | `skills/news-judgement/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `JOUR-201-1` | `skills/paragraph-purpose-check/skills.md` | stub | missing or empty (must be subset of cs/humanities); must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `POLISCI-210` | `skills/ai-explain/skills.md` | stub | missing — add a `## Tutor Stance` section with rules |
| `POLISCI-210` | `skills/counter-example/skills.md` | broken | skill_id 'counter-example' is already claimed by repo 'asian_am-225-skills'. Repo 'poli_sci-210-skills' is rejected. Rename this skill or coordinate with the 'asian_am-225-skills' team. |
| `POLISCI-210` | `skills/example-skill/skills.md` | broken | skill_id 'skill-name' is already claimed by repo 'jour-201-1-skills'. Repo 'poli_sci-210-skills' is rejected. Rename this skill or coordinate with the 'jour-201-1-skills' team. |
| `POLISCI-210` | `skills/extract-syllabus/skills.md` | stub | missing — add `## Usage` section |
| `POLISCI-210` | `skills/play-reviewer/skills.md` | stub | missing — add a `## Tutor Stance` section with rules |

## Issues by team

### ASIAN_AM 225

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `asian_am-225-skills` | `asian_am-225-skills/skills/claim_verification/skills.md` | **warn** | `example_exchange` | missing — strongly recommended |
| `asian_am-225-skills` | `asian_am-225-skills/skills/convert_request_into_safe_help_mode/skills.md` | **warn** | `skill_id` | length 35 > 18 chars — see Team-Guide §7 |
| `asian_am-225-skills` | `asian_am-225-skills/skills/example-skill/skills.md` | **ERROR** | `skill_id` | skill_id 'example-skill' is already claimed by repo 'cs-348-skills'. Repo 'asian_am-225-skills' is rejected. Rename this skill or coordinate with the 'cs-348-skills' team. |
| `asian_am-225-skills` | `asian_am-225-skills/skills/map_to_learning_goals/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `asian_am-225-skills` | `asian_am-225-skills/skills/reframe_with_analogy/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |

### CS-213

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `CS-213-skills` | `CS-213-skills/skills/cache_optimized_code/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |
| `CS-213-skills` | `CS-213-skills/skills/reframe_with_analogy/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |

### CS-214

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `cs-214-skills` | `cs-214-skills/skills/example-skill/skills.md` | **ERROR** | `skill_id` | skill_id 'example-skill' is already claimed by repo 'cs-348-skills'. Repo 'cs-214-skills' is rejected. Rename this skill or coordinate with the 'cs-348-skills' team. |

### CS-343

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `cs-343-skills` | `cs-343-skills/skills/ask_for_decomposition/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/connect_prior_knowledge/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/evaluate_readability_on_code/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/explain_function_responsibilities/skills.md` | **warn** | `skill_id` | length 33 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/explanation_nautilus_architecture/skills.md` | **warn** | `skill_id` | length 33 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/extract_requirements/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |
| `cs-343-skills` | `cs-343-skills/skills/narrow_the_bug_location/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |

### CS-348

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `cs-348-skills` | `cs-348-skills/skills/restate-the-problem/skills.md` | **warn** | `skill_id` | length 19 > 18 chars — see Team-Guide §7 |

### JOUR-201-1

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `jour-201-1-skills` | `jour-201-1-skills/skills/ask-for-example/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/ask-for-example/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/ask-for-example/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/depth-of-interviewing/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/depth-of-interviewing/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/depth-of-interviewing/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/depth-of-interviewing/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `jour-201-1-skills` | `jour-201-1-skills/skills/example-skill/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/example-skill/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/example-skill/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/give-structural-hint/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/give-structural-hint/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/give-structural-hint/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/give-structural-hint/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |
| `jour-201-1-skills` | `jour-201-1-skills/skills/news-judgement/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/news-judgement/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/news-judgement/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/paragraph-purpose-check/skills.md` | **ERROR** | `course_types` | missing or empty (must be subset of cs/humanities) |
| `jour-201-1-skills` | `jour-201-1-skills/skills/paragraph-purpose-check/skills.md` | **warn** | `learning_goal_tags` | missing — strongly recommended for orchestrator routing |
| `jour-201-1-skills` | `jour-201-1-skills/skills/paragraph-purpose-check/skills.md` | **ERROR** | `stance` | must be one of ['hint', 'meta', 'reframe', 'socratic'] |
| `jour-201-1-skills` | `jour-201-1-skills/skills/paragraph-purpose-check/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |

### POLISCI-210

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `poli_sci-210-skills` | `poli_sci-210-skills/skills/ai-explain/skills.md` | **ERROR** | `tutor_stance` | missing — add a `## Tutor Stance` section with rules |
| `poli_sci-210-skills` | `poli_sci-210-skills/skills/counter-example/skills.md` | **ERROR** | `skill_id` | skill_id 'counter-example' is already claimed by repo 'asian_am-225-skills'. Repo 'poli_sci-210-skills' is rejected. Rename this skill or coordinate with the 'asian_am-225-skills' team. |
| `poli_sci-210-skills` | `poli_sci-210-skills/skills/example-skill/skills.md` | **ERROR** | `skill_id` | skill_id 'skill-name' is already claimed by repo 'jour-201-1-skills'. Repo 'poli_sci-210-skills' is rejected. Rename this skill or coordinate with the 'jour-201-1-skills' team. |
| `poli_sci-210-skills` | `poli_sci-210-skills/skills/extract-syllabus/skills.md` | **ERROR** | `usage` | missing — add `## Usage` section |
| `poli_sci-210-skills` | `poli_sci-210-skills/skills/play-reviewer/skills.md` | **ERROR** | `tutor_stance` | missing — add a `## Tutor Stance` section with rules |

### cs338-skills

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `cs338-skills` | `cs338-skills/skills/ai-explanation-critique/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/analytical-question-formulation/skills.md` | **warn** | `skill_id` | length 31 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/answer-error-diagnosis/skills.md` | **warn** | `skill_id` | length 22 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/assembly-trace-reasoning/skills.md` | **warn** | `skill_id` | length 24 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/assumption-checking/skills.md` | **warn** | `skill_id` | length 19 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/calling-convention-reasoning/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/concept-distinction-reasoning/skills.md` | **warn** | `skill_id` | length 29 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/concurrency-failure-diagnosis/skills.md` | **warn** | `skill_id` | length 29 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/constraint-reasoning/skills.md` | **warn** | `skill_id` | length 20 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/counterevidence-engagement/skills.md` | **warn** | `skill_id` | length 26 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/cross-author-comparison/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/design-alternative-reasoning/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/endianness-byte-ordering/skills.md` | **warn** | `skill_id` | length 24 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/expectation_elicitation/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/follow-up-question-deepening/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/heuristic-admissibility-reasoning/skills.md` | **warn** | `skill_id` | length 33 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/historical-contextualization/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/historical-thesis-formulation/skills.md` | **warn** | `skill_id` | length 29 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/human-first-reasoning/skills.md` | **warn** | `example_exchange` | missing — strongly recommended |
| `cs338-skills` | `cs338-skills/skills/human-first-reasoning/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/hyperparameter-impact-reasoning/skills.md` | **warn** | `skill_id` | length 31 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/hypothesis-first-visualization/skills.md` | **warn** | `skill_id` | length 30 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/hypothesis-formulation/skills.md` | **warn** | `skill_id` | length 22 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/integer-overflow-reasoning/skills.md` | **warn** | `skill_id` | length 26 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/interview-preparation/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/iterative-improvement-reasoning/skills.md` | **warn** | `skill_id` | length 31 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/journalistic-lede-writing/skills.md` | **warn** | `skill_id` | length 25 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/local-vs-global-optimum-reasoning/skills.md` | **warn** | `skill_id` | length 33 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/meta-resource-awareness/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/method-selection-reasoning/skills.md` | **warn** | `skill_id` | length 26 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/multi-source-portrait-building/skills.md` | **warn** | `skill_id` | length 30 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/nut-graph-construction/skills.md` | **warn** | `skill_id` | length 22 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/observation-integration/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/parallel-text-comparison/skills.md` | **warn** | `skill_id` | length 24 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/pointer-address-reasoning/skills.md` | **warn** | `skill_id` | length 25 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/preemption-event-reasoning/skills.md` | **warn** | `skill_id` | length 26 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/preprocessing-impact-reasoning/skills.md` | **warn** | `skill_id` | length 30 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/prior-knowledge-elicitation/skills.md` | **warn** | `skill_id` | length 27 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/quote-selection-reasoning/skills.md` | **warn** | `skill_id` | length 25 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/research-relevance-reasoning/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/result-interpretation/skills.md` | **warn** | `skill_id` | length 21 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/scheduling-selection-reasoning/skills.md` | **warn** | `skill_id` | length 30 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/search-state-formulation/skills.md` | **warn** | `skill_id` | length 24 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/show-dont-tell-journalism/skills.md` | **warn** | `skill_id` | length 25 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/source-attribution-reasoning/skills.md` | **warn** | `skill_id` | length 28 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/story-angle-development/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/struct-layout-reasoning/skills.md` | **warn** | `skill_id` | length 23 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/study-limitation-identification/skills.md` | **warn** | `skill_id` | length 31 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/systematic-coverage-prompting/skills.md` | **warn** | `skill_id` | length 29 > 18 chars — see Team-Guide §7 |
| `cs338-skills` | `cs338-skills/skills/trend-analysis-reasoning/skills.md` | **warn** | `skill_id` | length 24 > 18 chars — see Team-Guide §7 |

### phil-219-skills

| Repo | Skill | Severity | Field | Message |
|------|-------|----------|-------|---------|
| `phil-219-skills` | `phil-219-skills/skills/prompt-reflection/skills.md` | **warn** | `example_exchange` | missing — strongly recommended |
