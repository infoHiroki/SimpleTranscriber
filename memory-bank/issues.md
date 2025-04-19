# 既知の問題と課題

## 実行時エラー

### 2025年4月20日に発生したエラー
アプリケーションをビルドして実行したところ、以下のエラーが発生しました：

```
エラーが発生しました: [Errno 2] No such file or directory: 'C:\Users\xxxhi\AppData\Local\Temp\_MEI184042\whisper\assets\mel_filters.npz'
```

このエラーはWhisperライブラリが必要とするアセットファイル（mel_filters.npz）を見つけられないことを示しています。

### 考えられる原因
1. PyInstallerによるパッケージング時にWhisperの必要なアセットファイルが含まれなかった
2. 実行時にWhisperアセットを正しいパスで見つけられない
3. アプリケーションが一時ディレクトリにアクセスする権限がない可能性

### 対応策
以下の方法でエラーを解決できる可能性があります：

1. **アセットファイルを明示的にパッケージに含める**
   - PyInstallerの`--add-data`オプションを使用してWhisperのアセットファイルを明示的に含める
   ```python
   # build.pyの修正例
   pyinstaller_cmd = [
       "pyinstaller",
       "--onefile",
       "--windowed",
       "--clean",
       "--name=SimpleTranscriber",
       # Whisperアセットを明示的に追加
       "--add-data=C:\\Users\\{ユーザー名}\\AppData\\Local\\Programs\\Python\\Python{バージョン}\\Lib\\site-packages\\whisper\\assets;whisper\\assets",
       "main.py"
   ]
   ```

2. **アセットのパスを動的に設定**
   - Whisperライブラリが使用するパスを動的に設定するコードを追加

3. **必要なファイルを手動でコピー**
   - ビルド後、必要なアセットファイルを手動でdistディレクトリにコピー

4. **FFmpegの確認**
   - FFmpegが正しくインストールされ、PATHに設定されているか確認

### 修正対応済み（2025年4月20日）
以下の修正を行いました：

1. **main.pyの修正**
   - 起動時にWhisperアセットを適切に設定する`_setup_whisper_assets`メソッドを追加
   - PyInstaller実行環境検出のためのコードを追加（`sys._MEIPASS`の活用）
   - エラーハンドリングの強化（各処理ステップでのtry-exceptブロックの追加）
   - 詳細なエラーメッセージの表示

2. **build.pyの修正**
   - `--hidden-import`オプションで必要なライブラリ（scipy, numpy, ffmpeg, whisper）を明示的に指定
   - `--collect-submodules=whisper`オプションでWhisperの全サブモジュールを含める設定
   - アセットファイル一覧の表示によるデバッグ情報の追加
   - OSごとのパス区切り文字の適切な設定

### 次のステップ
- 修正後のビルドを実行し、エラーが解消されたか確認
- 各モデルサイズでの動作確認
- 複数ファイル処理の安定性確認

### 備考
- ビルド後のアプリケーションはWhisperのダウンロード機能を持っているが、パッケージ化されたアプリケーションの場合はアセットファイルへのパスが異なる可能性がある
- Pythonバージョンによって、サイトパッケージの場所が異なる場合がある
