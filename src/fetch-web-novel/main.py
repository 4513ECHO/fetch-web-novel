#!/usr/bin/env python
from __future__ import annotations

import codecs
import enum
import logging
import os
import platform
import sys
import time
from argparse import ArgumentParser, Namespace
from typing import Callable, Optional, Union

import requests
import toml
from bs4 import BeautifulSoup, element


class Website(enum.Enum):
    narou = enum.auto()
    hameln = enum.auto()


def user_agent() -> str:
    pyproject_toml = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
    )
    poetry = toml.load(open(pyproject_toml))["tool"]["poetry"]
    _ua = "fetch-web-novel/{0} (compatible; python-requests/{1}; +{2}) {3} {4}".format(
        poetry["version"],
        poetry["dependencies"]["requests"].replace("^", ""),
        poetry["repository"],
        f"{platform.system()}-{platform.processor()}",
        f"python-{platform.python_version()}",
    )
    return _ua


logger = logging.getLogger(__name__)
headers = {
    "User-agent": user_agent(),
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
    os.chdir("sjis")
    with codecs.open(f"../{file}", "r", "utf-8") as f_utf, codecs.open(
        file, "w", "cp932"
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
    parser.add_argument("-s", "--start", type=int, default=1)
    parser.add_argument(
        "-J", "--toSJIS", action="store_true", help="create a file in Shift-JIS format"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=user_agent(),
        help="Show version and exit",
    )
    args = parser.parse_args()
    return args


def return_status(func: Callable[..., None]) -> Callable:
    def wrapper(*args, **kwargs):  # type: ignore
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as err:
            print(f"[ERROR]:{err}")
            sys.exit(1)
    return wrapper


@return_status
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
    print(f"{max_num=}")
    for x in range(args.start, max_num + 1):
        print(f"{x=}")
        honbun: str = novel.get_honbun(x)
        print("get_honbun")
        if args.toSJIS:
            file = write_file(x, honbun)
            print("write_file")
            write_sjis(file)
            print("write_file2")
        else:
            file = write_file(x, honbun)
            print("write_file")
        time.sleep(1)
        print(f"\rWriting... ({x} / {max_num})", end="")
    print("\nDone.")


if __name__ == "__main__":
    main()
