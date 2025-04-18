import os
import re
import subprocess
from typing import Optional, Dict, List, Any
from .config import ConfigManager
from .localization import LocalizationManager  # Изменили импорт
from .ui import UIManager
from .commands import GitCommands
from rich.table import Table
from rich.box import ROUNDED

class GitBranchManager:
    def __init__(self):
        try:
            self.config = ConfigManager()
            
            # Временная инициализация для первого запуска
            temp_locale = LocalizationManager(self.config)
            self.ui = UIManager(self.config, temp_locale)
            
            if self.config.is_first_run():
                try:
                    self.ui.run_first_time_setup()
                except Exception as e:
                    self.ui.console.print(f"[red]Ошибка при настройке: {str(e)}[/red]")
                    exit(1)
                    
            # Полная инициализация
            self.locale = LocalizationManager(self.config)
            self.ui = UIManager(self.config, self.locale)
            self.git = GitCommands(self.config, self.locale, self.ui)
            
            # Устанавливаем взаимные ссылки
            self.ui.git = self.git
            self.ui.manager = self
            self.git.ui = self.ui

        except Exception as e:
            print(f"Критическая ошибка инициализации: {str(e)}")
            exit(1)

        # Загружаем настройки
        self.config.load_settings()

    def tr(self, key: str, *args, fallback: Optional[str] = None) -> str:
        return self.locale.tr(key, *args, fallback=fallback)

    def run_git_command(self, command: str, check: bool = False, cwd: Optional[str] = None) -> Optional[str]:
        return self.git.run_git_command(command, check, cwd)

    def get_current_branch(self) -> Optional[str]:
        return self.git.get_current_branch()

    def show_prompt(self):
        print(self.ui.prompt(), end='', flush=True)

    def show_branches(self):
        self.ui.show_branches()

    def set_branch_prefix(self):
        self.ui.set_branch_prefix()

    def set_default_remote(self):
        self.ui.set_default_remote()

    def change_work_directory(self):
        self.ui.change_work_directory()

    def show_git_status(self):
        self.ui.show_git_status()

    def show_git_log(self):
        self.ui.show_git_log()

    def show_git_actions_menu(self):
        self.ui.show_git_actions_menu()

    def show_key_bindings_help(self):
        self.ui.show_key_bindings_help()

    def change_language_interactive(self):
        self.ui.change_language_interactive()

    def show_unknown_command(self, command: str):
        self.ui.show_unknown_command(command)

    def show_happy_cat(self, message: str):
        self.ui.show_happy_cat(message)

    def show_unhappy_cat(self, message: str):
        self.ui.show_unhappy_cat(message)

    def show_dragon(self):
        self.ui.show_dragon()

    def show_phoenix(self):
        self.ui.show_phoenix()

    def clear_screen(self):
        self.ui.clear_screen()

    def _save_history(self):
        self.ui._save_history()

    def new_branch_from_master(self):
        """Создает новую ветку от основной ветки"""
        prefix = self.config.branch_settings["Prefix"]
        work_dir = os.path.abspath(self.config.branch_settings["WorkDir"])

        if not os.path.isdir(work_dir):
            self.ui.show_unhappy_cat(f"🚫 {self.tr('errors.directory_not_exists').format(work_dir)}")
            return

        git_dir = os.path.join(work_dir, ".git")
        if not os.path.isdir(git_dir):
            self.ui.show_unhappy_cat(f"🚫 {self.tr('errors.not_git_repo')}")
            return

        default_branch = self.git._get_default_branch()

        print(f"\n{self.ui.color_codes['dark_cyan']}╭{'─' * 40}╮")
        print(f"│ {self.tr('branch.create_title').center(38)} │")
        print(f"│ {self.tr('branch.prefix_label').format(prefix=prefix).ljust(38)} │")
        print(f"│ {self.tr('branch.base_label').format(branch=default_branch).ljust(38)} │")
        print(f"╰{'─' * 40}╯{self.ui.color_codes['reset']}\n")

        while True:
            branch_number = input(self.tr("branch.enter_task_number")).strip()
            if not branch_number or not branch_number.isdigit():
                self.ui.show_unhappy_cat(f"❌ {self.tr('branch.invalid_task')}")
                continue

            branch_name = input(self.tr("branch.enter_name")).strip()
            if not branch_name or not re.match(r'^[\w-]+$', branch_name, re.ASCII):
                self.ui.show_unhappy_cat(f"❌ {self.tr('branch.invalid_name')}")
                continue

            full_branch_name = f"{prefix}{branch_number}/{branch_name}"

            if self._branch_exists(full_branch_name):
                choice = input(self.tr("branch.exists_switch")).lower()
                if choice == 'y':
                    if self.git.run_git_command(f"checkout {full_branch_name}") is not None:
                        self.ui.show_happy_cat(self.tr("branch.created").format(full_branch_name))
                        return
                continue

            commands = [
                ["git", "fetch", "origin"],
                ["git", "checkout", default_branch],
                ["git", "reset", "--hard", f"origin/{default_branch}"],
                ["git", "checkout", "-b", full_branch_name],
                ["git", "push", "-u", "origin", full_branch_name]
            ]

            print(f"\n{self.ui.color_codes['dark_gray']}{self.tr('commands.creating_branch').format(full_branch_name)}{self.ui.color_codes['reset']}")

            for cmd in commands:
                process = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
                if process.returncode != 0:
                    self.ui.show_unhappy_cat(f"🚫 {self.tr('errors.git_command_failed').format(process.stderr.strip() or self.tr('errors.unknown'))}")
                    return

            current_branch = self.git.get_current_branch()
            if current_branch == full_branch_name:
                self.ui.show_happy_cat(self.tr("branch.created").format(full_branch_name))
            else:
                self.ui.show_unhappy_cat(self.tr("branch.not_switched"))
            return

    def _branch_exists(self, branch: str) -> bool:
        """Проверяет существование ветки"""
        cmd = ["git", "show-ref", "--verify", f"refs/heads/{branch}"]
        return subprocess.run(cmd, cwd=self.config.branch_settings["WorkDir"]).returncode == 0

    def delete_branch(self):
        """Удаляет ветку"""
        current_branch = self.git.get_current_branch()
        if not current_branch:
            self.ui.show_unhappy_cat(self.tr("errors.no_current_branch"))
            return

        branch_data = self.git._get_branch_data()
        if not branch_data:
            self.ui.show_unhappy_cat(self.tr("errors.no_branches"))
            return

        self.ui.display_branch_table(branch_data, current_branch)
        branch_map = {str(idx + 1): b["local_branch"] for idx, b in enumerate(branch_data)}

        while True:
            choice = input(self.tr("branch.select_prompt").format(len(branch_data)))

            if choice.lower() == 'q':
                return

            if choice in branch_map:
                branch_to_delete = branch_map[choice]

                if branch_to_delete == current_branch:
                    self.ui.show_unhappy_cat(self.tr("branch.current_delete"))
                    continue

                confirm = input(self.tr("branch.delete_confirm").format(branch_to_delete)).strip().lower()
                if confirm != 'y':
                    continue

                result = self.git.run_git_command(f"branch -D {branch_to_delete}")
                if result is not None:
                    remote_branch = next((b["remote_branch"] for b in branch_data if b["local_branch"] == branch_to_delete), "")
                    if remote_branch:
                        remote_confirm = input(self.tr("branch.delete_remote").format(remote_branch)).strip().lower()
                        if remote_confirm == 'y':
                            self.git.run_git_command(f"push {self.config.branch_settings['DefaultRemote']} --delete {remote_branch}")

                    self.ui.show_happy_cat(self.tr("branch.deleted").format(branch_to_delete))
                    return
                else:
                    self.ui.show_unhappy_cat(self.tr("branch.delete_failed").format(branch_to_delete))
            else:
                self.ui.show_error(self.tr('errors.invalid_choice'))

    def reset_master_branch(self, confirm: bool = True):
        """Сбрасывает ветку master/main с проверкой незакоммиченных изменений"""
        # Проверяем наличие незакоммиченных изменений
        status = self.git.run_git_command("status --porcelain")
        changes_exist = bool(status)
        
        if changes_exist:
            self.ui.console.print("\n[bold yellow]⚠ Внимание! Есть незакоммиченные изменения:[/bold yellow]\n")
            
            # Выводим список измененных файлов
            changes_table = Table(
                box=ROUNDED,
                header_style="bold yellow",
                show_header=True,
                show_lines=False
            )
            changes_table.add_column("Статус", style="cyan", width=5)
            changes_table.add_column("Файл", style="white")
            
            for line in status.split('\n'):
                if line:
                    status_code = line[:2].strip()
                    filename = line[3:]
                    changes_table.add_row(status_code, filename)
            
            self.ui.console.print(changes_table)
            
            # Запрашиваем подтверждение только если есть изменения
            if confirm:
                choice = input("\nВы уверены, что хотите сбросить ветку с потерей изменений? (y/n): ").strip().lower()
                if choice != 'y':
                    return
        elif confirm:
            # Если изменений нет, запрашиваем стандартное подтверждение
            choice = input(self.locale.tr("reset.master_confirm")).strip().lower()
            if choice != 'y':
                return

        default_branch = self.git._get_default_branch()
        current_branch = self.git.get_current_branch()

        with self.ui.create_progress() as progress:
            task = progress.add_task(f"[cyan]{self.locale.tr('reset.fetching')}...", total=100)
            self.git.run_git_command("fetch")
            progress.update(task, advance=30)

            # Если текущая ветка не master/main, сначала переключаемся
            if current_branch != default_branch:
                progress.update(task, description=f"[cyan]Переключение на {default_branch}...")
                self.git.run_git_command(f"checkout -f {default_branch}")
                progress.update(task, advance=20)

            progress.update(task, description=f"[cyan]{self.locale.tr('reset.resetting')}...")
            self.git.run_git_command(f"reset --hard origin/{default_branch}")
            progress.update(task, advance=50)

        self.git._run_npm_install()
        self.ui.show_dragon()

    def reset_unstable_branch(self, confirm: bool = True):
        """Сбрасывает ветку unstable с проверкой незакоммиченных изменений"""
        # Проверяем наличие незакоммиченных изменений
        status = self.git.run_git_command("status --porcelain")
        changes_exist = bool(status)
        
        if changes_exist:
            self.ui.console.print("\n[bold yellow]⚠ Внимание! Есть незакоммиченные изменения:[/bold yellow]\n")
            
            # Выводим список измененных файлов
            changes_table = Table(
                box=ROUNDED,
                header_style="bold yellow",
                show_header=True,
                show_lines=False
            )
            changes_table.add_column("Статус", style="cyan", width=5)
            changes_table.add_column("Файл", style="white")
            
            for line in status.split('\n'):
                if line:
                    status_code = line[:2].strip()
                    filename = line[3:]
                    changes_table.add_row(status_code, filename)
            
            self.ui.console.print(changes_table)
            
            # Запрашиваем подтверждение только если есть изменения
            if confirm:
                choice = input("\nВы уверены, что хотите сбросить ветку с потерей изменений? (y/n): ").strip().lower()
                if choice != 'y':
                    return
        elif confirm:
            # Если изменений нет, запрашиваем стандартное подтверждение
            choice = input(self.locale.tr("reset.unstable_confirm")).strip().lower()
            if choice != 'y':
                return

        current_branch = self.git.get_current_branch()

        with self.ui.create_progress() as progress:
            task = progress.add_task(f"[cyan]{self.locale.tr('reset.fetching')}...", total=100)
            self.git.run_git_command("fetch")
            progress.update(task, advance=30)

            # Если текущая ветка не unstable, сначала переключаемся
            if current_branch != "unstable":
                progress.update(task, description=f"[cyan]Переключение на unstable...")
                self.git.run_git_command("checkout -f unstable")
                progress.update(task, advance=20)

            progress.update(task, description=f"[cyan]{self.locale.tr('reset.resetting')}...")
            self.git.run_git_command("reset --hard origin/unstable")
            progress.update(task, advance=50)

        self.git._run_npm_install()
        self.ui.show_phoenix()

    def soft_reset_to_master(self, confirm: bool = True):
        """Мягкий сброс до master/main"""
        if confirm:
            choice = input(self.tr("reset.soft_confirm")).strip().lower()
            if choice != 'y':
                return

        default_branch = self.git._get_default_branch()
        self.git.run_git_command(f"reset --soft {default_branch}")
        self.ui.show_success(self.tr('reset.soft_success').format(default_branch))

    def rebase_from_master(self, confirm: bool = True):
        """Ребейзит текущую ветку от master/main"""
        if confirm:
            choice = input(self.tr("reset.rebase_confirm")).strip().lower()
            if choice != 'y':
                return

        default_branch = self.git._get_default_branch()
        result = self.git.run_git_command(f"rebase {default_branch}")
        if result is not None:
            self.ui.show_success(self.tr('reset.rebase_success').format(default_branch))
        else:
            self.ui.show_error(self.tr('reset.rebase_error'))

    def clear_prefix_history(self):
        """Очищает историю префиксов"""
        confirm = input(self.tr("prefix.clear_confirm")).strip().lower()
        if confirm == 'y':
            self.config.clear_prefix_history()
            self.ui.show_success(self.tr('prefix.cleared'))

    def clear_history(self):
        """Очищает все истории"""
        confirm = input(self.tr("history.clear_confirm")).strip().lower()
        if confirm == 'y':
            self.config.clear_prefix_history()
            self.config.clear_dir_history()
            self.ui.show_success(self.tr('history.cleared'))
            
    def show_profiles_menu(self):
        """Показывает меню управления профилями"""
        profiles = self.config.profiles
        current = self.config.current_profile

        table = Table(
            title=self.tr("profiles.title"),
            box=ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("#", style="green", width=5)
        table.add_column(self.tr("profiles.name"), style="white", min_width=15)
        table.add_column(self.tr("profiles.prefix"), style="cyan", width=15)
        table.add_column(self.tr("profiles.workdir"), style="dim", min_width=30)
        table.add_column("", style="dim", width=5)

        for idx, profile in enumerate(profiles, 1):
            is_current = "✓" if profile["ProfileName"] == current else ""
            table.add_row(
                str(idx),
                profile["ProfileName"],
                profile["Prefix"],
                profile["WorkDir"],
                is_current
            )

        self.ui.console.print()
        self.ui.console.print(table)
        self.ui.console.print()

        options = [
            {"key": "s", "description": self.tr("profiles.switch"), "action": self._switch_profile},
            {"key": "a", "description": self.tr("profiles.add"), "action": self._add_profile},
            {"key": "d", "description": self.tr("profiles.delete"), "action": self._delete_profile},
            {"key": "q", "description": self.tr("menu.exit"), "action": lambda: None}
        ]

        for option in options:
            self.ui.console.print(f"[bold green]{option['key']}[/bold green] - {option['description']}")

        while True:
            choice = input(f"{self.tr('profiles.select_action')}: ").strip().lower()
            selected = next((o for o in options if o["key"].lower() == choice), None)

            if selected:
                try:
                    selected["action"]()
                    break
                except Exception as e:
                    self.ui.show_error(self.tr('errors.command_failed').format(e))
            else:
                self.ui.show_error(self.tr('errors.invalid_choice'))

    def _switch_profile(self):
        """Переключает профиль"""
        profiles = self.config.profiles
        choice = input(self.tr("profiles.select_switch")).strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            profile = profiles[int(choice)-1]
            if self.config.switch_profile(profile["ProfileName"]):
                self.ui.show_success(self.tr('profiles.switched').format(profile["ProfileName"]))
                # Обновляем локализацию
                self.locale.current_locale = profile["Locale"]
                self.locale.load_locales()
        else:
            self.ui.show_error(self.tr('errors.invalid_choice'))

    def _add_profile(self):
        """Добавляет новый профиль с выбором способа ввода рабочей папки"""
        try:
            from tkinter import filedialog
            from tkinter import Tk

            self.ui.console.print("\n[bold]Добавление нового профиля[/bold]")
            
            # Ввод имени профиля
            name = input("Введите имя нового профиля: ").strip()
            if not name:
                self.ui.show_error("Имя профиля не может быть пустым")
                return

            if any(p["ProfileName"] == name for p in self.config.profiles):
                self.ui.show_error("Профиль с таким именем уже существует")
                return

            # Ввод префикса
            prefix = input("Введите префикс веток (по умолчанию dl/TTSH-): ").strip() or "dl/TTSH-"
            
            # Ввод удаленного репозитория
            remote = input("Введите удаленный репозиторий (по умолчанию origin): ").strip() or "origin"

            # Выбор рабочей папки
            self.ui.console.print("\n[bold]Выбор рабочей папки:[/bold]")
            self.ui.console.print("1. Ввести путь вручную")
            self.ui.console.print("2. Выбрать через проводник")
            self.ui.console.print("3. Использовать текущую папку")
            
            work_dir = None
            while work_dir is None:
                choice = input("Ваш выбор (1-3): ").strip()
                
                if choice == '1':  # Ручной ввод
                    work_dir = input("Введите полный путь к рабочей папке: ").strip()
                    if not os.path.isdir(work_dir):
                        self.ui.show_error("Указанная папка не существует")
                        work_dir = None
                        
                elif choice == '2':  # Через проводник
                    root = Tk()
                    root.withdraw()
                    work_dir = filedialog.askdirectory(title="Выберите папку с git-репозиторием")
                    root.destroy()
                    if not work_dir:
                        self.ui.show_info("Выбор отменен, будет использована текущая папка")
                        work_dir = os.getcwd()
                        
                elif choice == '3':  # Текущая папка
                    work_dir = os.getcwd()
                    
                else:
                    self.ui.show_error("Неверный выбор")

            # Проверка git-репозитория
            if not os.path.isdir(os.path.join(work_dir, ".git")):
                confirm = input("Выбранная папка не содержит git-репозиторий. Продолжить? (y/n): ").strip().lower()
                if confirm != 'y':
                    return

            # Выбор языка из списка доступных
            locale = self._select_language()
            if not locale:
                return  # Пользователь отменил выбор

            # Создание профиля
            if self.config.add_profile(name, prefix, remote, work_dir, locale):
                self.ui.show_success(f"Профиль '{name}' успешно создан и активирован!")
                
                # Обновляем локализацию согласно новому профилю
                self.locale.change_language(locale)
                
                # Показываем информацию о текущем профиле
                current_settings = self.config.get_current_settings()
                self.ui.console.print(f"\nТекущий профиль: [bold green]{name}[/bold green]")
                self.ui.console.print(f"Рабочая папка: [cyan]{current_settings['WorkDir']}[/cyan]")
                self.ui.console.print(f"Язык интерфейса: [cyan]{locale}[/cyan]")
            else:
                self.ui.show_error("Не удалось создать профиль")
                
        except Exception as e:
            self.ui.show_error(f"Ошибка при создании профиля: {str(e)}")

    def _select_language(self) -> str:
        """Отображает список доступных языков и возвращает выбранный код языка"""
        languages = self.locale.get_supported_languages()
        if not languages:
            self.ui.show_error("Не найдено доступных языков")
            return ""

        # Создаем таблицу с доступными языками
        table = Table(
            title="Выберите язык интерфейса",
            box=ROUNDED,
            header_style="bold cyan",
            border_style="blue",
            show_lines=True
        )
        table.add_column("#", style="green", width=5)
        table.add_column("Язык", style="bold", min_width=15)
        table.add_column("Код", style="dim", width=5)

        for idx, lang in enumerate(languages, 1):
            table.add_row(
                str(idx),
                f"{lang['name']} ({lang['native_name']})",
                lang['code']
            )

        self.ui.console.print()
        self.ui.console.print(table)
        self.ui.console.print()

        while True:
            choice = input(f"Выберите язык (1-{len(languages)} или 'q' для отмены): ").strip().lower()
            
            if choice == 'q':
                return ""
                
            if choice.isdigit() and 1 <= int(choice) <= len(languages):
                return languages[int(choice)-1]['code']
                
            self.ui.show_error("Неверный выбор. Попробуйте снова.")

    def _delete_profile(self):
        """Удаляет профиль"""
        profiles = self.config.profiles
        if len(profiles) <= 1:
            self.ui.show_error(self.tr('profiles.cant_delete_last'))
            return

        choice = input(self.tr("profiles.select_delete")).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            profile = profiles[int(choice)-1]
            if profile["ProfileName"] == "default":
                self.ui.show_error(self.tr('profiles.cant_delete_default'))
                return

            confirm = input(self.tr("profiles.delete_confirm").format(profile["ProfileName"])).strip().lower()
            if confirm == 'y':
                if self.config.remove_profile(profile["ProfileName"]):
                    self.ui.show_success(self.tr('profiles.deleted').format(profile["ProfileName"]))