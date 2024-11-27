Создание рабочего каталога:
mkdir shell_emulator
cd shell_emulator

Подготовка виртуальной файловой системы:
mkdir vfs_root
cd vfs_root

Добавление файлов и директорий:
mkdir dir1 dir2
touch file1.txt dir1/file2.txt dir2/file3.txt
echo "Hello World!" > file1.txt
echo "Content of file2" > dir1/file2.txt
echo "Another file" > dir2/file3.txt

Возврат в корневой каталог проекта:
cd ..

Архивирование виртуальной файловой системы:
zip -r vfs.zip vfs_root

Запуск программы:
python shell_emulator.py --computer-name MyComputer --vfs-path vfs.zip