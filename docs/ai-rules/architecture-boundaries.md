# Architecture Boundaries

## 原則

アプリケーションは責務ごとに分離する。

代表的な責務は以下。

```txt
Presentation Layer
  UI / API Controller / Request / Response

Application Layer
  UseCase / Service / Application Service

Domain Layer
  Business Rule / Domain Model / Domain Service

Infrastructure Layer
  Repository / ORM / DB / External API / File / Queue
```

## Presentation Layer

ユーザー入力とレスポンスを扱う層。

### 責務

* リクエストの受け取り
* 入力値の形式確認
* 認証・認可の入口
* UseCase / Service の呼び出し
* レスポンス整形
* 画面表示用データの受け渡し

### 書かないもの

* 複雑な業務判断
* DBクエリ
* 外部APIの詳細処理
* 大量データ処理
* 複数データソースを組み合わせる処理

## Application Layer

業務ユースケースを実現する層。

### 責務

* 業務フロー
* トランザクション制御
* 条件の組み立て
* Repository / 外部API / Domain の組み合わせ
* 例外ケースの判断
* 処理順序の制御

### 書かないもの

* HTTPレスポンス生成
* UI都合に寄りすぎた処理
* 生SQLの詳細
* フレームワーク固有の表示処理

## Domain Layer

業務ルールそのものを表現する層。

### 責務

* 業務ルール
* 状態遷移
* 計算ロジック
* 不変条件
* ドメイン上の制約

### 書かないもの

* DB保存処理
* HTTP処理
* UI処理
* 外部API通信

## Infrastructure Layer

外部リソースとの接続を扱う層。

### 責務

* DB操作
* ORM / Query Builder
* 外部API通信
* ファイル操作
* Queue
* Cache
* Storage
* Mail
* Logging

### 書かないもの

* 業務判断
* UI都合の分岐
* ユースケース全体の制御

## 例外

小規模な取得処理では、Controller / Router から Repository / Model を直接呼ぶ構成も許容する。

ただし以下を満たすこと。

* 既存コードに同じパターンがある
* 単純な取得である
* 業務判断がない
* 将来肥大化しにくい
* テストしづらくならない

迷った場合は Application Layer / Service / UseCase に寄せる。
