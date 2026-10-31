# 大鵬 工事管理 v0.1

最大10人（管理者を含む）の個別ログインで利用する、1社向けクラウド対応工事管理アプリです。日本語UI、スマートフォン対応。Django / PostgreSQL構成、ローカル試用はSQLiteで起動できます。クラウドへの公開はまだ行っていません。

## 最初に読む
- [Windows・Macの起動手順](#ローカル起動)
- [Renderへの設置手順・バックアップ](docs/DEPLOY.md)
- [画面構成・権限・仮定・未実装](docs/SPEC.md)
- [検証結果と限界](docs/TEST_REPORT.md)
- [Codexでの開発継続](AGENTS.md)

## ローカル起動
Python 3.12を用意し、GitHubから取得またはZIPを展開して `manage.py` があるフォルダーで実行してください。

Windows PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEBUG = "1"
$env:SECRET_KEY = (.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))")
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py init_admin
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
macOS / Linux:
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export DEBUG=1
export SECRET_KEY=$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')
.venv/bin/python manage.py migrate
.venv/bin/python manage.py init_admin
.venv/bin/python manage.py runserver 127.0.0.1:8000
```
ブラウザで http://127.0.0.1:8000/login/ を開き、作成した管理者でログインします。初期パスワードは同梱していません。パスワードは対話入力し、12文字以上を指定します。

初期設定の順序：①担当者・ユーザー追加 → ②工事案件登録 → ③協力会社登録 → ④工程・見積などを登録。担当者と案件は選択式です。

新しいターミナルではDEBUGとSECRET_KEYを再設定してください。開発用秘密鍵を変更すると既存ログインが無効になります。`.env` はPython起動時に自動読込しません（Docker Composeのみ自動読込）。

## テスト
上記の環境変数を設定して実行します。
```bash
python manage.py test
python manage.py makemigrations --check --dry-run
```
CIはSQLiteとPostgreSQLの2構成で実行します。

## ファイル構成
```text
config/              設定、URL、WSGI
core/models.py       ユーザー・案件・工程・会計台帳
core/views.py        権限確認、画面、CSV、操作履歴
core/forms.py        入力検証
core/registry.py     機能一覧とロール権限
core/migrations/     DBスキーマと初期ロック行
core/tests.py        機能・セキュリティ回帰テスト
core/management/     初回管理者の作成
templates/           日本語画面
docs/                要件、運用、検証
render.yaml          Render用の構成例
Dockerfile           本番サーバー起動用
compose.yaml         ローカルPostgreSQL試用
.github/workflows/   SQLite / PostgreSQLテスト
```

## 既存試作版からの変更
以前のFastAPI試作版の11台帳とCSV出力、収支集計を引き継ぎ、認証・CSRF・フォーム検証を標準化するためDjangoで再実装しました。既存のSQLiteデータをそのまま流用する互換性はありません。旧版データがある場合は、別途変換・照合が必要です。本パッケージに既存データは含みません。

公開リポジトリにはソースと架空のテスト値のみを置きます。顧客情報・DB・バックアップ・秘密鍵・パスワードはコミットしないでください。`.gitignore` は登録済みファイルから機密情報を消す機能ではありません。
