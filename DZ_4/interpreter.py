import sys
import csv

def bitreverse(value):
    return int('{:032b}'.format(value)[::-1], 2)

def main():
    bin_file = sys.argv[1]
    result_file = sys.argv[2]
    mem_start = int(sys.argv[3])
    mem_end = int(sys.argv[4])

    # Initialize UVM memory
    memory = [0] * 1024  # Assuming memory size is 1024 words

    # Load binary file
    with open(bin_file, 'rb') as f:
        code = f.read()

    pc = 0
    while pc < len(code):
        opcode = (code[pc] >> 2) & 0x3F  # Extract bits 2-7 of the first byte
        if opcode == 58:
            # LOAD_CONST - 5 bytes
            instruction = int.from_bytes(code[pc:pc+5], byteorder='big')
            A = (instruction >> 34) & 0x3F
            B = (instruction >> 24) & 0x3FF
            C = instruction & 0xFFFFFF
            memory[B] = C
            pc += 5
        elif opcode == 63:
            # LOAD_MEM - 4 bytes
            instruction = int.from_bytes(code[pc:pc+4], byteorder='big')
            A = (instruction >> 26) & 0x3F
            B = (instruction >> 16) & 0x3FF
            C = instruction & 0xFFFF
            addr = memory[B]
            memory[C] = memory[addr]
            pc += 4
        elif opcode == 31:
            # STORE_MEM - 4 bytes
            instruction = int.from_bytes(code[pc:pc+4], byteorder='big')
            A = (instruction >> 26) & 0x3F
            B = (instruction >> 16) & 0x3FF
            C = instruction & 0xFFFF
            addr = memory[B]
            memory[addr] = memory[C]
            pc += 4
        elif opcode == 8:
            # BITREVERSE - 4 bytes
            instruction = int.from_bytes(code[pc:pc+4], byteorder='big')
            A = (instruction >> 26) & 0x3F
            B = (instruction >> 16) & 0x3FF
            C = instruction & 0xFFFF
            addr_B = memory[B]
            addr_C = memory[C]
            memory[addr_C] = bitreverse(memory[addr_B])
            pc += 4
        else:
            raise ValueError(f"Unknown opcode {opcode} at position {pc}")

    # Write the result to the file
    with open(result_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for addr in range(mem_start, mem_end+1):
            writer.writerow([addr, memory[addr]])

if __name__ == '__main__':
    main()