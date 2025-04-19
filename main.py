import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import shutil

class WhisperTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("シンプル文字起こしツール")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # アセットディレクトリの設定
        self._setup_whisper_assets()
        
        # 変数の初期化
        self.file_paths = []  # 複数ファイルのパスを保持するリスト
        self.model = tk.StringVar(value="tiny")
        self.language = tk.StringVar(value="ja")
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="ファイルを選択してください")
        self.current_file_index = 0  # 現在処理中のファイルインデックス
        
        # 出力先の設定
        self.output_dir = self._get_default_output_dir()
        
        # GUIの作成
        self._create_widgets()
        
        # プロセスの状態
        self.is_processing = False
        self.process_thread = None

    def _setup_whisper_assets(self):
        """Whisperのアセットディレクトリを設定"""
        # 実行ファイルとして実行されているか確認
        if getattr(sys, 'frozen', False):
            # PyInstallerでパッケージ化された場合
            base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            # アセットディレクトリを環境変数に設定
            os.environ["WHISPER_ASSETS_PATH"] = os.path.join(base_dir, "whisper", "assets")
            
            # アセットディレクトリが存在しない場合、一時ディレクトリを作成して移動
            assets_dir = os.environ["WHISPER_ASSETS_PATH"]
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir, exist_ok=True)
                # ここでアセットファイルを作成/コピーすることもできる
            
            # ログにパスを出力
            print(f"Whisperアセットパス: {assets_dir}")

    def _create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ファイル選択
        file_frame = ttk.LabelFrame(main_frame, text="入力ファイル", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="ファイルを追加...", command=self._browse_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="選択をクリア", command=self._clear_files).pack(side=tk.LEFT, padx=5)
        
        # ファイルリスト表示エリア
        files_list_frame = ttk.Frame(file_frame)
        files_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # スクロール可能なファイルリスト
        self.files_listbox = tk.Listbox(files_list_frame, height=4)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_scrollbar = ttk.Scrollbar(files_list_frame, command=self.files_listbox.yview)
        files_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)
        
        # オプション
        options_frame = ttk.LabelFrame(main_frame, text="オプション", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # モデル選択
        ttk.Label(options_frame, text="モデル:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        model_combo = ttk.Combobox(options_frame, textvariable=self.model, 
                                  values=["tiny", "base", "small", "medium", "large"], 
                                  state="readonly", width=10)
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 言語選択
        ttk.Label(options_frame, text="言語:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        lang_combo = ttk.Combobox(options_frame, textvariable=self.language, 
                                 values=["ja", "en", "auto"], 
                                 state="readonly", width=10)
        lang_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 説明
        models_info = ttk.Label(options_frame, text="tiny: 最速・低精度, base: 速い, small: バランス, medium: 高精度, large: 最高精度・最低速")
        models_info.grid(row=1, column=0, columnspan=4, padx=5, pady=2, sticky=tk.W)
        
        # 出力先設定
        output_frame = ttk.LabelFrame(main_frame, text="出力先", padding=5)
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.output_path_label = ttk.Label(output_path_frame, text=self.output_dir, width=50)
        self.output_path_label.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(output_path_frame, text="変更...", command=self._browse_output_dir).pack(side=tk.RIGHT, padx=5, pady=5)
        
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
    
    def _browse_files(self):
        """複数のファイルを選択するダイアログを表示"""
        file_paths = filedialog.askopenfilenames(
            title="音声/動画ファイルを選択",
            filetypes=[
                ("音声/動画ファイル", "*.mp3 *.wav *.mp4 *.avi *.mov *.ogg *.flac *.m4a"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_paths:
            # 既存のリストに追加
            for path in file_paths:
                if path not in self.file_paths:
                    self.file_paths.append(path)
                    self.files_listbox.insert(tk.END, os.path.basename(path))
            
            # ステータス更新
            if len(self.file_paths) == 1:
                self.status.set("1つのファイルが選択されています")
            else:
                self.status.set(f"{len(self.file_paths)}つのファイルが選択されています")
    
    def _clear_files(self):
        """選択されたファイルリストをクリア"""
        self.file_paths = []
        self.files_listbox.delete(0, tk.END)
        self.status.set("ファイルを選択してください")
    
    def _start_transcription(self):
        if self.is_processing:
            messagebox.showinfo("情報", "処理中です。しばらくお待ちください。")
            return
        
        if not self.file_paths:
            messagebox.showerror("エラー", "ファイルを選択してください。")
            return
        
        # 選択されたファイルの存在確認
        missing_files = [f for f in self.file_paths if not os.path.exists(f)]
        if missing_files:
            missing_files_str = "\n".join([os.path.basename(f) for f in missing_files])
            messagebox.showerror("エラー", f"以下のファイルが見つかりません:\n{missing_files_str}")
            return
        
        # 依存関係の確認
        try:
            import whisper
        except ImportError:
            # 依存関係のインストール処理
            self._update_status("必要なパッケージをインストールしています...", 5)
            
            try:
                import pip
                pip.main(['install', 'openai-whisper'])
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
            # 初期設定
            self.current_file_index = 0
            total_files = len(self.file_paths)
            all_results = []
            
            # モデルの準備
            self._update_status("モデルを準備中...", 10)
            
            # OpenAI Whisperのインポート
            try:
                # Whisperパッケージのロードを試行
                import whisper
                
                # モデルのロード
                model_name = self.model.get()
                language = self.language.get()
                
                # 言語が自動検出の場合は None を指定
                if language == "auto":
                    language = None
                
                # モデルを直接指定してロードする前に、正しいロード方法を試す
                try:
                    # モデルの読み込み（初回は自動ダウンロード）
                    self._update_status(f"モデル {model_name} を準備中... （初回実行時はダウンロードが必要です）", 10)
                    model = whisper.load_model(model_name)
                except Exception as model_error:
                    self._update_status(f"モデルの読み込みに失敗しました: {str(model_error)}", 0)
                    messagebox.showerror("エラー", f"モデルの読み込みに失敗しました: {str(model_error)}\n\n初回実行時はインターネット接続が必要です。")
                    return
                
                # 文字起こし結果のテキスト
                combined_text = ""
                
                # 各ファイルを順番に処理
                for i, file_path in enumerate(self.file_paths):
                    self.current_file_index = i
                    file_name = os.path.basename(file_path)
                    
                    # ファイルごとの進捗の計算
                    # 全体の10%をモデルの準備に使用し、残りの90%をファイル処理に均等に分配
                    file_progress_base = 10 + (i / total_files) * 90
                    file_progress_range = 90 / total_files
                    
                    # ファイル処理開始
                    self._update_status(f"ファイル {i+1}/{total_files} を処理中: {file_name}", 
                                      file_progress_base)
                    
                    # 実際の処理実行
                    try:
                        result = model.transcribe(file_path, language=language)
                        
                        # 結果をリストに追加
                        all_results.append({
                            "file": file_name,
                            "text": result["text"]
                        })
                        
                        # 自動保存
                        save_success = self._save_file_result(file_name, result["text"])
                        if save_success:
                            save_status = "（保存済み）"
                        else:
                            save_status = "（保存失敗）"
                        
                        # テキストを結合（ファイル名をヘッダーとして追加）
                        combined_text += f"# {file_name} {save_status}\n\n{result['text']}\n\n"
                        
                        # ファイル処理完了
                        self._update_status(f"ファイル {i+1}/{total_files} の処理が完了しました", 
                                          file_progress_base + file_progress_range * 0.9)
                    except Exception as file_error:
                        self._update_status(f"ファイル {file_name} の処理中にエラーが発生しました: {str(file_error)}", 
                                          file_progress_base)
                        combined_text += f"# {file_name} （エラー）\n\n処理中にエラーが発生しました: {str(file_error)}\n\n"
                
                # 全ての結果を表示
                self._update_result(combined_text)
                
                # 保存成功の数を計算
                saved_count = sum(1 for r in all_results if r.get("saved", False))
                self._update_status(f"{total_files}個のファイルの文字起こしが完了しました（{saved_count}個保存）", 100)
            
            except Exception as whisper_error:
                self._update_status(f"Whisperの初期化に失敗しました: {str(whisper_error)}", 0)
                messagebox.showerror("エラー", f"Whisperの初期化に失敗しました: {str(whisper_error)}")
                
        except Exception as e:
            self._update_status(f"エラーが発生しました: {str(e)}", 0)
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}")
        
        finally:
            self.is_processing = False
    
    def _get_default_output_dir(self):
        """デフォルトの出力ディレクトリ（デスクトップの文字起こし結果フォルダ）を取得"""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        output_dir = os.path.join(desktop_path, "文字起こし結果")
        return output_dir
    
    def _ensure_output_dir_exists(self):
        """出力ディレクトリが存在しない場合は作成する"""
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                messagebox.showerror("エラー", f"出力フォルダの作成に失敗しました: {str(e)}")
                return False
        return True
                
    def _browse_output_dir(self):
        """出力ディレクトリを選択するダイアログを表示"""
        dir_path = filedialog.askdirectory(
            title="文字起こし結果の保存先を選択",
            initialdir=self.output_dir
        )
        if dir_path:
            self.output_dir = dir_path
            self.output_path_label.config(text=self.output_dir)
    
    def _save_result(self):
        """全体の結果を手動保存"""
        if not self.result_text.get(1.0, tk.END).strip():
            messagebox.showinfo("情報", "保存する内容がありません。")
            return
        
        # 出力ディレクトリが存在することを確認
        if not self._ensure_output_dir_exists():
            return
        
        output_file = filedialog.asksaveasfilename(
            title="結果を保存",
            initialdir=self.output_dir,
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
    
    def _save_file_result(self, file_name, text):
        """個別のファイル結果を自動保存"""
        if not self._ensure_output_dir_exists():
            return False
        
        # 元のファイル名から拡張子を除去し、.txtを追加
        base_name = os.path.splitext(file_name)[0]
        output_file = os.path.join(self.output_dir, f"{base_name}.txt")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル {file_name} の保存中にエラーが発生しました: {str(e)}")
            return False
    
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
