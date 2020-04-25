### Shisetsu Scraper
- 施設予約システムから施設の空き状況を取得するためのツール
- 東京23区の施設から順に作成しています
  - [江東区](https://sisetun.kcf.or.jp/web/)
  - [江戸川区](https://www.edogawa-yoyaku.jp/edo-user/)

### 仕組み
- pythonとseleniumでスクレイピングしています

### common について
- webdriverを設定する部分と、データの出力に関する部分を共通化しています。
  - webdriverのpathは人によって違うため、ローカル開発時に手で書き換えるようになっています。
