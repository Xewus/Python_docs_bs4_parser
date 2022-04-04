import logging

from bs4 import BeautifulSoup
from requests import RequestException

import constants as const
from exceptions import ParserFindTagException, TableException


def get_response(session, url):
    """Перехват ошибки RequestException.

    Args:
        session (request.Session): Объект сессии.
        url (str): Адрес web-страницы.

    Returns:
        response(request.Response): Ответ сервера с запрошенного адреса.
        None: При ошибке загрузки запрошенной страницы.

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
    """Получение объекта BeautifulSoup.

    Args:
        url (str): Адрес web-сраницы.
        session (request.Session): Объект сессии.

    Returns:
        bs4.BeautifulSoup: Текст запрошенной страницы.
        None: При ошибке загрузки запрошенной страницы.
    """
    responce = get_response(session, url)
    if responce is None:
        return None
    return BeautifulSoup(responce.text, 'lxml')


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов.

    Args:
        soup (bs4.BeautifulSoup): Выбранная часть текста страницы.
        tag (str): Искомый тэг.
        attrs (dict, optional): Дополнительные метки для поиска.
                                  Defaults to None.

    Raises:
        ParserFindTagException: При отсутствии в тексте искомого тэга.

    Returns:
        bs4.BeautifulSoup: Часть текста находящейся в запрошенном тэге.
    """
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def view_pep_page(url, session):
    """Проверяет статус и тип на странице PEP`а.

    Args:
        url (str): Адрес web-страницы.
        session (request.Session): Объект сессии.

    Returns:
        tuple(str, str): Тип PEP`а, статус PEP`а.
    """
    tipe = status = ''
    soup = make_soup(url, session)
    if soup is None:
        return None
    pep_info = find_tag(soup, 'dl')
    dt_tags = pep_info.find_all('dt')
    dd_tags = pep_info.find_all('dd')
    dt_dd_tags = tuple(zip(dt_tags, dd_tags))
    for tags in dt_dd_tags:
        if tipe != '' and status != '':
            break
        if tags[0].text == 'Type':
            if tipe != '':
                logging.warning(
                    f'Повтор текста `Type` на странице {url}'
                )
            tipe = tags[1].text
        elif tags[0].text == 'Status':
            if status != '':
                logging.warning(
                    f'Повтор текста `Status` на странице {url}'
                )
            status = tags[1].text
    return tipe, status


def check_status(page_status, type_status_in_table, page_url):
    """Сравнивает статусы в основной таблице и на отдельной странице PEP.

    Args:
        page_status (str): Статус на странице PEP`а.
        type_status_in_table (str): Статус в таблице.
        page_url (str): адрес страницы PEP`а.

    Raises:
        TableException: Некорректное содержание статуса в таблице.
    """
    if len(type_status_in_table) <= 2:
        table_status = type_status_in_table[1:]
        if page_status not in const.EXPECTED_STATUS[table_status]:
            logging.info(f'Несовпадающие статусы:\n{page_url}')
    else:
        raise TableException(
            f'Неожиданное содержание статуса {type_status_in_table}'
            )
