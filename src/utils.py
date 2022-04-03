import logging

from bs4 import BeautifulSoup
from requests import RequestException

import constants as const
from exceptions import ParserFindTagException, TableException


def get_response(session, url):
    """Перехват ошибки RequestException.
    """
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def make_soup(url, session):
    """Получение объекта BeautifulSoup
    """
    responce = get_response(session, url)
    if responce is None:
        return None
    return BeautifulSoup(responce.text, 'lxml')


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов.
    """
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def view_pep_page(url, session):
    """Проверяет статус и тип на странице PEP`а.
    """
    tipe = status = None
    soup = make_soup(url, session)
    if soup is None:
        return None
    pep_info = find_tag(soup, 'dl')
    dt_tags = pep_info.find_all('dt')
    dd_tags = pep_info.find_all('dd')
    dt_dd_tags = tuple(zip(dt_tags, dd_tags))
    for tags in dt_dd_tags:
        if tipe is not None and status is not None:
            break
        if tags[0].text == 'Type':
            if tipe is not None:
                logging.warning(
                    f'Повтор текста в тегах типа на странице {url}'
                )
            tipe = tags[1].text
        elif tags[0].text == 'Status':
            if status is not None:
                logging.warning(
                    f'Повтор текста в тегах статуса на странице {url}'
                )
            status = tags[1].text
    return tipe, status


def add_to_dict(dic, value):
    """Увеличивает значении при наличии ключа либо создаёт новый ключ.
    """
    if value in dic:
        dic[value] += 1
    else:
        dic[value] = 1


def check_status(page_status, type_status_in_table, page_url):
    """Проверяет статусs в основной таблице и на отдельной странице PEP.
    """
    if len(type_status_in_table) == 2:
        table_status = type_status_in_table[1]
        if page_status not in const.EXPECTED_STATUS[table_status]:
            logging.info(f'Несовпадающие статусы:\n{page_url}')
    elif len(type_status_in_table) == 1:
        if page_status not in const.EXPECTED_STATUS['']:
            logging.info(f'Несовпадающие статусы:\n{page_url}')
    else:
        raise TableException(
            f'Неожиданная содержание статуса {type_status_in_table}'
            )
