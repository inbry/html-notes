# html-notes

Claudeに作ってもらった解説HTMLを蓄積し、一覧から読み返すためのサイト。

> 本リポジトリは個人の学習メモであり、所属組織の見解を示すものではありません。

## 運用フロー

1. Claudeのartifactを `.html` でダウンロードする
2. `docs/` に置く（ファイル名はリネームしない。日本語・スペースを含んでいてもよい）
3. commit & push する
4. GitHub Actionsが一覧ページを再生成し、GitHub Pagesにデプロイする

手でindexを編集する工程はない。

## 仕組み

- `build.py`（Python 3標準ライブラリのみ）が `docs/**/*.html` を走査し、`_site/` に一覧ページ (`index.html`) とHTML本体を出力する
- タイトルは `<title>` → 最初の `<h1>` → ファイル名 の優先順で決定する
- 更新日はそのファイルの最終コミット日（`git log`）。コミット履歴がない場合はファイルの更新日時にフォールバックする
- `.github/workflows/deploy.yml` が push をトリガーにビルドとPagesデプロイを行う

## ローカルでの確認

```bash
python build.py
python -m http.server -d _site 8000
```
