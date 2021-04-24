from datetime import datetime, timedelta
from random import randint

from tablepyxl import tablepyxl
from imgkit import from_string
from ics import Calendar, Event

from calculator.models import PHASES, Phase
from calculator.bot.config import CALENDAR_EVENT_NAME, EVENT_URL


with open("calculator/bot/table/table_styles.css", "r") as styles:
    table_css = styles.read().replace('\n', '')


def get_html(rows, column_titles, css):
    return f"""
<!DOCTYPE html>
<html>
 <head>
  <meta charset="utf-8">
  <style>
    {css}
  </style>
 </head>
 <body>
  <table>
   <tr class="phases">
     <td class="product-name"></td>
     <td>{f'</td><td>'.join([title for val, title in column_titles])}
   </tr>
   {rows}
  </table>

  <img class="watermark" src="logo.jpg" />
 </body>
</html>
"""


def get_table_cell_html(value, is_title=False, background=None):
    cell = f'<td '
    if is_title:
        cell += 'class="product-name"'

    if background:
        cell += f'style="background: {background}"'

    cell += f'>{value}</td>'
    return cell


def get_filled_html_string_table(row_products, column_titles, user_storage_volume: int):
    """Return result table html"""
    rows = []
    for product in row_products:
        row = '<tr>'

        try:
            row += get_table_cell_html(product.name, is_title=True, background=product.target.color)
        except AttributeError:
            row += get_table_cell_html(product.name, is_title=True)

        for col_value, _ in column_titles:
            try:
                r = user_storage_volume  # NEEDS FOR FORMULAS
                cell_value = eval(product.phases.get(name=col_value).formula)
            except:
                cell_value = '-'

            try:
                row += get_table_cell_html(cell_value, background=product.target.color)
            except AttributeError:
                row += get_table_cell_html(cell_value)
        rows.append(f'{row}</tr>')

    return get_html(rows, column_titles, table_css)


def get_rendered_table_img_path(row_products, user_storage_volume):
    """Create the table image and return the file path"""
    html_string = get_filled_html_string_table(row_products, PHASES, user_storage_volume)
    table_img_name = f'calculator/bot/tables_images/table-{randint(0, 99000)}.jpg'
    from_string(html_string, table_img_name, options={"enable-local-file-access": None})
    return table_img_name


def get_created_xls_table_path(row_products, user_storage_volume):
    """Create the xls table and return the file path"""
    table_html_string = get_filled_html_string_table(row_products, PHASES, user_storage_volume)
    xls_path = f'calculator/bot/tables_xls/table-{randint(1, 99000)}.xlsx'
    tablepyxl.document_to_xl(table_html_string, xls_path)
    return xls_path


def create_calendar_event(date, name, description):
    e = Event()
    e.name = name
    e.description = description
    e.begin = date
    e.end = date + timedelta(hours=24)
    e.url = EVENT_URL
    return e


def get_created_calendar_file_path(products, user_storage_volume, start_date: str):
    """Create the table .ics file and return the file path"""
    c = Calendar()
    r = user_storage_volume  # NEED FOR FORMULAS

    events_dates_and_descriptions = {}  # {Date obj: [product_description1, Product_description2]}
    for product in products:
        try:
            last_phase_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return ValueError(INCORRECT_START_CYCLE_MESSAGE)

        for phase in [phase for phase, val in PHASES]:
            try:
                product_phase = product.phases.get(name=phase)
            except Phase.DoesNotExist:
                continue

            if not product_phase.formula:
                continue

            description = f'{product.name} - {eval(product_phase.formula)} ml'
            try:
                events_dates_and_descriptions[last_phase_date].append(description)
            except:
                events_dates_and_descriptions[last_phase_date] = [description]

            last_phase_date += timedelta(weeks=product_phase.get_weeks())

    for date in events_dates_and_descriptions:
        description = '\n'.join([
            product_description for product_description in events_dates_and_descriptions[date]
        ])
        event = create_calendar_event(date, CALENDAR_EVENT_NAME.format(r), description)
        c.events.add(event)

    calendar_path = f'calendar-{randint(1, 99999)}.ics'
    with open(calendar_path, 'w') as f:
        f.writelines(c)

    return calendar_path
