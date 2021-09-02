#!/usr/bin/env python
import codecs
import enum
import os
import sys
import time
from argparse import ArgumentParser, Namespace
from typing import Callable, Optional, Union

import requests
from bs4 import BeautifulSoup, element


class Website(enum.Enum):
    narou = enum.auto()
    hameln = enum.auto()


headers = {
    "User-agent": "fetch-web-novel Crawler/0.2.3 (https://github.com/4513ECHO/fetch-web-novel)",
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

_error_handler_registered = False
# https://www.dsri.jp/database_service/jicfsifdb/mojicheck.html
_str_sjis_mapping = {"頬": "0x966a"}


def _error_handler(err: UnicodeError) -> tuple[bytes]:
    (encodeing, text, i, j, msg) = err.args
    return (_str_sjis_mapping.get(text[i], ""), j)


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
    global _error_handler_registered
    if not _error_handler_registered:
        codecs.register_error("my_custom_handler", _error_handler)
        _error_handler_registered = True
    os.chdir("sjis")
    with codecs.open(f"../{file}", "r", "utf-8") as f_utf, codecs.open(
        file, "w", "cp932", errors="my_custom_handler"
    ) as f_sjis:
        text = "\r\n".join(f_utf.read().splitlines())
        f_sjis.write(text)
    os.chdir("../")


# def show_progress(max: int, current: int) -> None:
#     pass


def get_args() -> Namespace:
    parser = ArgumentParser(
        description="CLI tool to retrieve the contents of "
        "a specified novel from a novel submission website",
        usage="./%(prog)s [options...] <novel_code>",
    )
    site = parser.add_mutually_exclusive_group(required=True)
    site.add_argument(
        "-N",
        "--narou",
        action="store_true",
        help="set the destination website to 'Shosetsuka ni Narou'",
    )
    site.add_argument(
        "-H",
        "--hameln",
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
        "-J", "--toSJIS", action="store_true", help="create a file in Shift-JIS format"
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

    max_num: int = novel.get_backnumber()
    for x in range(1, max_num + 1):
        honbun: str = novel.get_honbun(x)
        if args.toSJIS:
            file = write_file(x, honbun)
            write_sjis(file)
        else:
            file = write_file(x, honbun)
        time.sleep(1)
        print(f"\rWriting... ({x} / {max_num})", end="")
    print("\nDone.")


def return_status(func: Callable) -> int:
    try:
        func()
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as err:
        print(f"[ERROR]:{err}")
        sys.exit(1)


def script() -> None:
    return_status(main)


if __name__ == "__main__":
    script()
