# Design DNA: measurement and interpretation

## Measurements

Use `document_extract.py` and `design_analyzer.py` for slide/page size, shape geometry, text boxes, colors, font-name strings and font sizes. Record the extraction mechanism (`observed_xml`, `observed_pdf_extract`) and source ID. PDF embedded font names can be subset or corrupted. A frequent color is not automatically the official primary brand color.

## Visual inspection

Render representative pages if tools are available. Inspect actual page screenshots at final size: focal point, reading order, headline/image balance, whitespace, density, table treatment, repetition and different document families. Record page number, finding and evidence strength in a review note. Do not infer these from shape positions alone; leave `visual_interpretation.status=UNVERIFIED` when no render was seen.

## Draft tokens

The analyzer proposes colors/fonts/layout candidates only. Confirm them with an authorized person before marking the pack approved. Split proposals from executive reports or manuals when their composition differs.
