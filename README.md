# MangaPy (v1.1.0)
Python GUI that enables users to download manga chapters locally to their PC.

# Newest Features
* Dictionary now read/writes multiple mangas to json

## Manga Titles Supported
* Vagabond
* Berserk
* Steel Ball Run Colored (JJBA)

## Instructions
1. Clone this repository
2. pip install all unrecognized import libraries below in the `Downloader.py` file (you may have to do `pip install <library> --user`):
   * beautifulsoup4
   * requests
   * pyqt5
   * img2pdf
3. Run `Downloader.py` (or do the PyInstaller method below for easier future use)
4. Select the file path of where you want to download the chapters
5. Pick the chapter range to download and click "Download"
6. Click "Finish" when done downloading chapters


### Pyinstaller
These are the steps to downloading pyinstaller for easier access to GUI
1. `pip install pyinstaller`
2. Run `python -m PyInstaller Downloader.py --onefile`
3. Move the `Downloader.exe` file to the same level as the `Downloader.py` file
4. Run `Downloader.exe` or make a shortcut of the exe and put on your desktop