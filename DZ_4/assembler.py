import sys
import csv

def parse_instruction(line):
    parts = line.strip().split()
    cmd = parts[0]
    args = ''.join(parts[1:]).split(',')
    return cmd, [int(arg) for arg in args]

def assemble_instruction(cmd, args):
    if cmd == 'LOAD_CONST':
        A = 58  # Opcode for LOAD_CONST (adjusted)
        B = args[0]
        C = args[1]
        instruction = (A << 34) | (B << 24) | C
        size = 5
    elif cmd == 'LOAD_MEM':
        A = 63  # Opcode for LOAD_MEM (adjusted)
        B = args[0]
        C = args[1]
        instruction = (A << 26) | (B << 16) | C
        size = 4
    elif cmd == 'STORE_MEM':
        A = 31  # Opcode for STORE_MEM (adjusted)
        B = args[0]
        C = args[1]
        instruction = (A << 26) | (B << 16) | C
        size = 4
    elif cmd == 'BITREVERSE':
        A = 8  # Opcode for BITREVERSE (adjusted)
        B = args[0]
        C = args[1]
        instruction = (A << 26) | (B << 16) | C
        size = 4
    else:
        raise ValueError(f"Unknown command {cmd}")
    return instruction.to_bytes(size, byteorder='big'), {'A': A, 'B': B, 'C': C}

def main():
    src_file = sys.argv[1]
    bin_file = sys.argv[2]
    log_file = sys.argv[3]

    with open(src_file, 'r') as f:
        lines = f.readlines()

    binary_code = bytearray()
    log_entries = []

    for line in lines:
        if not line.strip() or line.strip().startswith(';'):
            continue  # Пропускаем пустые строки и комментарии
        cmd, args = parse_instruction(line)
        instruction_bytes, log_entry = assemble_instruction(cmd, args)
        binary_code.extend(instruction_bytes)
        log_entries.append(log_entry)

    with open(bin_file, 'wb') as f:
        f.write(binary_code)

    with open(log_file, 'w', newline='') as csvfile:
        fieldnames = ['A', 'B', 'C']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in log_entries:
            writer.writerow(entry)

if __name__ == '__main__':
    main()