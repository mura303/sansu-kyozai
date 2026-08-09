# 算数教材サイト セットアップ手順書(AIエージェント向け)

このリポジトリ一式を GitHub にプッシュし、GitHub Pages で公開するための手順書です。
`gh` CLI を使って全工程を自動で実行してください。各ステップに検証コマンドがあります。
**検証が失敗した場合は次のステップに進まず、末尾のトラブルシューティングを参照すること。**

## このzipの内容

```
sansu-kyozai/
├── README.md                      … この手順書
├── nenreizan-kyozai.html          … 教材1: 年齢算(14ステップ)
├── kabusokuzan-kyozai.html        … 教材2: 過不足算(16ステップ)
├── scripts/build_index.py         … 目次(index.html)の自動生成スクリプト
└── .github/workflows/deploy.yml   … push時に index生成 → Pages公開 を行うワークフロー
```

`index.html` は含まれていません。デプロイのたびにワークフローが自動生成するためです。

## 仕組み

main ブランチへの push をトリガーに GitHub Actions が起動し、
`scripts/build_index.py` がリポジトリ直下の全HTML(index.html を除く)から
`<title>` と `<meta name="description">` を読み取って目次ページを生成し、
サイト一式を GitHub Pages にデプロイします。

## 前提条件の確認

```bash
gh --version                 # gh CLI が入っていること
git --version
gh auth status               # ログイン済みであること
```

`gh auth status` が未ログインなら `gh auth login` を実行(対話が必要なためユーザーに依頼)。

**重要:** ワークフローファイル(.github/workflows/)を push するには、トークンに
`workflow` スコープが必要。push が `refusing to allow ... workflow` エラーで
拒否された場合は次を実行してから再 push する:

```bash
gh auth refresh -s workflow
```

## ステップ1: リポジトリの初期化とコミット

```bash
cd sansu-kyozai
git init -b main
git add -A
git commit -m "算数教材サイト: 教材2点と自動デプロイ設定"
```

検証:

```bash
git log --oneline            # コミットが1件あること
git ls-files                 # 4ファイル+README が含まれること
```

## ステップ2: GitHubリポジトリの作成とプッシュ

リポジトリ名は `sansu-kyozai`(既に同名があるなら別名に変更してよい)。
**GitHub Pages の無料利用には Public が必須。**

```bash
gh repo create sansu-kyozai --public --source=. --push
```

検証:

```bash
gh repo view --json name,visibility,url
git ls-remote --heads origin main    # main ブランチが存在すること
```

この push で初回のワークフローが起動するが、Pages 未設定のため
deploy ジョブが失敗する可能性がある。**この時点の失敗は正常。無視してよい。**

## ステップ3: GitHub Pages を有効化(公開元 = GitHub Actions)

```bash
gh api -X POST "repos/{owner}/{repo}/pages" -f build_type=workflow
```

- 成功: HTTP 201 が返る
- `409 Conflict`(すでにPagesが存在する)の場合は代わりに:

```bash
gh api -X PUT "repos/{owner}/{repo}/pages" -f build_type=workflow
```

検証:

```bash
gh api "repos/{owner}/{repo}/pages" --jq '.build_type'   # "workflow" であること
```

## ステップ4: ワークフローを実行して公開

初回 push 分が失敗していてもよいので、あらためて実行する:

```bash
gh workflow run "Build index and deploy to GitHub Pages"
sleep 10
gh run list --limit 1
gh run watch $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
```

検証(conclusion が success であること):

```bash
gh run list --limit 1 --json conclusion --jq '.[0].conclusion'
```

## ステップ5: 公開確認

```bash
SITE_URL=$(gh api "repos/{owner}/{repo}/pages" --jq '.html_url')
echo "$SITE_URL"
curl -sS -o /dev/null -w "%{http_code}\n" "$SITE_URL"          # 200 であること
curl -sS "$SITE_URL" | grep -o "単元 [0-9]*" | sort -u          # 単元 1 / 単元 2 が出ること
curl -sS -o /dev/null -w "%{http_code}\n" "${SITE_URL}nenreizan-kyozai.html"    # 200
curl -sS -o /dev/null -w "%{http_code}\n" "${SITE_URL}kabusokuzan-kyozai.html"  # 200
```

デプロイ直後は反映まで最大1〜2分かかることがある。404 なら60秒待って再試行(最大5回)。

最後に、公開URL(`$SITE_URL`)をユーザーに報告すること。

## 以後の運用: 新しい教材の追加

新しい教材HTMLをリポジトリ直下に置いて push するだけで、目次に自動追加されて公開される:

```bash
cp <新教材>.html sansu-kyozai/
cd sansu-kyozai
git add -A && git commit -m "教材追加: <教材名>" && git push
```

新教材HTMLが満たすべき規約:

1. **必須**: `<title>教材名 — 説明</title>` の形式(区切りは全角ダーシ「—」)。
   「—」の前が目次カードの見出しになる。
2. 推奨: `<meta name="description" content="...">` … 目次カードの説明文。
   なければ title の「—」の後ろが使われる。
3. 任意: `<meta name="course-order" content="3">` … 目次での並び順。
   なければ指定済み教材の後にファイル名順で並ぶ。
4. ファイル名は半角英数とハイフンのみ(例: `tsurukamezan-kyozai.html`)。
   `index.html` という名前は使用禁止(自動生成で上書きされる)。

push 後の検証は ステップ4の `gh run watch` とステップ5の `curl` を再利用する。

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| push が workflow スコープ不足で拒否される | `gh auth refresh -s workflow` 後に `git push` |
| Pages API が 404 を返す | リポジトリが Private になっていないか確認: `gh repo view --json visibility`。Private なら `gh repo edit --visibility public --accept-visibility-change-consequences` |
| Pages API が 409 を返す | POST の代わりに PUT を使う(ステップ3参照) |
| ワークフローが `build_index.py` で失敗 | `gh run view --log-failed` でログ確認。教材HTMLの title タグ形式(上記規約1)を確認 |
| サイトが404のまま | 1〜2分待って再試行。`gh api "repos/{owner}/{repo}/pages" --jq '.status'` が `built` になるまで待つ |
| 目次に教材が出ない | ファイルがリポジトリ直下にあるか、`index.html` 以外の名前かを確認 |
