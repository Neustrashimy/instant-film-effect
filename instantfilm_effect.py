import argparse
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter, ImageChops

verbose_output = False

def create_instax_frame(input_path, scale=10):
    """
    入力画像の中央部を「横46mm×縦62mm」のアスペクト比でクロップし、
    「横54mm×縦86mm」のinstax mini風の枠内に（上寄せで）配置した画像を作成する関数。

    :param input_path: 入力画像のファイルパス
    :param scale: mmからピクセルへの変換係数。例：scale=10なら1mm=10ピクセル
    :return: instax mini風に加工されたImageオブジェクト
    """
    # --- 各サイズ（mm単位） ---
    inner_width_mm = 46  # クロップした画像の幅
    inner_height_mm = 62  # クロップした画像の高さ
    frame_width_mm = 54  # 全体の枠の幅
    frame_height_mm = 86  # 全体の枠の高さ

    # mm -> ピクセル変換
    inner_width_px = inner_width_mm * scale  # 例: 46mm -> 460px
    inner_height_px = inner_height_mm * scale  # 62mm -> 620px
    frame_width_px = frame_width_mm * scale  # 54mm -> 540px
    frame_height_px = frame_height_mm * scale  # 86mm -> 860px

    # --- 画像の読み込み ---
    image = Image.open(input_path)
    img_width, img_height = image.size
    if verbose_output: print(f"元画像サイズ: {img_width}x{img_height} ピクセル")

    # --- 画像の中央クロップ ---
    # 目標のアスペクト比
    target_ratio = inner_width_mm / inner_height_mm
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        # 横長の場合は画像の高さをフルに使い、その高さに合う幅を求める
        new_height = img_height
        new_width = int(img_height * target_ratio)
    else:
        # 縦長の場合は画像の幅をフルに使い、その幅に合う高さを求める
        new_width = img_width
        new_height = int(img_width / target_ratio)

    # 中央を基準にクロップ領域を設定
    left = (img_width - new_width) // 2
    top = (img_height - new_height) // 2
    right = left + new_width
    bottom = top + new_height

    cropped_img = image.crop((left, top, right, bottom))

    # --- クロップした画像をinstax mini用の内側サイズにリサイズ ---
    resized_cropped = cropped_img.resize(
        (inner_width_px, inner_height_px), Image.LANCZOS
    )

    # --- instax mini風の枠を作成 ---
    # 枠は白いキャンバスを作成し、上部にリサイズ済みクロップ画像を貼り付け（下部に厚い余白ができる）
    framed_image = Image.new("RGB", (frame_width_px, frame_height_px), "white")
    paste_x = (frame_width_px - inner_width_px) // 2  # 水平方向の中央
    paste_y = 70  # 上端に貼り付け
    framed_image.paste(resized_cropped, (paste_x, paste_y))

    return framed_image


def add_light_leak_effect(
    image, leak_color=(255, 200, 0), intensity=0.5, leak_position="upper_right"
):
    """
    与えられたPillowのImageオブジェクトに光漏れ風エフェクトを付与する関数

    :param image: インスタントフィルム風の画像 (Pillow Imageオブジェクト)
    :param leak_color: 光漏れ効果に使用する色 (R, G, B)
    :param intensity: 光漏れ効果の強さ (0.0〜1.0、1.0に近いほど強め)
    :param leak_position: "upper_right", "upper_left", "bottom_right", "bottom_left" から選択
    :return: 光漏れ効果を適用したImageオブジェクト
    """
    width, height = image.size
    if verbose_output: print(f"枠画像サイズ: {width}x{height} ピクセル")

    # --- 光漏れ用のレイヤー作成 ---
    # 元サイズと同じ黒背景のキャンバス
    leak_layer = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(leak_layer)

    # --- 光漏れの位置と形状の決定 ---
    # ここでは楕円形で光漏れ効果を再現
    if verbose_output: print(f"光漏れ位置: {leak_position}")
    if leak_position == "upper_right":
        ellipse_box = [int(width * 0.6), 0, width, int(height * 0.5)]
    elif leak_position == "upper_left":
        ellipse_box = [0, 0, int(width * 0.4), int(height * 0.5)]
    elif leak_position == "bottom_right":
        ellipse_box = [int(width * 0.6), int(height * 0.5), width, height]
    elif leak_position == "bottom_left":
        ellipse_box = [0, int(height * 0.5), int(width * 0.4), height]
    else:
        ellipse_box = [int(width * 0.6), 0, width, int(height * 0.5)]

    # 楕円形で光漏れ部分を描画
    draw.ellipse(ellipse_box, fill=leak_color)

    # --- 自然な感じにするためにぼかしを適用 ---
    blur_radius = int(width * 0.1)  # 画像サイズに対するぼかし半径（調整可能）
    leak_layer = leak_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # --- 光漏れ効果の合成 ---
    # ImageChops.screenにより、明るい部分が強調される演出
    combined = ImageChops.screen(image, leak_layer)
    # intensityで元画像とのブレンド率を調整
    result = Image.blend(image, combined, intensity)

    return result


def main():
    """
    コマンドライン引数から入力ファイルと出力ファイルのパスを受け取り、
    instax mini風の余白枠と光漏れ効果を適用した画像を生成する。
    """
    # 引数のパース設定
    parser = argparse.ArgumentParser(
        description="instax mini風画像＋光漏れ効果を適用するスクリプト"
    )
    parser.add_argument("input_file", help="入力画像のファイルパス（例: input.jpg）")
    parser.add_argument("output_file", help="出力画像のファイルパス（例: output.jpg）")
    parser.add_argument('--leak-position', '--lp',
                    choices=['upper_left', 'upper_right', 'bottom_left', 'bottom_right'],
                    default='upper_right',
                    help='光漏れの位置を指定します。デフォルトは upper_right です。')
    parser.add_argument('--verbose', '-v', action="store_true", help="処理状況を表示します")

    args = parser.parse_args()

    # 冗長出力設定をグローバル変数に格納
    verbose_output = args.verbose

    # instax mini風の枠画像を生成
    instax_image = create_instax_frame(args.input_file, scale=10)

    # 光漏れ効果を追加
    final_image = add_light_leak_effect(
        instax_image,
        leak_color=(255, 200, 0),  # 温かいオレンジ色
        intensity=0.5,  # 効果の強さ（0.0～1.0）
        leak_position=args.leak_position,  # 光漏れの位置（引数で指定）
    )

    # 出力画像として指定されたファイルパスに保存
    final_image.save(args.output_file)
    if verbose_output: print(f"画像を保存しました: {args.output_file}")


if __name__ == "__main__":
    main()
