class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег.
    """
    pass


class TableException(Exception):
    """Вызывается при несоответствии таблицы на странице ожиданиям.
    """
    pass
