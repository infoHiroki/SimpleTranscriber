import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time

class WhisperTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("シンプル文字起こしツール")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 変数の初期化
        self.file_path = tk.StringVar()
        self.model = tk.StringVar(value="tiny")
        self.language = tk.StringVar(value="ja")
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="ファイルを選択してください")
        
        # GUIの作成
        self._create_widgets()
        
        # プロセスの状態
        self.is_processing = False
        self.process_thread = None

    def _create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ファイル選択
        file_frame = ttk.LabelFrame(main_frame, text="入力ファイル", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="参照...", command=self._browse_file).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # オプション
        options_frame = ttk.LabelFrame(main_frame, text="オプション", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # モデル選択
        ttk.Label(options_frame, text="モデル:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        model_combo = ttk.Combobox(options_frame, textvariable=self.model, 
                                  values=["tiny", "base", "small", "medium"], 
                                  state="readonly", width=10)
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 言語選択
        ttk.Label(options_frame, text="言語:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        lang_combo = ttk.Combobox(options_frame, textvariable=self.language, 
                                 values=["ja", "en", "auto"], 
                                 state="readonly", width=10)
        lang_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 説明
        models_info = ttk.Label(options_frame, text="tiny: 最速・低精度, base: 速い, small: バランス, medium: 高精度・低速")
        models_info.grid(row=1, column=0, columnspan=4, padx=5, pady=2, sticky=tk.W)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="文字起こし開始", command=self._start_transcription).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="結果を保存", command=self._save_result).pack(side=tk.RIGHT, padx=5)
        
        # プログレスバー
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # ステータス
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(status_frame, textvariable=self.status).pack(anchor=tk.W)
        
        # 結果テキストエリア
        result_frame = ttk.LabelFrame(main_frame, text="文字起こし結果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="音声/動画ファイルを選択",
            filetypes=[
                ("音声/動画ファイル", "*.mp3 *.wav *.mp4 *.avi *.mov *.ogg *.flac *.m4a"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_path:
            self.file_path.set(file_path)
    
    def _start_transcription(self):
        if self.is_processing:
            messagebox.showinfo("情報", "処理中です。しばらくお待ちください。")
            return
        
        if not self.file_path.get():
            messagebox.showerror("エラー", "ファイルを選択してください。")
            return
        
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("エラー", "選択されたファイルが存在しません。")
            return
        
        # 依存関係の確認
        try:
            import whisper_standalone_win
        except ImportError:
            # 依存関係のインストール処理
            self._update_status("必要なパッケージをインストールしています...", 5)
            
            try:
                import pip
                pip.main(['install', 'whisper-standalone-win'])
                self._update_status("パッケージのインストールが完了しました", 10)
            except Exception as e:
                messagebox.showerror("エラー", f"パッケージのインストールに失敗しました: {str(e)}")
                self._update_status("エラーが発生しました", 0)
                return
        
        # 処理開始
        self.is_processing = True
        self.progress.set(0)
        self.status.set("処理を開始します...")
        
        # 別スレッドで処理を実行
        self.process_thread = threading.Thread(target=self._run_transcription)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _run_transcription(self):
        try:
            input_file = self.file_path.get()
            
            self._update_status("モデルを準備中...", 10)
            
            # whisper-standalone-winのインポート
            import whisper_standalone_win as wsw
            
            # 進捗コールバック
            def progress_callback(percent):
                self._update_status(f"文字起こし処理中... {percent}%", 10 + percent * 0.85)
            
            # トランスクライバーの初期化（モデルは自動ダウンロード）
            transcriber = wsw.Transcriber(
                model_size=self.model.get(),
                language=self.language.get(),
                device="cpu"  # CPUでの処理を明示的に指定
            )
            
            # 文字起こし実行
            self._update_status("文字起こし処理中...", 15)
            result = transcriber.transcribe(input_file, progress_callback=progress_callback)
            
            # 結果表示
            self._update_result(result["text"])
            self._update_status("文字起こしが完了しました", 100)
            
        except Exception as e:
            self._update_status(f"エラーが発生しました: {str(e)}", 0)
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}")
        
        finally:
            self.is_processing = False
    
    def _save_result(self):
        if not self.result_text.get(1.0, tk.END).strip():
            messagebox.showinfo("情報", "保存する内容がありません。")
            return
        
        output_file = filedialog.asksaveasfilename(
            title="結果を保存",
            defaultextension=".txt",
            filetypes=[
                ("テキストファイル", "*.txt"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.get(1.0, tk.END))
                messagebox.showinfo("情報", f"結果を保存しました: {output_file}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました: {str(e)}")
    
    def _update_status(self, message, progress_value):
        def update():
            self.status.set(message)
            self.progress.set(progress_value)
        self.root.after(0, update)
    
    def _update_result(self, text):
        def update():
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, text)
        self.root.after(0, update)

def main():
    root = tk.Tk()
    app = WhisperTranscriberApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
