import os
import sys
import subprocess
import shutil
import site

def main():
    print("シンプル文字起こしツールのビルドを開始します...")
    
    # 必要なパッケージの確認
    try:
        import pyinstaller
    except ImportError:
        print("PyInstallerがインストールされていません。インストールします...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import whisper
    except ImportError:
        print("openai-whisperがインストールされていません。インストールします...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
    
    # ビルドディレクトリの確認とクリーン
    if os.path.exists("build"):
        print("古いビルドディレクトリを削除します...")
        shutil.rmtree("build", ignore_errors=True)
    
    if os.path.exists("dist"):
        print("古い配布ディレクトリを削除します...")
        shutil.rmtree("dist", ignore_errors=True)
    
    # Whisperのアセットパスを取得
    import whisper
    whisper_package_dir = os.path.dirname(whisper.__file__)
    whisper_assets_dir = os.path.join(whisper_package_dir, "assets")
    
    # アセットディレクトリ内のファイル一覧を表示（デバッグ用）
    print(f"Whisperアセットディレクトリ: {whisper_assets_dir}")
    if os.path.exists(whisper_assets_dir):
        print("アセットファイル一覧:")
        for file in os.listdir(whisper_assets_dir):
            print(f" - {file}")
    else:
        print("アセットディレクトリが見つかりません")
    
    # WindowsとLinux/Macでパス区切り文字を調整
    path_separator = ";" if sys.platform == "win32" else ":"
    
    # PyInstallerコマンドの構築
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",  # 単一の実行ファイルとして生成
        "--windowed",  # コンソールウィンドウを表示しない
        "--clean",     # 一時ファイルをクリーン
        "--name=SimpleTranscriber",  # 出力ファイル名
        # Whisperのアセットファイルを追加（パス区切り文字を環境に合わせる）
        f"--add-data={whisper_assets_dir}{path_separator}whisper/assets",
        "--collect-submodules=whisper",  # Whisperの全サブモジュールを含める
        "--hidden-import=scipy",  # 必要な依存関係を明示的に含める
        "--hidden-import=numpy",
        "--hidden-import=ffmpeg",
        "--hidden-import=whisper",
        "main.py"  # メインスクリプト
    ]
    
    # ビルドの実行
    print("ビルドを実行中...")
    subprocess.check_call(pyinstaller_cmd)
    
    print("ビルドが完了しました！")
    print(f"実行ファイルは dist/SimpleTranscriber{'.exe' if sys.platform == 'win32' else ''} にあります")

if __name__ == "__main__":
    main()