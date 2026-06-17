# FastAPI Stack Rules

## 1. FastAPIの基本方針

FastAPI は HTTP 入出力を扱うためのフレームワークである。

Router に業務ロジックやDB操作を集めず、以下の責務分離を守る。

```txt
Router
  ↓ request / response / dependency / status code

Service / UseCase
  ↓ business flow / transaction / validation beyond schema

Repository
  ↓ SQLAlchemy / DB access

Model / Schema
  ↓ DB structure / request-response structure
```

## 2. Router

Router は薄く保つ。

### Router の責務

* endpoint 定義
* path / query / body の受け取り
* Depends による依存注入
* 認証・認可の入口
* Service 呼び出し
* response_model の指定
* HTTPException / status code の返却
* APIレスポンス整形

### Router に書かないもの

* 複雑な業務判断
* SQLAlchemy クエリ
* 複数Repositoryを組み合わせる処理
* トランザクション制御
* 外部APIの詳細処理
* 大量データ処理
* CSV / batch / import / export の本体処理

## 3. Service / UseCase

Service は業務ユースケースを表現する。

### Service の責務

* 業務フロー
* 業務判断
* Repository の組み合わせ
* 外部API呼び出しの制御
* トランザクション境界
* 例外ケース判断
* 認可後の業務的な権限チェック
* Repository に渡す検索条件の組み立て

### Service に書かないもの

* FastAPI の Request / Response に依存した処理
* HTTPException の乱用
* SQLAlchemy の詳細なクエリ
* Pydantic Schema 前提の画面都合に寄りすぎた処理

ただし、既存コードが小規模で Router → Repository 直呼びの構成なら、既存パターンを確認した上で最小差分を優先する。

## 4. Repository

Repository は DB 操作に責務を限定する。

### Repository の責務

* SQLAlchemy ORM / Core によるDB操作
* select / join / where / order / limit / offset
* create / update / delete
* pagination
* bulk insert / bulk update
* DB都合の最適化
* eager loading の指定

### Repository に書かないもの

* 業務判断
* HTTPレスポンス生成
* FastAPI の Depends
* Pydantic response schema への過度な依存
* 複数ユースケースにまたがる大きな判断

## 5. Pydantic Schema

Pydantic は入出力の型定義・バリデーションに使う。

### Schema の責務

* Request body の型定義
* Response body の型定義
* 入力値の形式チェック
* API仕様の明確化
* OpenAPI生成

### Schema に書きすぎないもの

* 複雑な業務判断
* DBアクセス
* 外部APIアクセス
* 状態遷移ロジック
* 複数テーブルをまたぐ整合性チェック

## 6. SQLAlchemy

SQLAlchemy を使う場合、DBアクセスは Repository に寄せる。

### 原則

* 一覧取得では pagination / limit を意識する
* relation 取得では N+1 に注意する
* 必要に応じて selectinload / joinedload を使う
* select でカラムを絞る場合は、後続処理に必要なキーを欠落させない
* tenant_id / organization_id / user_id などのスコープ条件を必ず確認する
* session.query(...).all() や scalars(...).all() の全件取得に注意する

### 禁止

* 1000件以上になり得るデータの安易な `.all()`
* ループ内で relation に初アクセスして N+1 を発生させる
* スコープ条件なしの update / delete
* Service / Router に複雑なSQLAlchemyクエリを書く
* DBモデルをそのまま外部APIレスポンスに露出する

## 7. Transaction

トランザクション境界は原則 Service / UseCase に置く。

### 原則

* 複数Repositoryをまたぐ更新は Service で制御する
* commit / rollback の責務を曖昧にしない
* Repository 内で勝手に commit しない
* 既存コードの transaction 方針を確認する

Repository ごとに commit すると、途中失敗時に不整合が起きる可能性がある。

複数のDB更新を1つの業務処理として扱う場合は、Service 側で transaction をまとめる。

## 8. Dependency Injection

FastAPI の Depends は便利だが、責務を混ぜない。

### Depends に置いてよいもの

* DB session の取得
* 認証ユーザー取得
* 権限チェックの入口
* 設定値の注入
* Service / Repository の生成

### Depends に置きすぎないもの

* 複雑な業務判断
* DB更新処理
* 外部API呼び出し
* 重い処理
* 複数ユースケースにまたがる処理

## 9. Async / Sync

async / sync を混在させる場合は注意する。

### 確認すること

* DBドライバが async 対応か
* SQLAlchemy session が AsyncSession か通常 Session か
* 外部HTTPクライアントが async 対応か
* CPU-bound な処理を async にしていないか
* blocking I/O を async endpoint 内で直接呼んでいないか

### 禁止

* async endpoint 内で重い同期I/Oを直接実行する
* AsyncSession と通常 Session を曖昧に混ぜる
* async 化だけを目的に無意味に書き換える

## 10. Alembic / Migration

DB構造変更では Alembic migration を使う。

### 原則

* migration は既存パターンに合わせる
* データ喪失リスクのある変更は明示する
* 既存データへの影響を考慮する
* rollback / downgrade の扱いを確認する
* index 追加・削除の影響を報告する

### 禁止

* 既存データを壊す変更を説明なしに行う
* nullable / default / unique / foreign key の影響を無視する
* migration なしで model だけ変更する
* model 変更なしで migration だけ変更する

## 11. テスト

テストは pytest を前提とする。

### 確認すること

* TestClient / AsyncClient の既存パターン
* DB fixture の既存パターン
* transaction / rollback の扱い
* dependency override の使い方
* 認証ユーザーの作り方
* factory の使い方
* 外部HTTP mock の方法

### 禁止

* テストで外部HTTPを投げる
* 本物の外部APIキーを使う
* `.env` の秘密情報に依存する
* 既存fixtureを無視して独自fixtureを乱立する
* DB状態に依存して順序不安定なテストを書く

## 12. 外部HTTP

外部API呼び出しは Infrastructure 層に閉じる。

### 原則

* HTTPクライアントは直接散らばらせない
* timeout を設定する
* retry 方針を確認する
* エラー時の扱いを明確にする
* テストでは必ず mock / fake / stub する

### 禁止

* Router から直接外部HTTPを呼ぶ
* Service 内にURLや認証情報をベタ書きする
* テストで実HTTPを飛ばす
* timeout なしで外部APIを呼ぶ

## 13. API Response

APIレスポンスは response_model / schema で明示する。

### 原則

* DBモデルをそのまま返さない
* 不要な内部カラムを返さない
* null / 空配列 / 未存在データの返却形式を統一する
* ステータスコードを明確にする
* エラー形式を既存パターンに合わせる

### 確認すること

* フロント側が依存しているレスポンス構造
* OpenAPI に出る型
* optional / nullable の扱い
* datetime / decimal / enum のシリアライズ

## 14. 修正提案時の必須報告

FastAPI 関連の変更では、必ず以下を報告する。

* Router / Service / Repository のどこを変更するか
* 責務分離に合っているか
* Pydantic Schema への影響
* SQLAlchemy クエリへの影響
* N+1 の有無
* `.all()` など全件取得の有無
* スコープ条件の有無
* transaction への影響
* Alembic migration の要否
* APIレスポンス構造への影響
* pytest の追加・変更方針
* 外部HTTP mock の有無
