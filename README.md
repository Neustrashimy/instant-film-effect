# instant-film-effect
Pythonで画像クロップ＋インスタントフィルム風エフェクトをかけるやつ

## 使い方

```:basic usage
python instantfilm_effect.py [input file] [output file]
```

```:help
>python instantfilm_effect.py --help                                                                                      
usage: instantfilm_effect.py [-h] [--leak-style {warm,cool,pink,burn,none,auto}] [--leak-position {upper_left,upper_right,bottom_left,bottom_right,none}]
                             [--leak-intensity LEAK_INTENSITY] [--verbose]
                             input_file output_file

instax mini風画像＋光漏れ効果を適用するスクリプト

positional arguments:
  input_file            入力画像のファイルパス
  output_file           出力画像のファイルパス

options:
  -h, --help            show this help message and exit
  --leak-style {warm,cool,pink,burn,none,auto}, --ls {warm,cool,pink,burn,none,auto}
                        光漏れの色味プリセットを選択します。デフォルトは warm です。
  --leak-position {upper_left,upper_right,bottom_left,bottom_right,none}, --lp {upper_left,upper_right,bottom_left,bottom_right,none}
                        光漏れの位置を指定します。デフォルトは upper_right です。
  --leak-intensity LEAK_INTENSITY, --li LEAK_INTENSITY
                        光漏れの強度を指定します。範囲は 0.0 から 1.0 もしくは auto で、デフォルトは 0.5 です。
  --verbose, -v         処理状況を表示します

```


## Before / After サンプル

| 元画像 (Before) | 加工後画像 (After) |
|------------------|---------------------|
| ![Before](example/sample03_before.jpg) | ![After](example/sample03_after.jpg) |

`--leak-style` `--leak-intensity` は `auto`、`--leak-position` は `upper_right` です。