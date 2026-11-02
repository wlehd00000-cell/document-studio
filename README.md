# Document Studio

**AIが変わっても、会社の文書基準を次の仕事へ。**

企業でのAI活用を、文書業務から検証するオープンソースの実験です。人が確認した用語・文体・検討基準を、読み手と目的の異なる資料にも引き継ぐ方法を探っています。

[**日本語デモを開く**](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [**文書を大きく・全ページで見る**](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?doc=proposal&view=all&size=large) · [**導入ガイド**](docs/QUICKSTART_ja.md)

[한국어](README.ko.md) · [English / technical documentation](README.en.md)

[![日本語の企画提案書。架空のリフィル売場の試行導入について、範囲・予算・検証条件を示す画面](docs/assets/showcase/proposal-ja.jpg)](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?doc=proposal&view=all&size=large)

## まず、3つの文書を比較

同じ案件を、承認を求める資料、実行計画、現場で参照するガイドとして構成しました。インストールやログインは不要です。

| 文書 | 読み手が確認すること | 閲覧 |
|---|---|---|
| 企画提案書・4ページ | 範囲、仮説、予算、実行計画、終了後の判断 | [全ページを表示](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?doc=proposal&view=all&size=large) |
| 決裁サマリー・1ページ | 承認する事項、先行条件、承認に含めない範囲 | [大きく表示](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?doc=approval&view=all&size=large) |
| 業務ガイド・1ページ | 担当者、手順、例外発生時の対応、引継ぎ | [大きく表示](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?doc=guide&view=all&size=large) |

文書専用ビューは大きめの本文で全ページを表示します。1ページ表示、文字サイズ、共通基準の表示を切り替えられます。文書・ページ・表示方法・文字サイズをURLで共有できます。

会社、取引目標、費用は説明用の仮定です。予算は**240万ウォン（KRW）**で、円換算していません。画像は生成コンセプトであり、実際の店舗・設置実績ではありません。これは独立して制作した静的HTMLの例で、このページからAIを実行したり、Company Packの自動分析を再現したりするものではありません。

[HTML・JavaScript・確認条件](showcase/README.md) · [日本語・韓国語HTMLを保存](https://document-studio-public-experiment.wlehd00000.chatgpt.site/downloads/document-studio-demo.zip)

## この実験で考えていること

AIの性能が上がっても、組織で使うには、用語や文体、出典、確認責任をそろえる必要があります。一方で、構成や表現まで固定すると、新しい資料の目的に合わない場合があります。

Document Studioでは、会社が維持する基準を人が確認し、その範囲で資料の構成を変えられるようにする方法を試しています。モデルの性能比較にも関心を持ちながら、その性能を実際の仕事でどう使うかを継続して検証します。組織全体の生産性改善を実証した製品ではありません。

## 小さな仕事を1件試す

### Codex

Node.js 22.20以降とGitが必要です。自分の作業フォルダーで実行してください。

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

この方法はスキルを配置します。Codexの新しいセッションで `report-html-pptx` が認識されるか確認してください。会社別パッケージの書き出しツールは、別途ソース全体が必要です。

### ChatGPT

[Starter ZIP（alpha.6）](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip)と、[日本語の導入ガイド](docs/QUICKSTART_ja.md)を参照してください。Plugin Creatorの作成機能と保存権限のあるアカウントが必要です。ZIPの保存だけではプラグインの導入は完了しません。

### 最初の依頼例

> 架空の小売企業の運営責任者が検討する、4週間の試行導入の企画提案書を、日本語のHTMLで作成してください。<br>
> 1店舗・3品目・予算上限240万ウォン（KRW）という仮定を維持してください。<br>
> 費用内訳、担当者、週別の計画、成功基準と中止条件を含めてください。<br>
> 仮定と実際に確認した事実を区別し、実施した確認と未確認の範囲を示してください。

文書の見た目に加え、数値、担当者、条件、実施した確認の範囲を見てください。表示中のデモと同じ出力になる保証はありません。

## 仕組みと現在の範囲

基本の流れは、**利用権限のある参考資料 → 特徴と根拠の抽出 → 人による確認・承認 → Company Pack → 新しい資料の作成**です。8つの基本スキルと、日本語・韓国語の2つの任意言語スキルを収録しています。

| 項目 | 現在の状態 |
|---|---|
| PDF・PPTXからの文体・デザイン分析、ルールの確認・承認 | 実装済みの実験機能。人による解釈と確認が必要 |
| 架空・公開配布の権限を確認したCompany Packの書き出し | 実装済み。登録・導入は別工程 |
| 非公開の社内資料を基にしたパックの内部配布 | 公開エクスポーターでは未対応・ブロック対象 |
| ワークスペースへの自動配布 | 未対応。権限のある管理者による導入が必要 |
| HTML・編集可能なPPTXの最終品質 | 執筆・表示・変換・目視確認をそれぞれ実施する必要あり |

実験段階のalpha版です。モデル間の同一品質、自動的なブランド再現、企業全体の生産性改善は保証していません。[技術説明とCLI](README.en.md) · [管理者向けの現在の制約](docs/WORKSPACE_ADMIN_GUIDE.md) · [変更履歴](CHANGELOG.md)

## 使った結果を共有

この方向に関心があれば、**[GitHubのStarで保存](https://github.com/wlehd00000-cell/document-studio)**してください。初回利用で作れた資料、修正が必要だった箇所、繰り返し伝えていた基準などを、[初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)で共有いただけると、次の検証につながります。

機密資料を含まない、公開可能な例を使用してください。[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

## ライセンス

独自の成果物は[MIT](LICENSE)です。公開文書ビューに同梱するPretendard / Pretendard JPは、それぞれのOFLライセンス表示に従います。[第三者の権利表示](THIRD_PARTY_NOTICES.md)を参照してください。個人のオープンソースプロジェクトであり、勤務先や商標権者による導入・推奨・保証を示しません。
