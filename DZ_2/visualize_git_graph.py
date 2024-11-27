import configparser
import subprocess
import sys
import os
import tempfile
import shutil

def main():
    # Чтение конфигурационного файла
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        graphviz_program = config.get('Settings', 'graphviz_program')
        repo_path = config.get('Settings', 'repo_path')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print('Ошибка в конфигурационном файле:', e)
        sys.exit(1)

    # Проверка наличия программы визуализации
    if not shutil.which(graphviz_program):
        print(f'Программа визуализации "{graphviz_program}" не найдена.')
        sys.exit(1)

    # Проверка существования репозитория
    if not os.path.isdir(repo_path):
        print(f'Путь к репозиторию "{repo_path}" не существует.')
        sys.exit(1)

    # Переход в директорию репозитория
    os.chdir(repo_path)

    # Использование git log для получения данных о коммитах
    git_log_format = '%H;%P;%cI;%cN'
    git_log_command = ['git', 'log', '--pretty=format:' + git_log_format]

    try:
        output = subprocess.check_output(git_log_command).decode('utf-8')
    except subprocess.CalledProcessError as e:
        print('Ошибка при выполнении git log:', e)
        sys.exit(1)

    # Вернуться в исходную директорию
    os.chdir('..')

    # Построение графа зависимостей
    nodes = {}
    edges = []

    for line in output.strip().split('\n'):
        parts = line.strip().split(';')
        if len(parts) < 4:
            continue  # Пропустить некорректные строки
        commit_hash, parent_hashes, commit_date, commit_author = parts
        parent_hash_list = parent_hashes.strip().split()

        # Формирование метки узла с датой, временем и автором
        label = f"{commit_date}\\n{commit_author}"

        nodes[commit_hash] = label

        # Добавление ребер к родительским коммитам
        for parent_hash in parent_hash_list:
            edges.append((commit_hash, parent_hash))

    # Генерация описания графа в формате DOT
    dot_lines = ['digraph G {']

    # Добавление узлов
    for commit_hash, label in nodes.items():
        dot_lines.append(f'"{commit_hash}" [label="{label}"];')

    # Добавление ребер
    for child, parent in edges:
        dot_lines.append(f'"{child}" -> "{parent}";')

    dot_lines.append('}')
    dot_content = '\n'.join(dot_lines)

    # Сохранение описания графа во временный файл
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dot') as temp_dot_file:
        temp_dot_file.write(dot_content)
        dot_file_name = temp_dot_file.name

    # Генерация изображения графа с помощью программы визуализации
    output_image = 'git_graph.png'
    graphviz_command = [graphviz_program, '-Tpng', dot_file_name, '-o', output_image]

    try:
        subprocess.check_call(graphviz_command)
    except subprocess.CalledProcessError as e:
        print('Ошибка при генерации графа:', e)
        sys.exit(1)

    print(f'Граф зависимости коммитов сохранен в файл {output_image}.')

    # Открытие изображения графа
    if sys.platform.startswith('darwin'):
        subprocess.Popen(['open', output_image])
    elif sys.platform.startswith('linux'):
        subprocess.Popen(['xdg-open', output_image])
    elif sys.platform.startswith('win'):
        os.startfile(output_image)
    else:
        print('Неизвестная платформа; откройте файл изображения вручную.')

if __name__ == '__main__':
    main()