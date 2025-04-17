import os
import subprocess
import re
import time
from typing import Optional, List, Dict, Any
from .localization import LocalizationManager

class GitCommands:
    def __init__(self, config, locale, ui):
        self.config = config
        self.locale = locale
        self.ui = ui

    def run_git_command(self, command: str, check: bool = False, cwd: Optional[str] = None) -> Optional[str]:
        try:
            working_dir = self.config.branch_settings["WorkDir"]

            if not os.path.isdir(working_dir):
                self.ui.show_error(self.locale.tr('errors.directory_not_exists').format(working_dir))
                return None

            args = ["git"] + command.split()

            if len(args) > 2 and args[2] != '--show-current':
                self.ui.show_command(' '.join(map(str, args)))

            # Устанавливаем правильную кодировку
            import locale
            locale.setlocale(locale.LC_ALL, '')
            encoding = locale.getpreferredencoding()

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=check,
                cwd=working_dir,
                encoding=encoding  # Указываем кодировку
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.ui.show_error(self.locale.tr('errors.git_command_failed').format(e.stderr.strip()))
            return None

    def get_current_branch(self) -> Optional[str]:
        return self.run_git_command("branch --show-current")

    def _get_default_branch(self) -> str:
        """Определяет основную ветку (master или main)"""
        try:
            result = self.run_git_command("symbolic-ref refs/remotes/origin/HEAD")
            if result:
                return result.split('/')[-1]

            branches = self.run_git_command("branch -a")
            if 'origin/main' in branches:
                return 'main'
            return 'master'
        except:
            return 'master'

    def _get_branch_data(self) -> List[Dict[str, Any]]:
        """Получает данные о ветках"""
        raw_branches = self.run_git_command(
            "for-each-ref --format=%(refname:short)|%(committerdate:relative)|%(committerdate:unix)|%(upstream:short)|%(authorname) refs/heads/"
        )

        if not raw_branches:
            return []

        branch_data = []
        for line in raw_branches.split('\n'):
            parts = line.split('|')
            local = parts[0].strip() if parts[0] else ""
            commit_relative = parts[1].strip() if parts[1] else ""
            commit_timestamp = int(parts[2]) if parts[2] else 0
            remote = (parts[3].replace('origin/', '').strip() if parts[3] else "")
            author = parts[4].strip() if parts[4] else "unknown"

            branch_data.append({
                "local_branch": local,
                "last_commit_relative": commit_relative,
                "last_commit_timestamp": commit_timestamp,
                "remote_branch": remote,
                "author": author
            })

        return sorted(branch_data, key=lambda x: x["last_commit_timestamp"], reverse=True)

    def _run_npm_install(self):
        """Выполняет npm install в текущей директории"""
        work_dir = self.config.branch_settings["WorkDir"]

        if not os.path.isfile(os.path.join(work_dir, "package.json")):
            return

        self.ui.show_info(self.locale.tr('npm.installing'))

        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"

        with self.ui.create_progress() as progress:
            task = progress.add_task("[cyan]Running npm install...", total=None)
            process = subprocess.Popen(
                [npm_cmd, "i"],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while process.poll() is None:
                progress.update(task, advance=1)
                time.sleep(0.1)

        if process.returncode == 0:
            self.ui.show_success(self.locale.tr('npm.installed'))
        else:
            error_output = process.stderr.read()
            if error_output:
                self.ui.show_error(error_output)
            self.ui.show_error(self.locale.tr('npm.failed'))