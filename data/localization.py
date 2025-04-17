import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

class LocalizationManager:
    def __init__(self, config):
        self.config = config
        self.available_locales: Dict[str, dict] = {}
        self.current_locale: str = 'ru'
        self.load_locales()

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Динамически сканирует папку locales и возвращает список языков с метаданными"""
        locales_dir = Path(__file__).parent / 'locales'
        languages = []

        for locale_file in locales_dir.glob('*.json'):
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('_meta', {})

                    # Определяем код языка из имени файла или метаданных
                    lang_code = meta.get('language_code', locale_file.stem)

                    languages.append({
                        'code': lang_code,
                        'name': meta.get('language_name', lang_code),
                        'flag': meta.get('flag', '🌐'),
                        'file': locale_file.name,
                        'native_name': meta.get('native_name', lang_code)
                    })
            except Exception as e:
                print(f"Error loading locale {locale_file}: {str(e)}")

        # Сортируем языки по имени для удобства
        return sorted(languages, key=lambda x: x['name'])

    def load_locales(self):
        """Загружает все доступные локали из папки locales"""
        locales_dir = Path(__file__).parent / 'locales'
        self.available_locales = {}

        if not locales_dir.exists():
            print(f"Locales directory not found: {locales_dir}")
            return

        for locale_file in locales_dir.glob('*.json'):
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('_meta', {})
                    lang_code = meta.get('language_code', locale_file.stem)

                    # Убедимся, что есть минимально необходимые метаданные
                    if not meta.get('language_name'):
                        meta['language_name'] = lang_code.upper()
                    if not meta.get('native_name'):
                        meta['native_name'] = meta['language_name']
                    if not meta.get('flag'):
                        meta['flag'] = '🌐'

                    self.available_locales[lang_code] = {
                        'meta': meta,
                        'translations': {k: v for k, v in data.items() if not k.startswith('_')}
                    }
            except Exception as e:
                print(f"Error loading locale {locale_file}: {str(e)}")

    def tr(self, key: str, *args, fallback: Optional[str] = None) -> str:
        """Получает локализованную строку с поддержкой вложенных ключей"""
        def get_nested(data: dict, keys: list) -> Optional[str]:
            if not keys or not data:
                return None
            current_key = keys[0]
            if current_key in data:
                value = data[current_key]
                if len(keys) == 1:
                    return value
                elif isinstance(value, dict):
                    return get_nested(value, keys[1:])
            return None

        locale_data = self.available_locales.get(self.current_locale, {})
        translations = locale_data.get('translations', {})
        key_parts = key.split('.')
        text = get_nested(translations, key_parts)

        if text is None and self.current_locale != 'en':
            en_translations = self.available_locales.get('en', {}).get('translations', {})
            text = get_nested(en_translations, key_parts)

        if text is None:
            return fallback if fallback is not None else key

        if args:
            try:
                return text.format(*args)
            except:
                return text
        return text

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Динамически сканирует папку locales и возвращает список языков с метаданными"""
        locales_dir = Path(__file__).parent / 'locales'
        languages = []

        for locale_file in locales_dir.glob('*.json'):
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('_meta', {})

                    lang_code = meta.get('language_code', locale_file.stem)

                    # Устанавливаем значения по умолчанию для всех обязательных полей
                    languages.append({
                        'code': lang_code,
                        'name': meta.get('language_name', lang_code.upper()),
                        'flag': meta.get('flag', '🌐'),
                        'file': locale_file.name,
                        'native_name': meta.get('native_name', meta.get('language_name', lang_code.upper()))
                    })
            except Exception as e:
                print(f"Error loading locale {locale_file}: {str(e)}")

        # Сортируем языки по имени для удобства
        return sorted(languages, key=lambda x: x['name'])

    def change_language(self, lang_code: str):
        """Изменяет текущий язык"""
        if lang_code in self.available_locales:
            self.current_locale = lang_code
            self.config.branch_settings['Locale'] = lang_code
            self.config.save_settings()
            return True
        return False