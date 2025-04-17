import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

class ConfigManager:
    def __init__(self):
        self.branch_settings = {
            "Prefix": "dl/TTSH-",
            "DefaultRemote": "origin",
            "WorkDir": os.getcwd()
        }
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.settings_file = self.data_dir / 'config.json'
        self.prefix_history = []
        self.dir_history = []
        self.history_file = os.path.expanduser("~/.git_manager_history")

        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Создает папку data и locales, если их нет"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)

        locales_dir = self.data_dir / 'locales'
        if not locales_dir.exists():
            locales_dir.mkdir()

    def is_first_run(self) -> bool:
        """Проверяет, первый ли это запуск (нет файла конфига)"""
        return not self.settings_file.exists()

    def load_settings(self):
        """Загружает настройки из файла"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    # Важно: используем update чтобы сохранить значения по умолчанию для отсутствующих ключей
                    if 'current_settings' in data:
                        self.branch_settings.update(data['current_settings'])
                    if 'prefix_history' in data:
                        self.prefix_history = data['prefix_history']
                    if 'dir_history' in data:
                        self.dir_history = data['dir_history']
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.prefix_history = [self.branch_settings["Prefix"]]
            self.dir_history = [self.branch_settings["WorkDir"]]

    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            data = {
                'current_settings': self.branch_settings,
                'prefix_history': list(set(self.prefix_history))[:10],
                'dir_history': list(set(self.dir_history))[:10]
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_work_dir(self, new_dir: str):
        """Обновляет рабочую директорию"""
        if new_dir in self.dir_history:
            self.dir_history.remove(new_dir)
        self.dir_history.insert(0, new_dir)
        self.branch_settings["WorkDir"] = new_dir
        self.save_settings()

    def update_prefix(self, new_prefix: str):
        """Обновляет префикс ветки"""
        if new_prefix in self.prefix_history:
            self.prefix_history.remove(new_prefix)
        self.prefix_history.insert(0, new_prefix)
        self.branch_settings["Prefix"] = new_prefix
        self.save_settings()

    def clear_prefix_history(self):
        """Очищает историю префиксов"""
        self.prefix_history = [self.branch_settings["Prefix"]]
        self.save_settings()

    def clear_dir_history(self):
        """Очищает историю директорий"""
        self.dir_history = [self.branch_settings["WorkDir"]]
        self.save_settings()