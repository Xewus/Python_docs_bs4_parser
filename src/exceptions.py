class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег.
    """
    ...


class TableException(Exception):
    """Вызывается при несоответствии ожиданиям таблицы на странице.
    """
    ...
