from MangaCreator import MangaCreator
import os


def main():
    creator = MangaCreator()

    chapter_volume_list = []

    volume = int(input("Input volume number: Volume "))

    volume_chapters = creator.get_volume_chapters(volume)

    for chapter in volume_chapters:
        manga_pages = creator.get_pages(chapter)
        chapter_volume_list += manga_pages
    creator.create_book(chapter_volume_list, volume)

    [os.remove(f"images/pages/{file}") for file in os.listdir("images/pages")]


if __name__ == "__main__":
    main()
