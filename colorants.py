from pathlib import Path
import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent.resolve()
CACHE = HERE.joinpath("cache")
COLORCHEM_DIRECTORY = CACHE.joinpath("colorchem")
COLORCHEM_DIRECTORY.mkdir(parents=True, exist_ok=True)

URLS = [
    "https://www.colorchem.com/pet",
]
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}


def main():
    for url in URLS:
        path = COLORCHEM_DIRECTORY.joinpath(url.split("/")[-1] + ".html")
        if not path.is_file():
            res = requests.get(url, timeout=5, headers=headers)
            res.raise_for_status()
            path.write_text(res.text)
        soup = BeautifulSoup(path.read_text(), features="html.parser")

        for div in soup.find_all(class_="text"):
            print(div.prettify())


if __name__ == '__main__':
    main()
