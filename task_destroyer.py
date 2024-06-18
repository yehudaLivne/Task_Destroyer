import json
import os
import sys
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QTimer

class TaskDestroyer(QWidget):
    """
    Task Destroyer is an application to manage and gamify tasks with sound effects and drag-and-drop functionality.
    """
    def __init__(self, file_name='tasks.json'):
        """
        Initializes the Task Destroyer application.
        """
        super().__init__()
        pygame.mixer.init()
        self.file_name = file_name
        self.load_tasks()
        self.score = 0
        self.current_task_index = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.remaining_time = 0
        self.add_task_sound = os.path.join(os.path.dirname(__file__), 'add_task.wav')
        self.complete_task_sound = os.path.join(os.path.dirname(__file__), 'complete_task.wav')
        self.tick_sound = os.path.join(os.path.dirname(__file__), 'tick.wav')
        self.init_ui()

    def load_tasks(self):
        """
        Loads tasks from a JSON file.
        """
        if os.path.exists(self.file_name):
            try:
                with open(self.file_name, 'r') as file:
                    self.tasks = json.load(file)
                    for task in self.tasks:
                        if 'time_minutes' not in task:
                            task['time_minutes'] = 10  # Default value if not present
                        if 'points' not in task:
                            task['points'] = 10  # Default value if not present
            except json.JSONDecodeError:
                self.tasks = []
        else:
            self.tasks = []

    def save_tasks(self):
        """
        Saves tasks to a JSON file.
        """
        try:
            with open(self.file_name, 'w') as file:
                json.dump(self.tasks, file)
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def play_sound(self, sound_file):
        """
        Plays a sound effect.
        """
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except pygame.error as e:
            print(f"Error playing sound: {e}")

    def add_task(self, description, points, time_minutes):
        """
        Adds a new task.
        """
        task = {
            'description': description,
            'points': points,
            'time_minutes': time_minutes,
            'completed': False
        }
        self.tasks.append(task)
        self.save_tasks()
        self.play_sound(self.add_task_sound)
        self.update_display()
        if self.current_task_index is None:
            self.start_next_task()

    def edit_task(self, task_index, description, points, time_minutes):
        """
        Edits an existing task.
        """
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            task['description'] = description
            task['points'] = points
            task['time_minutes'] = time_minutes
            self.save_tasks()
            self.update_display()

    def complete_task(self):
        """
        Completes the current task.
        """
        if self.current_task_index is not None:
            task = self.tasks[self.current_task_index]
            if not task['completed']:
                self.timer.stop()
                if self.remaining_time > 0:
                    task['completed'] = True
                    self.score += task['points']
                else:
                    self.score -= task['points']
                self.save_tasks()
                self.play_sound(self.complete_task_sound)
                self.update_display()
                self.current_task_index = None
                self.start_next_task()

    def start_next_task(self):
        """
        Starts the next incomplete task.
        """
        for index, task in enumerate(self.tasks):
            if not task['completed']:
                self.start_task(index)
                break

    def start_task(self, task_index):
        """
        Starts a specific task by index.
        """
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if not task['completed']:
                self.current_task_index = task_index
                self.remaining_time = task['time_minutes'] * 60
                self.update_timer_display()
                self.timer.start(1000)

    def update_timer(self):
        """
        Updates the timer and handles the countdown.
        """
        if self.remaining_time > 0:
            self.remaining_time -= 1
            if self.remaining_time <= 60:
                self.play_sound(self.tick_sound)
            self.update_timer_display()
        else:
            self.timer.stop()
            self.score -= self.tasks[self.current_task_index]['points']
            self.tasks[self.current_task_index]['completed'] = True
            self.save_tasks()
            self.update_display()
            self.current_task_index = None
            self.start_next_task()

    def update_timer_display(self):
        """
        Updates the timer display.
        """
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.timer_label.setText(f"Time Remaining: {minutes:02}:{seconds:02}")

    def init_ui(self):
        """
        Initializes the user interface.
        """
        self.setWindowTitle('Task Destroyer')
        self.setStyleSheet("background-color: #2E3440; color: #D8DEE9;")
        
        self.layout = QVBoxLayout()

        self.score_label = QLabel(f"Current Score: {self.score}", self)
        self.score_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.score_label)

        self.next_task_label = QLabel("", self)
        self.next_task_label.setStyleSheet("font-size: 24px; color: #88C0D0;")
        self.layout.addWidget(self.next_task_label)

        self.timer_label = QLabel("", self)
        self.timer_label.setStyleSheet("font-size: 18px; color: #BF616A;")
        self.layout.addWidget(self.timer_label)

        self.task_list = QListWidget(self)
        self.task_list.setStyleSheet("background-color: #4C566A; color: #ECEFF4; font-size: 16px;")
        self.task_list.setDragDropMode(QListWidget.InternalMove)
        self.task_list.model().rowsMoved.connect(self.reorder_tasks)
        self.layout.addWidget(self.task_list)

        button_style = """
        QPushButton {
            background-color: #5E81AC;
            color: #ECEFF4;
            font-size: 16px;
            border-radius: 5px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #81A1C1;
        }
        """
        self.add_task_button = QPushButton('Add Task', self)
        self.add_task_button.setStyleSheet(button_style)
        self.add_task_button.clicked.connect(self.show_add_task_dialog)
        self.layout.addWidget(self.add_task_button)

        self.edit_task_button = QPushButton('Edit Task', self)
        self.edit_task_button.setStyleSheet(button_style)
        self.edit_task_button.clicked.connect(self.show_edit_task_dialog)
        self.layout.addWidget(self.edit_task_button)

        self.complete_task_button = QPushButton('Complete Task', self)
        self.complete_task_button.setStyleSheet(button_style)
        self.complete_task_button.clicked.connect(self.complete_task)
        self.layout.addWidget(self.complete_task_button)

        self.reset_button = QPushButton('Reset', self)
        self.reset_button.setStyleSheet(button_style)
        self.reset_button.clicked.connect(self.reset_tasks)
        self.layout.addWidget(self.reset_button)

        self.setLayout(self.layout)
        self.update_display()
        self.start_next_task()

    def show_add_task_dialog(self):
        """
        Shows a dialog to add a new task.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Task')
        dialog.setStyleSheet("background-color: #3B4252; color: #ECEFF4;")
        layout = QFormLayout(dialog)

        description_input = QLineEdit(dialog)
        points_input = QLineEdit(dialog)
        time_input = QLineEdit(dialog)
        layout.addRow('Description:', description_input)
        layout.addRow('Points:', points_input)
        layout.addRow('Time (minutes):', time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.setStyleSheet("background-color: #4C566A; color: #ECEFF4;")
        layout.addWidget(buttons)

        def add_task():
            description = description_input.text().strip()
            if not description:
                QMessageBox.warning(self, "Input Error", "Task description cannot be empty.")
                return

            try:
                points = int(points_input.text()) if points_input.text() else 10
                time_minutes = int(time_input.text()) if time_input.text() else 10
                if points < 0 or time_minutes < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Points and time must be positive integers.")
                return

            self.add_task(description, points, time_minutes)
            dialog.accept()

        buttons.accepted.connect(add_task)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()

    def show_edit_task_dialog(self):
        """
        Shows a dialog to edit an existing task.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Task')
        dialog.setStyleSheet("background-color: #3B4252; color: #ECEFF4;")
        layout = QFormLayout(dialog)

        task_index_input = QLineEdit(dialog)
        description_input = QLineEdit(dialog)
        points_input = QLineEdit(dialog)
        time_input = QLineEdit(dialog)
        layout.addRow('Task Index:', task_index_input)
        layout.addRow('Description:', description_input)
        layout.addRow('Points:', points_input)
        layout.addRow('Time (minutes):', time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.setStyleSheet("background-color: #4C566A; color: #ECEFF4;")
        layout.addWidget(buttons)

        def edit_task():
            try:
                task_index = int(task_index_input.text())
                if task_index < 0 or task_index >= len(self.tasks):
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Invalid task index.")
                return

            description = description_input.text().strip()
            if not description:
                QMessageBox.warning(self, "Input Error", "Task description cannot be empty.")
                return

            try:
                points = int(points_input.text()) if points_input.text() else 10
                time_minutes = int(time_input.text()) if time_input.text() else 10
                if points < 0 or time_minutes < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Points and time must be positive integers.")
                return

            self.edit_task(task_index, description, points, time_minutes)
            dialog.accept()

        buttons.accepted.connect(edit_task)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()

    def reset_tasks(self):
        """
        Resets all tasks and the score.
        """
        self.tasks = []
        self.save_tasks()
        self.score = 0
        self.timer.stop()
        self.current_task_index = None
        self.update_display()

    def update_display(self):
        """
        Updates the task list and other UI elements.
        """
        self.score_label.setText(f"Current Score: {self.score}")

        self.task_list.clear()
        if self.tasks:
            next_task = None
            for index, task in enumerate(self.tasks):
                item = QListWidgetItem(f"{index}. {task['description']} (Worth {task['points']} points, {task['time_minutes']} min)", self.task_list)
                item.setData(Qt.UserRole, index)  # Store the original index in the item
                if task['completed']:
                    item.setForeground(Qt.gray)
                elif next_task is None and not task['completed']:
                    next_task = task
                    item.setForeground(Qt.blue)
                else:
                    item.setForeground(Qt.black)

            if next_task:
                self.next_task_label.setText(f"Next Task: {next_task['description']}")
                self.remaining_time = next_task['time_minutes'] * 60
                self.update_timer_display()
            else:
                self.next_task_label.setText("All tasks completed!")
                self.timer_label.setText("")
        else:
            self.next_task_label.setText("No tasks available.")
            self.timer_label.setText("")

    def reorder_tasks(self, source_parent, source_start, source_end, dest_parent, dest_row):
        """
        Reorders tasks based on drag-and-drop.
        """
        self.tasks = [self.tasks[item.data(Qt.UserRole)] for item in self.task_list.findItems("*", Qt.MatchWildcard)]
        self.save_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = TaskDestroyer()
    manager.show()
    sys.exit(app.exec_())
