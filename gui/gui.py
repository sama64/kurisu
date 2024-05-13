import sys
import os
import json
import uuid
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QPushButton, QLabel, QCheckBox, QScrollArea
from PyQt5.QtCore import Qt, QTimer
from datetime import date, datetime


class ToDoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do Kurisu")
        self.setGeometry(100, 100, 400, 500)

        # Create the central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create the task input field and button
        task_input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        task_input_layout.addWidget(self.task_input)
        task_input_layout.addWidget(self.add_task_button)
        main_layout.addLayout(task_input_layout)

        # Create a scroll area for the task list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Create the task list
        self.task_list = QListWidget()
        self.task_list.setSpacing(10)  # Add spacing between items
        self.task_list.setWordWrap(True) 
        scroll_area.setWidget(self.task_list)

        # Create the button layout
        button_layout = QHBoxLayout()
        self.remove_task_button = QPushButton("Remove Task")
        self.remove_task_button.clicked.connect(self.remove_task)
        button_layout.addWidget(self.remove_task_button)
        main_layout.addLayout(button_layout)

        # Create a label for the current date
        self.date_label = QLabel(f"Current Date: {date.today().strftime('%Y-%m-%d')}")
        main_layout.addWidget(self.date_label)

        # Initialize the tasks list
        self.tasks = {}
        self.load_tasks_from_file()

    def add_task(self):
        task = self.task_input.text().strip()
        if task:
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = {"task": task, "completed": False, "completion_time": None}
            self.update_task_list()
            self.task_input.clear()
            self.sync_tasks_to_file()

    def remove_task(self):
        selected_items = self.task_list.selectedItems()
        if selected_items:
            for item in selected_items:
                task_index = self.task_list.row(item)
                task_id = list(self.tasks.keys())[task_index]
                self.tasks.pop(task_id)
            self.update_task_list()
            self.sync_tasks_to_file()

    def toggle_task_state(self, state, task_id):
        self.tasks[task_id]["completed"] = state == Qt.Checked
        if state == Qt.Checked:
            self.tasks[task_id]["completion_time"] = datetime.now().isoformat()
        else:
            self.tasks[task_id]["completion_time"] = None
        self.sync_tasks_to_file()

    def update_task_list(self):
        self.task_list.clear()
        for task_id, task_data in self.tasks.items():
            task = task_data["task"]
            completed = task_data["completed"]
            task_item = QListWidgetItem()
            task_checkbox = QCheckBox()
            task_checkbox.setChecked(completed)
            task_checkbox.stateChanged.connect(lambda state, task_id=task_id: self.toggle_task_state(state, task_id))
            label = QLabel(task)
            label.setStyleSheet("QLabel { padding-left: 10px; }")
            label.setWordWrap(True)  # Enable word wrapping
            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(task_checkbox)
            layout.addWidget(label)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setStretchFactor(label, 1)  # Allow the label to stretch and fill the available space
            widget.setLayout(layout)
            self.task_list.addItem(task_item)
            self.task_list.setItemWidget(task_item, widget)

    def load_tasks_from_file(self):
        today = date.today().strftime('%Y-%m-%d')
        tasks_dir = "tasks"
        os.makedirs(tasks_dir, exist_ok=True)
        file_name = os.path.join(tasks_dir, f"tasks_{today}.json")

        if os.path.exists(file_name):
            try:
                with open(file_name, "r") as file:
                    tasks_data = json.load(file)
                    self.tasks = {task_id: {"task": task_data["task"], "completed": task_data["completed"], "completion_time": task_data.get("completion_time", None)} for task_id, task_data in tasks_data.items()}
            except (json.JSONDecodeError, KeyError):
                print("Error: Invalid JSON file format")
        else:
            print(f"No tasks file found for {today}")

        self.update_task_list()

    def sync_tasks_to_file(self):
        today = date.today().strftime('%Y-%m-%d')
        tasks_dir = "tasks"
        os.makedirs(tasks_dir, exist_ok=True)
        file_name = os.path.join(tasks_dir, f"tasks_{today}.json")
        tasks_data = {task_id: {"task": task_data["task"], "completed": task_data["completed"], "completion_time": task_data["completion_time"]} for task_id, task_data in self.tasks.items()}
        try:
            with open(file_name, "w") as file:
                json.dump(tasks_data, file, indent=4)
        except Exception as e:
            print(f"Error: Unable to save tasks to file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    todo_app = ToDoApp()
    todo_app.show()
    sys.exit(app.exec_())