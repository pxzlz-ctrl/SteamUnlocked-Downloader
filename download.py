from PyQt5.QtCore import QObject, pyqtSignal
import os
import requests

class Downloader(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, game_url, save_path, parent=None):
        super().__init__(parent)
        self.game_url = game_url
        self.save_path = save_path
        self.proxy_url = f"http://129.213.118.151:5000/get?url={game_url}"

    def download(self):
        try:
            # Send a GET request to the proxy URL
            response = requests.get(self.proxy_url, stream=True)
            response.raise_for_status()  # Check for HTTP errors

            # Extract the filename from the Content-Disposition header if available
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                # Use the last part of the URL as the filename
                filename = os.path.basename(self.game_url)
            
            # Create the full path to save the file
            save_directory = os.path.dirname(self.save_path)
            os.makedirs(save_directory, exist_ok=True)

            # Save the file
            file_path = os.path.join(save_directory, filename)
            with open(file_path, 'wb') as file:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percentage = int(100 * downloaded_size / total_size) if total_size > 0 else 0
                        self.progress.emit(progress_percentage)

            self.finished.emit()
        except requests.RequestException as e:
            print(f"Error during download: {e}")
            self.finished.emit()  # Ensure to emit finished even on error
