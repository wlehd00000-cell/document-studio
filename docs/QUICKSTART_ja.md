# Document Studio — AI資料作成の手順と基準を再利用

**報告書や提案書を作るたびに、同じ指示を説明し直していませんか。**

Document Studioは、調査 → 構成 → 執筆 → デザイン → 確認を再利用する、MITライセンスのオープンソースツールキットです。ローカルCodex用のスキルと、作成権限のあるChatGPTアカウント向けのプラグインパッケージを提供します。韓国語・日本語のビジネス文章モジュールを選択できます。

[⭐ GitHubでStarして保存](https://github.com/wlehd00000-cell/document-studio) · [English](../README.md) · [한국어](QUICKSTART_ko.md)

## まず資料を1件作ってみる

会社資料の分析や管理者による配布から始める必要はありません。[初回利用ガイド](TRY_FIRST.md#日本語)には、導入手順とそのまま使える架空の提案書の依頼例があります。

| 利用環境 | 始め方 |
|---|---|
| ChatGPT | [Starter ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip)をPlugin Creatorで個人用プラグインとして登録。作成機能と権限のあるアカウントが必要です。 |
| ローカルCodex | 下記コマンドで配置し、新しいセッションで `report-html-pptx` が認識されるか確認します。 |
| 組織での評価 | まず一般的な資料を作成し、次に[架空企業デモ](TRY_FIRST.md#company-demo)で会社別ルールの適用を確認します。 |

```bash
git clone --branch v0.1.0-alpha.6 --depth 1 https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/install_local.py --language-skills ja
```

Python 3.12と、スキルを検出できるローカルエージェント環境が必要です。実行前にインストーラーを確認してください。ファイルの配置成功と、エージェントによる認識は別々に確認します。

## 通常の資料作成依頼との違い

毎回長い指示文を書く代わりに、作成手順と確認基準をスキルに分けています。会社別に承認したルールはCompany Packとして管理する設計です。単一の固定テンプレートを複製するのではなく、確認済みの文章・構成の原則を新しい資料に適用します。

品質向上率や所要時間の短縮率を測定した製品ではありません。同じモデル・同じ依頼を使い、スキルの有無による修正量や構成の違いを比較してください。

## 現在の範囲

実験的な **alpha.6** です。独自に学習したモデルや、ワンクリックで完成するPowerPointサービスではありません。非公開の社内資料を基にしたパックは、現在の公開エクスポーターでは配布できません。最終的なHTML/PPTX作成と表示確認は別工程です。モデル間で同じ結果は保証しません。

[導入の詳細と制約](DOWNLOAD_AND_INSTALL.md) · [会社別ルールの分析手順](DEMO_FLOW.md) · [初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/4)

役立ちそうだと感じたら、[GitHubで⭐ Star](https://github.com/wlehd00000-cell/document-studio)を付けていただけると励みになります。導入で止まった手順や具体的な修正点は、改善のための情報として歓迎します。
