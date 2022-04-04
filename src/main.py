import collections
import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

import configs as conf
import constants as const
import outputs
import utils

BASE_DIR = const.BASE_DIR


def whats_new(session):
    """Собирает ссылки на статьи о нововведениях в Python.

    Args:
       session (request.Session): Объект сессии.

    Returns:
        results (list[tuple]): Список с ссылками и авторами.
        None: При ошибке загрузки страницы.
    """
    whats_new_url = urljoin(const.MAIN_DOC_URL, 'whatsnew/')
    soup = utils.make_soup(whats_new_url, session)
    if soup is None:
        return None
    main_div = utils.find_tag(soup, 'div', {'id': 'what-s-new-in-python'})
    div_with_ul = utils.find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Aвтор')]
    for section in tqdm(sections_by_python, colour='green'):
        link = utils.find_tag(section, 'a')
        link = link['href']
        full_link = urljoin(whats_new_url, link)
        soup = utils.make_soup(full_link, session)
        if soup is None:
            continue
        h1 = utils.find_tag(soup, 'h1')
        h1_text = h1.text
        dl = utils.find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((full_link, h1_text, dl_text))

    return results


def latest_versions(session):
    """Собирает статусы и ссылки на документацию последних версий Python.

    Args:
        session (request.Session): Объект сессии.

    Raises:
        Exception: Некорректные настройки парсера для поиска.

    Returns:
        results (list[tuple]): Список ссылок на документацию.
        None: При ошибке загрузки страницы.
    """
    soup = utils.make_soup(const.MAIN_DOC_URL, session)
    if soup is None:
        return None
    sidebar = utils.find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
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
    """Загружает документацию (pdf) последней версии Python.

    Args:
        session (request.Session): Объект сессии.
    """
    downloads_url = urljoin(const.MAIN_DOC_URL, 'download.html')
    soup = utils.make_soup(downloads_url, session)
    if soup is None:
        return None

    table = utils.find_tag(soup, 'table')
    pdf = utils.find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
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
    return None


def pep(session):
    """Проверяет и подсчитывает статусы PEP`ов и их количество.

    Args:
        session (request.Session): Объект сессии.

    Returns:
        results (list[tuple]): Список со статусами PEP`ов.
        None: При ошибке загрузки страницы.
    """
    soup = utils.make_soup(const.PEP_DOC_URL, session)
    if soup is None:
        return None

    pep_index = utils.find_tag(soup, 'section', {'id': 'numerical-index'})
    index_body = utils.find_tag(pep_index, 'tbody')
    index_rows = index_body.find_all('tr')

    total_by_status = collections.defaultdict(int)
    results = [('Статус', 'Количество')]
    for row in tqdm(index_rows, colour='blue'):
        td_tag = utils.find_tag(row, 'td')
        type_status_in_table = td_tag.text

        link = utils.find_tag(row, 'a')
        link = link['href']
        page_url = urljoin(const.PEP_DOC_URL, link)

        type_status_on_page = utils.view_pep_page(page_url, session)
        if type_status_on_page is None:
            logging.warning(
                f'Не удалось просмотреть страницу:\n{page_url}'
            )
            continue

        _, page_status = type_status_on_page
        total_by_status[page_status] += 1
        utils.check_status(page_status, type_status_in_table, page_url)

    total = 0
    for key, value in total_by_status.items():
        results.append((key, value))
        total += value
    results.append(('Total', total))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'pep': pep,
    'download': download,
}


def main():
    """Запускает парсер.
    """
    conf.configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = conf.configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()

    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode

    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        outputs.control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
