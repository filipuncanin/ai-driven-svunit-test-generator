import re
import os

from mymodule import *

def connect_with_dut(vhd_file):
    inputs, outputs, signals, constants, states = read_vhdl_file(os.getcwd() + "/" + vhd_file)

    x = ""

    for element in inputs:
        if element['size'] == 1:
            x += f"\treg {element['name']};\n"
        else:
            x += f"\treg [{element['size']-1}:0] {element['name']};\n"

    x += "\n"

    for element in outputs:
        x += f"\twire {element['name']};\n"

    x += "\n"

    for element in signals:
        if element['size'] == 1:
            x += f"\treg {element['name']};\n"
        else:
            x += f"\treg [{element['size']-1}:0] {element['name']};\n"

    x += "\n"

    for element in constants:
        value = element['value'].strip('"')  # Uklanjanje navodnika sa početka i kraja
        n = element['size']
        formatted_value = f"{n}'b{value}"
        
        if n == 1:
            x += f"\treg {element['name']} = {formatted_value};\n"
        else:
            x += f"\treg [{n-1}:0] {element['name']} = {formatted_value};\n"

    x += "\n\ttop_wrapper my_top_wrapper(.*);\n\n"

    x += "\tassign sSTATE = my_top_wrapper.top_inst.sstate;\n"
    x += "\tassign sNEXT_STATE = my_top_wrapper.top_inst.snext_state;\n"

    for element in signals:
        x += "\tassign " + element['name'] + " = my_top_wrapper.top_inst." + element['name'] + ";\n"

    return x

def get_test_signals(file_path):
    def convert_vhdl_signals_to_sv_signals(vhdl_signals):
        def modify_line(line): 
            # Zamenjuje 's' sa 'i' samo na početku linije
            line = re.sub(r'^s', 'i', line)

            if '#' in line:
                # Stavljanje sadrzaja izmedju '#' i ';' u zagrade (#20*CLK_period to #(20*CLK_period)
                line = re.sub(r'#(.*?)\s*;', r'#(\1);', line)
            return line
        
        # funkcija za pretvaranje oblika "111" u 3'b111
        def replace_string(match):
            value = match.group(1)
            bit_length = len(value)
            return f"{bit_length}'b{value}"

        vhdl_signals = vhdl_signals.replace("<=", "=")
        vhdl_signals = vhdl_signals.replace("--", "//")
        vhdl_signals = vhdl_signals.replace("wait for ", "#")
        vhdl_signals = vhdl_signals.replace("wait;", "")
        vhdl_signals = vhdl_signals.replace("'", "")

        lines = vhdl_signals.splitlines()
        modified_lines = [modify_line(line) for line in lines]
        vhdl_signals = "\n".join(modified_lines)

        pattern = r'\"([01]+)\"'
        vhdl_signals = re.sub(pattern, replace_string, vhdl_signals)

        return vhdl_signals
    
    vhdl_signals = read_file(file_path)
    vhdl_signals = vhdl_signals.splitlines()

    signals = []

    for i in range(len(vhdl_signals) - 1, -1, -1):  # pronalazenje prvog begina od kraja fajla (nakon toga idu signali)
        if "begin" in vhdl_signals[i]:
            i += 1  # prelazimo u red nakon "begin"
            break
    
    while i < len(vhdl_signals) and "end process;" not in vhdl_signals[i]:
        signals.append(vhdl_signals[i].strip())
        i += 1

    vhdl_signals = '\n'.join(signals)

    sv_signals = convert_vhdl_signals_to_sv_signals(vhdl_signals)

    return sv_signals

def create_unit_test(assertions_file, vhd_file, tb_file, output_file, unit_test_kostur_file):
    # ucitavamo kostur unit test-a, signale za povezivanje sa dut-om, assertions-e i povorku signala
    unit_test_kostur = read_file(unit_test_kostur_file).splitlines()
    dut_signals = connect_with_dut(vhd_file).splitlines()
    assertions = read_file(assertions_file).splitlines()
    test_signals = get_test_signals(tb_file).splitlines()
    
    # umecemo signale za povezivanje sa dut-om, assertions-e i povorku signala u kostur unit test-a
    # -- pronalazimo liniju nakon koje umecemo signale za povezivanje sa dut-om i assertions-e
    for i, line in enumerate(unit_test_kostur):
        if "localparam iCLK_period" in line:
            insert_index = i + 1
            break

    for line in reversed(dut_signals):
        unit_test_kostur.insert(insert_index, line)

    for line in reversed(assertions):
        unit_test_kostur.insert(insert_index + len(dut_signals), "\t" + line)

    # -- pronalazimo liniju nakon koje umecemo povorku signala
    for i, line in enumerate(unit_test_kostur):
        if "`SVTEST" in line:
            insert_index = i + 1
            break

    for line in reversed(test_signals):
        unit_test_kostur.insert(insert_index, "\t\t\t" + line)

    unit_test_kostur = '\n'.join(unit_test_kostur)

    write_file(output_file, unit_test_kostur)
    
if __name__ == "__main__":

    if os.path.isfile('processed_assertions_dut.txt'):
        create_unit_test('processed_assertions_dut.txt', 'top.vhd', 'top_full_tb.vhd', 'top_wrapper_unit_test.sv', 'scripts/top_wrapper_unit_test_base.sv')
    else: 
        create_unit_test('assertions.txt', 'top.vhd', 'top_full_tb.vhd', 'top_wrapper_unit_test.sv', 'scripts/top_wrapper_unit_test_base.sv')

    if os.path.isfile('processed_assertions_tb.txt'):
        create_unit_test('processed_assertions_tb.txt', 'top.vhd', 'top_tb.vhd', 'top_tb_wrapper_unit_test.sv', 'scripts/top_tb_wrapper_unit_test_base.sv')
    else:
        create_unit_test('assertions.txt', 'top.vhd', 'top_tb.vhd', 'top_tb_wrapper_unit_test.sv', 'scripts/top_tb_wrapper_unit_test_base.sv')
