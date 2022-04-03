import csv
import datetime as dt
import logging

from prettytable.colortable import ColorTable, Themes

from constants import BASE_DIR, DATETIME_FORMAT


def control_output(results, cli_args):
    if cli_args.output == 'file':
        file_output(results, cli_args)
    elif cli_args.output == 'pretty':
        pretty_output(results)
    else:
        default_output(results)


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results):
    table = ColorTable(theme=Themes.OCEAN)
    table.field_names = results[0]
    table.align = 'l'
    # Добавляем все строки, начиная со второй (с индексом 1).
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now}.csv'
    file_path = results_dir / file_name
    with open(file=file_path, mode='w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)

    logging.info(f'Файл с результатами был сохранён: {file_path}')