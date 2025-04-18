import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
import os

class LocalizationManager:
    def __init__(self, config):
        self.config = config
        self._locales_dir = Path(__file__).parent / 'locales'
        self._available_locales = {}  # type: Dict[str, dict]
        self.current_locale = 'ru'
        self._load_locales()
        
        # Привязка текущей локали к конфигу
        if current_profile := self.config.get_current_settings():
            self.current_locale = current_profile.get('Locale', 'ru')

    def _load_locales(self):
        """Загружает все локали один раз при инициализации"""
        if not self._locales_dir.exists():
            print(f"Locales directory not found: {self._locales_dir}")
            return

        for locale_file in self._locales_dir.glob('*.json'):
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('_meta', {})
                    lang_code = meta.get('language_code', locale_file.stem)
                    
                    # Стандартизация метаданных
                    meta.update({
                        'language_name': meta.get('language_name', lang_code.upper()),
                        'native_name': meta.get('native_name', meta.get('language_name', lang_code.upper())),
                        'flag': meta.get('flag', '🌐')
                    })
                    
                    self._available_locales[lang_code] = {
                        'meta': meta,
                        'translations': {k: v for k, v in data.items() if not k.startswith('_')}
                    }
            except Exception as e:
                print(f"Error loading locale {locale_file}: {str(e)}")

    @lru_cache(maxsize=1024)
    def tr(self, key: str, *args, fallback: Optional[str] = None) -> str:
        """
        Оптимизированный метод перевода с кешированием результатов.
        Поддерживает вложенные ключи через точку.
        """
        def get_nested(data: dict, keys: list) -> Optional[str]:
            for key_part in keys:
                if not isinstance(data, dict):
                    return None
                data = data.get(key_part)
            return data

        # Основной язык
        locale_data = self._available_locales.get(self.current_locale, {})
        text = get_nested(locale_data.get('translations', {}), key.split('.'))
        
        # Фолбек на английский
        if text is None and self.current_locale != 'en':
            en_data = self._available_locales.get('en', {})
            text = get_nested(en_data.get('translations', {}), key.split('.'))
        
        # Финальный фолбек
        if text is None:
            return fallback if fallback is not None else key

        try:
            return text.format(*args) if args else text
        except (IndexError, KeyError):
            return text

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Возвращает оптимизированный список языков с кешированием"""
        if not hasattr(self, '_cached_languages'):
            languages = []
            for lang_code, data in self._available_locales.items():
                meta = data['meta']
                languages.append({
                    'code': lang_code,
                    'name': meta['language_name'],
                    'native_name': meta['native_name'],
                    'flag': meta['flag']
                })
            self._cached_languages = sorted(languages, key=lambda x: x['name'])
        return self._cached_languages

    def change_language(self, lang_code: str) -> bool:
        """Изменяет язык с обновлением кеша"""
        if lang_code in self._available_locales:
            self.current_locale = lang_code
            self.tr.cache_clear()  # Очищаем кеш переводов
            
            # Обновляем конфиг
            if current_settings := self.config.get_current_settings():
                current_settings["Locale"] = lang_code
                self.config.save_settings()
            return True
        return False

    # Оптимизация для часто используемых элементов интерфейса
    COMMON_STRINGS = {
        'errors.invalid_choice': "Неверный выбор",
        'menu.exit': "Выход",
        # Добавьте другие часто используемые строки
    }

    def fast_tr(self, key: str) -> str:
        """Ультрабыстрый метод для часто используемых строк"""
        return self.COMMON_STRINGS.get(key, self.tr(key))
    
    def load_locales(self):
        """Алиас для совместимости (метод может вызываться из других классов)"""
        self._load_locales()