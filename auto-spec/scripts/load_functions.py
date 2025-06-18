import re
import json

def load_function_registry(registry):
    functions, skipped = [], []
    with open(registry, 'r') as fp:
        lines = fp.read().splitlines()
    curr_fun, curr_fun_data = None, {
        'signatures': []
    }

    for line in lines:
        if line.startswith('-'):
            if 'No Type Checking' in line:
                continue
            for match in re.findall(r"\[[\w,]+\]", line):
                types = match.strip('[]')
                curr_fun_data['signatures'].append(types.split(','))
        else:
            if curr_fun is None:
                pass
            elif curr_fun_data["signatures"] == []:
                skipped.append(curr_fun)
            else:
                functions.append(curr_fun_data)
            curr_fun = line
            curr_fun_data = { 'name': line, 'signatures': [] }
    
    return functions, skipped

if __name__ == "__main__":
    functions, skipped = load_function_registry('scripts/input_data/functions_raw.txt')
    with open("data/function_signatures.json", "w") as fp:
        json.dump(functions, fp, indent=2)
    with open("data/skipped_functions.json", "w") as fp:
        json.dump(skipped, fp, indent=2)
