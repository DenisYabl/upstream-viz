# upstream-viz
Приложение для визуализации работы подсистемы "Мехподъем".

## Требования

- requirements.txt
- upstreampy~=0.1.0
- ot_simple_connector~=0.1.7

## Запуск
```bash
streamlit run app.py
```

## Добавление новых страниц

- Создать в папке `pages` файл с описанием страницы.
- Добавить в app.py нужный импорт и строку с добавлением страницы. Пример:

```python

from pages.well import tubing_selection

app.add_page("Подбор НКТ", tubing_selection.app)
```
