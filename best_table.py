import sys
import re

def parse_table(lines):
    caption_regex = re.compile(r'\\caption\{([^}]*)\}')
    data_line_regex = re.compile(r'^\s*(\d+)\s*&\s*([\-\d\.]+)\s*&\s*([\-\d\.]+)\s*&\s*([\-\d\.]+)\s*\\\\')
    
    sections_map = {
        'Best $P_{opt}$': 'Popt',
        'Best $P_{unf}$': 'Punf',
        'Best $E$': 'E'
    }

    result = {
        'caption': '',
        'instance_name': '',
        'data': {
            'Popt': [],
            'Punf': [],
            'E': []
        }
    }

    current_section = None

    for line in lines:
        # Trova la caption
        c = caption_regex.search(line)
        if c:
            caption_text = c.group(1)
            result['caption'] = caption_text
            # Si Estrae l'istanza dalla caption
            # Si assume che la caption contenga la stringa: "Comparison best results on Problem_..."
            # Cerco "Problem_" e prendo tutto fino alla fine della parola
            instance_match = re.search(r'Problem\S*', caption_text)
            if instance_match:
                result['instance_name'] = instance_match.group(0)

        # Controlla se la linea contiene il nome di una sezione
        for s_txt, s_key in sections_map.items():
            if s_txt in line:
                current_section = s_key

        # Riga di dati
        m = data_line_regex.match(line)
        if m and current_section is not None:
            p = int(m.group(1))
            val_1000 = float(m.group(2))
            val_2000 = float(m.group(3))
            val_3000 = float(m.group(4))
            result['data'][current_section].append((p, val_1000, val_2000, val_3000))

    return result

def format_table_latex(table_data):
    caption = table_data['caption']
    instance_name = table_data['instance_name']

    # Nuova struttura colonne:
    # Instance | p | C1000 | C2000 | Δ(2000-1000) | C3000 | Δ(3000-1000)
    latex = []
    latex.append("\\begin{table}[!htbp]")
    latex.append("    \\renewcommand{\\arraystretch}{0.7}")
    latex.append("    \\scriptsize")
    latex.append("    \\centering")
    latex.append(f"    \\caption{{{caption}}}")
    latex.append("    \\begin{adjustbox}{max width=\\columnwidth}")
    latex.append("        \\begin{tabularx}{\\columnwidth}{c|c c c c c c}")
    latex.append("            \\toprule")
    latex.append("            \\textbf{Instance} & \\textbf{p} & \\textbf{COBYLA 1000} & \\textbf{COBYLA 2000} & $\\Delta(2000-1000)$ & \\textbf{COBYLA 3000} & $\\Delta(3000-1000)$ \\\\")
    latex.append("            \\midrule")

    def print_section(name, key):
        latex.append(f"            \\multicolumn{{7}}{{c}}{{\\textbf{{{name}}}}} \\\\ \\midrule")
        for (p, v1000, v2000, v3000) in table_data['data'][key]:
            delta_2000 = (v2000 - v1000) / v1000
            delta_3000 = (v3000 - v1000) / v1000
            latex.append(f"            {instance_name} & {p} & {v1000:.3f} & {v2000:.3f} & {delta_2000:.3f} & {v3000:.3f} & {delta_3000:.3f} \\\\")

    # Stampa le tre sezioni
    print_section("Best $P_{opt}$", "Popt")
    print_section("Best $P_{unf}$", "Punf")
    print_section("Best $E$", "E")

    latex.append("            \\bottomrule")
    latex.append("        \\end{tabularx}")
    latex.append("    \\end{adjustbox}")
    latex.append("\\end{table}")
    latex.append("")

    return "\n".join(latex)

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 add_deltas_with_instance.py best_table.tex")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file, 'r') as f:
        content = f.read()

    # Separiamo le tabelle
    tables_raw = re.split(r'(\\begin{table}\[!htbp\].*?\\end{table})', content, flags=re.DOTALL)
    tables_raw = [t.strip() for t in tables_raw if t.strip().startswith("\\begin{table}")]

    output_tables = []

    for t in tables_raw:
        lines = t.split('\n')
        table_data = parse_table(lines)
        # Se ci sono dati, modifico la tabella
        if any(table_data['data'][sec] for sec in ['Popt', 'Punf', 'E']):
            new_table = format_table_latex(table_data)
            output_tables.append(new_table)
        else:
            # Nessun dato, mantengo la tabella invariata
            output_tables.append(t)

    with open("output_tables.tex", "w") as out:
        out.write("\n".join(output_tables))

    print("Tabelle modificate con istanza e colonne Δ generate in output_tables.tex")

if __name__ == "__main__":
    main()
