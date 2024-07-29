import sys
from PyQt5.QtWidgets import QApplication
import threading
import gui

def start_gui():
    gui.run_gui()

def main():
    gui_thread = threading.Thread(target=start_gui)
    gui_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    start_gui()
