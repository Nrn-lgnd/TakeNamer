import shutil

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QTableWidget

from faster_whisper import WhisperModel
from pathlib import Path

from scripts import extract_audio_snippet, transcribe_clip, rename_file, folder_selection, process_folder, is_media_file, get_regex_pattern

class TakeRenameWorker(QThread):
    data = pyqtSignal(str, int, str)
    percentage = pyqtSignal(int)

    def __init__(self, folder_path, files, regex, file_regex, output_folder, whisper_model = "base", transcript_time = 15):
        super().__init__()
        self.model = WhisperModel(whisper_model, device="cpu", compute_type="int8")

        self.folder_path = folder_path
        self.files = files
        self.regex = regex
        self.file_regex = file_regex
        self.output_folder = output_folder
        self.transcript_time = transcript_time

        #self.output_file_path = Path(self.output_folder.replace("$d", str(self.folder_path)))
        output_str = str(output_folder)
        if "$d" in output_str:
            rel_part = output_str.replace("$d", "").strip("/\\")
            self.output_file_path = self.folder_path / rel_part if rel_part else self.folder_path
        else:
            self.output_file_path = Path(output_str)

    def run(self):
        print (self.output_file_path)
        self.output_file_path.mkdir(parents=True, exist_ok=True)

        for self.index, filename in enumerate(self.files):
            file_path = self.folder_path / filename
            file_ending = file_path.suffix
            temp_audio = file_path.with_suffix(".mp3")

            success = extract_audio_snippet(file_path, temp_audio, self.transcript_time)
            if not success:
                print("  -> Warning: Could not extract audio. Skipping.")
                continue

            self.transcript, console_log = transcribe_clip(temp_audio, self.model)

            if self.transcript:
                extracted_values = rename_file(file_path, self.transcript, self.regex)
                if len(extracted_values) >= 3:
                    self.scene_num = extracted_values[0]
                    self.shot_num = extracted_values[1]
                    self.take_num = extracted_values[2]
                    #self.new_filename = f"{self.scene_num}-{self.shot_num}-{self.take_num}{file_ending}"
                    self.new_filename = (
                        self.file_regex
                        .replace("$n1", str(self.scene_num))
                        .replace("$n2", str(self.shot_num))
                        .replace("$n3", str(self.take_num))
                        .replace(".file_ending", str(file_ending))
                    )
                    new_path = self.output_file_path / filename
                    new_path = new_path.with_name(self.new_filename)
                    shutil.copy2(file_path, new_path)

            if temp_audio.exists():
                temp_audio.unlink()

            self.emit_signals()

    def emit_signals(self):
        index = self.index+1
        total_files = len(self.files)
        percentage = (index/total_files)*100
        percentage = min(max(int(percentage), 0), 100)

        self.percentage.emit(percentage)

        if total_files == index:
            self.percentage.emit(100)



        self.data.emit("trans",self.index, self.transcript)
        self.data.emit("scene", self.index, self.scene_num)
        self.data.emit("shot", self.index, self.shot_num)
        self.data.emit("take", self.index, self.take_num)
        self.data.emit("new_filename", self.index, self.new_filename)

    def return_output_path(self):
        return self.output_file_path

class DragDropTable(QTableWidget):
    data = pyqtSignal(Path)
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 1, parent)
        self.files: list[str] = []
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        #self.setHorizontalHeaderLabels(["File Path"])
        self.horizontalHeader().setStretchLastSection(True)

    def _has_folder(self, mime: QMimeData | None) -> bool:
        if mime is None or not mime.hasUrls():
            return False
        for url in mime.urls():
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir():
                return True
        return False

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._has_folder(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._has_folder(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if not self._has_folder(mime):
            event.ignore()
            return

        added = False
        for url in mime.urls():
            print(f"[dropEvent] url={url.toString()} | isLocal={url.isLocalFile()}")
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                #self.files.append(path)
                # row = self.rowCount()
                # self.insertRow(row)
                # self.setItem(row, 0, QTableWidgetItem(path))
                added = True

        print(f"[dropEvent] total files stored: {len(self.files)}")
        if added:
            event.acceptProposedAction()

        self.data.emit(path)



