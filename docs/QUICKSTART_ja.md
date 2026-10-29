# Document Studio クイックスタート

**既存の資料から文書の作法を分析し、承認済みルールを組み込んだ専用プラグインへ。**

[English README](../README.md) · [ワークスペース管理者向けガイド](WORKSPACE_ADMIN_GUIDE.md) · [5シーンのデモ構成](DEMO_FLOW.md) · [한국어](QUICKSTART_ko.md)

## Document Studio とは

企業の企画書や報告書には、固有の文章表現・色・構成・承認基準があります。本ツールキットは、**利用許可のある PDF / PowerPoint** から根拠となる特徴を抽出し、人が確認・承認した **Company Pack** を文書作成ワークフローで再利用するためのものです。

想定する一連の流れは **参考資料 → 分析 → 人によるレビュー・承認 → 専用プラグイン ZIP → 新規資料の作成**。現段階では手作業を伴い、完全なワンクリック自動化ではありません。

## 架空企業のデモを試す

```bash
git clone https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/export_company_plugin.py \
  --company-pack company-packs/demo-retail \
  --language-skills ko,ja \
  --output ./dist/demo-retail-documents.zip
```

出力されるのは、**独自に作成した架空企業の承認済みプロファイル**を含むプラグイン ZIP です。ChatGPT への登録や組織内への公開は別の操作です。[管理者向け手順](WORKSPACE_ADMIN_GUIDE.md)をご覧ください。

## 現行バージョンの制約

- **`v0.1.0-alpha.5` の実験版**です。社内限定・非公開の原本に由来する Company Pack は、現在の公開用エクスポーターでは**出力できません**。社内専用の配布フローは今後の開発課題です。
- 出典、フォント・画像の利用権、提案されたデザイン規則を担当者が確認・承認する必要があります。
- HTML / PPTX の最終制作とブラウザーによる視覚検証は別工程です。
- Business ワークスペースへの展開は管理者の権限とプラットフォーム側の提供機能によります。

まずは架空企業のデモで動作を確認してください。英語の[技術ドキュメントと MIT ライセンス](../README.md)も公開しています。
