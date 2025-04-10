# instant-film-effect
Pythonで画像クロップ＋インスタントフィルム風エフェクトをかけるやつ

## 使い方

```:basic usage
python instantfilm_effect.py [input file] [output file]
```

```:help
>python instantfilm_effect.py --help                                                                   
usage: instantfilm_effect.py [-h] [--leak-position {upper_left,upper_right,bottom_left,bottom_right}] [--verbose] input_file output_file

instax mini風画像＋光漏れ効果を適用するスクリプト

positional arguments:
  input_file            入力画像のファイルパス（例: input.jpg）
  output_file           出力画像のファイルパス（例: output.jpg）

options:
  -h, --help            show this help message and exit
  --leak-position {upper_left,upper_right,bottom_left,bottom_right}, --lp {upper_left,upper_right,bottom_left,bottom_right}
                        光漏れの位置を指定します。デフォルトは upper_right です。
  --verbose, -v         処理状況を表示します
```