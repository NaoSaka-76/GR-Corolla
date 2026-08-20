# GR Corolla Watch

GR Corollaに関する情報を1か所に集約するモニタリングダッシュボード。GitHub Actionsで
1日3回(JST 07:00 / 12:00 / 17:00)自動的にデータを収集し、GitHub Pagesで公開する。

**公開ページ:** Settings > Pages で有効化後、`https://<owner>.github.io/GR-Corolla/`

## 集約している情報

| セクション | 内容 | 取得方法 |
| --- | --- | --- |
| トヨタ/販売会社 最新リリース | トヨタ自動車・世界各地の販売会社によるGR Corolla関連発表 | Google News RSS(日英・複数地域クエリ) |
| モータースポーツ | TC America(米)・ARA(米ラリー)・スーパー耐久 水素エンジンGRカローラ(日)のトピックス/レース結果/ランキング関連。TC Americaのみ公式サイト実データのドライバーズランキングをグラフ表示 | Google News RSS + TC America公式サイト(標準スクレイピング) + 公式サイト検索リンク |
| YouTube 人気動画 / 新着動画(グローバル・日本語) | 「GR Corolla」(グローバル)と「GRカローラ」(日本語限定)それぞれで、再生数順・投稿日順に整理(サムネイル付き) | YouTube検索結果ページのベストエフォート・スクレイピング |
| SNSでの話題 | X/Facebookの投稿の代替として、ニュース・ブログでの話題言及 | Google News RSS |
| 自動車メディア評価記事 | Car and Driver, MotorTrend等の評価記事 | Google News RSS |
| お客様の声・クレーム関連情報 | リコール・不具合報道など公開情報 | Google News RSS |

トヨタ公式発表以外の全セクションには、見出し文からの簡易センチメント判定(ポジティブ/ネガティブ)を
付与している(英語: VADER、日本語: 自動車レビュー向け手作り極性辞書)。ダッシュボード上では
各記事の左端の色帯とバッジで一目で判別でき、バッジにマウスオーバー(タッチ操作の場合はタップ)
すると判定根拠となった単語がツールチップで表示される。あくまで見出し文のみに基づく自動推定であり、
参考値として利用すること。

## 既知の制約

- **公式API未使用**: YouTube Data API・X API・Facebook Graph API のキーは未設定。すべて
  無料の公開エンドポイント(Google News RSS、YouTube検索ページ)をベストエフォートで
  利用しているため、件数の正確性・網羅性は公式APIに劣る。
- **X/Facebookの投稿本体は含まれない**: 現状、投稿そのものを合法的・安定的に無料取得する
  手段がないため、ニュース/ブログでの言及を代替指標として表示している。
- **クレーム情報は社内システム未連携**: 社内CRM等とは接続しておらず、公開されている
  報道・SNS言及のみを集約した簡易モニタリング。
- **YouTube検索スクレイピングの脆弱性**: YouTube側のページ構造変更により取得に失敗する
  可能性がある。失敗時はダッシュボード上に取得エラーとして表示される。
- **グラフィカルなシリーズランキングはTC Americaのみ**: TC Americaは公式サイト
  (tcamerica.us)の順位表HTMLが安定して取得できるため、ドライバーズランキングを実データで
  グラフ表示している。ARAは公式サイトに順位表がなく、外部の非公式サイトがJavaScriptで
  描画する非公開フォーマットのため誤表示リスクを避けて非対応。スーパー耐久は、水素エンジン
  GRカローラが参戦するST-Qクラスが開発車両専用クラスでポイントランキングの対象外のため
  非対応(いずれも「公式ランキングを検索」リンクから確認可能)。
- **センチメント判定は見出し文のみの自動推定**: 本文全体やコメント欄までは解析していない。

より高精度な情報が必要な場合は、各社の公式APIキー(YouTube Data API v3, X API,
Facebook Graph API)を取得し、`scripts/sources/` 配下の該当モジュールを差し替えることで
精度を向上できる。

## 構成

```
scripts/
  fetch_data.py        # 全ソースを集約し site/data/latest.json を生成
  sources/
    common.py           # RSS取得・数値/日時パース等の共通処理
    sentiment.py         # 見出し文からのポジティブ/ネガティブ推定(VADER + 日本語辞書、判定根拠語も返す)
    toyota_news.py
    motorsports.py       # TC America / ARA / スーパー耐久
    standings.py          # TC America公式サイトの実データランキング取得
    youtube.py
    social_buzz.py
    media_reviews.py
    complaints.py
site/
  index.html / style.css / app.js   # ダッシュボード本体(静的サイト)
  data/latest.json                  # 自動生成される最新データ(コミット対象外)
.github/workflows/update-dashboard.yml  # 1日3回の自動更新 + GitHub Pagesデプロイ
```

## ローカルでの動作確認

```bash
cd scripts
pip install -r requirements.txt
python fetch_data.py          # site/data/latest.json を生成
cd ../site
python3 -m http.server 8000   # http://localhost:8000 で確認
```

## GitHub Pagesの有効化(初回のみ)

リポジトリの Settings > Pages > Build and deployment > Source を
**GitHub Actions** に設定する。設定後、`update-dashboard` ワークフローの実行(スケジュール
または手動の workflow_dispatch)によって自動的に公開される。
