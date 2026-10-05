# envdoctor

**`.env` が壊れていないか、1コマンドで診断。** `.env` と `.env.example` を突き合わせ、設定漏れ・未ドキュメントの変数・空の値・`.env.example` に混入した本物の秘密情報・`.gitignore` 漏れを検出します。Python 3 標準ライブラリだけ、単一ファイル、依存ゼロ。

```console
$ python envdoctor.py
✗ DB_URL is in .env.example but missing from .env
! DEBUG is in .env but not documented in .env.example
! PORT is empty in .env (example has a default)
✗ API_KEY in .env.example looks like a real secret; use a placeholder
✗ .env is not in .gitignore - it could be committed
```

## 検出するもの
| コード | レベル | 内容 |
|---|---|---|
| `missing` | error | `.env.example` にあるが `.env` にない |
| `extra` | warn | `.env` にあるが `.env.example` に書かれていない |
| `empty` | warn | `.env.example` に既定値があるのに `.env` が空 |
| `leaked-secret` | error | `.env.example` に本物らしい秘密情報(AWS/GitHub/OpenAI/Slack/Google のキー形式、または `*_KEY`/`*_TOKEN`/`*_SECRET` で 16 文字以上の実値) |
| `not-ignored` | error | `.env` が `.gitignore` されていない |
| `syntax` | warn | 解釈できない行 |

`export KEY=value`、クォート、行末コメントに対応。

## 使い方
```
python envdoctor.py [--env .env] [--example .env.example] [--strict] [--json]
```
- 終了コード: `0` 正常 / `1` 問題あり / `2` ファイルが読めない
- `--strict` 警告もエラー扱い
- `--json` 機械可読な出力

### CI (GitHub Actions)
```yaml
- run: python envdoctor.py --env .env.ci --example .env.example --strict
```

### pre-commit フック
`.git/hooks/pre-commit` に `python envdoctor.py || exit 1`

## テスト
`python -m unittest discover tests`

## License
MIT
