import os.path
from urllib import parse
from bs4 import BeautifulSoup
import requests
from fpdf import FPDF
from PIL import Image
import logging
import uuid


class MangaCreator:
    def __init__(self):
        self.__manga_base_site = "https://ww6.readblackclover.com/chapter"
        self.__chapter_base_site = "https://blackclover.fandom.com/wiki/List_of_Chapters_and_Volumes"

        logging.basicConfig(filename="app.log", filemode="w", format="%(asctime)s - %(message)s", datefmt="%M:%S")
        logging.root.setLevel(logging.INFO)
        self.__logger = logging.getLogger()
        self.__logger.addHandler(logging.StreamHandler())

    def get_pages(self, chapter_no: int):
        self.__logger.info(f"Getting pages for chapter {chapter_no}")
        manga_site_url = f"{self.__manga_base_site}/black-clover-chapter-{chapter_no}/"

        html_page = requests.get(manga_site_url).text
        soup = BeautifulSoup(html_page, "html.parser")

        all_pages = soup.find_all("img", class_="js-page")

        page_urls = [page["src"] for page in all_pages]

        filenames: list = []
        for url in page_urls:
            filename = f"images/pages/{str(uuid.uuid4())}.png"
            with open(filename, "wb") as file:
                if "http" not in url:
                    url = f"{manga_site_url}{url}"

                url_quote = parse.quote_plus(url).replace("%0D", "")
                url = parse.unquote_plus(url_quote)
                response = requests.get(url)
                response_content = response.content

                file.write(response_content)
            image = Image.open(filename)
            image.save(filename, "PNG", quality=100, optimize=True)

            filenames.append(filename)

        self.__logger.info(f"There are {len(filenames)} pages in {chapter_no}")

        return filenames

    def get_volume_chapters(self, volume_no: int):
        html_page = requests.get(self.__chapter_base_site).text
        soup = BeautifulSoup(html_page, "html.parser")

        all_captions = soup.find_all("div", class_="lightbox-caption")
        for caption in all_captions:
            volume_name = caption.find("a").text
            if volume_name == fr"Volume {volume_no}":
                try:
                    chapter_boundaries = caption.text.split("Chapters")[1].split("-")
                except IndexError:
                    chapter_boundaries = caption.text.split("Chapter")[1].split("-")

                start, end = int(chapter_boundaries[0]), int(chapter_boundaries[1]) + 1
                chapters = [chapter for chapter in range(start, end)]

                self.__logger.info(f"Volume {volume_no} has {len(chapters)} chapters")

                return chapters

        self.__logger.error(f"Invalid volume {volume_no} inputted")
        raise ValueError("INVALID VOLUME INPUTTED")

    def create_book(self, manga_pages: list, volume_no: int):
        pdf = FPDF(unit="mm")
        self.__logger.info("Initializing fpdf object")

        manga_pages.insert(0, "images/cover.png")

        for page in manga_pages:
            file_obj = Image.open(page)
            w, h = file_obj.size

            width, height = float(w * 0.264583), float(h * 0.264583)

            # given we are working with A4 format size
            pdf_size = {"P": {"w": 210, "h": 297}, "L": {"w": 297, "h": 210}}

            # get page orientation from image size
            orientation = "P" if width < height else "L"

            #  make sure image size is not greater than the pdf format size
            width = width if width < pdf_size[orientation]["w"] else pdf_size[orientation]["w"]
            height = height if height < pdf_size[orientation]["h"] else pdf_size[orientation]["h"]

            pdf.add_page(orientation=orientation)

            background_file_name = "images/black_coloured.png"
            if not os.path.isfile(background_file_name):
                background = Image.new("RGB", (210, 297), "#000000")
                background.save(background_file_name)

            pdf.image(background_file_name, x=0, y=0, w=210, h=297)
            pdf.image(page, 0, 0, width, height)

            self.__logger.info(f"Creating page")

        file_name = f"Manga-Creator/output/Black-Clover-v{volume_no}.pdf"

        pdf.set_author("Yūki Tabata")
        pdf.set_creator("MangaCreator")
        pdf.set_title(f"Black Clover v{volume_no}")
        pdf.output(file_name)

        self.__logger.info("Book creation complete")
