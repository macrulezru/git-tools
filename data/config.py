import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

class ConfigManager:
    def __init__(self):
        self.profiles = [{
            "ProfileName": "default",
            "Prefix": "dl/TTSH-",
            "Remote": "origin",
            "WorkDir": os.getcwd(),
            "Locale": "ru"
        }]
        self.current_profile = "default"
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

    def get_current_settings(self) -> Optional[Dict[str, Any]]:
        """Возвращает настройки текущего профиля"""
        for profile in self.profiles:
            if profile["ProfileName"] == self.current_profile:
                return profile
        return None

    def is_first_run(self) -> bool:
        """Проверяет, первый ли это запуск (нет файла конфига)"""
        return not self.settings_file.exists()

    def load_settings(self):
        """Загружает настройки из файла"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.profiles = data.get('profiles', self.profiles)
                    self.current_profile = data.get('currentProfile', self.current_profile)
                    self.prefix_history = data.get('prefix_history', [])
                    self.dir_history = data.get('dir_history', [])
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.prefix_history = [self.get_current_settings()["Prefix"]]
            self.dir_history = [self.get_current_settings()["WorkDir"]]

    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            data = {
                'profiles': self.profiles,
                'currentProfile': self.current_profile,
                'prefix_history': list(set(self.prefix_history))[:10],
                'dir_history': list(set(self.dir_history))[:10]
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_work_dir(self, new_dir: str):
        """Обновляет рабочую директорию текущего профиля"""
        if new_dir in self.dir_history:
            self.dir_history.remove(new_dir)
        self.dir_history.insert(0, new_dir)
        current = self.get_current_settings()
        if current:
            current["WorkDir"] = new_dir
        self.save_settings()

    def update_prefix(self, new_prefix: str):
        """Обновляет префикс ветки текущего профиля"""
        if new_prefix in self.prefix_history:
            self.prefix_history.remove(new_prefix)
        self.prefix_history.insert(0, new_prefix)
        current = self.get_current_settings()
        if current:
            current["Prefix"] = new_prefix
        self.save_settings()

    def clear_prefix_history(self):
        """Очищает историю префиксов"""
        self.prefix_history = [self.get_current_settings()["Prefix"]]
        self.save_settings()

    def clear_dir_history(self):
        """Очищает историю директорий"""
        self.dir_history = [self.get_current_settings()["WorkDir"]]
        self.save_settings()

    def add_profile(self, name: str, prefix: str, remote: str, work_dir: str, locale: str) -> bool:
        """Добавляет новый профиль с проверкой уникальности имени"""
        if not name or any(p["ProfileName"] == name for p in self.profiles):
            return False
            
        self.profiles.append({
            "ProfileName": name,
            "Prefix": prefix,
            "Remote": remote,
            "WorkDir": os.path.abspath(work_dir),
            "Locale": locale
        })
        self.current_profile = name
        self.save_settings()
        return True

    def remove_profile(self, name: str):
        """Удаляет профиль"""
        if name != "default" and len(self.profiles) > 1:
            self.profiles = [p for p in self.profiles if p["ProfileName"] != name]
            if self.current_profile == name:
                self.current_profile = "default"
            self.save_settings()
            return True
        return False

    def switch_profile(self, name: str):
        """Переключает текущий профиль"""
        if any(p["ProfileName"] == name for p in self.profiles):
            self.current_profile = name
            self.save_settings()  # Это сохранит все настройки, включая локаль
            return True
        return False
    
    def initialize_first_profile(self, prefix: str, work_dir: str, locale: str):
        """Сохраняет первый профиль с полученными настройками"""
        self.profiles = [{
            "ProfileName": "default",
            "Prefix": prefix,
            "Remote": "origin",
            "WorkDir": work_dir,
            "Locale": locale
        }]
        self.current_profile = "default"
        self.prefix_history = [prefix]
        self.dir_history = [work_dir]
        self.save_settings()