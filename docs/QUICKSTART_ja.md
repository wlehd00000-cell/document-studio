# 日本語で、最初の資料を1件作る

[日本語トップ](../README.md) · [文書ガイド一覧](README.md) · [한국어](QUICKSTART_ko.md) · [English](TRY_FIRST.md)

まずは実在企業の資料を使わず、一般的な文書制作スキルで架空の1件を作ります。会社の資料分析や、社員全員への配布から始める必要はありません。見た目を先に確認したい場合は、[インストール不要の作例](SHOWCASE.md)を開いてください。

## 1. 使う環境を選ぶ

| 環境 | 必要なこと | 導入後の確認 |
|---|---|---|
| ローカルCodex | Node.js 22.20以降とGit。下のスキル配置コマンドを使う | 新しいセッションで `report-html-pptx` の認識を確認 |
| ChatGPT | Plugin Creatorの作成機能と、対象アカウントの保存権限 | 保存したプラグインのURL/IDとスコープを確認し、新しいチャットで選択 |
| 会社別パッケージの評価 | ソース全体、Python環境、Packの確認・承認と導入権限 | [管理者ガイド](MANAGER_GUIDE_ja.md)の架空Packで別途評価 |

ChatGPTに必要な作成機能がない場合、このZIP登録経路は利用できません。ファイルの保存や再ダウンロードで解決したことにはなりません。

## 2. スキルまたはプラグインを導入する

### ローカルCodex

自分の作業フォルダーで実行します。Document Studioのソースを置いたフォルダーで実行する必要はありません。

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

この経路は10個のスキルを配置します。ChatGPTへの登録や、会社別ZIPの生成ツールの導入は行いません。新しいCodexセッションで `report-html-pptx` が使えることを確認してください。[配置先とPythonを使う別経路 — English](TRY_FIRST.md#local-codex)

### ChatGPT

[Starter ZIP（alpha.6）](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip)とチェックサムを[配布ページ](https://github.com/wlehd00000-cell/document-studio/releases/tag/v0.1.0-alpha.6)で確認します。内容を確認してから、権限のある対象アカウントで[登録手順 — English](DOWNLOAD_AND_INSTALL.md#in-three-steps)に従います。

登録時には、添付ZIPから対象アカウントで非公開のDocument Studioプラグインを作成し、実際に保存したURL/IDと適用範囲を返すよう依頼します。アクティブなワークスペースがある場合はそのワークスペース、ない場合は個人アカウントへの保存となるため、保存先を確認してください。返されたプラグインを新しいチャットで選択します。ZIP生成・保存だけでは登録完了ではありません。[ZIPの違い](FAQ_ja.md#どのzipを選べばよいですか)

## 3. 最初の依頼を送る

導入済みのプラグイン、または認識済みの `report-html-pptx` に依頼します。

> 架空の小売企業の運営責任者が検討する、4週間の試行導入の企画提案書を、日本語のHTMLで作成してください。1店舗・3品目・予算上限240万ウォン（KRW）を仮定として維持してください。
>
> 費用内訳、担当者、週別の計画、成功基準と中止条件を含めてください。一般的な制作工程を使い、実在企業のブランドや非公開資料は使わないでください。
>
> 原稿と実際のHTML表示を確認し、実施した確認と未確認の範囲を示してください。PPTXが必要な場合は、HTML確認後に編集可能なPPTXへ変換し、実際の出力・表示・編集性を確認してください。

PPTXが不要ならHTMLまでで完了できます。変換環境・依存関係が使えない場合は、その範囲を未確認として報告させます。詳しくは[PowerPoint出力](PPTX_OUTPUT_ja.md)を参照してください。

## 4. 作成された結果を確認する

- 原稿：目的、読み手、数値・単位・前提条件が維持され、仮定と確認済みの事実が分かれているか。
- HTML：実際に開き、文字・書体・図表・画像の収まりを確認したか。
- PPTX：必要な場合に変換し、実際の表示と編集性を確認したか。未実施の確認を完了扱いにしていないか。

作例と同じ見た目や、モデル間の同一品質を保証するものではありません。スキルなしの依頼と比較するなら、同じモデル・同じ条件で実施し、修正が必要だった箇所を記録してください。

## 会社の基準を使いたくなったら

[管理者の評価ガイド](MANAGER_GUIDE_ja.md)で、承認Company Pack、基本スキル8個、選択言語モジュールと、導入後の新しい依頼の確認へ進みます。現在の公開エクスポーターは、非公開資料に由来するPackの内部配布を提供していません。

[よくある質問](FAQ_ja.md) · [初回利用の結果を共有](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md) · [技術ガイド — English](TECHNICAL_GUIDE.md)
