import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
from bs4 import BeautifulSoup as bs
import requests
import os
import img2pdf as converter
import shutil
import json

# TODO: Chapter adjustments and arrows?
# TODO: Better variable names
# TODO: Logging instead of printing
# TODO: URL Select
# TODO: Page offset

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
        self.configurations = ""

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

            print(f"...retrieving Pg #{index}...")
            with open(name.replace(" ", "-") + ".jpg", "wb") as f:
                im = requests.get(source)
                f.write(im.content)
            self.pageLabel.setText(f"Page {index + 1} / {pageCount}")
            self.pageProgress.setValue((index + 1) * 100 // pageCount)

    def browseFiles(self):
        """Allow user to open file explorer and select a directory"""
        # fname=QFileDialog.getOpenFileName(self, 'Open file', 'C:\\', 'Images (*.png, *.xmp *.jpg)')
        fname = QFileDialog.getExistingDirectory(self, "Open File")
        print(fname)
        self.pathText.setText(fname)
        self.writeConfig()

    def deleteTempImages(self, dir: str):
        """Delete images in directory provided

        Args:
        dir -- Directory to delete imgs from
        """
        x = os.listdir(dir)
        for img in x:
            if img.endswith(".jpg"):
                os.remove(os.path.join(dir, img))

    # TODO: Type checking
    def downloadChapters(self):
        """Download a range of chapters and update progress bars"""
        self.exportPath = self.pathText.text()

        s, e = self.startChapter.value(), self.endChapter.value()

        if s > e:
            e, s = s, e

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
        # self.exportPath = self.pathText.text()
        # # ? Manga Title, Export Path, Last Chapter, URL, SRC, KEY

        # # TODO: Add image src and keyword into dictionary
        dictionary = {
            "Manga": self.mangaTitle,
            "Export Path": self.exportPath,
            "Last Chapter": self.endChapter.value(),
        }

        # # Writing to sample.json
        with open(self.configFileName, "w") as outfile:
            json.dump(dictionary, outfile)

        pass

    def readConfig(self):
        """Reads in configuration file and sets attributes in class"""
        if not os.path.exists(self.configFileName):
            return
        try:
            with open(self.configFileName, "r") as openfile:
                json_object = json.load(openfile)

            print(json_object)

            """Format: Manga, Path, LastChapterDownloaded, URL"""
            self.mangaTitle = json_object["Manga"]
            self.exportPath = json_object["Export Path"]
            self.defaultChapter = json_object["Last Chapter"]

            # Set newly read values on GUI
            self.pathText.setText(self.exportPath)
            self.startChapter.setValue(int(self.defaultChapter))
            self.endChapter.setValue(int(self.defaultChapter))

        except:
            print("Failed to read configuration file")

    def download(self, chapter: int):
        """Download a given chapter to export path with webscraping"""
        url = f"https://steel-ball-run.com/manga/jojos-bizarre-adventure-steel-ball-run-chapter-{chapter}/"
        try:
            r = requests.get(url)
            soup = bs(r.text, "html.parser")

            images = soup.find_all("img")  # Get all images
        except:
            print("Error Accessing WebPage")
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

        print("DONE Success")

        self.deleteTempImages(self.tempFolder)
        print("Deleted")

        # Move pdf to exportPath
        self.exportPath = self.pathText.text()
        try:
            shutil.move(f"{chapter}.pdf", self.exportPath)
        except:
            os.remove(f"{chapter}.pdf")
            print("Chapter already exists")
        print(f"Moved chapter {chapter}")


app = QApplication(sys.argv)
mainwindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(1135)
widget.setFixedHeight(494)
widget.show()
sys.exit(app.exec_())
