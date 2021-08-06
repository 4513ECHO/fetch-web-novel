#!/usr/bin/env python
from argparse import ArgumentParser, Namespace
import codecs
import enum
import time
from typing import Union, Optional, Callable
import os

from bs4 import BeautifulSoup, element
import requests


class Website(enum.Enum):
    narou = enum.auto()
    hameln = enum.auto()


headers = {
    "User-agent": "fetch-web-novel Crawler/0.2.0 (https://github.com/4513ECHO/fetch-web-novel)",
    "Crawl-delay": "3",
}
site_data = {
    Website.narou: {
        "name": "narou",
        "url": "https://ncode.syosetu.com/{0}/{1}/",
        "headers": headers,
        "honbun": "#novel_honbun",
        "backnumber": "#novel_no",
    },
    Website.hameln: {
        "name": "hameln",
        "url": "https://syosetu.org/novel/{0}/{1}.html",
        "headers": headers,
        "honbun": "#honbun",
        "backnumber": ".ss > div:first-of-type",
    },
}


class Novel:
    def __init__(self, website: Website, novel_code: str) -> None:
        self.website: Website = website
        self.site_data: dict[str] = site_data[self.website]
        self.novel_code: str = novel_code

    def _request(self, num: int) -> BeautifulSoup:
        res: requests.medels.Response = requests.get(
            self.site_data["url"].format(self.novel_code, num),
            headers=self.site_data["headers"],
        )
        return BeautifulSoup(res.text, "html.parser")

    def get_backnumber(self) -> int:
        soup: BeautifulSoup = self._request(1)
        backnumber: element.Tag = soup.select_one(self.site_data["backnumber"]).text
        return int(backnumber.split("/")[-1])

    def get_honbun(self, num: int) -> str:
        soup: BeautifulSoup = self._request(num)
        honbun: element.Tag = soup.select_one(self.site_data["honbun"])
        if self.site_data["name"] == "narou":
            return self._narou(honbun)
        if self.site_data["name"] == "hameln":
            return self._hameln(honbun)

    def _narou(self, soup: element.Tag) -> str:
        return soup.text

    def _hameln(self, soup: element.Tag) -> str:
        text = map(lambda x: x.text, soup)
        return "\n".join(text)


def write_file(name: Union[str, int], text: str) -> str:
    with open(f"{name}.txt", "w") as f:
        f.write(text)
        return f.name


def write_sjis(file: str) -> None:
    with codecs.open(file, "r", "utf-8") as f_utf, codecs.open(
        f"sjis_{file}", "w", "shift_jis"
    ) as f_sjis:
        text = f_utf.read()
        f_sjis.write(text)


# def show_progress(max: int, current: int) -> None:
#     pass


def get_args() -> Namespace:
    parser = ArgumentParser(
        description="CLI tool to retrieve the contents of "\
                    "a specified novel from a novel submission website",
        usage="./%(prog)s [options...] <novel_code>"
    )
    site = parser.add_mutually_exclusive_group(required=True)
    site.add_argument(
        "-N", "--narou",
        action="store_true",
        help="set the destination website to 'Shosetsuka ni Narou'",
    )
    site.add_argument(
        "-H", "--hameln",
        action="store_true",
        help="set the destination website to 'Hameln'",
    )
    parser.add_argument("novel_code", help="set the code of the novel to be retrieve")
    # parser.add_argument(
    #     "-b", "--back-number",
    #     default=None,
    #     metavar="<INT>-<INT>"
    #     type=lambda x: map(int, x.split("-"))[:2],
    # )
    # parser.add_argument("-d", "--dirname", default=None)
    parser.add_argument(
        "-J", "--toSJIS",
        action="store_true",
        help="create a file in Shift-JIS format"
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args: Namespace = get_args()
    if args.narou:
        website = Website.narou
    elif args.hameln:
        website = Website.hameln
    novel: Novel = Novel(website, args.novel_code)
    os.makedirs(novel.novel_code, exist_ok=True)
    os.chdir(novel.novel_code)
    if args.toSJIS:
        os.makedirs("sjis", exist_ok=True)
        os.chdir("sjis")

    max_num: int = novel.get_backnumber()
    for x in range(1, max_num + 1):
        honbun: str = novel.get_honbun(x)
        file = write_file(x, honbun)
        if args.toSJIS:
            write_sjis(file)
        time.sleep(1)
        print(f"\rWriting... ({x} / {max_num})", end="")
    print("\nDone.")


def return_status(func: Callable) -> int:
    try:
        func()
        return 0
    except Exception as err:
        print(f"[ERROR]:{err}")
        return 1


if __name__ == "__main__":
    return_status(main)
