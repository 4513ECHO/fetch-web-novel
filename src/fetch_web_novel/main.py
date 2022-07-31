#!/usr/bin/env python
from __future__ import annotations

import asyncio
import codecs
import enum
import io
import logging
import os
import platform
import sys
import time
import traceback
from argparse import ArgumentParser, Namespace
from typing import Callable, Optional, Union

import aiofiles
import aiohttp
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
    _ua = "fetch-web-novel/{0} (compatible; python-aiohttp/{1}; +{2}) {3} {4}".format(
        poetry["version"],
        poetry["dependencies"]["aiohttp"].replace("^", ""),
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

    async def _request(self, num: int) -> BeautifulSoup:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.site_data["url"].format(self.novel_code, num),
                headers=self.site_data["headers"],
            ) as res:
                html = await res.text()
                return BeautifulSoup(html, "html.parser")

    async def get_backnumber(self) -> int:
        soup: BeautifulSoup = await self._request(1)
        backnumber: element.Tag = soup.select_one(self.site_data["backnumber"]).text
        return int(backnumber.split("/")[-1])

    async def get_honbun(self, num: int) -> str:
        soup: BeautifulSoup = await self._request(num)
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


async def write_file(name: int, text: str) -> str:
    async with aiofiles.open(f"{name:03}.txt", "w") as f:
        await f.write(text)
        return f.name


async def write_sjis(file: str) -> None:
    os.chdir("sjis")
    encoder = codecs.getincrementalencoder("cp932")(errors="replace")
    async with aiofiles.open(f"../{file}", "r") as src:
        async with aiofiles.open(file, "wb") as dest:
            text = encoder.encode(await src.read())
            await dest.write(text.replace(b"\n", b"\r\n"))
            await dest.flush()
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
            loop = asyncio.get_event_loop()
            loop.run_until_complete(func(*args, **kwargs))
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    return wrapper


@return_status
async def main() -> None:
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

    max_num: int = await novel.get_backnumber()
    for x in range(args.start, max_num + 1):
        honbun: str = await novel.get_honbun(x)
        if args.toSJIS:
            file = await write_file(x, honbun)
            await write_sjis(file)
        else:
            file = await write_file(x, honbun)
        time.sleep(1)
        print(f"\rWriting... ({x} / {max_num})", end="")
    print("\nDone.")


if __name__ == "__main__":
    main()
