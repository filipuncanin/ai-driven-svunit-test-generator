from mymodule import *

def create_sv_holder(vhd_file):
    inputs, outputs, signals, constants, states = read_vhdl_file(os.getcwd() + "/" + vhd_file)
    
    # Početak modula
    sv_code = f"module top (\n"

    # Dodajemo ulaze
    for inp in inputs:
        sv_code += f"    input  logic"
        if inp['size'] > 1:
            sv_code += f" [{inp['size']-1}:0]"
        sv_code += f"   {inp['name']},\n"

    # Dodajemo izlaze
    for outp in outputs:
        sv_code += f"    output logic"
        if outp['size'] > 1:
            sv_code += f" [{outp['size']-1}:0]"
        sv_code += f"   {outp['name']},\n"

    # Uklanjamo poslednji zarez i dodajemo zatvaranje porta
    sv_code = sv_code.rstrip(",\n") + "\n);\n"

    # Dodajemo tSTATE tip i stanja
    sv_code += "\ttypedef enum logic [3:0] {\n"
    for state in states:
        sv_code += f"\t\t{state},\n"
    sv_code = sv_code.rstrip(",\n") + "\n\t} tSTATE;\n\n"
    
    # Dodajemo signale i stanja
    sv_code += "\ttSTATE sSTATE, sNEXT_STATE;\n\n"
    for sig in signals:
        sv_code += f"\tlogic"
        if sig['size'] > 1:
            sv_code += f" [{sig['size']-1}:0]"
        sv_code += f" {sig['name']};\n"

    # Dodajemo konstante
    for const in constants:
        sv_code += f"\n\tlocalparam {const['name']}"
        if const['size'] > 1:
            sv_code += f" = {const['size']}'b{const['value'].strip('\"')};"
        else:
            sv_code += f" = 1'b{const['value'].strip('\"')};"
    
    # Zatvaranje modula
    sv_code += "\n\nendmodule\n"

    write_file("top.sv", sv_code)

def generate_opis(file_path):
    # GENERISANJE OPISA ZADATAKA NA OSNOVU TOP.VHD DATOTEKE
    if not os.path.isfile('assertions.txt'):
        content = read_file(file_path)

        gpt_message = "Please provide a detailed explanation of the functionality and structure of this code:\n" + content

        print("CHATGPT: Textual interpretation of the top unit. Waiting for response...") 
        response = ask_chatgpt(gpt_message)

        write_file("opis.txt", response)

def generate_assertions(top_file):

    def create_assertions(top_file):

        def adjust_assertions():
            file_path = 'assertions.txt'
            content = read_file(os.getcwd() + "/" + file_path)
            
            # Funkcija za transformaciju bitova
            def transform_bits(text):
                # Zameni bitove u formatu "xxxx" sa n'bx
                def replace_bit_format(match):
                    bits = match.group(1)
                    return f"{len(bits)}'b{bits}"
                
                # Zameni pojedinačne '0' i '1' sa 1'b0 i 1'b1
                def replace_single_bits(match):
                    bit = match.group(1)
                    return f"1'b{bit}"
                
                # Pronađi sve izraze u formatu "xxxx" i zameni ih
                text = re.sub(r'"([01]+)"', replace_bit_format, text)
                
                # Pronađi sve izraze '0' i '1' i zameni ih
                text = re.sub(r"'([01])'", replace_single_bits, text)
                
                return text
            
            transformed_content = transform_bits(content)
            
            #write_file(file_path, transformed_content)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(transformed_content)
                
        # GENERISANJE ASSERTIONA NA OSNOVU TOP.SV FAJLA I OPISA ZADATKA 
        if os.path.isfile(os.path.join(os.getcwd(), 'assertions.txt')):
            print("Requested assertions.txt already exists.")
        else:
            content = read_file(top_file)
            opis = read_file('opis.txt')

            gpt_message = (
                "Please generate SystemVerilog assertions based on the provided code and its textual description. Ensure the following:\n"
                "1. **Coverage**: Assertions should cover all possible cases.\n"
                "2. **Quantity**: Generate at least 50 unique assertions in a meaningful order.\n"  
                "3. **Uniqueness**: Avoid identical assertions; each must be distinct.\n"
                "4. **Syntax**:\n"
                "   - Assertion should be evaluated on the rising edge of the clock signal `iCLK`.\n"
                "   - Use only overlapped implication `( |-> )`.\n"
                "   - Each assertion should end with a `$display` statement for the pass case.\n"
                "   - Avoid `$info`, `$warning`, `$error`, or `$fatal`.\n"
                "   - `$display` message should start with 'ASSERTION i:', where `i` is the assertion number.\n"
                "   - Do not make false statement message.\n"
                "   - The number of open and closed parentheses must be the same.\n"
                "   - Use disable iff (iRST) every time when not checking iRST.\n"
                "5. **Formatting**:\n"
                "   - Each assertion and its corresponding `$display` statement must be on a single line.\n"
                "   - Do not create separate properties or sequences.\n"
                "   - Example: 'assert propery (@(posedge iCLK) causal property |-> consequence) $display('ASSERTION i: message');'\n"
                "6. **Syntax Checking**: Ensure that every open parenthesis is properly closed and that each assertion is syntactically correct.\n"
                "7. **Comments**: Do not include any comments in the code or outside of it.\n"
                "SystemVerilog code:\n" + content + "\n"
                "DESCRIPTION OF FUNCTIONALITY:\n" + opis)

            print("CHATGPT: Assertions creation. Waiting for response...")    
            response = ask_chatgpt(gpt_message)

            write_file("assertions.txt", response)

            adjust_assertions() # ukoliko kreiramo na osnovu vhd fajlova potrebno prilagodjavanje dodele vrednosti iz oblika npr. "1111" u 4'b1111 (GPT ne odradi to sam)

    def prepare_dut_for_vlog(input_file1, input_file2, output_file):
        # Otvaranje fajlova
        with open(input_file1, 'r', encoding='utf-8') as top_file:
            top_content = top_file.readlines()

        with open(input_file2, 'r', encoding='utf-8') as assertions_file:
            assertions_content = assertions_file.read()

        # Umećanje sadržaja assertions.txt pre linije sa 'endmodule'
        for i, line in enumerate(top_content):
            if 'endmodule' in line:
                top_content.insert(i, assertions_content + '\n')
                break

        # Pisanje izmenjenog sadržaja u top_test.sv
        with open(output_file, 'w', encoding='utf-8') as top_test_file:
            top_test_file.writelines(top_content)

    def check_one_line_assertion():
        with open('assertions.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        all_lines_valid = True

        for line_number, line in enumerate(lines, start=1):
            line = line.strip()  # Ukloni bele prostore oko linije
            if line:  # Ako linija nije prazna
                if 'assert property' not in line:
                    all_lines_valid = False
        
        if all_lines_valid:
            return 0
        else:
            return 1
        
    create_assertions(top_file)
    error_counter = 1

    print("Checking assertions syntax...")

    while error_counter:
        prepare_dut_for_vlog('top.sv', 'assertions.txt', 'top_test.sv')
        os.system('vlog top_test.sv > log.txt')
        with open('log.txt', 'r', encoding='utf-8') as f:
            log_content = f.read()
            match = re.search(r'Errors:\s*(\d+)', log_content)
            error_counter = int(match.group(1)) if match else 0

        print("ERROR COUNTER: " + str(error_counter))

        if(check_one_line_assertion()): error_counter = 999       # proverava da li je svaki assertion iskljucivo u jednoj liniji

        os.system('del top_test.sv log.txt')
        if(error_counter):
            print("There is a syntax error in the assertions. Trying again...")
            os.system('del assertions.txt') 
            create_assertions(top_file)

    os.system('del top.sv opis.txt')
    print("Assertions created successfuly.")

def convert_states_to_lowercase(top_file):
    inputs, outputs, signals, constants, states = read_vhdl_file(os.getcwd() + "/" + top_file)

    with open('assertions.txt', 'r', encoding="utf-8") as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        for state in states:
            line = line.replace(f' {state}', f' {state.lower()}')
        modified_lines.append(line)

    with open('assertions.txt', 'w', encoding="utf-8") as file:
        file.writelines(modified_lines)
   
def main():
    top_file = "top.vhd"  
    create_sv_holder(top_file)  # kreiramo sv kostur fajl u koji mozemo da umetnemo assertione kako bi kompajliranjem (vlog) proverili ispravnost sintakse
    generate_opis(top_file)
    generate_assertions(top_file)

    convert_states_to_lowercase(top_file)   # sva stanja pretvaramo u mala slova (prilikom kompajliranja -mixedsvvh pretvara u mala slova)

if __name__ == "__main__":
    main()
