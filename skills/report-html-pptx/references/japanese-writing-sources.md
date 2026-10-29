# Japanese writing references and adoption notes

Reviewed 2026-09-28. Maintenance note; document drafting loads japanese-writing.md only. The local module supports report, proposal, execution-plan and presentation files, using synthesized guidance and original examples. It does not install the source repositories or their broader workflows.

| Primary source | Elements used | Boundary |
|---|---|---|
| [coji/natural-japanese](https://github.com/coji/natural-japanese), [skill](https://github.com/coji/natural-japanese/blob/main/skills/natural-japanese/SKILL.md), [readability](https://github.com/coji/natural-japanese/blob/main/skills/natural-japanese/references/readability-principles.md) | Reader-aware organization and revising unclear sentence relationships before shortening | No import of full-mode subagents, mandatory lint steps, timing estimates or universal heading conventions |
| [textlint technical-writing preset](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | Review repeated constructions, double negatives and inappropriate register mixing | Technical lint thresholds are not general business-writing quality requirements |
| [textlint JTF-style preset](https://github.com/textlint-ja/textlint-rule-preset-JTF-style) | Consistent notation and distinguishing body/headline roles | It implements a translation style guide; some rules are dictionary-based, optional or unimplemented. House style, official strings and genre remain authoritative |

No external code or bulk text was copied. No new dependency, automatic fixer or background agent was installed. These references inform drafting and review, not claims of measured speed or literary quality. Revisit upstream documentation when changing an actual lint configuration.

2026-10-01: The Japanese prose owner moved to the packaged business-japanese-translation module. Current popularity/source/adoption notes are in [translation sources](translation-sources.md). Routine production loads the selected target language only; source maintenance notes are not a required drafting stage.
