# Markers Extractor

In Adobe Audition, it's not possible to move markers created in Waveform mode directly into the Multitrack timeline. This utility solves that problem by automatically extracting markers from WAV files and positioning them on the timeline based on clip positions defined in the Adobe Audition project file (SESX file).

## How It Works
- The utility parses the Adobe Audition project file (.sesx) and determines the position of each WAV file on the timeline.
- It extracts embedded markers (including ranges) from the WAV files.
- For each marker, it calculates the absolute position on the timeline based on the clip offset.
- The result is saved in a CSV file compatible with Adobe Audition.

## How It Looks

![](screen%20ui.png)

![](screen_1.png)

### Project File Analysis
![Project File Analysis](screen_2.png)

### Extracting Markers and Creating CSV
![Extracting Markers](screen_3.png)

## Usage
- Run via `run_extractor.bat` (Windows) or manually with `python markers_extractor.py`
- In the interface, select the SESX file (Adobe Audition project), click "Analyze Project File", then click "Extract Markers and Create CSV"

## Requirements
- Python 3.6+
- Internet connection (for automatic dependency installation)

## Output
- A CSV file with absolute timecodes for all markers, ready for import into Audition.

---
Licensed under the MIT License

100% Vibe coding. The author didn’t write a single line.

---

# Markers Extractor

В Adobe Audition невозможно напрямую переместить маркеры, созданные в режиме Waveform, в окно таймлайна Multitrack. Эта утилита решает эту проблему: она автоматически извлекает маркеры из WAV-файлов и размещает их на таймлайне согласно позициям клипов, описанных в файле проекта Adobe Audition (SESX-файл).

## Как это работает
- Утилита анализирует файл проекта Adobe Audition (расширение .sesx) и определяет, где на таймлайне расположен каждый WAV-файл.
- Из этих WAV-файлов извлекаются встроенные маркеры (в том числе диапазоны).
- Для каждого маркера вычисляется его абсолютная позиция на таймлайне с учётом смещения клипа.
- Результат сохраняется в CSV-файл, совместимый с Adobe Audition.

## Как это выглядит

![](screen%20ui.png)

![](screen_1.png)

### Анализ файла проекта
![Анализ файла](screen_2.png)

### Извлечение маркеров и создание CSV
![Извлечение маркеров](screen_3.png)

## Использование
- Запуск через `run_extractor.bat` (Windows) или вручную через `python markers_extractor.py`
- В интерфейсе выбрать SESX-файл (файл проекта Adobe Audition), нажать "Анализировать файл проекта", затем "Извлечь маркеры и создать CSV"

## Требования
- Python 3.6+
- Наличие интернета для установки зависимостей (автоматически)

## Результат
- CSV-файл с абсолютными таймкодами всех маркеров. Готов для импорта в Audition.

---
Проект под лицензией MIT

100% Vibe coding. Автор не написал ни строчки.
