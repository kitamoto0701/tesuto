# クラウド設置と運用

## Renderの手順
今回の作業では契約・有料リソース作成・インターネット公開を行っていません。`render.yaml` をRenderで適用するとWebサービスとPostgreSQLの有料リソースが作成されます。適用画面で最新料金を確認してください。

1. GitHubの `kitamoto0701/tesuto` をRenderに接続する。
2. New → Blueprintからリポジトリを指定し、`render.yaml` の構成を確認する。これはPython Web Serviceで、Static Siteではありません。
3. WebサービスとDBのプラン・リージョンを確認して適用する。リージョン指定はYAMLで固定していないため、同一リージョンを選ぶ。
4. 秘密鍵 `SECRET_KEY` はRenderで生成、`DATABASE_URL` はDB接続情報から設定。`DEBUG=0`、`TRUST_PROXY=1`、`DB_SSLMODE=require`。秘密値をREADMEやGitHubに貼らない。
5. ビルド：`pip install -r requirements.txt`。Pre-deploy：`python manage.py migrate --noinput`。Start：`python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --access-logfile -`。
6. Render Shellから `python manage.py init_admin` を実行。管理者名とパスワードを対話入力する。パスワードをコマンド引数にしない。
7. HTTPSの公開URLでログイン。担当者を追加し、架空案件で動作確認する。秘密鍵は再起動ごとに変更せず、RenderのSecret設定で維持する。
8. 独自ドメインの場合は `ALLOWED_HOSTS=example.jp` と `CSRF_TRUSTED_ORIGINS=https://example.jp` を設定する。Render標準ホストは `RENDER_EXTERNAL_HOSTNAME` から許可する。
9. バックアップ・復元、10名での同時利用、各ロールの見え方を確認してから実運用へ移行する。

設定で長い秘密鍵とPostgreSQLを本番必須にしています。HTTPSへリダイレクトし、Secure / HttpOnlyセッションクッキー、HSTS、CSRF防御、フレーム埋込防止を有効にします。Render以外で `TRUST_PROXY=1` を指定する場合、フロントのプロキシが利用者の転送ヘッダーを除去して上書きすることを確認してください。

アプリはDBセッションを使うため複数ワーカーで共有できます。SQLiteファイルをRenderの一時ディスクに置く構成は使用しません。図面写真の本体は未保管です。

## PostgreSQLをローカルで試す
Dockerが利用できるPCで `.env.example` を `.env` にコピーし、ランダムなSECRET_KEYと `POSTGRES_PASSWORD`（URLに安全な英数字のランダム値）を設定します。
```bash
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py init_admin
docker compose up -d web
docker compose run --rm web python manage.py test
```
http://127.0.0.1:8000 で確認します。DBは名前付きボリュームに保存。`docker compose down -v` はデータを消すため使用しないでください。このcomposeはローカル専用で、DBのTLSを無効化しています。

## バックアップ・復元
Renderのバックアップ保持期間・復元機能は契約プランにより確認する。初期運用案は日次バックアップ、保持30日、月1回の別環境復元テスト。目標RPO 24時間 / RTO 4時間は仮設定で、実測保証ではありません。

PostgreSQLクライアントを導入した管理端末で、`PGHOST` / `PGPORT` / `PGUSER` / `PGDATABASE` / `PGSSLMODE=require` を秘密管理から設定し、`pg_dump -W` の対話プロンプトでパスワードを入力します。接続URLをシェル履歴に保存しないこと。
```bash
pg_dump -W -Fc -f taiho-backup.dump
# 別の空の検証DBをPGDATABASEに設定してから実行
pg_restore -W --no-owner --no-privileges -d "$PGDATABASE" taiho-backup.dump
```
DBの外部接続は初期設定で禁止しています。バックアップ管理端末を使用する場合だけ、その固定IPをRenderのDB許可リストに追加してください（全IP許可はしない）。

バックアップは暗号化された社内保管先へ移し、GitHubへ追加しません。復元後はログイン、案件数、請求合計、操作履歴を照合。アプリのSECRET_KEYも別途安全に保管します。復元先はインターネット非公開で検証してください。

## 更新・障害時
- 更新前にDBバックアップ、ステージングでmigrationとテストを実行。
- 本番で `python manage.py check --deploy` を実行。
- DBスキーマを戻す場合は移行の可逆性とデータを確認。コードだけの巻戻しでDBが戻るわけではありません。
- `/health/` はDB接続確認を含む。監視はHTTPSで実行。HTTPアクセスログには入力本文やパスワードを記録しない。
- 失敗ログインの記録はユーザー名のSHA-256のみで、5回/15分の制限。大量の未知ユーザー名への攻撃やDoSはプロバイダ/WAFのIP制限も併用する。
- 監査履歴はアプリから削除不可ですが、DB管理者に対する改ざん耐性はありません。厳格な監査は外部保管を追加。
- 退職者は即時無効化。パスワード再設定で既存セッションは失効。共有アカウントは禁止。

参考： https://render.com/docs/deploy-django 、https://render.com/docs/blueprint-spec 、https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
