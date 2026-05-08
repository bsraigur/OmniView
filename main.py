import sys
import os
import shutil
# pip install PyQt6==6.6.1 PyQt6-Qt6==6.6.1
# FORCE X11/XCB TO FIX UBUNTU WAYLAND BLACK SCREEN BUG
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QGridLayout, QLabel, 
                             QInputDialog, QMessageBox, QSizePolicy, QSlider,
                             QDialog, QRadioButton, QLineEdit, QDialogButtonBox, 
                             QSpinBox, QFormLayout, QGroupBox, QCheckBox, 
                             QComboBox)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer

class SaveDialog(QDialog):
    # ... (SaveDialog remains exactly the same as before) ...
    def __init__(self, sample_filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.resize(400, 320)
        
        layout = QVBoxLayout(self)
        
        self.radio_default = QRadioButton("Default Save (to '_save_' folder)")
        self.radio_default.setChecked(True)
        self.radio_pattern = QRadioButton("Pattern Save (Extract folder from filename)")
        
        layout.addWidget(self.radio_default)
        layout.addWidget(self.radio_pattern)
        
        self.pattern_group = QGroupBox("Pattern Settings")
        form_layout = QFormLayout(self.pattern_group)
        
        self.lbl_sample = QLabel(f"<b>File:</b> {sample_filename}")
        form_layout.addRow(self.lbl_sample)
        
        self.separator_input = QLineEdit("_")
        self.separator_input.setPlaceholderText("e.g. _ or -")
        
        self.part_input = QSpinBox()
        self.part_input.setMinimum(1)
        self.part_input.setValue(1) 
        
        self.extraction_mode = QComboBox()
        self.extraction_mode.addItems(["Single Part Only (e.g., word 2)", "Cumulative (e.g., up to word 2)"])
        
        self.lbl_preview = QLabel("Folder: <b>-</b>")
        
        form_layout.addRow("Separator:", self.separator_input)
        form_layout.addRow("Part to use:", self.part_input)
        form_layout.addRow("Mode:", self.extraction_mode)
        form_layout.addRow("Preview:", self.lbl_preview)
        
        layout.addWidget(self.pattern_group)
        self.pattern_group.setEnabled(False) 
        
        self.chk_remember = QCheckBox("Remember my choice for all future videos")
        self.chk_remember.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.chk_remember)

        self.radio_pattern.toggled.connect(self.pattern_group.setEnabled)
        self.separator_input.textChanged.connect(self.update_preview)
        self.part_input.valueChanged.connect(self.update_preview)
        self.extraction_mode.currentIndexChanged.connect(self.update_preview)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.sample_filename = sample_filename
        self.update_preview()

    def update_preview(self):
        sep = self.separator_input.text()
        part_idx = self.part_input.value() - 1 
        name_only = os.path.splitext(self.sample_filename)[0]
        mode = self.extraction_mode.currentIndex() 
        
        if sep and sep in name_only:
            parts = name_only.split(sep)
            if 0 <= part_idx < len(parts):
                if mode == 0:
                    preview_text = parts[part_idx]
                else:
                    preview_text = sep.join(parts[:part_idx + 1]) 
                    
                self.lbl_preview.setText(f"Folder: <b style='color:green;'>{preview_text}</b>")
            else:
                self.lbl_preview.setText("Folder: <b style='color:red;'>[Index out of range]</b>")
        else:
            self.lbl_preview.setText(f"Folder: <b>{name_only}</b> (Separator not found)")

    def get_save_mode(self):
        settings = {"remember": self.chk_remember.isChecked()}
        
        if self.radio_default.isChecked():
            settings.update({"mode": "default"})
        else:
            settings.update({
                "mode": "pattern",
                "separator": self.separator_input.text(),
                "part": self.part_input.value() - 1,
                "cumulative": self.extraction_mode.currentIndex() == 1
            })
        return settings


class VideoPlayerCard(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window 
        self.current_file = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # PyQt6 Media Player Setup
        self.mediaPlayer = QMediaPlayer()
        self.audioOutput = QAudioOutput() 
        self.mediaPlayer.setAudioOutput(self.audioOutput)
        
        self.videoWidget = QVideoWidget()
        # FIX: Changed to Expanding so the video actually takes up space and renders
        self.videoWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        
        self.mediaPlayer.mediaStatusChanged.connect(self.status_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        
        # ADDED ERROR HANDLING TO SEE WHY IT FAILS
        self.mediaPlayer.errorOccurred.connect(self.handle_error)

        # UI Elements
        self.label = QLabel("No video loaded")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; padding: 5px;")

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus) 

        # Buttons
        self.btn_backward = QPushButton("⏪ -3s")
        self.btn_play_pause = QPushButton("⏸️ Pause")
        self.btn_forward = QPushButton("+3s ⏩")
        
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setStyleSheet("background-color: #d4edda; color: #155724;") 
        self.btn_replay = QPushButton("🔄 Replay")
        self.btn_next = QPushButton("⏭️ Next")
        self.btn_delete = QPushButton("🗑️ Trash") 
        self.btn_delete.setStyleSheet("background-color: #ffcccc; color: red;")

        for btn in [self.btn_backward, self.btn_play_pause, self.btn_forward, 
                    self.btn_save, self.btn_replay, self.btn_next, self.btn_delete]:
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_backward.clicked.connect(lambda: self.seek_relative(-3000))
        self.btn_forward.clicked.connect(lambda: self.seek_relative(3000))
        self.btn_save.clicked.connect(self.save_video)
        self.btn_replay.clicked.connect(self.replay)
        self.btn_next.clicked.connect(self.load_next)
        self.btn_delete.clicked.connect(self.delete_video)

        # Layout
        controls_layout_1 = QHBoxLayout()
        controls_layout_1.addWidget(self.btn_backward)
        controls_layout_1.addWidget(self.btn_play_pause)
        controls_layout_1.addWidget(self.btn_forward)

        controls_layout_2 = QHBoxLayout()
        controls_layout_2.addWidget(self.btn_save)
        controls_layout_2.addWidget(self.btn_replay)
        controls_layout_2.addWidget(self.btn_next)
        controls_layout_2.addWidget(self.btn_delete)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.videoWidget, stretch=1)
        main_layout.addWidget(self.position_slider) 
        main_layout.addLayout(controls_layout_1)
        main_layout.addLayout(controls_layout_2)
        
        self.setLayout(main_layout)

    def handle_error(self, error, error_string):
        print(f"\n[MEDIA ERROR] File: {self.current_file}")
        print(f"[MEDIA ERROR] Details: {error_string}\n")
        self.label.setText(f"❌ ERROR: Cannot play file")
        self.label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f8d7da; color: #721c24;")

    def position_changed(self, position):
        self.position_slider.setValue(position)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def load_next(self):
        if self.main_window.master_queue:
            self.current_file = self.main_window.master_queue.pop(0)
            
            # Load the source
            self.mediaPlayer.setSource(QUrl.fromLocalFile(self.current_file))
            
            self.label.setText(f"▶️ {os.path.basename(self.current_file)}")
            self.label.setStyleSheet("font-weight: bold; padding: 5px; color: black; background-color: none;")
            
            # FIX: Adding a tiny delay allows PyQt6 to mount the file to the OS decoder before playing
            QTimer.singleShot(100, self._start_playback)
            
        else:
            self.mediaPlayer.stop()
            self.label.setText("Queue Empty")
            self.label.setStyleSheet("font-weight: bold; padding: 5px; color: gray; background-color: none;")
            self.current_file = None
            self.btn_play_pause.setText("▶️ Play")
            self.position_slider.setValue(0) 
        
        self.main_window.update_title()

    def _start_playback(self):
        self.mediaPlayer.play()
        self.mediaPlayer.setPlaybackRate(self.main_window.current_speed)
        self.btn_play_pause.setText("⏸️ Pause")

    def toggle_play(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
            self.btn_play_pause.setText("▶️ Play")
        else:
            self.mediaPlayer.play()
            self.btn_play_pause.setText("⏸️ Pause")

    def seek_relative(self, ms):
        if self.current_file:
            new_position = max(0, self.mediaPlayer.position() + ms)
            self.mediaPlayer.setPosition(new_position)

    def save_video(self):
        if self.current_file and os.path.exists(self.current_file):
            filename = os.path.basename(self.current_file)
            settings = None
            
            if self.main_window.saved_save_mode:
                settings = self.main_window.saved_save_mode
            else:
                dialog = SaveDialog(filename, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    settings = dialog.get_save_mode()
                    if settings.get("remember"):
                        self.main_window.saved_save_mode = settings
                else:
                    return

            folder_name = "_save_"
            if settings["mode"] == "pattern":
                name_only = os.path.splitext(filename)[0]
                sep = settings["separator"]
                part_idx = settings["part"]
                is_cumulative = settings.get("cumulative", False)
                
                if sep and sep in name_only:
                    parts = name_only.split(sep)
                    if 0 <= part_idx < len(parts):
                        if is_cumulative:
                            folder_name = sep.join(parts[:part_idx + 1])
                        else:
                            folder_name = parts[part_idx]
                    else:
                        folder_name = name_only 
                else:
                    folder_name = name_only
            
            self.mediaPlayer.stop()
            self.mediaPlayer.setSource(QUrl()) 
            
            try:
                current_dir = os.path.dirname(self.current_file)
                save_dir = os.path.join(current_dir, folder_name)
                os.makedirs(save_dir, exist_ok=True) 
                dest_path = os.path.join(save_dir, filename)
                
                shutil.move(self.current_file, dest_path)
                print(f"Saved to: {dest_path}")
                
                self.load_next() 
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not move file.\n{e}")

    def replay(self):
        if self.current_file:
            self.mediaPlayer.setPosition(0)
            self.mediaPlayer.play()
            self.mediaPlayer.setPlaybackRate(self.main_window.current_speed)
            self.btn_play_pause.setText("⏸️ Pause")
            self.label.setText(f"▶️ {os.path.basename(self.current_file)}")
            self.label.setStyleSheet("font-weight: bold; padding: 5px; color: black; background-color: none;")

    def status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.btn_play_pause.setText("▶️ Play")
            if self.current_file:
                self.label.setText(f"✅ FINISHED: {os.path.basename(self.current_file)}")
                self.label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #c3e6cb; color: #155724; border-radius: 3px;")

    def delete_video(self):
        if self.current_file and os.path.exists(self.current_file):
            file_to_move = self.current_file
            self.mediaPlayer.stop()
            self.mediaPlayer.setSource(QUrl()) 
            try:
                current_dir = os.path.dirname(file_to_move)
                delete_dir = os.path.join(current_dir, "_delete_")
                os.makedirs(delete_dir, exist_ok=True)
                filename = os.path.basename(file_to_move)
                dest_path = os.path.join(delete_dir, filename)
                shutil.move(file_to_move, dest_path)
                print(f"Moved to: {dest_path}")
                self.load_next() 
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not move file.\n{e}")

class MultiVideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.current_speed = 1.0  
        self.master_queue = []  
        self.total_video_count = 0 
        self.saved_save_mode = None 
        
        self.resize(1200, 800)
        self.players = [] 
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 
        self.setup_ui()

    def update_title(self):
        active_screens = sum(1 for p in self.players if p.current_file is not None)
        queued = len(self.master_queue)
        title_string = (f"Tri-Netra | Speed: {int(self.current_speed)}x | "
                        f"Total Found: {self.total_video_count} | "
                        f"Currently Viewing: {active_screens} | "
                        f"Remaining in Queue: {queued}")
        self.setWindowTitle(title_string)

    def setup_ui(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if not folder_path:
            sys.exit()

        valid_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv')
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path) and f.lower().endswith(valid_extensions):
                self.master_queue.append(full_path) 
        
        self.total_video_count = len(self.master_queue)

        if not self.master_queue:
            QMessageBox.information(self, "No Videos", "No video files found in that folder.")
            sys.exit()

        num_players, ok = QInputDialog.getInt(self, "Number of Screens", 
                                              "How many videos at a time? (1-10):", 
                                              4, 1, 10, 1)
        if not ok:
            sys.exit()

        grid_layout = QGridLayout()
        self.setLayout(grid_layout)

        cols = 2 if num_players <= 4 else 3 if num_players <= 6 else 4
        num_rows = (num_players + cols - 1) // cols
        
        for col in range(cols):
            grid_layout.setColumnStretch(col, 1)
        for row in range(num_rows):
            grid_layout.setRowStretch(row, 1)

        for i in range(num_players):
            row = i // cols
            col = i % cols
            
            player = VideoPlayerCard(self)
            self.players.append(player)
            grid_layout.addWidget(player, row, col)
            
        for player in self.players:
            player.load_next() 

        self.update_title()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_all_play()
        elif event.key() == Qt.Key.Key_Right:
            self.seek_all(2000) 
        elif event.key() == Qt.Key.Key_Left:
            self.seek_all(-2000) 
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.change_speed(1.0) 
        elif event.key() == Qt.Key.Key_Minus:
            self.change_speed(-1.0) 
        else:
            super().keyPressEvent(event)

    def change_speed(self, delta):
        new_speed = self.current_speed + delta
        if 1.0 <= new_speed <= 4.0:
            self.current_speed = new_speed
            self.update_title() 
            for p in self.players:
                if p.current_file:
                    p.mediaPlayer.setPlaybackRate(self.current_speed)

    def toggle_all_play(self):
        is_playing = any(p.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState 
                         for p in self.players if p.current_file)
        for p in self.players:
            if p.current_file:
                if is_playing:
                    p.mediaPlayer.pause()
                    p.btn_play_pause.setText("▶️ Play")
                else:
                    p.mediaPlayer.play()
                    p.btn_play_pause.setText("⏸️ Pause")

    def seek_all(self, ms):
        for p in self.players:
            p.seek_relative(ms)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    player = MultiVideoPlayer()
    player.show()
    sys.exit(app.exec())
