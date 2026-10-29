# Korean / Japanese font setup

The public repository intentionally omits binary font packages. Browser/system fallback may use Noto Sans KR, Noto Sans JP or another locally installed CJK font. For pixel-accurate HTML-to-PowerPoint work, download and install appropriately licensed fonts independently, place their WOFF2 assets under `assets/brand/` with the optional `_external_` filenames referenced in `system/design-tokens.json`, and rerun actual font/overflow/export checks. Do not claim embedded font fidelity until the quality contract passes.
