import sys
import os
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QLineEdit, QLabel, QPushButton, 
                             QHBoxLayout, QMenu, QAction, QMessageBox, QListWidgetItem, QDialog, QDialogButtonBox, QProgressBar)
from PyQt5.QtCore import pyqtSignal, QThread, QObject, QTimer, Qt
import json
import requests
from download import Downloader  # Ensure you have a Downloader class in download.py

class GameDetailDialog(QDialog):
    def __init__(self, title, description, url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Details")
        self.setModal(True)
        self.url = url

        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #007bff;
                color: #FFFFFF;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                background-color: #1E1E1E;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #FFFFFF;
            }
        """)

        self.downloader = None
        self.download_thread = None

        layout = QVBoxLayout()
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(title_label)

        description_label = QLabel(description)
        layout.addWidget(description_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        button_box = QDialogButtonBox()
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.on_download_clicked)
        button_box.addButton(self.download_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(QPushButton("Close"), QDialogButtonBox.RejectRole)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_download_clicked(self):
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)

        # Ensure the file name is valid and create the save path
        file_name = os.path.basename(self.url.split('/')[-1])
        save_directory = os.path.join(os.path.expanduser("~"), "SteamUnlockedLibrary")
        save_path = os.path.join(save_directory, file_name)
    
        # Ensure the directory exists
        os.makedirs(save_directory, exist_ok=True)

        # Print the save_path for debugging
        print(f"Save path: {save_path}")

        # Initialize Downloader with the URL and save path
        self.downloader = Downloader(self.url, save_path)
        self.download_thread = QThread()
    
        self.downloader.moveToThread(self.download_thread)
        self.downloader.progress.connect(self.progress_bar.setValue)
        self.downloader.finished.connect(self.on_download_finished)

        self.download_thread.started.connect(self.downloader.download)
        self.download_thread.start()

    def on_download_finished(self):
        self.download_thread.quit()
        self.download_thread.wait()
        self.download_button.setEnabled(True)
        QMessageBox.information(self, "Download Complete", "The download has completed successfully.")

class ScraperWorker(QObject):
    games_fetched = pyqtSignal(list)

    def __init__(self, driver_path, url):
        super().__init__()
        self.driver_path = driver_path
        self.url = url

    def run(self):
        import scraper
        scraper.get_game_list(self.games_fetched.emit, self.driver_path, self.url)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Finder")
        self.setGeometry(100, 100, 1280, 720)

        self.driver_path = "chromedriver.exe"
        self.url = "https://steamunlocked.net/all-games-2/"

        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #FFFFFF;
                background-color: #1E1E1E;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QListWidget {
                border: 1px solid #333333;
                border-radius: 5px;
                color: #FFFFFF;
                background-color: #1E1E1E;
            }
            QListWidget::item {
                padding: 10px;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: #FFFFFF;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.header_label = QLabel("SteamUnlocked Downloader")
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.layout.addWidget(self.header_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a game...")
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.apply_filter)

        self.game_list_widget = QListWidget()
        self.layout.addWidget(self.game_list_widget)

        self.game_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_list_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.game_list_widget.itemDoubleClicked.connect(self.show_game_details)

        self.all_games = []
        self.displayed_games = []
        self.game_descriptions = {}

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_displayed_games)
        self.search_text = ""

        self.load_cached_games()

    def load_cached_games(self):
        cached_games = []
        if os.path.exists("cached_games.json"):
            with open("cached_games.json", "r", encoding="utf-8") as file:
                cached_games = json.load(file)
        self.add_games(cached_games)

    def add_games(self, game_titles_with_urls):
        self.all_games = [title for title, url in game_titles_with_urls]
        self.game_descriptions = dict(game_titles_with_urls)
        self.apply_filter()

    def apply_filter(self):
        self.search_text = self.search_bar.text().lower()
        self.timer.start(300)

    def update_displayed_games(self):
        self.game_list_widget.clear()
        filtered_games = [game for game in self.all_games if self.search_text in game.lower()]
        self.displayed_games = filtered_games
        self.game_list_widget.addItems(filtered_games)

    def show_context_menu(self, pos):
        item = self.game_list_widget.itemAt(pos)
        if item:
            game_title = item.text()
            if game_title in self.game_descriptions:
                url = self.game_descriptions[game_title]
                menu = QMenu(self)
                action = QAction(f"URL: {url}", self)
                menu.addAction(action)
                menu.exec_(self.game_list_widget.viewport().mapToGlobal(pos))

    def show_game_details(self, item):
        game_title = item.text()
        url = self.game_descriptions.get(game_title, "")
        description = "No description available"
        dialog = GameDetailDialog(game_title, description, url, self)
        dialog.exec_()

    def check_and_add_new_games(self, new_games):
        existing_titles = set(self.all_games)
        for title, url in new_games:
            if title not in existing_titles:
                self.all_games.append(title)
                self.game_descriptions[title] = url
                self.game_list_widget.addItem(title)
                existing_titles.add(title)

def run_gui():
    app = QApplication(sys.argv)
    main_window = MainWindow()

    scraper_worker = ScraperWorker(main_window.driver_path, main_window.url)
    scraper_thread = QThread()
    scraper_worker.moveToThread(scraper_thread)

    scraper_worker.games_fetched.connect(main_window.check_and_add_new_games)
    scraper_thread.started.connect(scraper_worker.run)
    scraper_thread.start()

    main_window.show()
    sys.exit(app.exec_())
