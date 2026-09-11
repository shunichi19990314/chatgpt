# ClipKeep

Render にそのままデプロイできる、個人利用・許可済みコンテンツ向けの YouTube ダウンローダーです。YouTube URL を確認して、MP4（動画）または MP3（音声）として保存できます。

## Render へのデプロイ

1. このリポジトリを GitHub にプッシュします。
2. Render Dashboard で **New +** → **Blueprint** を選び、リポジトリを接続します。
3. `render.yaml` を承認してデプロイします。Docker により `yt-dlp` と `ffmpeg` が自動的にインストールされます。

Render が `PORT` 環境変数を割り当てるため、追加設定は不要です。死活監視には `/health` を使用します。

## ローカル起動

```bash
docker build -t clipkeep .
docker run --rm -p 10000:10000 clipkeep
```

`http://localhost:10000` を開いてください。

## 利用上の注意

このアプリは、自身が著作権その他の必要な権利を持つ動画、または権利者から明示的に保存を許可された動画のみに使用してください。YouTube の利用規約および適用される法令を遵守してください。
