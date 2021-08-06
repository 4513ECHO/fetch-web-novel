# fetch-web-novel

小説投稿サイトから指定した小説の内容を取得するCLIツール

> **WARNING**
> このツールの使用は個人での利用にとどめ、絶対に日本の法律に違反しないようにしてください。また、Webスクレイピングに関する注意事項([ここ](https://qiita.com/nezuq/items/c5e827e1827e7cb29011)などが詳しいです)を必ず守ってください。

## Usage

### 準備

依存パッケージが`requestments.txt`に書いてあります。お使いのパッケージマネージャーでインストールしてください。

```pipの場合
pip install -r requestments.txt
```

### コマンド

作者の信条によりヘルプは全て英語です。わからないときはこのREADMEを読むか、issueを立ててください。

```
usage: ./fetch_web_novel.py [options...] <novel_code>

CLI tool to retrieve the contents of a specified novel from a novel submission website

positional arguments:
  novel_code    set the code of the novel to be retrieve

optional arguments:
  -h, --help    show this help message and exit
  -N, --narou   set the destination website to 'Shosetsuka ni Narou'
  -H, --hameln  set the destination website to 'Hameln'
  -J, --toSJIS  create a file in Shift-JIS format
```

| オプション   |        |
|:------------:|--------|
| -h, --help   | ヘルプを表示します |
| <novel_code> | 取得したい小説のコードを設定します |
| -N, --narou  | 取得先のWebサイトを「小説家になろう」に設定します |
| -H, --hameln | 取得先のWebサイトを「小説家になろう」に設定します |
| -J, --toSJIS | Shift-JIS形式のファイルを作成します |

## License

MIT License

