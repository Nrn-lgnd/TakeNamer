import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QDialog, QHeaderView, QTableWidgetItem
from PyQt6 import uic

from scripts import extract_audio_snippet, transcribe_clip, rename_file, folder_selection, process_folder, is_media_file, get_regex_pattern
from classes import TakeRenameWorker, DragDropTable

WHISPER_MODELS = [
    ("Tiny (Fastest, Lowest Accuracy)", "tiny"),
    ("Tiny - English Only", "tiny.en"),
    ("Base (Lightweight)", "base"),
    ("Base - English Only", "base.en"),
    ("Small (Balanced)", "small"),
    ("Small - English Only", "small.en"),
    ("Medium (High Accuracy)", "medium"),
    ("Medium - English Only", "medium.en"),
    ("Large v3 (Maximum Accuracy)", "large-v3"),
    ("Turbo (Fast & Near-Large Accuracy)", "turbo"),
    ("Distil Large v3 (Optimized)", "distil-large-v3"),
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Transcode")
        uic.loadUi("main.ui", self)

        self.index = 0

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget.verticalHeader().setMaximumSectionSize(30)
        self.tableWidget.verticalHeader().setDefaultSectionSize(20)
        self.tableWidget.setHorizontalHeaderLabels(["Filename", "Transcript", "Roll", "Scene", "Take", "Added Info", "New Filename", "Status"])

        for display_name, model_id in WHISPER_MODELS:
            self.model_combo.addItem(display_name, model_id)
            index = self.model_combo.findData("base")
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

        self.folder_selection_button.clicked.connect(self.handle_folder_select)

        self.rename_button.setEnabled(False)
        self.rename_button.clicked.connect(self.handle_process)

        self.scene_edit.textChanged.connect(self.update_update_button)
        self.shot_edit.textChanged.connect(self.update_update_button)
        self.take_edit.textChanged.connect(self.update_update_button)

        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_file_name)

        self.tableWidget.cellClicked.connect(self.update_rename_input)

        self.tableWidget.data.connect(self.handle_folder_select)

        self.transcript_time = self.time_spin.value()

    def handle_folder_select(self, data = None):

        if data:
            self.files, self.folder_path = process_folder(data)

        else:
            self.files, self.folder_path = folder_selection(self)

        if self.files:
            self.tableWidget.setRowCount(len(self.files))

            for file in self.files:
                for row_idx, file in enumerate(self.files):
                    self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(file))

        self.update_ui_state()

    def handle_process(self):
        self.rename_button.setEnabled(False)
        regex = self.regex_input.text().strip()
        self.file_regex = self.rename_input.text().strip()
        output_folder = self.output_folder_input.text().strip()

        if not regex:
            regex = "Szene $n, Shot $n, Take $n"

        if not self.file_regex:
            self.file_regex = "$n1-$n2-$n3.file_ending"

        if not output_folder:
            output_folder = "$d/renamed"

        self.rename_worker = TakeRenameWorker(
            folder_path=self.folder_path,
            files=self.files,
            regex=regex,
            file_regex=self.file_regex,
            output_folder=output_folder,
            whisper_model=self.model_combo.currentData(),
            transcript_time=self.transcript_time
        )
        self.rename_worker.data.connect(self.update_table)
        self.rename_worker.percentage.connect(self.update_progress_bar)


        self.rename_worker.start()

        self.output_folder = self.rename_worker.return_output_path()

    def update_ui_state(self):
        has_files = bool(self.files)

        if has_files:
            self.rename_button.setEnabled(True)
        else:
            self.rename_button.setEnabled(False)
            self.tableWidget.setRowCount(0)

    def update_progress_bar(self, percentage):
        self.process_progress_bar.setValue(percentage)

    def update_table(self, col_type, row, value):
        match col_type:
            case "trans":
                self.tableWidget.setItem(row, 1, QTableWidgetItem(value))
            case "scene":
                self.tableWidget.setItem(row, 2, QTableWidgetItem(value))
            case "shot":
                self.tableWidget.setItem(row, 3, QTableWidgetItem(value))
            case "take":
                self.tableWidget.setItem(row, 4, QTableWidgetItem(value))
            case "new_filename":
                self.tableWidget.setItem(row, 6, QTableWidgetItem(value))

    def update_rename_input(self, row, col):
        self.index = row

        scene_item = self.tableWidget.item(row, 2)
        shot_item = self.tableWidget.item(row, 3)
        take_item = self.tableWidget.item(row, 4)
        transcript_item = self.tableWidget.item(row, 1)

        scene_num = scene_item.text() if scene_item else ""
        shot_num = shot_item.text() if shot_item else ""
        take_num = take_item.text() if take_item else ""
        transcript = transcript_item.text() if transcript_item else ""

        self.scene_edit.setText(scene_num)
        self.shot_edit.setText(shot_num)
        self.take_edit.setText(take_num)

        if transcript:
            self.transcript_display.setPlainText(transcript)

            self.scene_edit.setReadOnly(False)
            self.shot_edit.setReadOnly(False)
            self.take_edit.setReadOnly(False)

        self.update_button.setEnabled(False)

    def get_selected_model(self):
        return self.model_combo.currentData()

        self.files = None

        self.remove_item.setEnabled(False)
        self.remove_item.clicked.connect(self.handle_file_removal)

        self.folder_selection_button.clicked.connect(self.handle_folder_select)

        self.rename_button.clicked.connect(self.handle_process)

    def update_file_name(self):
        filename = self.tableWidget.item (self.index, 6)

        filename_str = filename.text() if filename else ""
        file_ending = Path(filename_str).suffix

        file_path = Path(self.output_folder) / filename_str

        scene_num = self.scene_edit.text()
        shot_num = self.shot_edit.text()
        take_num = self.take_edit.text()

        new_filename = (
            self.file_regex
            .replace("$n1", str(scene_num))
            .replace("$n2", str(shot_num))
            .replace("$n3", str(take_num))
            .replace(".file_ending", str(file_ending))
        )

        new_file_path = Path(self.output_folder) / new_filename

        self.tableWidget.setItem(self.index, 0, QTableWidgetItem(filename_str))
        self.tableWidget.setItem(self.index, 6, QTableWidgetItem(new_filename))

        self.tableWidget.setItem(self.index, 2, QTableWidgetItem(scene_num))
        self.tableWidget.setItem(self.index, 3, QTableWidgetItem(shot_num))
        self.tableWidget.setItem(self.index, 4, QTableWidgetItem(take_num))

        self.update_button.setEnabled(False)

        print (new_file_path)

        file_path.rename(new_file_path)

    def update_update_button(self):
        self.update_button.setEnabled(True)





if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r") as f:
        style = f.read()
        app.setStyleSheet(style)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
