# Raster scenes, illustrations and edits

Use current runtime tool documentation and the available official imagegen skill when applicable. The normal route is the built-in image-generation tool; it does not require a new API key or provider installation. A different provider/CLI requires the user's explicit choice or consent and its actual supported interface.

## References and scope

Inspect local images before using them, and label their roles: style, composition, subject, supporting insert or edit target. A provided style reference does not mean edit the source image. Pass only actual available files/images; use a concise verbal style description when no file is available and record that limitation.

Keep a stable anchor and a short shared specification for the set. Include the accepted first output as an anchor only when it improves the basis and is allowed by the current interaction mode. Do not assume unsupported seed, `style_id`, LoRA, numeric fidelity or native batch controls. Read the active tool schema; named conceptual fields in our contract are not tool arguments.

For local edit targets, use the runtime's inspection/reference mechanism. Ask the tool for real alpha when a transparent asset is needed and preserve alpha in the saved output. Use targeted edits for corrections; do not paint over an image's text with ad hoc raster overlays. If unwanted text persists, regenerate without it or fix it through the supported image edit route.

## Page art direction before the prompt

Reuse the designer's purpose profile/page family and role of the image. Full-bleed photography/concept, product hero, architectural/location frame, strong crop or image plus quiet title zone are valid. Preserve final aspect, image occupancy, focal subject, allowed crop, camera/view, caption relation and editable text regions. The surrounding document owns title/labels/figures. A visually photographic generation is still a generated concept, never evidence of an actual DEMO facility/event.

## Prompt record

For a DEMO-C-007-like connected scene, translate [DEMO image layout](../../report-html-pptx/references/demo-esg-image-layout.md) into the actual brief: the current project's subjects/actions and relationships, intended frame, primary/secondary zones, consistent projection and controlled detail, focal hierarchy, and only the needed quiet label regions. Describe an integrated space across the frame. Keep the report's small Pretendard text and meaningful connectors as document overlays. Do not ask imagegen to produce an entire business report page with tiny baked-in Korean/Japanese text. A standard isolated vector icon family is not a substitute for a requested large explanatory scene.

Persist the common specification and each final per-asset prompt in the existing project location, such as `qa/visual-assets/prompts/<asset-id>.md`. Do not duplicate the full report or provenance inventory in every prompt. Preserve the designer's essential subjects, relationship direction, factual/proposal status, quiet regions and crop intent. Leave nonessential scenic detail open to creative judgment.

Default to no embedded text for business documents. Important Korean/Japanese labels, conditions, numbers and connectors belong to editable document overlays. Exact necessary printed markings can remain when explicitly required and inspected. Never regenerate a supplied official logo, package or character merely for visual convenience.

## Execution and recovery

For distinct bitmaps, use one supported generation request per asset or variant. Reuse the common style reference; save selected results before generating or correcting the next dependent item. Use parallel calls only if the actual tool/runtime permits them, and do not create extra agents simply to render images.

Copy the selected workspace-bound output into `html/assets/` or the explicit destination, with a stable asset ID and versioned filename. Check its actual size and format using available metadata tools. Do not promise requested pixel dimensions solely from a prompt, or describe upsampling as new native detail.

Review meaning and requested invariants before stylistic polish. For consistency problems, isolate the cause: projection, material, color role, scale, light or crop. Make a focused correction while repeating the anchor and invariants. Do not regenerate already satisfactory set members. If an environmental failure persists, report the specific limitation and preserve good outputs; switch to a different provider or install nothing without the required consent.

The generator's selected save path, tool output and actual files are evidence of file production. They are not evidence of visual inspection or user acceptance. Return an honest `partial`/`blocked` asset when essential subjects, alpha or preservation cannot be achieved. A generated factory/city remains a concept scene unless sourced as an actual original photograph.
