import subprocess
import re
from rich.style import Style
from rich.color import Color
from rich.panel import Panel
from rich.console import Console
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Prompt
import random
import os
from tkinter import Tk, filedialog
from pyreadline3 import Readline
from typing import List, Dict, Optional, Callable, Any
from .localization import LocalizationManager

readline = Readline()

class UIManager:
    def __init__(self, config, locale):
        self.config = config
        self.locale = locale
        self.git = None
        self.manager = None
        self.console = Console()
        self.history_file = self.config.history_file

        self.color_codes = {
            "reset": "\033[0m",
            "bright_blue": "\033[94m",
            "bright_green": "\033[92m",
            "bright_cyan": "\033[96m",
            "bright_red": "\033[91m",
            "bright_yellow": "\033[93m",
            "dark_gray": "\033[90m",
            "dark_cyan": "\033[36m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "bold": "\033[1m",
        }

    def run_first_time_setup(self):
        """Запускает красивый мастер первоначальной настройки"""
        # Красивое приветствие
        self.console.print(Panel.fit(
            "[bold green]🌍 Git Branch Manager - Первоначальная настройка[/]",
            subtitle="[dim]Давайте настроим ваш инструмент[/dim]",
            border_style="green",
            padding=(1, 2)
        ))

        # 1. Выбор языка
        self._setup_language()

        # 2. Выбор рабочей директории
        work_dir = self._setup_work_directory(first_run=True)

        # 3. Настройка префикса веток
        prefix = self._setup_branch_prefix(first_run=True)

        # Создаем первый профиль
        self.config.initialize_first_profile(
            prefix=prefix,
            work_dir=work_dir,
            locale=self.locale.current_locale
        )

        # Итоговое сообщение
        summary = Columns([
            Panel(
                f"[bold]Язык:[/]\n{self._get_current_language_display()}",
                border_style="blue"
            ),
            Panel(
                f"[bold]Директория:[/]\n[cyan]{work_dir}[/]",
                border_style="blue"
            ),
            Panel(
                f"[bold]Префикс:[/]\n[cyan]{prefix}[/]",
                border_style="blue"
            )
        ], expand=True)

        self.console.print(Panel.fit(
            "[bold green]✓ Настройка завершена успешно![/]",
            border_style="green",
            padding=(1, 2)
        ))
        self.console.print(summary)

        # Сообщение о перезапуске
        restart_message = Text.assemble(
            ("⚠ ", "bold yellow"),
            ("Для применения настроек ", ""),
            ("перезапустите скрипт", "bold yellow"),
            (" вручную\n", ""),
            ("Команда: ", "dim"),
            ("python git_tools.py", "bold cyan")
        )

        self.console.print(Panel(
            restart_message,
            title="[yellow]Действие требуется[/yellow]",
            border_style="yellow",
            padding=(1, 2),
            width=60
        ))

        exit(0)

    def _setup_language(self):
        """Красивый выбор языка с автоматическим определением доступных языков"""
        languages = self.locale.get_supported_languages()

        # Проверяем, что есть хотя бы один язык
        if not languages:
            self.console.print("[red]Не найдено ни одного файла локализации![/red]")
            exit(1)

        table = Table(
            title="[bold]1. Выберите язык интерфейса[/bold]",
            box=ROUNDED,
            header_style="bold cyan",
            border_style="blue",
            show_lines=True
        )

        table.add_column("#", style="green", width=3)
        table.add_column("Язык", style="bold", min_width=12)
        table.add_column("Нативное название", style="bright_cyan", min_width=12)
        table.add_column("Код", style="dim", width=5)

        for idx, lang in enumerate(languages, 1):
            lang_name = lang.get('name', lang['code'].upper())
            native_name = lang.get('native_name', lang_name)
            is_current = "✓" if lang['code'] == self.locale.current_locale else ""
            table.add_row(
                str(idx),
                lang_name,
                native_name,
                f"[dim]{lang['code']}[/dim]"
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            choice = input(f"{self.locale.tr("language_selection.prompt").format(len(languages))}").strip()

            if choice.isdigit() and 1 <= int(choice) <= len(languages):
                selected = languages[int(choice)-1]
                if self.locale.change_language(selected['code']):
                    break
            else:
                self.console.print(f"[red]{self.locale.tr('errors.invalid_choice')}[/red]")

    def _setup_work_directory(self, first_run=False):
        """Выбор папки репозитория с учетом первого запуска"""
        if first_run:
            self.console.print(Panel.fit(
                "[bold]1. Выберите рабочую директорию с git-репозиторием[/bold]",
                border_style="blue"
            ))

        while True:
            # Создаем и сразу скрываем окно Tkinter
            root = Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)  # Окно поверх других
            
            work_dir = filedialog.askdirectory(title="Выберите папку с git-репозиторием")
            root.destroy()  # Закрываем окно после выбора

            if not work_dir:  # Если пользователь отменил выбор
                work_dir = os.getcwd()
                self.console.print(f"[yellow]{self.locale.tr("directory.using_current").format(work_dir=work_dir)}[/yellow]")
            
            # Проверяем, что это git-репозиторий
            if os.path.isdir(os.path.join(work_dir, ".git")):
                return work_dir
                
            self.console.print(f"[red]{self.locale.tr('errors.not_git_repo')}[/red]")

        while True:
            self.console.print("\n[dim]Текущий выбор:[/dim] [cyan]Выберите папку[/cyan]")
            self.console.print("[yellow]1.[/] Выбрать через проводник")
            self.console.print("[yellow]2.[/] Ввести путь вручную")
            self.console.print("[yellow]q.[/] Отмена")

            choice = input("Ваш выбор (1/2/q): ").strip().lower()

            if choice == '1':
                root = Tk()
                root.withdraw()
                work_dir = filedialog.askdirectory()
                root.destroy()

                if work_dir:
                    if os.path.isdir(os.path.join(work_dir, ".git")):
                        # Сохраняем директорию в настройках
                        self.config.branch_settings["WorkDir"] = work_dir
                        # Обновляем историю директорий
                        if work_dir in self.config.dir_history:
                            self.config.dir_history.remove(work_dir)
                        self.config.dir_history.insert(0, work_dir)
                        # Сохраняем настройки в файл
                        self.config.save_settings()
                        break
                    self.console.print("[red]Выбранная папка не содержит git-репозиторий![/red]")

            elif choice == '2':
                work_dir = input("Введите полный путь к папке: ").strip()
                if os.path.isdir(work_dir) and os.path.isdir(os.path.join(work_dir, ".git")):
                    # Сохраняем директорию в настройках
                    self.config.branch_settings["WorkDir"] = work_dir
                    # Обновляем историю директорий
                    if work_dir in self.config.dir_history:
                        self.config.dir_history.remove(work_dir)
                    self.config.dir_history.insert(0, work_dir)
                    # Сохраняем настройки в файл
                    self.config.save_settings()
                    break
                self.console.print(f"[red]{self.locale.tr('errors.not_git_repo')}[/red]")

            elif choice == 'q':
                exit(0)

            else:
                self.console.print(f"[red]{self.locale.tr('errors.invalid_choice')}[/red]")

    def _setup_branch_prefix(self, first_run=False):
        """Настройка префикса веток с учетом первого запуска"""
        if first_run:
            self.console.print(Panel.fit(
                "[bold]2. Настройте префикс для новых веток[/bold]",
                border_style="blue"
            ))
    
        return input("Введите префикс (например, dl/TTSH-): ").strip() or "dl/TTSH-"
        
        """Настройка префикса веток"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold]3. Настройте префикс для новых веток[/bold]",
            border_style="blue"
        ))

        prefix = input(f"Введите префикс (например, dl/TTSH-): ").strip() or "dl/TTSH-"
        self.config.branch_settings["Prefix"] = prefix
        self.config.prefix_history = [prefix]

    def _get_current_language_display(self):
        """Возвращает отформатированное отображение текущего языка"""
        for lang in self.locale.get_supported_languages():
            if lang['code'] == self.locale.current_locale:
                return f"{lang['native_name']} ([dim]{lang['code']}[/])"
        return ""

    def show_amiga_banner(self):
        """Идеально выровненный радужный GITTOOLS"""
        from rich.text import Text
        from rich.console import Console

        console = Console()

        letters = {
            'G': [
                "  ██████╗ ",
                " ██╔════╝ ",
                " ██║  ███╗",
                " ██║   ██║",
                " ╚██████╔╝",
                "  ╚═════╝ "
            ],
            'I': [
                " ██╗",
                " ██║",
                " ██║",
                " ██║",
                " ██║",
                " ╚═╝"
            ],
            'T': [
                " ████████╗",
                " ╚══██╔══╝",
                "    ██║   ",
                "    ██║   ",
                "    ██║   ",
                "    ╚═╝   "
            ],
            'O': [
                "  ██████╗ ",
                " ██╔═══██╗",
                " ██║   ██║",
                " ██║   ██║",
                " ╚██████╔╝",
                "  ╚═════╝ "
            ],
            'L': [
                " ██╗     ",
                " ██║     ",
                " ██║     ",
                " ██║     ",
                " ███████╗",
                " ╚══════╝"
            ],
            'S': [
                "  ██████╗ ",
                " ██╔════╝ ",
                " ╚█████╗  ",
                "  ╚═══██╗ ",
                " ██████╔╝ ",
                " ╚═════╝  "
            ]
        }

        # Радужные цвета
        colors = [
            "#FF0000", "#FF7F00", "#FFFF00",
            "#00FF00", "#0000FF", "#9400D3"
        ]

        # Собираем строки
        banner_lines = []
        for row in range(6):
            line = []
            for char in "GITTOOLS":
                line.append(letters[char][row])
            banner_lines.append("".join(line))

        # Вычисляем максимальную длину строки
        max_length = max(len(line) for line in banner_lines)

        # Выводим с цветами и центровкой
        banner = Text()
        for i, line in enumerate(banner_lines):
            # Центрируем каждую строку вручную
            padding = (console.width - len(line)) // 2
            banner.append(" " * padding + line, style=colors[i])
            banner.append("\n")

        console.print(banner)

    def show_error(self, message: str):
        """Показывает сообщение об ошибке"""
        self.console.print(f"[red]{message}[/red]")

    def show_success(self, message: str):
        """Показывает сообщение об успехе"""
        self.console.print(f"[green]{message}[/green]")

    def show_info(self, message: str):
        """Показывает информационное сообщение"""
        self.console.print(f"[cyan]{message}[/cyan]")

    def show_command(self, command: str):
        """Показывает выполняемую команду"""
        self.console.print(f"[dim]{command}[/dim]")

    def create_progress(self, quiet: bool = False) -> Progress:
        """Создает прогресс-бар"""
        if quiet:
            return Progress(console=Console(quiet=True))

        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
            console=self.console
        )

    def prompt(self) -> str:
        """Формирует приглашение командной строки"""
        current_settings = self.config.get_current_settings()
        if not current_settings:
            return "gitTools [ERROR: No profile]> "
        
        current_path = current_settings["WorkDir"]
        branch = self.git.get_current_branch() if self.git else None

        prefix_color = self.color_codes["dark_gray"]
        path_color = self.color_codes["bright_blue"]
        branch_color = self.color_codes["bright_green"]
        reset_color = self.color_codes["reset"]

        shortened_path = current_path
        home_dir = os.path.expanduser("~")
        if current_path.startswith(home_dir):
            shortened_path = current_path.replace(home_dir, "~", 1)

        if branch:
            return f"{prefix_color}gitTools -> {path_color}{shortened_path}{branch_color} [{branch}]{reset_color}> "
        else:
            return f"{prefix_color}gitTools -> {path_color}{shortened_path}{reset_color}> "

    def display_branch_table(self, branch_data: List[Dict[str, Any]], current_branch: Optional[str]):
        """Отображает таблицу с ветками"""
        table = Table(
            title=self.locale.tr("branch.list_title"),
            box=ROUNDED,
            header_style="bold cyan",
            border_style="dim",
            show_lines=True
        )

        table.add_column(self.locale.tr("branch.number"), style="green", width=5)
        table.add_column(self.locale.tr("branch.name"), style="white", min_width=20)
        table.add_column(self.locale.tr("branch.last_commit"), style="dim", width=18)
        table.add_column(self.locale.tr("branch.author"), style="dim", width=20)

        for idx, branch in enumerate(branch_data, 1):
            is_current = branch["local_branch"] == current_branch
            branch_style = "bold green" if is_current else ""
            icon = " " if is_current else "  "

            branch_text = Text()
            branch_text.append(icon, style=branch_style)
            branch_text.append(branch["local_branch"], style=branch_style)

            remote_text = Text()
            remote_text.append("  ⤷ ", style="dim")
            remote_text.append(branch["remote_branch"] if branch["remote_branch"] else "─", style="dim")

            full_branch_text = Text("\n").join([branch_text, remote_text])

            table.add_row(
                f"[green][{idx}][/green]",
                full_branch_text,
                f"[dim]{branch['last_commit_relative']}[/dim]",
                f"[dim]{branch['author']}[/dim]"
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def show_branches(self):
        """Показывает список веток с возможностью выбора"""
        current_settings = self.config.get_current_settings()
        if not current_settings:
            self.show_error("No active profile")
            return
        
        branch_data = self.git._get_branch_data()
        if not branch_data:
            self.show_error(self.locale.tr('errors.no_branches'))
            return

        current_branch = self.git.get_current_branch()
        self.display_branch_table(branch_data, current_branch)
        self._select_branch_interaction(branch_data, current_branch)

    def _select_branch_interaction(self, branch_data: List[Dict[str, Any]], current_branch: Optional[str]):
        """Обрабатывает выбор ветки пользователем"""
        branch_map = {str(idx + 1): branch["local_branch"] for idx, branch in enumerate(branch_data)}

        while True:
            try:
                choice = input(self.locale.tr("branch.select_prompt").format(len(branch_data))).strip()

                if choice.lower() == 'q':
                    break

                if choice in branch_map:
                    selected_branch = branch_map[choice]
                    result = self.git.run_git_command(f"checkout {selected_branch}")
                    new_branch = self.git.get_current_branch()

                    if new_branch == selected_branch:
                        self.show_success(self.locale.tr('branch.switch_success').format(selected_branch))
                        
                        # Проверяем наличие package.json
                        work_dir = self.config.branch_settings["WorkDir"]
                        package_json = os.path.join(work_dir, "package.json")

                        if os.path.isfile(package_json):
                            self.console.print(f"\n[bold yellow]{self.locale.tr("npm.detected")}[/bold yellow]")
                            self.git._run_npm_install()
                        else:
                            self.console.print(f"\n[dim]{self.locale.tr("npm.not_detected")}[/dim]")
                        
                        return
                    else:
                        self._handle_branch_switch_error(selected_branch, new_branch)
                else:
                    self.show_error(self.locale.tr('errors.invalid_choice'))

            except Exception as e:
                self.show_error(f"Error: {str(e)}")
                break

    def _handle_branch_switch_error(self, selected_branch: str, current_branch: str):
        """Обрабатывает ошибки при переключении ветки"""
        error_panel = Panel(
            Text(f"{self.locale.tr('branch.switch_failed').format(selected_branch)}\n"
                 f"{self.locale.tr('branch.current').format(current_branch)}"),
            title="[red]Switch Error[/red]",
            border_style="red",
            width=60
        )
        self.console.print(error_panel)

        status = self.git.run_git_command("status --porcelain -u")
        if status:
            changes_table = Table(
                title="[yellow]Uncommitted Changes[/yellow]",
                box=ROUNDED,
                header_style="bold yellow",
                show_header=True,
                show_lines=False
            )
            changes_table.add_column("Status", style="cyan", width=5)
            changes_table.add_column("File", style="white")

            for line in status.split('\n'):
                if line:
                    status_code = line[:2].strip()
                    filename = line[3:]
                    changes_table.add_row(status_code, filename)

            self.console.print(changes_table)

        force_choice = Prompt.ask(
            "[yellow]Try force checkout?[/yellow]",
            choices=["y", "n"],
            default="n"
        )

        if force_choice == 'y':
            self.git.run_git_command(f"checkout -f {selected_branch}")
            new_branch = self.git.get_current_branch()
            if new_branch == selected_branch:
                self.show_success(f"Switched to [bold green]{selected_branch}[/bold green] (forced)")

    def show_git_log(self):
        """Показывает историю коммитов в табличном формате без графов"""
        console = Console()

        # Устанавливаем правильную кодировку для вывода
        import locale
        locale.setlocale(locale.LC_ALL, '')  # Устанавливаем системную локаль
        encoding = locale.getpreferredencoding()

        # Иконки для разных типов коммитов
        commit_icons = {
            "feat": "✨",
            "fix": "🐛",
            "docs": "📚",
            "style": "🎨",
            "refactor": "♻️",
            "test": "🧪",
            "chore": "🔧",
            "build": "📦",
            "ci": "⚙️",
            "perf": "🚀",
            "revert": "⏪"
        }

        # Получаем данные без графа с указанием кодировки
        log_cmd = [
            "git",
            "log",
            "--all",
            "--pretty=format:%h|%s|%an|%ad|%d",
            "--date=format:%Y-%m-%d %H:%M",
            "--abbrev-commit",
            "-n20"
        ]

        try:
            result = subprocess.run(log_cmd,
                                    cwd=self.config.branch_settings["WorkDir"],
                                    capture_output=True,
                                    text=True,
                                    encoding=encoding)  # Указываем кодировку явно
            log_data = result.stdout.strip()
        except Exception as e:
            console.print(f"[red]{self.locale.tr('errors.git_command_failed').format(str(e))}[/red]")
            return

        if not log_data:
            console.print(f"[yellow]{self.locale.tr('errors.no_commit_data')}[/yellow]")
            return

        table = Table(
            title=f"[bold magenta]{self.locale.tr('history.title')}[/bold magenta]",
            box=ROUNDED,
            header_style="bold cyan",
            border_style="dim blue",
            show_header=True,
            show_lines=True
        )

        table.add_column("#", style="green", width=4)
        table.add_column(self.locale.tr("history.hash"), style="bright_green", width=10)
        table.add_column(self.locale.tr("history.message"), style="white", min_width=30, max_width=50)
        table.add_column(self.locale.tr("history.author"), style="bright_cyan", width=15)
        table.add_column(self.locale.tr("history.date"), style="dim", width=12)
        table.add_column(self.locale.tr("history.refs"), style="yellow", width=20)

        commit_icons = {
            "feat": "✨",
            "fix": "🐛",
            "docs": "📚",
            "style": "🎨",
            "refactor": "♻️",
            "test": "🧪",
            "chore": "🔧",
            "build": "📦",
            "ci": "⚙️",
            "perf": "🚀",
            "revert": "⏪"
        }

        for idx, line in enumerate(log_data.split('\n'), start=1):
            parts = line.split('|')
            if len(parts) < 5:
                continue

            commit_hash = parts[0].strip()[:7] if parts[0] else ""
            message = parts[1].strip() if len(parts) > 1 else ""
            author = parts[2].strip() if len(parts) > 2 else ""
            date = parts[3].strip() if len(parts) > 3 else ""
            refs = parts[4].strip() if len(parts) > 4 else ""

            icon = "● "
            for prefix, emoji in commit_icons.items():
                if message.lower().startswith(prefix):
                    icon = f"{emoji} "
                    break

            message_text = Text()
            message_text.append(icon, style="dim")

            task_match = re.search(r'([A-Z]+-\d+)', message)
            if task_match:
                start, end = task_match.span()
                message_text.append(message[:start])
                message_text.append(message[start:end], style="bold yellow")
                message_text.append(message[end:])
            else:
                message_text.append(message)

            refs_text = Text()
            if refs:
                for ref in refs.strip('()').split(', '):
                    if not ref:
                        continue

                    if 'HEAD' in ref:
                        refs_text.append("🔷 ", style="bold blue")
                    elif 'tag:' in ref:
                        refs_text.append("🏷 ", style="bold yellow")
                        ref = ref.replace('tag:', '').strip()
                    elif 'origin/' in ref:
                        refs_text.append("🌍 ", style="bold green")
                        ref = ref.replace('origin/', '')
                    else:
                        refs_text.append("⎇ ", style="dim")

                    refs_text.append(ref + " ", style="yellow")

            table.add_row(
                str(idx),
                commit_hash,
                message_text,
                author,
                date,
                refs_text if refs else "-"
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def show_git_status(self):
        """Показывает статус git"""
        status = self.git.run_git_command("status -sb")
        if not status:
            self.show_error(self.locale.tr('errors.no_status'))
            return

        panel = Panel.fit(
            status,
            title=f"[bold green]{self.locale.tr('status.title')}[/bold green]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def show_git_actions_menu(self):
        """Показывает меню действий"""
        default_branch = self.git._get_default_branch().upper() if self.git else "MASTER"

        options = [
            {"key": "1", "description": self.locale.tr("menu.reset_master").format(default_branch), "action": lambda: self.manager.reset_master_branch(True)},
            {"key": "2", "description": self.locale.tr("menu.reset_unstable"), "action": lambda: self.manager.reset_unstable_branch(True)},
            {"key": "3", "description": self.locale.tr("menu.soft_reset"), "action": lambda: self.manager.soft_reset_to_master(True)},
            {"key": "4", "description": self.locale.tr("menu.rebase"), "action": lambda: self.manager.rebase_from_master(True)},
            {"key": "5", "description": self.locale.tr("menu.new_branch"), "action": self.manager.new_branch_from_master},
            {"key": "6", "description": self.locale.tr("menu.show_branches"), "action": self.show_branches},
            {"key": "7", "description": self.locale.tr("menu.change_prefix"), "action": self.set_branch_prefix},
            {"key": "8", "description": self.locale.tr("menu.show_log"), "action": self.show_git_log},
            {"key": "9", "description": self.locale.tr("menu.keys_title"), "action": self.show_key_bindings_help},
            {"key": "s", "description": self.locale.tr("menu.show_status"), "action": self.show_git_status},
            {"key": "d", "description": self.locale.tr("menu.delete_branch"), "action": self.manager.delete_branch},
            {"key": "w", "description": self.locale.tr("menu.change_directory"), "action": self.change_work_directory},
            {"key": "r", "description": self.locale.tr("menu.change_remote"), "action": self.set_default_remote},
            {"key": "n", "description": self.locale.tr("menu.npm_scripts"), "action": self.show_npm_scripts},
            {"key": "p", "description": self.locale.tr("menu.profiles"), "action": self.manager.show_profiles_menu()},
            {"key": "l", "description": self.locale.tr("menu.change_language"), "action": self.change_language_interactive},
            {"key": "Q", "description": self.locale.tr("menu.exit"), "action": lambda: None},
        ]

        table = Table(
            title=self.locale.tr("menu.main_title"),
            box=ROUNDED,
            header_style="bold magenta",
            border_style="green",
            show_lines=True
        )

        table.add_column(self.locale.tr("menu.key_column"), style="bright_green", width=8)
        table.add_column(self.locale.tr("menu.action_column"), style="white", min_width=30)

        for option in options:
            table.add_row(
                f"[bold bright_green]{option['key']}[/bold bright_green]",
                option["description"]
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            choice = input(f"{self.locale.tr('menu.select_action')}: ").strip().lower()
            selected = next((o for o in options if o["key"].lower() == choice), None)

            if selected:
                try:
                    selected["action"]()
                    break
                except Exception as e:
                    self.show_error(self.locale.tr('errors.command_failed').format(e))
            else:
                self.show_error(self.locale.tr('errors.invalid_choice'))

    def show_key_bindings_help(self):
        """Показывает подсказку по клавишам"""
        default_branch = self.git._get_default_branch().upper() if self.git else "MASTER"

        bindings = [
            {"key": "1", "description": self.locale.tr("menu.reset_master").format(default_branch)},
            {"key": "2", "description": self.locale.tr("menu.reset_unstable")},
            {"key": "3", "description": self.locale.tr("menu.soft_reset")},
            {"key": "4", "description": self.locale.tr("menu.rebase")},
            {"key": "5", "description": self.locale.tr("menu.new_branch")},
            {"key": "6", "description": self.locale.tr("menu.show_branches")},
            {"key": "7", "description": self.locale.tr("menu.change_prefix")},
            {"key": "8", "description": self.locale.tr("menu.show_log")},
            {"key": "s", "description": self.locale.tr("menu.show_status")},
            {"key": "d", "description": self.locale.tr("menu.delete_branch")},
            {"key": "w", "description": self.locale.tr("menu.change_directory")},
            {"key": "r", "description": self.locale.tr("menu.change_remote")},
            {"key": "n", "description": self.locale.tr("menu.npm_scripts")},
            {"key": "m", "description": self.locale.tr("menu.show_menu")},
            {"key": "p", "description": self.locale.tr("menu.profiles")},
            {"key": "l", "description": self.locale.tr("menu.change_language")},
            {"key": "Q", "description": self.locale.tr("menu.exit")},
        ]

        table = Table(
            title=self.locale.tr("menu.keys_title"),
            box=ROUNDED,
            header_style="bold cyan",
            border_style="blue",
            show_lines=True
        )

        table.add_column(self.locale.tr("menu.key_column"), style="green", width=8)
        table.add_column(self.locale.tr("menu.description_column"), style="white", min_width=30)

        for binding in bindings:
            table.add_row(
                f"[bold green]{binding['key']}[/bold green]",
                binding["description"]
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def set_branch_prefix(self):
        """Устанавливает префикс для веток"""
        if not self.config.prefix_history:
            self.config.prefix_history = [self.config.branch_settings["Prefix"]]

        current_prefix = self.config.branch_settings["Prefix"]

        table = Table(
            title=self.locale.tr("prefix.title"),
            box=ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("#", style="green", width=3)
        table.add_column(self.locale.tr("prefix.prefix"), style="white", min_width=20)
        table.add_column("", style="dim", width=10)

        for idx, prefix in enumerate(self.config.prefix_history, 1):
            is_current = "✓" if prefix == current_prefix else ""
            table.add_row(str(idx), prefix, is_current)

        table.add_row("N", self.locale.tr("prefix.enter_new"), "")

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            choice = input(f"{self.locale.tr('menu.select_prefix')} (1-{len(self.config.prefix_history)}/N/q): ").strip().lower()

            if choice == 'q':
                return
            elif choice == 'n':
                new_prefix = input(self.locale.tr("prefix.enter_new")).strip()
                if new_prefix:
                    self.config.update_prefix(new_prefix)
                    self.show_happy_cat(self.locale.tr("prefix.changed").format(new_prefix))
                    return
            elif choice.isdigit() and 1 <= int(choice) <= len(self.config.prefix_history):
                selected_prefix = self.config.prefix_history[int(choice)-1]
                self.config.update_prefix(selected_prefix)
                self.show_happy_cat(self.locale.tr("prefix.changed").format(selected_prefix))
                return
            else:
                self.show_error(self.locale.tr('errors.invalid_choice'))

    def set_default_remote(self):
        """Устанавливает удаленный репозиторий по умолчанию"""
        remotes = self.git.run_git_command("remote")
        if not remotes:
            self.show_unhappy_cat(self.locale.tr("errors.no_remotes"))
            return

        current_remote = self.config.branch_settings["DefaultRemote"]

        table = Table(
            box=ROUNDED,
            show_header=False,
            border_style="dim blue",
            padding=(0, 1)
        )
        table.add_column("", style="bold cyan")
        table.add_column("", style="white")

        table.add_row(self.locale.tr("settings.option"), f"[bold]{self.locale.tr('remote.title')}[/bold]")
        table.add_row(self.locale.tr("settings.current_value"),
                      f"{self.locale.tr('remote.current').format(current_remote)}\n"
                      f"{self.locale.tr('remote.available').format(remotes)}")

        self.console.print()
        self.console.print(table)
        self.console.print()

        new_remote = input(f"  {self.locale.tr('remote.enter_new')}").strip()
        if new_remote:
            self.config.branch_settings["DefaultRemote"] = new_remote
            self.config.save_settings()
            self.show_success(self.locale.tr('remote.changed').format(new_remote))
            self.show_happy_cat(self.locale.tr('remote.changed').format(new_remote))

    def change_work_directory(self):
        """Изменяет рабочую директорию"""
        current_dir = self.config.branch_settings["WorkDir"]

        table = Table(
            title=self.locale.tr("directory.title"),
            box=ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("#", style="green", width=3)
        table.add_column(self.locale.tr("directory.path"), style="white", min_width=40)
        table.add_column("", style="dim", width=10)

        for idx, dir_path in enumerate(self.config.dir_history, 1):
            is_current = "✓" if dir_path == current_dir else ""
            short_path = str(dir_path).replace(os.path.expanduser("~"), "~")
            table.add_row(str(idx), short_path, is_current)

        table.add_row("N", self.locale.tr("directory.enter_new"), "")
        table.add_row("B", self.locale.tr("directory.select_gui"), "")

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            choice = input(f"{self.locale.tr('menu.select_directory')} (1-{len(self.config.dir_history)}/N/B/q): ").strip().lower()

            if choice == 'q':
                return
            elif choice == 'n':
                new_dir = input(self.locale.tr("directory.enter_new")).strip()
                self._update_directory(new_dir)
                return
            elif choice == 'b':
                if os.name == 'nt':
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    new_dir = filedialog.askdirectory()
                    if new_dir:
                        self._update_directory(new_dir)
                    return
                else:
                    self.show_error(self.locale.tr('errors.windows_only'))
            elif choice.isdigit() and 1 <= int(choice) <= len(self.config.dir_history):
                selected_dir = self.config.dir_history[int(choice)-1]
                self._update_directory(selected_dir)
                return
            else:
                self.show_error(self.locale.tr('errors.invalid_choice'))

    def _update_directory(self, new_dir: str):
        """Обновляет рабочую директорию"""
        if not os.path.isdir(new_dir):
            self.show_error(self.locale.tr('errors.directory_not_exists').format(new_dir))
            return

        if not os.path.isdir(os.path.join(new_dir, ".git")):
            self.show_error(self.locale.tr('errors.not_git_repo'))
            return

        self.config.update_work_dir(new_dir)
        os.chdir(new_dir)
        self.show_success(self.locale.tr('directory.changed').format(new_dir))
        self.show_git_status()

    def change_language_interactive(self):
        """Интерактивное меню выбора языка"""
        languages = self.locale.get_supported_languages()

        if not languages:
            self.show_error(self.locale.tr('errors.no_languages'))
            return

        current_lang = next(
            (lang for lang in languages if lang['code'] == self.locale.current_locale),
            None
        )

        if current_lang:
            self.console.print(
                f"\n{self.locale.tr('language.current')}: "
                f"[bold]{current_lang['name']}[/bold] "
                f"({current_lang['code']})\n"
            )

        table = Table(
            title=self.locale.tr("menu.language_title"),
            box=ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("#", style="green", width=5)
        table.add_column(self.locale.tr("menu.language"), style="white")
        table.add_column("Code", style="dim")
        table.add_column("", style="dim", width=5)

        for idx, lang in enumerate(languages, 1):
            is_current = "✓" if lang['code'] == self.locale.current_locale else ""
            table.add_row(
                str(idx),
                lang['name'],
                lang['code'],
                is_current
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            choice = input(f"{self.locale.tr('menu.select_language')} (1-{len(languages)}/q): ").strip().lower()

            if choice == 'q':
                self.console.print(f"[yellow]{self.locale.tr('menu.language_change_cancelled')}[/yellow]")
                return
            elif choice.isdigit() and 1 <= int(choice) <= len(languages):
                selected = languages[int(choice)-1]
                if self.locale.change_language(selected['code']):
                    # После изменения языка обновляем конфиг
                    current_settings = self.config.get_current_settings()
                    if current_settings:
                        current_settings["Locale"] = selected['code']
                        self.config.save_settings()
                    self.console.print(f"[green]✓ {self.locale.tr('menu.language_changed').format(selected['name'])}[/green]")
                    return
            else:
                self.show_error(self.locale.tr('errors.invalid_choice'))

    def show_happy_cat(self, message: str):
        """Показывает довольного кота"""
        current_branch = self.git.get_current_branch() if self.git else "unknown"
        print(f"""
        /\\_/\\
        ( ◕‿◕ )
        > ^ <

        {self.color_codes['green']}{message}{self.color_codes['reset']}
        {self.color_codes['dark_gray']}{self.locale.tr('branch.current').format(current_branch)}{self.color_codes['reset']}
    """)

    def show_unhappy_cat(self, message: str):
        """Показывает недовольного кота"""
        print(f"""
      /\\_/\\  
     ( ≖_≖ ) 
      > ᴖ <  
    
    {self.color_codes['red']}✗ {message}{self.color_codes['reset']}
""")

    def show_dragon(self):
        """Показывает дракона"""
        print(f"""
     /\\___/\\
    (🔥˃▽˂🔥)
     /|\\_/|\\
      /   \\    {self.color_codes['bright_red']}{self.locale.tr('reset.master_message').format(self.git._get_default_branch().upper())}{self.color_codes['reset']}
""")

    def show_phoenix(self):
        """Показывает феникса"""
        print(f"""
    /\\_/\\
   (╯°□°╯）
     /|\\
    /   \\     {self.color_codes['bright_yellow']}{self.locale.tr('reset.unstable_message')}{self.color_codes['reset']}
""")

    def show_unknown_command(self, command: str):
        """Показывает сообщение о неизвестной команде"""
        ascii_arts = [
            {
                "art": """
                .-~~~~-.
                { o  o }
                |  ?   |
                '.____.'
                """,
                "style": "bright_yellow"
            },
            {
                "art": """
                ┌─┐
                ┴─┴ 
                ಠ_ರೃ
                """,
                "style": "bright_red"
            },
            {
                "art": """
                ╔════╗
                ║ ?? ║
                ╚════╝
                """,
                "style": "bright_magenta"
            },
            {
                "art": """
                ┌───────┐
                │       │
                │   ?   │
                │       │
                └───────┘
                """,
                "style": "bright_blue"
            }
        ]

        selected_art = random.choice(ascii_arts)
        art = Text(selected_art["art"], style=selected_art["style"])

        error_text = Text()
        error_text.append(f"{self.locale.tr('errors.unknown_command').format(command)}: ", style="bold red")
        error_text.append("\n", style="dim")
        error_text.append(self.locale.tr("errors.use_help"), style="dim")

        content = Text.assemble(art, "\n", error_text)

        panel = Panel(
            content,
            title=f"[bold yellow]⚠ {self.locale.tr("errors.error")}[/bold yellow]",
            subtitle=f"[dim]{self.locale.tr("ui.try_commands")}[/dim]",
            border_style=selected_art["style"],
            box=ROUNDED,
            padding=(1, 2),
            width=60
        )

        self.console.print(panel)

    def clear_screen(self):
        """Очищает экран"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def show_npm_scripts(self):
        """Показывает и выполняет npm-скрипты из package.json"""
        if not self.git:
            self.show_error(self.locale.tr('errors.git_not_initialized'))
            return

        scripts = self.git.get_npm_scripts()
        if not scripts:
            self.show_error(self.locale.tr('errors.no_package_json'))
            return

        table = Table(
            title=self.locale.tr("npm.scripts_title"),
            box=ROUNDED,
            header_style="bold cyan",
            border_style="blue",
            show_lines=True
        )

        table.add_column("#", style="green", width=5)
        table.add_column(self.locale.tr("npm.script_name"), style="bright_cyan", width=25)
        table.add_column(self.locale.tr("npm.script_command"), style="white", width=60)

        for idx, (name, cmd) in enumerate(scripts.items(), 1):
            table.add_row(
                str(idx),
                name,
                cmd
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        while True:
            # Исправленная строка с подстановкой количества скриптов
            choice = input(self.locale.tr("npm.select_script").format(len(scripts))).strip().lower()
            if choice == 'q':
                return

            if choice.isdigit() and 1 <= int(choice) <= len(scripts):
                selected_script = list(scripts.keys())[int(choice)-1]
                self._run_npm_script(selected_script, scripts[selected_script])
                return
            else:
                self.show_error(self.locale.tr('errors.invalid_choice'))

    def _run_npm_script(self, script_name: str, script_cmd: str):
        """Запускает npm-скрипт в новом терминале"""
        work_dir = self.config.branch_settings["WorkDir"]
        
        try:
            if os.name == 'nt':
                # Для Windows
                import subprocess
                subprocess.Popen(
                    f'start cmd /k "cd /d "{work_dir}" && npm run {script_name} && exit"',
                    shell=True
                )
            else:
                # Для Linux/MacOS
                import subprocess
                terminal = os.environ.get('TERMINAL', 'x-terminal-emulator')
                subprocess.Popen(
                    f'{terminal} -e "bash -c \'cd "{work_dir}" && npm run {script_name}; exec bash\'"',
                    shell=True
                )
            
            self.show_success(self.locale.tr('npm.script_started').format(script_name))
        except Exception as e:
            self.show_error(self.locale.tr('npm.script_error').format(script_name, str(e)))