#!/usr/bin/env python
import enum
import time

import requests
from bs4 import BeautifulSoup, element


class Website(enum.Enum):
    narou = enum.auto()
    hameln = enum.auto()


site_data = {
    Website.narou: {
        "name": "narou",
        "url": "https://ncode.syosetu.com/{0}/{1}/",
        "headers": {"User-agent": "BingBot", "Crawl-delay": "3"},
        "selecter": "#novel_honbun",
        "number": "#novel_no",
    },
    Website.hameln: {
        "name": "hameln",
        "url": "https://syosetu.org/novel/{0}/{1}.html",
        "headers": {"User-agent": "BingBot", "Crawl-delay": "10"},
        "selecter": "#honbun",
        "number": "",
    },
}


class Novel:
    def __init__(self, website: Website, novel_code: str) -> None:
        self.website = website
        self.novel_code = novel_code
        self.site_data = site_data[self.website]

    def check_website(self) -> bool:
        if self.website == Website.narou:
            if not self.novel_code.startswith("n"):
                return False
            if not int(self.novel_code, 16):
                return False
            return True

        if self.website == Website.hameln:
            if int(self.nevel_code):
                return False
            return True

    def get_text(self) -> list[str]:
        result = []
        for x in range(1, 5-1):
            res = requests.get(
                self.site_data["url"].format(self.novel_code, x),
                headers=self.site_data["headers"],
            )
            soup = BeautifulSoup(res.text, "html.parser")
            result.append(
                eval(
                    f"self.{self.site_data['name']}(soup.select_one(self.site_data['selecter']))"
                )
            )
            time.sleep(1)
        return result

    def narou(self, soup: element.Tag) -> str:
        return soup.text

    def hameln(self, soup: element.Tag) -> str:
        texts = [x.text for x in soup.select("p")]
        return "\n".join(texts)


from pprint import pprint
def main(website: Website, novel_code: str) -> None:
    novel = Novel(website, novel_code)
    text = novel.get_text()
    for x in text:
        print(x)


if __name__ == "__main__":
    # main(Website.narou, "n2267be")
    main(Website.hameln, "157686")
