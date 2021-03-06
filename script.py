#!/usr/bin/env python3

import sys
import os
import shutil
from datetime import datetime
from pymediainfo import MediaInfo
# На всякий случай подстрахуемся от отсутствия ExifRead`а.
try:
    import exifread

except ImportError:
    sys.exit("Для работы скрипта необходим модуль EXIFREAD, \
            а он у вас, похоже, не установлен. \
             \nЗадание не выполнено.")

# На всякий случай подстрахуемся от отсутствия cv2.


DEFAULT_OUTPUT = r'D:\YandexDisk\Отсортировать\after'
DEFAULT_INPUT = r'D:\YandexDisk\Отсортировать\before'

def confirm():
    while True:
        answer = input('Приступаем: [Y]/n? ').lower()
        if answer in ['', 'y']:
            return True
        elif answer == 'n':
            return False


def getDirs(args, default=''):
    while True:
        argsCount = len(args)
        if argsCount > 1:
            if os.path.isdir(args[1]):
                dirs = [args[1]]
            else:
                args[1] = input(
                    'Исходный путь для импорта не верен, задайте правильный: ')
                continue
            if argsCount >= 3:
                dirs.append(args[2])
            else:
                dirs.append(default)
                args.append(dirs[1])
            try:
                os.makedirs(dirs[1], exist_ok=True)
                break
            except PermissionError:
                args[2] = input(
                    'Целевой каталог не доступен на запись, задайте другой: ')
        else:
            # Если скрипт запущен без аргументов, то просим это исправить.
            args.append(input("Задайте исходный каталог: "))
    return dirs


def main():
    # Получаем исходную и целевую дирректории.
    dirslist = getDirs(sys.argv, DEFAULT_OUTPUT)
    # Показываем куда и откуда будет импорт.
    print('Источник импорта: ', dirslist[0])
    print('Дирректория назначения: ', dirslist[1])
    # Просим подтверждение перед началом работы.
    #if not confirm():
     #   sys.exit("Задание отменено")

    # Задаем счетчики "плохих" и "хороших" операций.
    fTotal = okOp = badOp = 0
    badFiles = []
    # Собственно, импорт.
    for root, dirs, files in os.walk(dirslist[0]):
        i = 0
        for name in files:
            i += 1
            fTotal += 1
            filePath = os.path.join(root, name)
            # Отображаем текущий процесс и прогресс выполнения.
            fileExtension = os.path.splitext(name)[1]
            print('Обработка файла {} из {} (дир. -= {} =-)'
                  .format(i, len(files), os.path.basename(root).upper()))
            if fileExtension.upper() == '.MP4' and MediaInfo.can_parse():
                media_info = MediaInfo.parse(filePath)
                # wrongDate = datetime.strptime(media_info.tracks[0].encoded_date, "UTC %Y-%m-%d %H:%M:%S").year == 1970
                # encodedDate = media_info.tracks[0].file_creation_date__local.replace('-', ':') if wrongDate else media_info.tracks[0].encoded_date.replace('-', ':')
                encodedDate = media_info.tracks[0].encoded_date.replace('-', ':')
                exifDateTime = encodedDate.replace('UTC ', '')

            elif fileExtension == '.JPG':
                with open(filePath, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    exifDateTime = tags.get('EXIF DateTimeOriginal')

                    # При отсутствии у фото EXIF-данных - файл пропускаем,
                    # занося его в список "плохих" файлов.
                    if not exifDateTime:
                        print('Отсутствуют EXIF данные. Файл пропущен!!!', name)
                        badOp += 1
                        badFiles.append(filePath)
                        continue
            else:
                print('Неизвестный файл', name)
                badOp += 1
                badFiles.append(filePath)
                continue

            exifDate, exifTime = str(exifDateTime).split(' ')
            year, month, day = exifDate.split(':')
            hour, minute, sec = exifTime.split(':')


            # Задаем название импортированного файла.
            newFileName = '{}-{}-{}'.format(year + month + day, hour,
                                                 minute)
            path = dirslist[1]

            if not os.path.exists(path):
                print('Создаем новую папку')
                os.makedirs(path, exist_ok=True)
            newPath = os.path.join(path, newFileName)
            # Найдем подходящие имя для файла
            tmpPath = newPath
            fileindex = 1
            while os.path.exists(tmpPath + fileExtension):
                tmpPath = newPath + '_{}'.format(fileindex)
                fileindex += 1
            newPath = tmpPath + fileExtension
            try:
                shutil.copy2(filePath, newPath)
                print('OK')
                okOp += 1
            except (IOError, Exception) as e:
                print('BAD ' + e)
                badOp += 1
    # По завершении импорта выводим статистику сделанного.
    print('Обработано файлов всего:', fTotal)
    print('Успешных операций:', okOp)
    print('Завершенных с ошибками:', badOp)
    # И имена "плохих" файлов, если таковые есть.
    if len(badFiles):
        print('Необработанные файлы: ')
        for bf in badFiles:
            print(bf)


if __name__ == '__main__':
    main()