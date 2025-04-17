#!/usr/bin/env python3
import os
import io
import sys
from pathlib import Path

# Устанавливаем стандартные потоки ввода-вывода в UTF-8
if sys.version_info[0] == 3:
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if os.name == 'nt':
    os.system('chcp 65001')  # Устанавливаем кодовую страницу UTF-8 в Windows

# Добавляем папку data в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent / 'data'))

from data.manager import GitBranchManager

def main():
    manager = GitBranchManager()

    print(f"{manager.tr('app.title')}")
    print(f"{manager.tr('app.help_prompt')}")

    while True:
        manager.show_prompt()
        try:
            command = input().strip().lower()

            if not command:
                continue

            if command in ['q', 'quit', 'exit']:
                manager._save_history()
                break
            elif command in ['h', 'help']:
                manager.show_key_bindings_help()
            elif command == '1':
                manager.reset_master_branch(True)
            elif command == '2':
                manager.reset_unstable_branch(True)
            elif command == '3':
                manager.soft_reset_to_master(True)
            elif command == '4':
                manager.rebase_from_master(True)
            elif command == '5':
                manager.new_branch_from_master()
            elif command == '6':
                manager.show_branches()
            elif command == '7':
                manager.set_branch_prefix()
            elif command == '8':
                manager.show_git_log()
            elif command == '9':
                manager.show_key_bindings_help()
            elif command == 's':
                manager.show_git_status()
            elif command == 'd':
                manager.delete_branch()
            elif command == 'w':
                manager.change_work_directory()
            elif command == 'r':
                manager.set_default_remote()
            elif command == 'l':
                manager.change_language_interactive()
            elif command == 'm':
                manager.show_git_actions_menu()
            else:
                manager.show_unknown_command(command)

        except KeyboardInterrupt:
            print(f"\n{manager.tr('app.quit_prompt')}")
            manager.show_prompt()
        except EOFError:
            print(f"\n{manager.tr('app.closing')}")
            manager._save_history()
            break

if __name__ == "__main__":
    main()