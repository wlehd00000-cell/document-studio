# Document Studio ドキュメント

[日本語トップ](../README.ja.md) · [한국어](../README.ko.md) · [English](../README.en.md) · [紹介サイト](https://document-studio-public-experiment.wlehd00000.chatgpt.site/)

目的に合う入口から進んでください。日本語を中心に、詳細な実装・導入資料には英語の文書もあります。

## まず見る・試す

| 知りたいこと | 読む資料 | 言語 |
|---|---|---|
| PNG・PDF・編集用HTMLがそろった新しい文書4点 | [文書コレクション](../examples/document-collection/README.md) | English / 作例は韓国語・日本語 |
| 文書の見た目、固定ルール、目的別構成、創造性 | [公開作例の見方](SHOWCASE.md) | 日本語 |
| 自分で1件作るための環境選択と依頼文 | [日本語の初回利用](QUICKSTART_ja.md) / [한국어 첫 사용](QUICKSTART_ko.md) / [First use](TRY_FIRST.md) | 日本語 / 한국어 / English |
| 管理者が何を用意し、何を評価するか | [会社別プラグインの評価](MANAGER_GUIDE_ja.md) | 日本語 |
| HTMLから編集可能なPPTXになる構造 | [PowerPoint出力と業務利用](PPTX_OUTPUT_ja.md) | 日本語 |
| ZIPの違い、Company Pack、現在の制約 | [よくある質問](FAQ_ja.md) | 日本語 |

紹介する場合は、[3言語の紹介文と共有用リンク](LAUNCH_KIT.md)を使えます。

## 導入・実装を確認する

| 目的 | 資料 | 言語 |
|---|---|---|
| 環境、権限、ワークスペース導入の確認 | [管理者向け詳細](WORKSPACE_ADMIN_GUIDE.md) | English |
| 配布ZIPの選択、チェックサム、登録 | [ダウンロードと導入](DOWNLOAD_AND_INSTALL.md) | English |
| 参考資料の分析から確認・承認・パッケージ生成 | [5場面の実行ガイド](DEMO_FLOW.md) | English |
| CLI、スキル一覧、Company Pack、Layout Grammar | [技術ガイド](TECHNICAL_GUIDE.md) | English |
| 公開HTML例の原稿・規則・測定範囲 | [showcaseのソース案内](../showcase/README.md) | 日本語 |
| 公開資料の分析評価と、その方法・限界 | [独立した評価記録](../evaluation/public-company-fidelity-2026-10-29.md) | English |

## ソースを読む場所

| 場所 | 入っているもの |
|---|---|
| [`skills/`](../skills) | 基本スキル8個、選択言語2個の指示・参照・スクリプト |
| [`company-packs/`](../company-packs) | 独立して作成した架空の小売・製造業Pack |
| [`scripts/`](../scripts) | 導入、検証、分析、配布用ZIP生成などのツール |
| [`showcase/`](../showcase) | 公開サイトの静的HTML・CSS・JavaScript |
| [`tests/`](../tests) | 機能・拒否条件などの回帰テスト |

現在はalpha.6です。公開作例の表示、配布用パッケージの生成、対象環境での導入、新しい文書とPPTXの品質確認は別工程です。非公開資料からの内部配布は公開エクスポーターでは未対応です。

[初回利用の結果を共有](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md) · [不具合・改善案](https://github.com/wlehd00000-cell/document-studio/issues/new/choose) · [貢献方法](../CONTRIBUTING.md) · [変更履歴](../CHANGELOG.md)
