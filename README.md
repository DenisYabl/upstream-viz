# upstream-viz
Приложение для визуализации работы подсистемы "Мехподъем".

## Требования

- streamlit=0.83.0
- upstreampy=...


## Запуск
```bash
streamlit run app.py
```

## Добавление новых страниц

- Создать в папке `pages` файл с описанием страницы.
- Добавить в app.py нужный импорт и строку с добавлением страницы. Пример:

```python
from pages import tubing_selection

app.add_page("Подбор НКТ", tubing_selection.app)
```
