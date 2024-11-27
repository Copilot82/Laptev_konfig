import os
import zlib
import configparser
import subprocess

def read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    viz_program = config.get('DEFAULT', 'viz_program')
    repo_path = config.get('DEFAULT', 'repo_path')
    return viz_program, repo_path

def get_loose_commit_objects(repo_path):
    objects_path = os.path.join(repo_path, '.git', 'objects')
    commit_objects = {}
    for root, dirs, files in os.walk(objects_path):
        # Исключаем директории pack и info
        dirs[:] = [d for d in dirs if d != 'pack' and d != 'info']
        for name in files:
            if len(name) != 38 or len(os.path.basename(root)) != 2:
                continue
            obj_dir = os.path.basename(root)
            obj_hash = obj_dir + name
            obj_path = os.path.join(root, name)
            with open(obj_path, 'rb') as f:
                compressed_data = f.read()
                try:
                    data = zlib.decompress(compressed_data)
                    if data.startswith(b'commit'):
                        commit_objects[obj_hash] = data
                except zlib.error:
                    continue
    return commit_objects

def parse_commit(data):
    # Разделяем заголовок и тело коммита
    _, content = data.split(b'\x00', 1)
    lines = content.decode('utf-8', errors='replace').split('\n')
    parents = []
    author = ''
    date = ''
    for line in lines:
        if line.startswith('parent '):
            parents.append(line[7:].strip())
        elif line.startswith('author '):
            author_info = line[7:].strip()
            if '>' in author_info:
                author = author_info.split('>')[0] + '>'
                date_parts = author_info.split('>')[1].strip().split()
                if len(date_parts) >= 2:
                    timestamp = date_parts[0]
                    timezone = date_parts[1]
                    from datetime import datetime
                    dt = datetime.fromtimestamp(int(timestamp))
                    date = dt.strftime('%Y-%m-%d %H:%M:%S')
        elif line == '':
            break
    return parents, author, date

def build_graph(commit_objects):
    graph = 'digraph G {\n    node [shape=box];\n'
    nodes = {}
    for obj_hash, data in commit_objects.items():
        parents, author, date = parse_commit(data)
        label = f'"{obj_hash[:7]}\\n{date}\\n{author}"'
        nodes[obj_hash] = f'node_{obj_hash}'
        graph += f'    {nodes[obj_hash]} [label={label}];\n'
    for obj_hash, data in commit_objects.items():
        parents, _, _ = parse_commit(data)
        for parent in parents:
            if parent in nodes:
                graph += f'    {nodes[parent]} -> {nodes[obj_hash]};\n'
    graph += '}'
    return graph

def visualize_graph(graph, viz_program):
    process = subprocess.Popen([viz_program, '-Tpng'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    img_data, _ = process.communicate(input=graph.encode('utf-8'))
    if img_data:
        # Сохранение изображения во временный файл и его отображение
        import tempfile
        import webbrowser
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(img_data)
            webbrowser.open('file://' + tmp_file.name)

def main():
    config_path = 'config.ini'
    viz_program, repo_path = read_config(config_path)
    commit_objects = get_loose_commit_objects(repo_path)
    if not commit_objects:
        print("Не найдено незапакованных коммитов в репозитории.")
        return
    graph = build_graph(commit_objects)
    visualize_graph(graph, viz_program)

if __name__ == '__main__':
    main()