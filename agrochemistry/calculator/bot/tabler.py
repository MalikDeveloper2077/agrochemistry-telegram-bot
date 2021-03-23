from random import randint

from imgkit import from_string

from calculator.models import PHASES


table_css = """
body {
  font-family: sans-serif;
  font-size: 13px;
}
td {
  padding: 10px;
  text-align: center;
  background: #A1D8D6;
  color: #00675a;
}
.product-name {
  width: 20%;
  text-align: left;
  background: #b1d2d1;
}
.blank, .phases td {
  background: #fff;
  color: #000;
}
table {
  width: 100%;
  margin: 0 auto;
}
"""


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
 </body>
</html>
"""


def get_filled_html_string_table(row_products, column_titles, user_storage_volume: int):
    rows = []
    for product in row_products:
        row = f'<tr><td class="product-name">{product.name}</td>'
        for col_value, _ in column_titles:
            try:
                r = user_storage_volume  # NEEDS FOR FORMULAS
                cell_value = eval(product.phases.get(name=col_value).formula)
            except:
                cell_value = '-'
            row += f'<td>{cell_value}</td>'
        rows.append(row)

    return get_html(rows, column_titles, table_css)


def get_rendered_table_img_path(row_products, user_storage_volume):
    html_string = get_filled_html_string_table(row_products, PHASES, user_storage_volume)
    table_img_name = f'calculator/bot/tables_images/table-{randint(0, 99000)}.jpg'
    from_string(html_string, table_img_name)
    return table_img_name
