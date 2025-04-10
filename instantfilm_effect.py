import argparse
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter, ImageChops
import numpy as np



def create_instax_frame(image, scale=10):
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

    # --- 画像の縦横比取得 ---
    img_width, img_height = image.size
    if verbose_output:
        print(f"元画像サイズ: {img_width}x{img_height} ピクセル")

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

def estimate_leak_intensity(image):
    """
    入力画像の全体の明るさに基づいて、光漏れ強度（intensity）を自動設定します。
    
    :param image: PIL.Image オブジェクト
    :return: 推定された強度（float, 0.0〜1.0）
    """
    if verbose_output: print("画像の平均輝度から光漏れ強度を推定します")

    image = image.convert("RGB")
    np_image = np.array(image)

    # 輝度 = RGB平均でざっくりと定義
    brightness = np.mean(np_image, axis=2)
    avg_brightness = np.mean(brightness)

    if verbose_output:
        print(f"画像の平均輝度: {avg_brightness:.2f}")

    # 明るさに応じて intensity を調整（必要ならカスタム可能）
    if avg_brightness < 100:
        if verbose_output: print("判定：暗い")
        return 0.6  # 暗い
    elif avg_brightness < 180:
        if verbose_output: print("判定：中間")
        return 0.5  # 中間
    else:
        if verbose_output: print("判定：明るい")
        return 0.3  # 明るい

def estimate_light_color(image, brightness_threshold=200):
    """
    入力画像の明るいピクセルから平均色（光漏れに使えそうな色）を推定します。

    :param image: PILのImageオブジェクト
    :param brightness_threshold: 明るさの閾値（RGBの平均値）
    :return: 推定された光漏れカラー (R, G, B)
    """
    if verbose_output: print(f"光源色の推定を行います")
    image = image.convert("RGB")
    np_image = np.array(image)

    # RGBの平均 = 明るさの近似値とする
    brightness = np.mean(np_image, axis=2)

    # 明るいピクセルを抽出
    mask = brightness > brightness_threshold
    bright_pixels = np_image[mask]

    if bright_pixels.size == 0:
        # 明るいピクセルがなかった場合は白に近い色にする
        return (255, 255, 255)

    # 明るいピクセルの平均色を計算
    avg_color = np.mean(bright_pixels, axis=0).astype(int)
    if verbose_output: print(f"光源色推定: {avg_color}")
    return tuple(avg_color)



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
    if verbose_output:
        print(f"枠画像サイズ: {width}x{height} ピクセル")

    # --- 光漏れ用のレイヤー作成 ---
    # 元サイズと同じ黒背景のキャンバス
    leak_layer = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(leak_layer)

    # --- 光漏れの位置と形状の決定 ---
    # ここでは楕円形で光漏れ効果を再現
    if verbose_output:
        print(f"光漏れ位置: {leak_position}")
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

def parse_argument():
    # 引数のパース設定
    parser = argparse.ArgumentParser(
        description="instax mini風画像＋光漏れ効果を適用するスクリプト"
    )
    parser.add_argument("input_file", help="入力画像のファイルパス")
    parser.add_argument("output_file", help="出力画像のファイルパス")
    parser.add_argument("--leak-style", "--ls",
        choices=const_leak_style.keys(),
        default="warm",
        help="光漏れの色味プリセットを選択します。デフォルトは warm です。")
    parser.add_argument(
        "--leak-position",
        "--lp",
        choices=["upper_left", "upper_right", "bottom_left", "bottom_right", "none"],
        default="upper_right",
        help="光漏れの位置を指定します。デフォルトは upper_right です。",
    )
    parser.add_argument(
        "--leak-intensity",
        "--li",
        default=0.5,
        help="光漏れの強度を指定します。範囲は 0.0 から 1.0 もしくは auto で、デフォルトは 0.5 です。"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="処理状況を表示します"
    )
    return parser.parse_args()
    



def main():
    """
    コマンドライン引数から入力ファイルと出力ファイルのパスを受け取り、
    instax mini風の余白枠と光漏れ効果を適用した画像を生成する。
    """
    global verbose_output
    global const_leak_style
    
    # 光漏れのスタイル定義
    const_leak_style = {
        "warm": (255, 180, 100),
        "cool": (100, 180, 255),
        "pink": (255, 150, 200),
        "burn": (255, 60, 60),
        "none": None,
        "auto": "auto",
    }
    
    # 引数のパース
    args = parse_argument()

    # 冗長出力設定をグローバル変数に格納
    verbose_output = args.verbose



    # --- 画像の読み込み ---
    try:
        image = Image.open(args.input_file)
    except FileNotFoundError:
        print(f"Error: 入力ファイルが見つかりません: {args.input_file}")
        exit(1)
    except Exception as e:
        print(f"Error: 入力画像の読み込みに失敗しました: {e}")
        exit(1)

    # 光漏れ強度設定
    leak_intensity = args.leak_intensity
    if leak_intensity == "auto": leak_intensity = estimate_leak_intensity(image)
    # 光漏れ強度範囲チェック
    if (leak_intensity > 1.0 or leak_intensity < 0.0):
        print(f"Error: Out of bound for leak-intensity: {leak_intensity}")
        exit(1)
        
    # 光漏れ処理
    style = args.leak_style
    if const_leak_style[style] == "auto":
        leak_color = estimate_light_color(image)
    elif const_leak_style[style] is None:
        leak_color = None  # 光漏れスキップ
    else:
        leak_color = const_leak_style[style]

    # instax mini風の枠画像を生成
    instax_image = create_instax_frame(image, scale=10)

    # 光漏れ効果を追加
    if leak_color is None or args.leak_position == "none":
        final_image = instax_image
    else:
        final_image = add_light_leak_effect(
            instax_image,
            leak_color=leak_color,
            intensity=leak_intensity,  # 効果の強さ（0.0～1.0）
            leak_position=args.leak_position,  # 光漏れの位置（引数で指定）
        )

    # 出力画像として指定されたファイルパスに保存
    final_image.save(args.output_file)
    if verbose_output: print(f"画像を保存しました: {args.output_file}")


if __name__ == "__main__":
    main()
    exit(0)
