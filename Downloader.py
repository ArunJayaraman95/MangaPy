import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox
from PyQt5.uic import loadUi
from bs4 import BeautifulSoup as bs
import requests
import os
import img2pdf as converter
import shutil
import json
import logging


# TODO: Better variable names
# TODO: URL Class Atrribute
# TODO: URL Select
# TODO: Type checking

logger = logging.getLogger("MANGAPY")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(name)s[%(levelname)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("MangaGUI.ui", self)
        self.label.setText("Steel Ball Run Downloader")

        # Variables
        self.tempFolder = os.getcwd()
        self.mangaTitle = "SBR"
        self.exportPath = r"C:/Users/ripar/Documents/Books/Jojolion/"
        self.mangaAbbrv = "page"
        self.defaultChapter = 1
        self.configFileName = "sample.json"
        self.alternator = True
        self.pathText.setText(self.exportPath)
        self.pageProgress.setValue(0)
        self.srcTag = "src"
        self.tagKeyword = "blogspot"

        # Connections
        self.browseButton.clicked.connect(self.browseFiles)
        self.cancelButton.clicked.connect(self.exit)
        self.downloadButton.clicked.connect(self.downloadChapters)

        self.readConfig()
        self.writeConfig()


    def exit(self):
        """Writes config values and exits the GUI"""

        self.writeConfig()
        sys.exit()


    # TODO: Make the source / keyword availa
    def getMangaOnlyImages(self, imageList: list):
        """Return images maching certain attributes"""

        return [
            img
            for img in imageList
            if img.has_attr(self.srcTag) and self.tagKeyword in img[self.srcTag]
        ]


    def writeImages(self, chapter: int, imageList: list, nickName: str):
        """Write image contents into jpg files"""

        pageCount = len(imageList)

        for index, image in enumerate(imageList):
            name = f"{nickName}-{chapter}-{index}"
            source = image[self.srcTag]

            logger.info(f"...retrieving Pg #{index}...")
            with open(name.replace(" ", "-") + ".jpg", "wb") as f:
                im = requests.get(source)
                f.write(im.content)
            self.pageLabel.setText(f"Page {index + 1} / {pageCount}")
            self.pageProgress.setValue((index + 1) * 100 // pageCount)


    def browseFiles(self):
        """Allow user to open file explorer and select a directory"""

        fname = QFileDialog.getExistingDirectory(self, "Open File")
        logger.debug(f"{fname}")
        self.pathText.setText(fname)
        self.writeConfig()


    def deleteTempImages(self, dir: str):
        """Delete images in directory provided"""

        x = os.listdir(dir)
        for img in x:
            if img.endswith(".jpg"):
                os.remove(os.path.join(dir, img))


    def downloadChapters(self):
        """Download a range of chapters and update progress bars"""

        self.exportPath = self.pathText.text()

        s, e = self.startChapter.value(), self.endChapter.value()

        if s > e:
            msgBox = QMessageBox()

            msgBox.setWindowTitle("Error Downloading")
            msgBox.setText("Invalid range. Start chapter cannot be greater than end chapter. Try again.")
            msgBox.setIcon(QMessageBox.Warning)

            msgBox.exec()
            return

        self.chapterLabel.setText(f"Starting download...")

        for i in range(self.startChapter.value(), self.endChapter.value() + 1):
            self.chapterLabel.setText(
                f"Downloading Chapter #{i} ({i + 1 - s}/{e - s + 1})"
            )
            self.download(i)
            self.chapterProgress.setValue((i - s + 1) * 100 // (e - s + 1))

        self.chapterLabel.setText("ALL CHAPTERS DOWNLOADED")
        self.cancelButton.setText("Finish")
        self.writeConfig()


    def writeConfig(self):
        """Write exportPath and next chapter to config file"""

        # ? Manga Title, Export Path, Last Chapter, URL, SRC, KEY
        # # TODO: Add image src and keyword into dictionary
        dictionary = {
            "Manga": self.mangaTitle,
            "Export Path": self.exportPath,
            "Last Chapter": self.endChapter.value() + 1,
        }

        # # Writing to sample.json
        with open(self.configFileName, "w") as outfile:
            json.dump(dictionary, outfile)


    def readConfig(self):
        """Reads in configuration file and sets attributes in class"""

        try:
            with open(self.configFileName, "r") as openfile:
                json_object = json.load(openfile)

            logger.debug(json_object)

            # Format: Manga, Path, LastChapterDownloaded, URL
            self.mangaTitle = json_object["Manga"]
            self.exportPath = json_object["Export Path"]
            self.defaultChapter = json_object["Last Chapter"]

            # Set newly read values on GUI
            self.pathText.setText(self.exportPath)
            self.startChapter.setValue(int(self.defaultChapter))
            self.endChapter.setValue(int(self.defaultChapter))
        except:
            logger.error("Failed to read configuration file")
            logger.error("Exiting Program...")
            exit(0)


    def download(self, chapter: int):
        """Download a given chapter to export path with webscraping"""

        url = f"https://steel-ball-run.com/manga/jojos-bizarre-adventure-steel-ball-run-chapter-{chapter}/"

        try:
            r = requests.get(url)
            soup = bs(r.text, "html.parser")
            images = soup.find_all("img")  # Get all images
        except:
            logger.error("Error Accessing WebPage")
            exit(0)

        # Filter to only get imags in the manga itself
        images = self.getMangaOnlyImages(images)
        self.writeImages(chapter, images, self.mangaAbbrv)

        # List of Input file names
        inputFiles = [
            f"{self.mangaAbbrv}-{chapter}-{i}.jpg" for i in range(0, len(images))
        ]

        outputFile = open(f"{chapter}.pdf", "wb")
        outputFile.write(converter.convert(inputFiles))
        outputFile.close()
        logger.info("Completed Download!")

        self.deleteTempImages(self.tempFolder)
        logger.info("Temp Files Deleted")

        # Move pdf to exportPath
        self.exportPath = self.pathText.text()

        try:
            shutil.move(f"{chapter}.pdf", self.exportPath)
        except:
            os.remove(f"{chapter}.pdf")
            logger.warning("Chapter already exists")

        logger.info(f"Moved chapter {chapter}")


app = QApplication(sys.argv)
mainwindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(1135)
widget.setFixedHeight(494)
widget.show()
sys.exit(app.exec_())