# Chat selection replaces the legacy intake screen

First-use help and requested selection now follow [staff onboarding](staff-onboarding.md). Use the existing chat question control if available, or a short numbered list. Apply actual chat answers directly and reuse known conditions. No separate screen, summary confirmation or JSON transfer is part of startup.

The old assets/onboarding files and render_intake.py remain compatibility material for existing files and tests. Do not read, render, open or repair them for routine help or production. The onboarding renderer connection is disabled in the plugin manifests.

Existing received JSON remains compatible with intake.py import; JSON is never required from staff. Preserve explicit/reused/delegated provenance and pending required fields. Imported blank/skipped choices and old assumptions remain unresolved; validate actual payloads before production. Draft widget state is not a chat answer, factual evidence or authorization.
