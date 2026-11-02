# 公開文書例のソースと確認条件

日本語を主言語とする、インストール不要のHTMLショーケースです。

[公開サイト](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [日本語の文書を全ページで表示](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?view=all&size=large) · [韓国語版](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko)

## 収録内容

| 文書 | 目的 | ページ |
|---|---|---|
| 企画提案書 | 範囲・仮説・予算・実行・終了後の判断 | P1–P4 |
| 決裁サマリー | 承認する事項と除外範囲 | A1 |
| 業務ガイド | 手順・担当・例外・引継ぎ | G1 |

![日本語の企画提案書](../docs/assets/showcase/proposal-ja.jpg)

![決裁サマリー](../docs/assets/showcase/decision-ja.jpg)

![業務ガイド](../docs/assets/showcase/guide-ja.jpg)

## 開き方と操作

このフォルダーの `index.html` は紹介ページ、`example.html` は文書専用ビューです。クローンしたファイルはブラウザーで開けます。公開版では次のURLを使用します。

- `example?doc=proposal&view=all&size=large`：提案書を大きめの文字で連続表示。
- `example?doc=approval&view=all&size=large`：決裁サマリー。
- `example?doc=guide&view=all&size=large`：業務ガイド。
- `view=one&page=2`：選択した文書の2ページ目を1ページずつ表示。
- `ko` / `example-ko`：韓国語の紹介と文書例。

日本語ビューでは、文書タブ、全ページ／1ページ表示、文字サイズ、共通基準表示を切り替えられます。韓国語版は従来の1ページずつの表示です。文書専用ビューでは設定がURLに反映されます。依頼文のコピーはブラウザーの許可と実行環境によって利用できない場合があり、その際は選択してコピーする案内を表示します。

日本語本文は [documents-ja.js](documents-ja.js)、韓国語本文は [documents.js](documents.js)、共通の文書レイアウトは [demo.css](demo.css) です。外部API・アカウント・アップロードは使用しません。このフロントエンドはAIモデルを呼び出さず、作成済みの文書を切り替えて表示します。

## 事実・仮定・確認状態

この文書例は、公開用に独立して制作した架空案件です。実際の会社資料の分析、承認済みCompany Packの自動適用、新しいモデルでの生成試験、企業全体の生産性改善を再現・実証したものではありません。

- モア・リテールは架空企業です。対象は1店舗・3品目・4週間です。
- 予算上限は240万ウォン（KRW）。120万＋40万＋25万＋35万＋20万ウォンの合計です。円換算していません。
- 取引目標は20＋35＋45＋50＝150件です。実際の顧客調査や達成実績ではありません。
- 記録率95%以上、介入時間の中央値3分以下などは提案した検討基準です。
- 展開、収益性、環境効果を承認済み・実証済みと扱いません。供給条件と品目・容器の適合性は確認前提です。
- コンセプト画像は生成AIで制作したものです。ガイドに使用した画像は、表紙と同じ原本の一部です。

日本語化では、見出し・本文・図表・注記・金額・担当・除外範囲・未確認状態を対照しました。表示の確認と、実際の業務への採用・成果の検証は別です。PowerPointや印刷結果はこのショーケースでは検証していません。

## ライセンス

独自のHTML・CSS・JavaScriptは[MIT](../LICENSE)。[Pretendard / Pretendard JPのOFL表示](assets/LICENSE-Pretendard.txt)を同梱しています。これらのフォントファイルは、この独立した公開ビューのために `showcase/assets/` に配置しており、スキル本体のフォント導入を代替するものではありません。
