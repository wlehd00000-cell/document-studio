# Coherent business pictograms

## Available starter vectors

`assets/icons/lucide/` contains `leaf`, `factory`, `truck`, `store`, `users`, `package`.
`assets/icons/phosphor-duotone/` contains `leaf`, `factory`, `truck`, `storefront`, `users-three`, `package`.

These are original upstream SVGs for reuse, not AI-generated DEMO artwork. Their metadata and upstream hashes are in `icon-sources.json`. Preserve the original license in each family folder when copying/adapting vectors into a project, and record the source/family in the registry. Lucide's bundled notice includes ISC and applicable Feather MIT attribution; Phosphor's notice is MIT.

Select the library whose meaning and geometry suit the design. The starter set is deliberately small; it does not cover all topics. Use a local established family or retrieve an appropriate source with its usage terms when needed. Do not pass an unrelated standard icon off as a bespoke explanation of a complex concept.

## Production

- Keep one chosen grid/viewBox, stroke/fill weight, cap, corner and perspective convention for the set. The supplied Lucide grid and Phosphor grid differ; use each family consistently rather than numerically merging them.
- Match apparent size and weight at the intended placement, allowing optical adjustments for sparse and dense shapes. Use the library's weight consistently; do not make a single icon bolder merely by enlarging its stroke.
- Color is a role, not decoration. For duotone, retain a consistent relation between the main shape and secondary fill. Do not change color meaning across members.
- Extend a native vector family with compatible geometry when the subject can be expressed accurately. For an original illustrative bitmap pictogram requested by the designer, use the image production route and the same anchor/specification.
- Return separate assets for independently placed symbols. A contact sheet or sprite alone does not satisfy six requested independent icons. A bitmap placed in an SVG wrapper remains a bitmap.
- Keep background/alpha and crop intentional. Deliver color variants only when requested or needed for the real background; do not generate all possible colors and sizes.

Verify semantics as a set: can users distinguish the intended roles without relying entirely on labels? View at final small size; remove details that disappear or cause confusion. Record missing distinctions and send them back to design rather than inventing unsupported meanings.

SVGs remain editable vectors in HTML and vector-capable consumers. Actual PowerPoint editability depends on its export route; do not promise native PowerPoint shapes merely because the source is SVG.
