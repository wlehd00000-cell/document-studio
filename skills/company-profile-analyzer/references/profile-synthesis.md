# Company Pack synthesis and approval

The builder writes a new immutable directory and refuses overwrite. It creates `draft` metadata, measured layout candidates, proposed colors and writing references, a redacted source inventory, an unverified font policy and a review record.

Review sequence:

1. Present findings and linked source IDs; distinguish extracted measurement from interpretation.
2. Resolve family-specific conflicts, replace inferred colors/font families with authorized decisions, review visual examples, and check glossary/rights.
3. Record a named reviewer and rationale using `build_company_pack.py review PACK --reviewer NAME --note NOTE`.
4. Only after explicit authorization, record `build_company_pack.py approve PACK --reviewer NAME --note NOTE`.

Never update an existing approved pack in place for a different version; build into a new directory and keep project snapshot SHA-256 values for past documents. A new version invalidates affected quality reviews, not accepted source claims by itself.
