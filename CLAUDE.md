# Project AI Development Rules

## このプロジェクトについて

このプロジェクトは FastAPI を使ったバックエンドアプリケーションである。

ただし、FastAPI はあくまで道具であり、以下のシステム開発原則を優先する。

- 「動く」と「運用に耐える」は別物
- 責務分離を守る
- 既存コードの意図を読む
- 本番データ規模を想像する
- 他ユーザー・他テナント・他組織のデータ混入を防ぐ
- N+1 / 全件取得 / メモリ爆発を避ける
- テストで外部HTTPを投げない
- 差分は最小にする
- 意図不明コードを勝手に削除・置換しない

## 必ず参照するルール

実装・修正・レビュー前に、必要に応じて以下を参照すること。

- `docs/ai-rules/core-engineering-principles.md`
- `docs/ai-rules/architecture-boundaries.md`
- `docs/ai-rules/data-scope-performance.md`
- `docs/ai-rules/test-external-io-safety.md`
- `docs/ai-rules/code-context-awareness.md`
- `docs/ai-rules/response-format.md`
- `docs/ai-rules/stacks/fastapi.md`

## FastAPIでの責務対応

このプロジェクトでは、概念上のレイヤーを以下のように対応させる。

```txt
Presentation Layer
  FastAPI Router / Request Schema / Response Schema

Application Layer
  Service / UseCase

Domain Layer
  Domain Model / Business Rule / Value Object

Infrastructure Layer
  Repository / SQLAlchemy / DB / External API / File / Cache
```

## 実装前の基本手順

明らかな typo や単純な修正を除き、いきなり実装しない。

まず以下を整理する。

1. 現状理解
2. 既存コードの意図の推定
3. 影響範囲
4. データ規模・メモリ・SQL・外部IOへの影響
5. 修正方針
6. テスト方針
7. ユーザー確認が必要な箇所

## 禁止事項

* 理由なく大きくリファクタリングしない
* 関係ないファイルを変更しない
* 既存の命名・構造を無視しない
* Router に業務ロジックを増やさない
* Repository に業務判断を入れない
* SQLAlchemy のクエリを Service に直接書かない
* Pydantic Schema に業務ロジックを入れすぎない
* DBモデルをそのままAPIレスポンスとして返さない
* スコープ条件なしで一覧・更新・削除しない
* 1000件以上になり得るデータを安易に全件取得しない
* ループ内でDBクエリや外部APIを発生させない
* テストで外部HTTPを投げない
* `.env` / secrets / credentials を読まない
* 意図不明コードを黙って削除しない

## 回答フォーマット

実装提案・修正提案では、原則として以下の形式で回答する。

### Step 1. 現状理解

* 対象ファイル
* 対象処理の責務
* 現在の処理の流れ
* 既存コードの意図の推定
* 影響範囲

### Step 2. 修正方針

* 何を変更するか
* 何を変更しないか
* FastAPI / Service / Repository の責務分離に合っているか
* 既存パターンと合っているか
* データ規模への影響
* メモリへの影響
* SQL / クエリ数への影響
* N+1 の有無
* スコープ条件の有無
* APIレスポンスへの影響
* テスト方針
* ユーザー確認が必要な箇所

### Step 3. 実装

* 差分最小
* 既存命名を踏襲
* 関係ない整形をしない
* 共通部品を不用意に変えない
* 既存テストの書き方に合わせる

### Step 4. 確認

* 実行したテスト
* 追加したテスト
* 手動確認ポイント
* 未確認リスク
