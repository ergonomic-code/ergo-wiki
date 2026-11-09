"""Проверяет внутренние ссылки, изображения и якоря в статьях собранной вики."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.article = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'article':
            self.article = True
        if self.article:
            for attr in ('href', 'src'):
                if attrs.get(attr):
                    self.links.append(attrs[attr])

    def handle_endtag(self, tag):
        if tag == 'article':
            self.article = False


def check(root, base_url):
    base_url = base_url.rstrip('/') + '/'
    base = urlsplit(base_url)
    pages = {file: Page(file.read_text()) for file in root.rglob('*.html')}
    errors = []
    checked = 0
    for file, page in pages.items():
        url = urljoin(base_url, file.relative_to(root).as_posix().removesuffix('index.html'))
        for link in page.links:
            target = urlsplit(urljoin(url, link))
            if target.netloc != base.netloc or target.scheme not in ('http', 'https'):
                continue
            checked += 1
            if not target.path.startswith(base.path):
                errors.append(f'{file.relative_to(root)}: ссылка вне сайта {link}')
                continue
            path = root / unquote(target.path[len(base.path):])
            if path.is_dir():
                path /= 'index.html'
            if not path.is_file():
                errors.append(f'{file.relative_to(root)}: отсутствует {link}')
            elif path in pages and target.fragment and unquote(target.fragment) not in pages[path].ids:
                errors.append(f'{file.relative_to(root)}: отсутствует якорь {link}')
    print(f'HTML: {len(pages)}; внутренних ссылок/изображений: {checked}; ошибок: {len(errors)}')
    for error in errors:
        print(error)
    return bool(errors or not pages)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--base-url', default='https://ergowiki.azhidkov.pro/')
    args = parser.parse_args()
    raise SystemExit(check(args.directory.resolve(), args.base_url))
