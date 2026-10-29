# Translation and business-writing research

Maintenance reference only. Do not load this research bibliography for ordinary translation. The runnable instructions and examples are original adaptations for Document Studio business-document files; upstream code and complete skill texts are not bundled or executed.

## Primary sources, checked 2026-10-01

GitHub repository API snapshots record repository-wide stars, not stars for an individual skill. Popularity helps select references; it does not establish translation accuracy. Counts can change. Exact source URLs, licenses, bytes and SHA-256 snapshots are in [translation-source-records.json](translation-source-records.json).

| Repository / source | Repository stars | Adopted for business documents |
|---|---:|---|
| [blader/humanizer](https://github.com/blader/humanizer/blob/main/SKILL.md) | 53,130 | Repair repetitive structure and empty abstraction; preserve information and the appropriate voice. |
| [JimLiu/baoyu-skills: baoyu-translate](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-translate/SKILL.md) | 26,244 | Target reader, terminology and source context; compare and improve translation; keep context across meaningful sections. |
| [NomaDamas/k-skill: korean-humanizer](https://github.com/NomaDamas/k-skill/blob/main/korean-humanizer/instruction.md) | 7,728 | Korean word order and sentence flow, conservative editing, concrete actions and register-sensitive revision. |
| [andrewyng/translation-agent](https://github.com/andrewyng/translation-agent/blob/main/README.md) | 5,819 | Draft, source comparison and focused improvement. This is a research implementation, not a packaged agent skill or a quality guarantee. |
| [coji/natural-japanese](https://github.com/coji/natural-japanese/blob/main/skills/natural-japanese/SKILL.md) | 1,813 | Reader-aware Japanese structure, natural subjects/modifiers, factual source preservation and genre-sensitive wording. |
| [DaleSeo/korean-skills](https://github.com/DaleSeo/korean-skills/blob/main/skills/humanizer/SKILL.md) | 220 | Supplemental Korean calques, noun-heavy sentences and repeated passive constructions. |
| [matsutouya/humanizer-ja](https://github.com/matsutouya/humanizer-ja/blob/main/SKILL.md) | 5 | Supplemental Japanese genre distinctions and subject clarity. Included for relevance, not popularity. |

## Deliberate adaptations and exclusions

- Business reports retain evidence, conditions and explanatory prose. Informal first-person reactions, emotional voice, unsupported opinions and promises are not added for naturalness.
- Source comparison protects actors, negation, scope, amounts, tax treatment, deadlines and approval status. Terminology follows user-approved usage and verified official names rather than random synonyms.
- Integrated review is the default; consequential passages receive focused additional review. Do not require multiple agents, another model/API, fixed chunk lengths, every draft/critique file, an upsell to a slower mode or tool installation.
- Do not use AI detector scores, change percentages, mechanical banned-word counts, intentional errors or shuffled endings as quality standards. Correct spelling, corporate genre and source fidelity govern revisions.
- The Korean and Japanese skills retain separate register/example references. [The canonical translation quality layer](../system/translation-quality.md) owns their shared source/status/number preservation, terminology and comparison. They inherit the existing brief and permit read-only source preflight before production decisions; a scoped translation does not restart intake.

MIT licenses were recorded from each repository's API metadata. No upstream source code or substantial verbatim skill text has been copied into this package. Existing bundled resources retain their own notices.
