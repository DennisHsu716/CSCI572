import re
import requests
from urllib.parse import quote_plus, unquote
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.yahoo.com/",
}


def unwrap_yahoo_redirect(href):
    m = re.search(r"/RU=([^/]+)/", href)
    if m:
        return unquote(m.group(1))
    return href


def scrape_search_result(soup):
    containers = soup.find_all(
        "div",
        attrs={"class": lambda c: c and {"algo", "algo-sr"}.issubset(c.split())}
    )
    print(f"找到 {len(containers)} 個候選結果容器\n")

    results = []
    for container in containers:
        link_tag = container.find("a", href=True)
        if not link_tag:
            continue
        real_url = unwrap_yahoo_redirect(link_tag["href"])
        if real_url not in results:
            results.append(real_url)
        if len(results) == 10:
            break

    return results


url = "https://www.search.yahoo.com/search?p=" + quote_plus("eiffel tower")
response = requests.get(url, headers=HEADERS, timeout=10)
print("狀態碼:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
results = scrape_search_result(soup)

print(f"\n抓到 {len(results)} 個結果：")
for i, r in enumerate(results, 1):
    print(f"{i}. {r}")
