import sys
import os
import json
import uuid
from datetime import datetime, timedelta
from PyQt6.QtCore import QSize, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from ui.task_ui import Ui_TaskForm
from ui.main_ui import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.list_view = self.ui.task_listView
        self.add_btn = self.ui.add_btn
        self.task_input = self.ui.new_task

        self.list_model = QStandardItemModel()
        self.init_ui()

        self.tasks_folder_path = os.path.join(os.getcwd(), "tasks")
        os.makedirs(self.tasks_folder_path, exist_ok=True)

        self.current_date = datetime.now().date()
        self.task_file_path = os.path.join(self.tasks_folder_path, f"{self.current_date.isoformat()}.json")

        self.task_list = self.get_tasks()
        self.show_tasks(self.task_list)

        self.ui.set_reload_task_list_callback(self.reload_task_list)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_changes)
        self.timer.start(500)

    def init_ui(self):
        self.list_view.setModel(self.list_model)
        self.list_view.setSpacing(5)
        self.list_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        icon_path = os.path.join(os.getcwd(), "static/icons/add-black.min.svg")
        self.add_btn.setIcon(QIcon(icon_path))
        self.add_btn.clicked.connect(self.add_new_task)

    def add_new_task(self):
        new_task = self.task_input.text().strip()
        if new_task:
            task_uuid = str(uuid.uuid4())
            self.task_list.append({"uuid": task_uuid, "name": new_task, "completed": False, "completed_time": None})
            self.save_tasks()
            self.show_tasks(self.task_list)
            self.task_input.clear()

    def remove_item(self, position):
        self.list_model.removeRow(position)
        self.task_list.pop(position)
        self.save_tasks()
        self.show_tasks(self.task_list)

    def get_tasks(self):
        if os.path.exists(self.task_file_path):
            with open(self.task_file_path, "r") as f:
                tasks_data = json.load(f)
                return tasks_data
        else:
            return []

    def save_tasks(self):
        with open(self.task_file_path, "w") as f:
            json.dump(self.task_list, f, indent=2)

    def show_tasks(self, task_list):
        self.list_model.clear()
        if task_list:
            for i, task in enumerate(task_list):
                item = QStandardItem()
                self.list_model.appendRow(item)
                widget = Ui_TaskForm(task["name"], task["completed"], i, task["uuid"])
                widget.closeClicked.connect(self.remove_item)
                widget.checkboxStateChanged.connect(self.update_task_status)
                item.setSizeHint(widget.sizeHint())
                self.list_view.setIndexWidget(self.list_model.indexFromItem(item), widget)

    def update_task_status(self, position, state):
        task = self.task_list[position]
        task["completed"] = state
        if state:
            task["completed_time"] = datetime.now().isoformat()
        else:
            task["completed_time"] = None
        self.save_tasks()

    def reload_task_list(self):
        self.task_list = self.get_tasks()
        self.show_tasks(self.task_list)

    def check_for_changes(self):
        now = datetime.now()
        if now.date() != self.current_date and now.time() >= datetime.min.time().replace(hour=6):
            self.current_date = now.date()
            self.task_file_path = os.path.join(self.tasks_folder_path, f"{self.current_date.isoformat()}.json")
            self.task_list = self.get_tasks()
            self.show_tasks(self.task_list)

        if os.path.exists(self.task_file_path):
            modified_time = os.path.getmtime(self.task_file_path)
            if not hasattr(self, "last_modified_time") or modified_time > self.last_modified_time:
                self.last_modified_time = modified_time
                self.task_list = self.get_tasks()
                self.show_tasks(self.task_list)

    def closeEvent(self, event):
        self.save_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())