import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser as parser, configure_logging
import constants as const
from constants import BASE_DIR  # especially for tests
from outputs import control_output as output
from utils import find_tag, make_soup, view_pep_page


def whats_new(session):
    whats_new_url = urljoin(const.MAIN_DOC_URL, 'whatsnew/')
    soup = make_soup(whats_new_url, session)
    if soup is None:
        return
    main_div = find_tag(soup, 'div', {'id': 'what-s-new-in-python'})
    div_with_ul = main_div.find('div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Aвтор')]
    for section in tqdm(sections_by_python, colour='green'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        soup = make_soup(version_link, session)
        if soup is None:
            continue
        h1 = soup.find('h1')
        h1_text = h1.text
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1_text, dl_text))

    return results


def latest_versions(session):
    soup = make_soup(const.MAIN_DOC_URL, session)
    if soup is None:
        return None
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )

    return results


def download(session):
    downloads_url = urljoin(const.MAIN_DOC_URL, 'download.html')
    soup = make_soup(downloads_url, session)
    if soup is None:
        return
    table = find_tag(soup, 'table')
    pdf = table.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_link = pdf['href']
    pdf_url = urljoin(downloads_url, pdf_link)
    filename = pdf_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    zip_path = downloads_dir / filename

    responce = session.get(pdf_url)
    with open(zip_path, 'wb') as file:
        file.write(responce.content)

    logging.info(f'Архив был загружен и сохранён: {zip_path}')


def pep(session):
    results = [('Статус', 'Количество')]
    total_by_status = {}
    for value in const.EXPECTED_STATUS.values():
        for key in value:
            total_by_status[key] = 0
    soup = make_soup(const.PEP_DOC_URL, session)
    if soup is None:
        return None
    pep_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    index_body = find_tag(pep_index, 'tbody')
    index_rows = index_body.find_all('tr')

    for row in tqdm(index_rows, colour='blue'):
        if row.td is None:
            logging.warning(f'Не найден тэг <td> в строке {row}')
            continue
        type_status_in_table = row.td.text
        link = find_tag(row, 'a')
        link = link['href']
        page_url = urljoin(const.PEP_DOC_URL, link)
        type_status = view_pep_page(page_url, session)
        if type_status is None:
            continue
        _, page_status = type_status
        if page_status in total_by_status:
            total_by_status[page_status] += 1
        else:
            total_by_status[page_status] = 1  # for `April Fool!`
        if len(type_status_in_table) == 2:
            table_status = type_status_in_table[1]
            if page_status not in const.EXPECTED_STATUS[table_status]:
                logging.info(f'Несовпадающие статусы:\n{page_url}')

    [results.append((key, value)) for key, value in total_by_status.items()]
    results.append(('Total', sum(value for value in total_by_status.values())))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'pep': pep,
    'download': download,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()

    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode

    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
