import csv
import datetime as dt
import logging

from prettytable import PrettyTable

import constants as const
from constants import BASE_DIR  # especially for tests


def control_output(results, cli_args):
    """Управляет выводом результата работы парсера.

    Args:
        results (list): Список с результатми парсера.
        cli_args (Namespace): Управляющие аргументы.
    """
    if cli_args.output == 'file':
        file_output(results, cli_args)
    elif cli_args.output == 'pretty':
        pretty_output(results)
    else:
        default_output(results)


def default_output(results):
    """Выводит результаты работы парсера `по-умолчанию`.
      Печатает результаты в окне терминала.

    Args:
        results (list): Список с результатми работы парсера.
    """
    for row in results:
        print(*row)


def pretty_output(results):
    """Выводит результаты работы парсера в терминал в виде таблицы.

    Args:
        results (list): Список с результатми работы парсера.
    """
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    """Сохраняет результаты работы парсера в файл .csv .

    Args:
        results (list): Список с результатми работы парсера.
        cli_args (Namespace): Управляющие аргументы.
    """
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now = now.strftime(const.DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now}.csv'
    file_path = results_dir / file_name
    with open(file=file_path, mode='w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)

    logging.info(f'Файл с результатами был сохранён: {file_path}')
