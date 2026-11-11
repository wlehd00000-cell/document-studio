# Document Studio

[日本語](README.md) · [한국어](README.ko.md) · [English](README.en.md)

**報告書・提案書のつくり方を、毎回の長いプロンプトから再利用できるCodexスキルへ。**

日本語・韓国語の業務文書を繰り返し作る方へ。構成・執筆・HTMLデザイン・確認の手順をまとめ、必要に応じて編集可能なPowerPointへつなげます。

会社で評価する場合は、人が承認したルールを **Company Pack** としてまとめ、文書制作スキルとともにパッケージ化できます。

[紹介サイトを開く](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [管理者の評価手順](docs/MANAGER_GUIDE_ja.md) · [文書ガイド一覧](docs/README.md)

実験段階の **alpha.6** です。現在の公開エクスポーターは架空Pack・配布権限を確認した公開資料が対象で、非公開の社内資料からの内部配布は未対応です。

## まずは、会社資料なしで1件試す

[作例を比較する（インストール不要）](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare) · [最初の依頼文](docs/TRY_FIRST.md#日本語) · [English quick start](docs/TRY_FIRST.md#fast-agent-skill-install)

**ローカルCodexをお使いなら：** Node.js 22.20以降とGitを用意し、スキルの内容を確認したうえで、自分の作業用プロジェクトフォルダから実行します。

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

新しいCodexセッションで `report-html-pptx` が認識されることを確認し、[架空の2ページ提案書の依頼文](docs/TRY_FIRST.md#日本語)を送ってください。会社の資料やCompany Packの準備は不要です。この方法は10個のエージェントスキルをコピーします。AIモデル・変換環境・ChatGPTプラグインの登録は含みません。[導入の範囲と別の方法](docs/TRY_FIRST.md)

役に立ちそうなら、ページ上部の **Star** で保存できます。使えたこと・止まったところは[初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)へ。

## まず、知りたいことを選ぶ

| 目的 | 次に見るもの |
|---|---|
| どんな資料が作れるか見たい | [インストール不要の作例](docs/SHOWCASE.md) |
| チームで使えるか評価したい | [管理者ガイド：準備・現在の制約・架空Packの評価](docs/MANAGER_GUIDE_ja.md) |
| 自分で資料を1件作りたい | [日本語の初回利用：環境選択から最初の依頼まで](docs/QUICKSTART_ja.md) |
| 実装やコマンドを確認したい | [技術ガイド — English](docs/TECHNICAL_GUIDE.md) |

## 管理者が基準を整え、社員が資料を依頼する

会社の用語・文体・デザイン・出典などを、確認した根拠とともに **Company Pack** で管理します。必要な会社基準を維持し、その範囲で構成や表現を目的に合わせる設計です。指定様式がある資料では、その配置規則も使います。

| 担当 | 進め方 |
|---|---|
| 管理者 | 権限のある参考資料を選ぶ → 提案された規則を確認・承認 → Packとスキルをパッケージ化 → 対応環境への導入と動作確認 |
| 社員の依頼後 | 目的・読み手・言語・形式と使用Packを確認 → 構成と必要な調査 → 執筆と言語確認 → HTMLデザインと確認 → 必要なPPTX出力と最終確認 |

基本スキル8個に、選択した日本語・韓国語の校閲モジュールを組み合わせます。導入先のAIが役割別の指示とスクリプトを適用します。社員が内部スキル名を順に指定する必要はありません。[内部フローの図解](https://document-studio-public-experiment.wlehd00000.chatgpt.site/#plugin-flow) · [実際のスキルと条件](docs/MANAGER_GUIDE_ja.md#社員の1件の依頼はどう進むか)

## 作例で確かめる、3つの違い

| 見るポイント | 作例 |
|---|---|
| 決めたデザイン規則を維持 | [同じ2ページを、白黒A4・整列A4・横型提案で比較](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare) |
| 読み手に合わせた情報の順序 | [企画提案書4ページ・決裁サマリー・業務ガイド](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?view=all&size=large) |
| 表現を大胆に変える | [同じ案件の要点を再編集した、創造性の1ページ](https://document-studio-public-experiment.wlehd00000.chatgpt.site/creative) |

[![同じ内容を白黒A4と整列A4の規則で表示した日本語の作例](docs/assets/showcase/comparison-ja.jpg)](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare)

日本語が標準で、韓国語へ切り替えられます。作例は架空の案件で、予算は240万ウォン（KRW）。静的HTMLを表示し、サイト内ではAIを実行しません。測定はこのHTML例の表示に限り、新規生成・企業成果・印刷・PPTXの検証結果ではありません。[原稿・規則・確認条件](showcase/README.md)

論点から検討したい場合は、任意の[深掘りコンサルティング企画](https://document-studio-public-experiment.wlehd00000.chatgpt.site/consulting)も紹介しています。創造性設定とは別で、明示的に選んだ場合に利用する進め方です。

## HTMLから、編集できるPowerPointへ

HTMLで原稿とレイアウトを確認した後、ブラウザーの位置・寸法・文字を測り、対応する本文・数値・図形をPowerPointの編集可能な要素として組み直します。会議前の数値修正、担当者名や文章の更新を続けるための工程です。

写真や複雑な装飾は画像として保持する場合があります。出力後の書体・表示・編集性の確認が必要で、任意のHTMLの完全一致は保証しません。公開作例のPPTX変換は未検証です。[業務での使い方と変換構造](docs/PPTX_OUTPUT_ja.md)

## 最初は、小さな1件から

個人で使う場合は[初回利用ガイド](docs/QUICKSTART_ja.md)から、会社別パッケージを評価する場合は[管理者ガイド](docs/MANAGER_GUIDE_ja.md)の架空Packから始められます。

| 確認すること | 現在の状態 |
|---|---|
| 承認した架空Pack・配布権限のある公開資料のPackをZIPに出力 | 実装済みの評価経路 |
| インストール、Packの選択、新しい依頼、HTML/PPTX品質 | 導入先で別途確認 |
| 非公開資料の内部配布、ワンクリック社内導入 | 未対応 |

[HTML閲覧ZIP・プラグインZIP・ソースの違い](docs/FAQ_ja.md#どのzipを選べばよいですか)も確認してください。ZIPの保存だけではプラグインは導入されません。

企業でAIをどう使うかを、文書業務から検証する個人のプロジェクトです。関心があればStarで保存し、試した結果や必要だった修正を[初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)で教えてください。日本語・한국어・Englishで投稿できます。

[よくある質問](docs/FAQ_ja.md) · [貢献する](CONTRIBUTING.md) · [変更履歴](CHANGELOG.md) · [セキュリティ](SECURITY.md)

独自の成果物は[MIT](LICENSE)、同梱書体などは[第三者の権利表示](THIRD_PARTY_NOTICES.md)に従います。勤務先や商標権者による導入・推奨・保証を示しません。
