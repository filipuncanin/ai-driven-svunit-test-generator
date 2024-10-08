import openpyxl
import re

def process_file(sv_file, xlsx_file):
    # Učitaj Excel tabelu
    workbook = openpyxl.load_workbook(xlsx_file)
    sheet = workbook.active

    # Pročitaj sve linije iz .sv datoteke
    with open(sv_file, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    # Procesiraj svaki red u tabeli
    for row in sheet.iter_rows(min_row=2, values_only=True):
        search_text = row[0]
        insert_text = row[2]

        # Obradi svaku liniju u datoteci 
        for i in range(len(lines)):
            if search_text in lines[i]:      
                end_quote_index = lines[i].rfind('")')
                if end_quote_index != -1:
                    lines[i] = (
                        lines[i][:end_quote_index] +
                        f' |{insert_text}|' +
                        lines[i][end_quote_index:]
                    )
                    
    # Sačuvaj izmene u novu datoteku
    with open(sv_file, 'w') as file:
        file.writelines(lines)

def main():
    process_file('top_wrapper_unit_test.sv', 'tabela_svojstava_dut.xlsx')
    process_file('top_tb_wrapper_unit_test.sv', 'tabela_svojstava_tb.xlsx')

    print("Bodovi dodati u Unit Test-ove.")

if __name__ == "__main__":
    main()

