import argparse
import zipfile
import os
import sys
import shutil
import tempfile
import getpass
import stat
import pwd
import grp
from datetime import datetime

permissions = {}

def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки')
    parser.add_argument('--computer-name', required=True, help='Имя компьютера для приглашения к вводу')
    parser.add_argument('--vfs-path', required=True, help='Путь к ZIP-архиву виртуальной файловой системы')
    args = parser.parse_args()
    return args.computer_name, args.vfs_path

def load_virtual_file_system(vfs_zip_path):
    if not zipfile.is_zipfile(vfs_zip_path):
        print(f"Ошибка: файл '{vfs_zip_path}' не является корректным ZIP-архивом.")
        sys.exit(1)

    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(vfs_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    # Устанавливаем текущий пользователь как владелец файлов
    for root, dirs, files in os.walk(temp_dir):
        for momo in dirs + files:
            path = os.path.join(root, momo)
            os.chmod(path, 0o755)
    return temp_dir

def print_long_format(path):
    st = os.lstat(path)

    # Получение симулированных прав доступа или текущих
    sim_permissions = permissions.get(path)
    if sim_permissions:
        mode = sim_permissions
    else:
        mode = stat.filemode(st.st_mode)

    n_links = st.st_nlink
    uid = st.st_uid
    gid = st.st_gid
    size = st.st_size
    mtime = datetime.fromtimestamp(st.st_mtime).strftime('%b %d %H:%M')
    name = os.path.basename(path)

    # Симуляция владельца и группы, если недоступно
    try:
        user = pwd.getpwuid(uid).pw_name
    except KeyError:
        user = uid
    try:
        group = grp.getgrgid(gid).gr_name
    except KeyError:
        group = gid

    print(f"{mode} {n_links} {user} {group} {size} {mtime} {name}")

def ls_command(current_dir, args):
    long_format = False
    paths = []

    # Разбор опций и аргументов
    for arg in args:
        if arg == '-l':
            long_format = True
        else:
            paths.append(arg)

    if not paths:
        paths = ['.']

    for path_arg in paths:
        path = os.path.join(current_dir, path_arg)
        if not os.path.exists(path):
            print(f"ls: не могу получить доступ к '{path_arg}': Нет такого файла или директории")
            continue
        if os.path.isfile(path):
            if long_format:
                print_long_format(path)
            else:
                print(os.path.basename(path))
        else:
            if len(paths) > 1:
                print(f"{path_arg}:")
            items = os.listdir(path)
            if long_format:
                for item in items:
                    item_path = os.path.join(path, item)
                    print_long_format(item_path)
            else:
                print('  '.join(items))
            if len(paths) > 1:
                print()

def cd_command(current_dir, vfs_root, args):
    if not args:
        return vfs_root  # Переход в домашнюю директорию
    target = args[0]
    if target == '/':
        new_path = vfs_root
    elif target.startswith('/'):
        new_path = os.path.join(vfs_root, target[1:])
    else:
        new_path = os.path.join(current_dir, target)
    if not os.path.exists(new_path):
        print(f"cd: {target}: Нет такого файла или директории")
        return current_dir
    if not os.path.isdir(new_path):
        print(f"cd: {target}: Не является директорией")
        return current_dir
    return os.path.normpath(new_path)

def pwd_command(current_dir, vfs_root):
    rel_path = os.path.relpath(current_dir, vfs_root)
    print('/' if rel_path == '.' else f"/{rel_path}")

def chmod_command(current_dir, args):
    if len(args) != 2:
        print("Использование: chmod MODE FILE")
        return
    mode_str, filename = args
    path = os.path.join(current_dir, filename)
    if not os.path.exists(path):
        print(f"chmod: не могу получить доступ к '{filename}': Нет такого файла или директории")
        return
    try:
        mode = int(mode_str, 8)
    except ValueError:
        print(f"chmod: неверный режим: '{mode_str}'")
        return
    os.chmod(path, mode)
    permissions[path] = stat.filemode(mode)
    print(f"Права доступа для '{filename}' установлены в '{mode_str}'")

def who_command():
    user = getpass.getuser()
    print(user)

def shell_loop(computer_name, vfs_root):
    current_dir = vfs_root

    while True:
        try:
            rel_path = os.path.relpath(current_dir, vfs_root)
            prompt_path = '~' if rel_path == '.' else rel_path
            prompt = f"{getpass.getuser()}@{computer_name}:{prompt_path}$ "
            command_input = input(prompt)
            command_parts = command_input.strip().split()
            if not command_parts:
                continue
            command = command_parts[0]
            args = command_parts[1:]

            if command == 'exit':
                break
            elif command == 'ls':
                ls_command(current_dir, args)
            elif command == 'cd':
                current_dir = cd_command(current_dir, vfs_root, args)
            elif command == 'pwd':
                pwd_command(current_dir, vfs_root)
            elif command == 'chmod':
                chmod_command(current_dir, args)
            elif command == 'who':
                who_command()
            else:
                print(f"{command}: команда не найдена")
        except KeyboardInterrupt:
            print("\nДля выхода из оболочки введите 'exit'.")
        except Exception as e:
            print(f"Ошибка: {e}")

    # Очистка временной директории перед выходом
    shutil.rmtree(vfs_root)

def main():
    computer_name, vfs_zip_path = parse_arguments()
    vfs_root = load_virtual_file_system(vfs_zip_path)
    shell_loop(computer_name, vfs_root)

if __name__ == '__main__':
    main()