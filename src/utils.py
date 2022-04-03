import logging

from bs4 import BeautifulSoup
from requests import RequestException
from exceptions import ParserFindTagException


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
    soup = make_soup(url, session)
    if soup is None:
        return None
    pep_info = find_tag(soup, 'dl')
    print(pep_info)
