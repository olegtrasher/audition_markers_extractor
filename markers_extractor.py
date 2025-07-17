#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интерфейс для извлечения маркеров из WAV файлов с учетом позиций клипов в SESX файле
"""

import os
import csv
import sys
import xml.etree.ElementTree as ET
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def install_required_packages():
    """Устанавливает необходимые пакеты, если они не установлены"""
    required_packages = ['wavinfo']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} уже установлен")
        except ImportError:
            print(f"Устанавливаю {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} успешно установлен")
            except subprocess.CalledProcessError:
                print(f"✗ Ошибка установки {package}")
                return False
    return True

def parse_sesx_file(sesx_file_path: str) -> Tuple[Dict[str, int], List[str]]:
    """
    Парсит SESX файл и извлекает информацию о клипах и пути к WAV файлам
    Args:
        sesx_file_path: Путь к SESX файлу
    Returns:
        Tuple[словарь_клипов, список_путей_к_wav]
    """
    clips_info = {}
    wav_files = []
    try:
        # Парсим XML
        tree = ET.parse(sesx_file_path)
        root = tree.getroot()

        print(f"\n=== Парсинг SESX файла ===")

        # Ищем все audioClip элементы
        for audio_clip in root.findall('.//audioClip'):
            name = audio_clip.get('name', '')
            start_point = audio_clip.get('startPoint', 0)
            # Очищаем имя файла (убираем расширение если есть)
            clean_name = name.replace('.WAV', '').replace('.wav', '')
            if clean_name and start_point:
                clips_info[clean_name] = int(float(start_point))
                print(f"  Клип: {clean_name} -> startPoint: {start_point}")

        # Ищем все file элементы с WAV файлами
        for file_elem in root.findall('.//file'):
            relative_path = file_elem.get('relativePath', '')
            if relative_path.lower().endswith('.wav'):
                # Получаем абсолютный путь к WAV файлу
                sesx_dir = os.path.dirname(os.path.abspath(sesx_file_path))
                wav_path = os.path.join(sesx_dir, relative_path)
                if os.path.exists(wav_path):
                    wav_files.append(wav_path)
                    print(f"  WAV файл: {relative_path}")

        print(f"Найдено клипов: {len(clips_info)}")
        print(f"Найдено WAV файлов: {len(wav_files)}")

    except Exception as e:
        print(f"Ошибка при парсинге SESX файла: {e}")
    return clips_info, wav_files

def extract_markers_from_wav(wav_file_path: str) -> List[Dict]:
    """
    Извлекает маркеры из WAV файла с помощью wavinfo
    Args:
        wav_file_path: Путь к WAV файлу
    Returns:
        Список словарей с информацией о маркерах
    """
    markers = []
    try:
        # Импортируем wavinfo
        from wavinfo import WavInfoReader

        # Открываем WAV файл с помощью wavinfo
        wav = WavInfoReader(wav_file_path)

        # Получаем sample rate для вычисления времени
        sample_rate = wav.fmt.sample_rate if hasattr(wav.fmt, 'sample_rate') else 48000
        # Проверяем cues (основной способ получения маркеров в wavinfo)
        if hasattr(wav, 'cues') and wav.cues:
            if hasattr(wav.cues, 'cues'):
                cue_list = wav.cues.cues
                labels_list = wav.cues.labels if hasattr(wav.cues, 'labels') else []
                ranges_list = wav.cues.ranges if hasattr(wav.cues, 'ranges') else []

                # Создаем словари для связи позиций с названиями и длинами
                labels_dict = {}
                ranges_dict = {}

                for label in labels_list:
                    if hasattr(label, 'name') and hasattr(label, 'text'):
                        labels_dict[label.name] = label.text

                for range_item in ranges_list:
                    if hasattr(range_item, 'name') and hasattr(range_item, 'length'):
                        ranges_dict[range_item.name] = range_item.length

                for i, cue_marker in enumerate(cue_list):
                    marker_name = cue_marker.name
                    marker_text = labels_dict.get(marker_name, f'Marker {marker_name}')

                    # Получаем длину диапазона, если есть
                    duration = ranges_dict.get(marker_name, 0)

                    marker_info = {
                        'filename': os.path.basename(wav_file_path),
                        'name': marker_text,
                        'position': getattr(cue_marker, 'position', 0),
                        'time_seconds': getattr(cue_marker, 'position', 0) / sample_rate,
                        'time_formatted': format_time(getattr(cue_marker, 'position', 0) / sample_rate),
                        'type': 'Cue',
                        'sample_rate': sample_rate,
                        'duration': duration  # Длина диапазона или 0 для обычных маркеров
                    }
                    markers.append(marker_info)

    except Exception as e:
        print(f"Ошибка при чтении файла {wav_file_path}: {e}")
    return markers

def format_time(seconds: float) -> str:
    """
    Форматирует время в секундах в формат MM:SS.mmm
    Args:
        seconds: Время в секундах
    Returns:
        Отформатированная строка времени
    """
    if seconds < 0:
        return "00:00.000"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:06.3f}"

def save_markers_to_csv(markers: List[Dict], output_file: str):
    """
    Сохраняет маркеры в СSV (табличный файл с разделителем табуляция), совместимый с Adobe Audition
    Args:
        markers: Список словарей с маркерами
        output_file: Путь к выходному CSV файлу
    """
    if not markers:
        print("Маркеры не найдены")
        return

    # Формируем строки для нового формата
    rows = []
    header = ["Name", "Start", "Duration", "Time Format", "Type", "Description"]
    rows.append(header)
    for marker in markers:
        sample_rate = marker.get('sample_rate', 48000)
        duration = marker.get('duration', 0)
        name = marker.get('name', '')
        start = int(marker.get('position', 0))
        time_format = f"{sample_rate} Hz"
        type_str = "Cue"
        description = marker.get('description', '')

        # Добавляем информацию о диапазоне в описание, если есть
        if duration > 0:
            duration_seconds = duration / sample_rate
            description = f"Range: {format_time(duration_seconds)}"
        row = [name, start, duration, time_format, type_str, description]
        rows.append(row)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        for row in rows:
            line = '\t'.join(str(cell) for cell in row)
            csvfile.write(line + '\n')

    print(f"Маркеры сохранены в файл: {output_file}")

class MarkersExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение маркеров из SESX")
        self.root.geometry("800x500")
        # Переменные
        self.sesx_file_path = tk.StringVar()
        self.clips_info = {}
        self.wav_files = []
        self.all_markers = []
        self.create_widgets()

    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.grid(row=0, column=0, sticky='nsew')
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Устанавливаем веса строк: treeview (row=5ксимальный
        for i in range(7):
            main_frame.rowconfigure(i, weight=0)
        main_frame.rowconfigure(5, weight=1)
        # Заголовок
        title_label = ttk.Label(main_frame, text="Извлечение маркеров из SESX файла",
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0,10))
        # Выбор SESX файла
        ttk.Label(main_frame, text="SESX файл:").grid(row=1, column=0, sticky='w', pady=2)
        ttk.Entry(main_frame, textvariable=self.sesx_file_path, width=60).grid(row=1, column=1, sticky='we', padx=5)
        ttk.Button(main_frame, text="Обзор", command=self.browse_sesx_file).grid(row=1, column=2, padx=5)
        # Примечание под выбором SESX файла
        sesx_note = ttk.Label(main_frame, text="SESX файл — это файл проекта Adobe Audition (*.sesx)", foreground="gray")
        sesx_note.grid(row=2, column=0, columnspan=3, sticky='w', pady=(0,5))
        # Кнопки анализа и извлечения в одном ряду
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=2)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        ttk.Button(button_frame, text="Анализировать SESX файл",
                   command=self.analyze_sesx_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Извлечь маркеры и создать CSV",
                   command=self.extract_markers).grid(row=0, column=1, padx=(5, 0))
        # Пояснение под кнопками
        extract_note = ttk.Label(
            main_frame,
            text="После нажатия кнопки Извлечь маркеры и создать CSV рядом с выбранным файлом проекта будет создан файл '<имя_проекта> timeline markers.csv'. Его нужно импортировать в Adobe Audition через окно Markers.",
            foreground="gray",
            wraplength=400,
            font=("Arial", 9)
        )
        extract_note.grid(row=4, column=0, columnspan=3, sticky='w', pady=(0, 2))
        # Treeview для отображения клипов и маркеров
        self.tree = ttk.Treeview(main_frame, columns=("start", "markers"), show="tree headings")
        self.tree.heading("#0", text="Клип")
        self.tree.heading("start", text="Start Point")
        self.tree.heading("markers", text="Маркеры")
        self.tree.column("#0", width=30)
        self.tree.column("start", width=10)
        self.tree.column("markers", width=20)
        self.tree.grid(row=5, column=0, columnspan=3, sticky='nsew', pady=2)
        # Скроллбар для treeview
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=5, column=3, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

    def browse_sesx_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите SESX файл",
            filetypes=[("SESX files", "*.sesx"), ("All files", "*.*")]
        )
        if filename:
            self.sesx_file_path.set(filename)

    def analyze_sesx_file(self):
        sesx_path = self.sesx_file_path.get()
        if not sesx_path:
            messagebox.showerror("Ошибка", "Выберите SESX файл")
            return

        if not os.path.exists(sesx_path):
            messagebox.showerror("Ошибка", "SESX файл не найден")
            return

        try:
            self.root.update()

            # Парсим SESX файл
            self.clips_info, self.wav_files = parse_sesx_file(sesx_path)

            # Очищаем treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Отображаем только клипы с WAV файлами и маркерами
            for clip_name, start_point in self.clips_info.items():
                # Ищем соответствующий WAV файл
                wav_file = None
                for wav_path in self.wav_files:
                    if clip_name.lower() in os.path.basename(wav_path).lower():
                        wav_file = wav_path
                        break

                # Проверяем, есть ли WAV файл и маркеры
                if wav_file and os.path.exists(wav_file):
                    markers = extract_markers_from_wav(wav_file)
                    if markers:  # Показываем только клипы с маркерами
                        # Добавляем клип в treeview
                        clip_item = self.tree.insert("", "end", text=clip_name,
                                                   values=(start_point, f"Найдено маркеров: {len(markers)}"))

                        # Добавляем маркеры как дочерние элементы
                        for marker in markers:
                            marker_text = f"{marker['name']} - {marker['time_formatted']}"
                            if marker['duration'] > 0:
                                duration_seconds = marker['duration'] / marker['sample_rate']
                                marker_text += f" (диапазон: {format_time(duration_seconds)})"
                            self.tree.insert(clip_item, "end", text=marker_text)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе SESX файла: {e}")

    def extract_markers(self):
        if not self.clips_info or not self.wav_files:
            messagebox.showerror("Ошибка", "Сначала проанализируйте SESX файл")
            return

        try:
            self.root.update()

            sesx_path = self.sesx_file_path.get()
            sesx_dir = os.path.dirname(sesx_path)
            sesx_name = os.path.splitext(os.path.basename(sesx_path))[0]
            output_file = os.path.join(sesx_dir, f"{sesx_name} timeline markers.csv")

            all_markers = []

            # Обрабатываем каждый WAV файл
            for wav_file in self.wav_files:
                if not os.path.exists(wav_file):
                    continue

                filename = os.path.basename(wav_file)
                clean_filename = filename.replace('.wav', '').replace('.WAV', '')

                # Ищем соответствующий клип в SESX
                clip_start = self.clips_info.get(clean_filename, 0)

                # Извлекаем маркеры из WAV
                markers = extract_markers_from_wav(wav_file)

                if markers:
                    # Смещаем таймкоды маркеров
                    for marker in markers:
                        # Добавляем позицию клипа к позиции маркера
                        original_position = marker['position']
                        marker['position'] = original_position + clip_start

                        # Пересчитываем время
                        sample_rate = marker['sample_rate']
                        marker['time_seconds'] = marker['position'] / sample_rate
                        marker['time_formatted'] = format_time(marker['time_seconds'])
                    all_markers.extend(markers)

            # Сохраняем результаты
            if all_markers:
                save_markers_to_csv(all_markers, output_file)

                messagebox.showinfo("Успех", f"Извлечено маркеров: {len(all_markers)}\nФайл сохранен: {output_file}")
            else:
                messagebox.showwarning("Предупреждение", "Маркеры не найдены ни в одном файле")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении маркеров: {e}")

def main():
    """Основная функция"""
    print("=== Извлечение маркеров из WAV файлов с учетом позиций клипов ===\n")

    # Устанавливаем необходимые пакеты
    if not install_required_packages():
        print("Ошибка установки необходимых пакетов")
        return

    # Создаем GUI
    root = tk.Tk()
    app = MarkersExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 