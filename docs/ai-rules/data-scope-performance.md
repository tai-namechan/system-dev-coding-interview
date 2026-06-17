# Data Scope & Performance

## 原則

本番で何千件・何万件のデータが流れるかを常に想像する。

## 1. データスコープ

マルチテナント・店舗別・ユーザー別・組織別のデータは、必ずスコープ条件を確認する。

例:

- tenant_id
- shop_id
- organization_id
- company_id
- user_id
- account_id

### 禁止

- スコープなしの一覧取得
- スコープなしの更新
- スコープなしの削除
- フロント側だけでスコープを絞る
- JOIN 後にしかスコープが効かない重いクエリ

## 2. 大量データ取得

1000件以上になり得るデータの全件取得は避ける。

避けるもの:

- 全件取得
- 全件配列化
- 全件をメモリ上でfilter/map/sort
- 全件をフロントへ返却
- IDリストを大量に作って一括 whereIn / IN 句へ渡す

代替:

- pagination
- limit
- cursor
- streaming
- chunk
- batch
- background job
- DB側での集計・絞り込み

## 3. N+1防止

一覧処理では、ループ内で追加クエリや外部API呼び出しが発生しないか確認する。

確認すること:

- relation / association / join の取得方法
- serializer / resource / presenter 内の遅延取得
- UI表示用の追加データ取得
- 外部APIのループ呼び出し

## 4. JOIN / IN / Subquery

関連データ取得では、件数・index・可読性を考慮して選択する。

原則:

- 関連テーブルの絞り込みは JOIN を優先
- 少量データや可読性重視の場合は IN / subquery も許容
- 大量IDリストをメモリに持たない
- index が使われる条件を意識する

## 5. 一括処理

大量の insert / update / delete / export / import は分割実行する。

目安:

| 件数 | 方針 |
|---:|---|
| 〜100件 | 一括で問題なし |
| 100〜1000件 | 一括可。ただしSQLサイズ・メモリ確認 |
| 1000件〜 | chunk / batch / pagination 必須 |
| 数万件〜 | 非同期処理・Queue・Job・index設計を検討 |

## 6. 報告義務

DB / API / メモリに影響する変更では、必ず以下を報告する。

- 想定データ件数
- クエリ数
- N+1 の有無
- スコープ条件の有無
- 全件取得の有無
- chunk / pagination の必要性
- メモリ影響
- index 利用の見込み
- 外部API呼び出し回数
