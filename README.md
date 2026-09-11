# ClipKeep

Render にそのままデプロイできる、個人利用・許可済みコンテンツ向けの YouTube ダウンローダーです。YouTube URL を確認して、MP4（動画）または MP3（音声）として保存できます。

## Render へのデプロイ

1. このリポジトリを GitHub にプッシュします。
2. Render Dashboard で **New +** → **Blueprint** を選び、リポジトリを接続します。
3. `render.yaml` を承認してデプロイします。Docker により `yt-dlp` と `ffmpeg` が自動的にインストールされます。

Render が `PORT` 環境変数を割り当てるため、追加設定は不要です。死活監視には `/health` を使用します。

### YouTube 側のアクセス制限について

YouTube はクラウドサービスや共有 IP アドレスからのアクセスを制限する場合があります。その場合、動画の公開状況やダウンロード許可にかかわらず、Render 上の `yt-dlp` が情報を取得できないことがあります。本アプリは失敗理由を画面と Render のログに表示しますが、YouTube のボット検知やアクセス制限を回避する機能は提供しません。

`yt-dlp` は YouTube 側の変更に追随できるよう、Docker ビルド時に最新版をインストールします。デプロイ済みサービスで問題が起きた場合は **Manual Deploy** → **Clear build cache & deploy** を実行して再ビルドしてください。

## ローカル起動

```bash
docker build -t clipkeep .
docker run --rm -p 10000:10000 clipkeep
```

`http://localhost:10000` を開いてください。

## 利用上の注意

このアプリは、自身が著作権その他の必要な権利を持つ動画、または権利者から明示的に保存を許可された動画のみに使用してください。YouTube の利用規約および適用される法令を遵守してください。
