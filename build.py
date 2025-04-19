import os
import sys
import subprocess
import shutil

def main():
    print("シンプル文字起こしツールのビルドを開始します...")
    
    # 必要なパッケージの確認
    try:
        import pyinstaller
    except ImportError:
        print("PyInstallerがインストールされていません。インストールします...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import whisper_standalone_win
    except ImportError:
        print("whisper-standalone-winがインストールされていません。インストールします...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "whisper-standalone-win"])
    
    # ビルドディレクトリの確認とクリーン
    if os.path.exists("build"):
        print("古いビルドディレクトリを削除します...")
        shutil.rmtree("build", ignore_errors=True)
    
    if os.path.exists("dist"):
        print("古い配布ディレクトリを削除します...")
        shutil.rmtree("dist", ignore_errors=True)
    
    # PyInstallerコマンドの構築
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",  # 単一の実行ファイルとして生成
        "--windowed",  # コンソールウィンドウを表示しない
        "--clean",     # 一時ファイルをクリーン
        "--name=SimpleTranscriber",  # 出力ファイル名
        # 追加のデータファイルが必要な場合はここに記述
        "transcriber_app.py"  # メインスクリプト
    ]
    
    # ビルドの実行
    print("ビルドを実行中...")
    subprocess.check_call(pyinstaller_cmd)
    
    print("ビルドが完了しました！")
    print(f"実行ファイルは dist/SimpleTranscriber{'.exe' if sys.platform == 'win32' else ''} にあります")

if __name__ == "__main__":
    main()
