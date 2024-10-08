import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def read_file(filepath):
    #print(f"Reading file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    #print(f"File content read successfully.")
    return content

def write_file(filepath, content):
    #print(f"Writing file: {filepath}")
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Content successfully written to file {filepath}")

def ask_chatgpt(question):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role":"user", "content":question
            }
        ]
    )
    response = completion.choices[0].message.content

    for substring in ["```", "systemverilog"]:
        response = response.replace(substring, "")

    return response

def read_vhdl_file(filepath):
    vhdl_code = read_file(filepath)
    
    # Liste za čuvanje ulaza, izlaza, signala, konstanti i stanja
    inputs = []
    outputs = []
    signals = []
    constants = []
    states = []

    # Regularni izrazi za pronalaženje signala, ulaza/izlaza, konstanti i stanja
    port_pattern = re.compile(
        r'(?P<name>\w+)\s*:\s*(?P<direction>in|out)\s*(?P<type>std_logic(?:_vector\(\d+ downto \d+\))?)'
    )
    signal_pattern = re.compile(
        r'signal\s+(?P<name>\w+)\s*:\s*(?P<type>std_logic(?:_vector\(\d+ downto \d+\))?)'
    )
    constant_pattern = re.compile(
        r'constant\s+(?P<name>\w+)\s*:\s*(?P<type>std_logic(?:_vector\(\d+ downto \d+\))?)\s*:=\s*(?P<value>".*?")'
    )
    state_pattern = re.compile(
        r'type\s+tSTATE\s+is\s*\((.*?)\);', re.DOTALL
    )

    # Prolaz kroz svaku liniju VHDL koda
    for line in vhdl_code.splitlines():
        # Pronađi ulazne/izlazne portove
        port_match = port_pattern.search(line)
        if port_match:
            element_info = {
                'name': port_match.group('name'),
                'direction': port_match.group('direction'),
                'signal_type': port_match.group('type')
            }

            # Izračunaj veličinu signala ako je std_logic_vector
            if 'std_logic_vector' in element_info['signal_type']:
                size_match = re.search(r'\((\d+) downto (\d+)\)', element_info['signal_type'])
                if size_match:
                    element_info['size'] = int(size_match.group(1)) - int(size_match.group(2)) + 1
                else:
                    element_info['size'] = 1
            else:
                element_info['size'] = 1

            # Dodaj u odgovarajuću listu
            if element_info['direction'] == 'in':
                inputs.append(element_info)
            elif element_info['direction'] == 'out':
                outputs.append(element_info)

        # Pronađi signale
        signal_match = signal_pattern.search(line)
        if signal_match:
            element_info = {
                'name': signal_match.group('name'),
                'signal_type': signal_match.group('type')
            }

            # Izračunaj veličinu signala ako je std_logic_vector
            if 'std_logic_vector' in element_info['signal_type']:
                size_match = re.search(r'\((\d+) downto (\d+)\)', element_info['signal_type'])
                if size_match:
                    element_info['size'] = int(size_match.group(1)) - int(size_match.group(2)) + 1
                else:
                    element_info['size'] = 1
            else:
                element_info['size'] = 1

            signals.append(element_info)

        # Pronađi konstante
        constant_match = constant_pattern.search(line)
        if constant_match:
            element_info = {
                'name': constant_match.group('name'),
                'signal_type': constant_match.group('type'),
                'value': constant_match.group('value')
            }

            # Izračunaj veličinu konstante ako je std_logic_vector
            if 'std_logic_vector' in element_info['signal_type']:
                size_match = re.search(r'\((\d+) downto (\d+)\)', element_info['signal_type'])
                if size_match:
                    element_info['size'] = int(size_match.group(1)) - int(size_match.group(2)) + 1
                else:
                    element_info['size'] = 1
            else:
                element_info['size'] = 1

            constants.append(element_info)

        # Pronađi stanja iz tSTATE
        state_match = state_pattern.search(vhdl_code)
        if state_match:
            state_list = state_match.group(1).split(',')
            states = [state.strip() for state in state_list]

    return inputs, outputs, signals, constants, states