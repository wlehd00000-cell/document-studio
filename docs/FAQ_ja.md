# よくある質問

[日本語トップ](../README.ja.md) · [文書ガイド一覧](README.md) · [紹介サイト](https://document-studio-public-experiment.wlehd00000.chatgpt.site/)

## Document Studioは何をするものですか

人が承認した会社ルールをCompany Packにまとめ、文書制作のスキルと一緒に会社別プラグインのパッケージを作るオープンソース実験です。会社別の準備をせず、一般的な文書制作スキルから試すこともできます。独自に学習したAIモデルや、サイト内で文書を生成するサービスではありません。

## まずどこから見ればよいですか

見た目は[公開作例](SHOWCASE.md)、管理者としての評価は[管理者ガイド](MANAGER_GUIDE_ja.md)、自分で1件作る場合は[初回利用](QUICKSTART_ja.md)から進めます。インストールしなくてもサイトの作例は閲覧できます。

## Company Packとスキルは何が違いますか

Company Packは、会社の文体・用語・デザインなどの規則、根拠、確認・承認状態を持つものです。スキルは、構成・調査・執筆・デザイン・出力などを進める役割別の指示とスクリプトです。公開パッケージは基本スキル8個と、選択した日本語・韓国語モジュールを含みます。

会社別の依頼では、制作の窓口が使用する承認済みPackを明示的に選択・検証します。同梱しただけで、適用や動作が確認できたことにはなりません。

## どのZIPを選べばよいですか

| ファイル | 目的 | 導入との関係 |
|---|---|---|
| [公開サイトのHTML閲覧ZIP](https://document-studio-public-experiment.wlehd00000.chatgpt.site/downloads/document-studio-demo.zip) | 作成済みの静的作例を見る | プラグインのインストーラーではない |
| [Starter plugin ZIP](DOWNLOAD_AND_INSTALL.md) | 一般的な文書制作スキルを試す | 対応アカウントで別途登録が必要。会社Packは含まない |
| [架空の小売デモplugin ZIP](DOWNLOAD_AND_INSTALL.md) | 承認済みの架空Company Packを評価 | 対応アカウントで別途登録し、新しい依頼でPackの使用を確認 |
| GitHubのCode → Download ZIP | ソース・スクリプト・テストを取得 | そのままChatGPTに登録するためのplugin ZIPではない |

リリースのplugin ZIPは[alpha.6の配布ページ](https://github.com/wlehd00000-cell/document-studio/releases/tag/v0.1.0-alpha.6)から取得します。チェックサムと内容を確認し、[導入手順](DOWNLOAD_AND_INSTALL.md)へ進んでください。ダウンロードだけで導入は完了しません。

## ChatGPTとローカルCodexでは何が違いますか

ChatGPTでは、Plugin Creatorの作成機能と対象アカウントの権限を確認してプラグインを登録します。機能がないアカウントでは、このZIP登録経路を使えません。

ローカルCodexでは、スキルを所定の場所に配置し、新しいセッションで認識を確認します。会社別ZIP生成には、スキルだけでなくソース全体とPython環境が必要です。[日本語の初回利用](QUICKSTART_ja.md)

## 非公開の社内資料で、社内専用プラグインを配布できますか

現在の公開エクスポーターでは未対応です。非公開・制限付き資料に由来するPackは拒否されます。公開資料としてのラベル変更や承認情報の偽装で通す方法は使わないでください。

最初の評価は、同梱した架空Pack、または配布権限を確認した公開資料のPackを使います。[現在の範囲と導入条件](MANAGER_GUIDE_ja.md)

## 固定のルールと、創造性は両立しますか

会社の用語・文体・出典などの基準と、目的によって変える構成・表現を分ける設計です。固定様式を選んだ場合は、その配置規則も維持します。[比較画面](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare)は、事前に定めた3様式の静的HTML例を表示します。新規AI生成の遵守率を測ったものではありません。

[創造性の1ページ](https://document-studio-public-experiment.wlehd00000.chatgpt.site/creative)は、同じ案件の要点を別の表現で再編集した例です。比較画面の2ページ全文と同一ではありません。

## コンサルティング企画は毎回入りますか

明示的に選んだときの任意工程です。独立調査・反論・構成の代案を検討し、方向性と最終原稿を確認してから通常の制作へ戻ります。創造性設定とは別です。サイトでは進め方を説明しており、相談を実行していません。[コンサルティングの説明](https://document-studio-public-experiment.wlehd00000.chatgpt.site/consulting)

## PowerPointで文字や数値を直せますか

対応する文字・数値・図形を編集可能な要素として組み立てる出力工程があります。画像や複雑な装飾は画像として残る場合があります。対象環境での変換・表示・編集性の確認が必要です。[変換構造と確認範囲](PPTX_OUTPUT_ja.md)

## モデルを変えても同じ品質になりますか

Company Packは基準を再利用するための入力であり、モデル間の同一出力を保証するものではありません。モデル・スキル・Packの版を変えたときは、新しい依頼と実際の出力で再評価します。企業全体の生産性改善も、この公開実験では実証していません。

## 問題や使用結果はどこに書けばよいですか

[初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)には、進めた段階と、できたこと・止まったことを短く書けます。不具合や改善案は[投稿の入口](https://github.com/wlehd00000-cell/document-studio/issues/new/choose)へ。日本語・한국어・Englishで受け付けます。公開できる架空・匿名化例を使い、機密資料・資格情報は含めないでください。
