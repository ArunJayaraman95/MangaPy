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
        self.srcTag = "src"
        self.tagKeyword = "blogspot"
        self.url = f"https://steel-ball-run.com/manga/jojos-bizarre-adventure-steel-ball-run-chapter-%replace%/"

        # Connections
        self.browseButton.clicked.connect(self.browseFiles)
        self.cancelButton.clicked.connect(self.exit)
        self.downloadButton.clicked.connect(self.downloadChapters)

        self.pathText.setText(self.exportPath)
        self.pageProgress.setValue(0)
        self.readConfig()
        self.writeConfig()


    def exit(self):
        """Writes config values and exits the GUI"""

        logger.debug("Exiting")
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

        logger.debug("Writing images to jpgs")
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

        logger.debug("Open folder browser")
        fname = QFileDialog.getExistingDirectory(self, "Open File")
        logger.debug(f"{fname}")
        self.pathText.setText(fname)
        self.exportPath = self.pathText.text()
        self.writeConfig()


    def deleteTempImages(self, dir: str):
        """Delete images in directory provided"""

        logger.debug("Deleting temporary images")
        x = os.listdir(dir)
        for img in x:
            if img.endswith(".jpg"):
                os.remove(os.path.join(dir, img))


    def downloadChapters(self):
        """Download a range of chapters and update progress bars"""

        logger.debug("Beginning chapter download")
        startValue = self.startChapter.value()
        endValue = self.endChapter.value()
        chapterTotal = endValue - startValue + 1
        isInvalidRange = startValue > endValue

        if isInvalidRange:
            msgBox = QMessageBox()

            msgBox.setWindowTitle("Error Downloading")
            msgBox.setText("Invalid range. Start chapter cannot be greater than end chapter. Try again.")
            msgBox.setIcon(QMessageBox.Warning)

            msgBox.exec()
            return

        self.chapterLabel.setText(f"Starting download...")

        for chapter in range(startValue, endValue + 1):
            relativeChapter = chapter - startValue + 1
            self.chapterLabel.setText(
                f"Downloading Chapter #{chapter} ({relativeChapter}/{chapterTotal})"
            )
            self.download(chapter)
            self.chapterProgress.setValue(relativeChapter * 100 // chapterTotal)

        self.chapterLabel.setText("ALL CHAPTERS DOWNLOADED")
        self.cancelButton.setText("Finish")
        self.writeConfig()


    def writeConfig(self):
        """Write exportPath and next chapter to config file"""

        logger.debug("Writing to Config File")
        # ? Manga Title, Export Path, Last Chapter, URL, SRC, KEY
        # # TODO: Add image src and keyword into dictionary
        dictionary = {
            "Manga": self.mangaTitle,
            "Export Path": self.exportPath,
            "Last Chapter": self.endChapter.value() + 1,
        }

        # # Writing to sample.json
        with open(self.configFileName, "w") as outfile:
            json.dump(dictionary, outfile, indent = 4)


    def readConfig(self):
        """Reads in configuration file and sets attributes in class"""

        logger.debug("Reading Config File")
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

        # Sub in chapter number into url
        url = self.url.replace(f"%replace%", str(chapter))

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