import argparse # TODO: replace with https://github.com/swansonk14/typed-argument-parser
import functools
import json
import os
from os.path import isfile
import pathlib
import subprocess
import sys
import time

from datetime import datetime
from typing import Union, cast

import colorama
from tabulate import tabulate

from sort_me.types import BaseSubmission, FailedSubmission, ShortSubmission, ShortSubmissionBase, ContestTask, Config
from sort_me.main import AuthProvider, SortMeAPI
from sort_me.exceptions import *

SEPARATORS = [',', ' ']

_superscript_map = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ",
    "e": "ᵉ", "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ᶦ", "j": "ʲ", "k": "ᵏ",
    "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "q": "۹", "r": "ʳ",
    "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ",
    "z": "ᶻ", "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ", "E": "ᴱ", "F": "ᶠ",
    "G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ", "M": "ᴹ",
    "N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "Q": "Q", "R": "ᴿ", "S": "ˢ", "T": "ᵀ",
    "U": "ᵁ", "V": "ⱽ", "W": "ᵂ", "X": "ˣ", "Y": "ʸ", "Z": "ᶻ", "+": "⁺",
    "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾"}
SUP_TRANS = str.maketrans(
    ''.join(_superscript_map.keys()),
    ''.join(_superscript_map.values()))

_subscript_map = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
    "7": "₇", "8": "₈", "9": "₉", "a": "ₐ", "b": "♭", "c": "꜀", "d": "ᑯ",
    "e": "ₑ", "f": "բ", "g": "₉", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
    "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "q": "૧", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "w": "w", "x": "ₓ", "y": "ᵧ",
    "z": "₂", "A": "ₐ", "B": "₈", "C": "C", "D": "D", "E": "ₑ", "F": "բ",
    "G": "G", "H": "ₕ", "I": "ᵢ", "J": "ⱼ", "K": "ₖ", "L": "ₗ", "M": "ₘ",
    "N": "ₙ", "O": "ₒ", "P": "ₚ", "Q": "Q", "R": "ᵣ", "S": "ₛ", "T": "ₜ",
    "U": "ᵤ", "V": "ᵥ", "W": "w", "X": "ₓ", "Y": "ᵧ", "Z": "Z", "+": "₊",
    "-": "₋", "=": "₌", "(": "₍", ")": "₎"}

SUB_TRANS = str.maketrans(
    ''.join(_subscript_map.keys()),
    ''.join(_subscript_map.values()))


class PrettyPrinter:
    @classmethod
    def _print_json(cls, obj: BaseSubmission | FailedSubmission | ShortSubmission | ShortSubmissionBase, end='\r', a_size=0, b_size=0):
        if 'total_points' not in obj or obj['total_points'] == 0:
            color = colorama.Fore.RED
        elif obj['total_points'] < 100:
            color = colorama.Fore.RESET
        else:
            color = colorama.Fore.GREEN

        print(colorama.Style.RESET_ALL, end='')

        sep = f'{colorama.Fore.RESET}{colorama.Fore.WHITE}{colorama.Style.DIM} | {colorama.Style.NORMAL}{color}'

        pretty_str = f"{end}{color}"
        if 'total_points' in obj:
            pretty_str += f"{obj['total_points']}{' ' * (a_size - len(str(obj['total_points'])))}" + sep
        else:
            pretty_str += ' ' * a_size + '   '

        pretty_str += obj['shown_verdict_text'] + (' ' * (b_size - len(obj["shown_verdict_text"])))

        if 'shown_test' in obj:
            pretty_str += sep + str(obj['shown_test'])

        print(pretty_str, colorama.Style.RESET_ALL)

        # print(f"{end}{color}{str(obj['total_points']) + ('  ' if obj['total_points'] == 0 else '') + sep if 'total_points' in obj else ' '}{obj['shown_verdict_text']}{(sep + str(obj['shown_test'])) if 'shown_test' in obj else ''}{colorama.Style.RESET_ALL}")

    @classmethod
    def _print_int(cls, num: int):
        print(f"\r{colorama.Style.DIM}Проверяется... {num}", end='')

    @classmethod
    def print(cls, obj: int | Union[BaseSubmission, FailedSubmission, ShortSubmission]):
        if isinstance(obj, int):
            cls._print_int(obj)
        else:
            cls._print_json(obj)

    @classmethod
    def print_list(cls, obj: list[ShortSubmission | ShortSubmissionBase]):
        max_a = 0
        max_b = 0
        for submission in obj:
            if 'total_points' in submission:
                max_a = max(max_a, len(str(submission['total_points'])))
            max_b = max(max_b, len(submission['shown_verdict_text']))

        max_spaces = len(str(len(obj)))

        for idx, submission in enumerate(obj):
            print(f'{" " * (max_spaces - len(str(idx+1)))}{idx+1}. ', end='')
            cls._print_json(submission, end='', a_size=max_a, b_size=max_b)


def tex_to_text(data: str) -> str:
    i = 0
    out = ""
    while i < len(data):
        if data[i] == '\\':
            i += 1
            buf = ""
            while i < len(data) and data[i] not in SEPARATORS:
                buf += data[i]
                i += 1
                # print(buf)
                if buf == 'leq':
                    out += '≤'
                    break
                elif buf == 'cdot':
                    out += ' 🞄'
                    break

        elif data[i] == '^':
            i += 1
            out += data[i].translate(SUP_TRANS)
            i += 1

        elif data[i] == '_':
            i += 1
            buf = ""
            while i < len(data) and data[i] not in SEPARATORS:
                buf += data[i]
                i += 1

            out += buf.translate(SUB_TRANS)
        else:
            out += data[i]
            i += 1

    return f'{colorama.Style.BRIGHT}{out}{colorama.Style.NORMAL}'

def tex(x: str) -> str:
    # return x
    out = ""
    i = 0
    while i < len(x):
        if x[i] == '$':
            buf = ""
            i += 1
            # print('iter', i)
            # print('size', len(x))
            while i < len(x) and x[i] != '$':
                buf += x[i]
                i += 1
            out += tex_to_text(buf)
            i += 1
        else:
            out += x[i]
            i += 1
    return out


def print_task(task: ContestTask):
    dim = lambda x: f'{colorama.Style.DIM}{x}{colorama.Style.NORMAL}'
    bright = lambda x: f'{colorama.Style.BRIGHT}{x}{colorama.Style.NORMAL}'
    print(bright(task.name), end='\n\n')
    print(tex(task.main_description.replace('\n\n', '\n')), end='\n\n')
    print(dim("Входные данные:"))
    print(tex(task.in_description.replace('\n\n', '\n')), end='\n\n')
    print(dim("Выходные данные:"))
    print(tex(task.out_description.replace('\n\n', '\n')))

    if task.subtasks:
        print()
        print(dim('Подзадачи:'))
        print(tabulate([[x.num, x.points, ''.join([str(y) for y in x.necessary_subtasks]) if x.necessary_subtasks else '', x.description] for x in task.subtasks], headers=[dim(x) for x in ['#','Баллы','Подзадачи','Описание']], tablefmt='rounded_grid'))

    print()
    print(dim('Пример:'))
    print(tabulate([[x.input, x.output] for x in task.samples], headers=[dim('STDIN'), dim("STDOUT")], tablefmt='rounded_grid'))

    if task.comment:
        print(f"\n{colorama.Style.DIM}Примечание:{colorama.Style.NORMAL}")
        print(task.comment.replace('\n\n', '\n'))

    print(dim('\nОграничения:'))
    print(f'Лимит по времени:', bright(str(task.time_limit_milliseconds) + 'мс'))
    print(f'Лимит по памяти: ', bright(str(task.memory_limit_megabytes) + "МБ"))


def printn(x):
    if '\n' in x:
        print(f'\n{x}\n')
    else:
        print(f' {x}')

class ApiWorker():
    _api: SortMeAPI

    def __init__(self):
        data_path = os.environ.get('XDG_DATA_HOME') or os.environ['HOME'] + "/.local/share"
        filepath = data_path + "/sortme_config.json"

        if not os.path.isdir(data_path):
            os.makedirs(data_path, exist_ok=True)

        if not os.path.isfile(filepath):
            print("Authorization:")
            config = {}
            config["phone"] = input("Phone: ")
            # i'm sure people won't get this and break their installs
            # nc_tmp_ = input("Naming convention [(\\w).cpp]: ")
            # config["naming_convention"] = nc_tmp_ if nc_tmp_ else "(\\w).cpp"
            config["naming_convention"] = "(\\w).cpp"

            self._auth_provider = AuthProvider(config["phone"])
            print("You have to approve the login request in Telegram")
            config["api_key"] = self._auth_provider.auth()

            template_path = input('Full path to your template (used in "sm create", can be ommited): ')
            while template_path and not os.path.isfile(template_path):
                print("File not found!")
                template_path = input('Full path to your template (used in "sm create", can be ommited): ')

            if template_path:
                config['template_path'] = template_path

            with open(filepath, "w") as config_file:
                json.dump(config, config_file)

            self._config = Config(**config)

        with open(filepath) as config_file:
            self._config = Config(**json.load(config_file))

        self._api = SortMeAPI(self._config.api_key)

    def reauth(self):
        filepath = os.environ['HOME'] + "/sortme_config.json"
        with open(filepath) as config_file:
            cfg = json.load(config_file)

        cfg['api_key'] = self._auth_provider.auth()

        with open(filepath, 'w') as config_file:
            json.dump(cfg, config_file)
            self._api = SortMeAPI(cfg['api_key'])

    def push(self, args: argparse.Namespace):
        while True:
            if not os.path.isfile('./.sortme.json'):
                print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
                exit(1)

            with open(".sortme.json") as datafile:
                data = json.load(datafile)

            if '.cpp' in args.filename:
                filename = args.filename
            else:
                filename = args.filename.upper() + '.cpp'
                if not os.path.isfile(filename):
                    filename = filename.lower()

            if not os.path.isfile(filename):
                print(f"Error! {filename} doesn't exist!", file=sys.stderr)
                exit(1)

            with open(filename) as code_file:
                code = code_file.read()

            if args.task_id:
                if args.task_id.isnumeric():
                    task_id = int(args.task_id)
                else:
                    task_id = data['tasks'][ord(args.task_id.upper()) - ord('A')]
            else:
                task_id = data['tasks'][ord(pathlib.Path(filename).stem.upper()) - ord('A')]

            try:
                id = self._api.upload_code(code, data['contest_id'], task_id)
                for message in self._api.get_task_stats(id):
                    PrettyPrinter.print(message)
                break
            except SortMeAPIException as exc:
                if exc.status_code == 429:
                    time.sleep(3)
                    continue

                print(exc, exc.status_code)
                break

    # def show(self, args):
    #     print_task(self._api.get_contest_task(172, ord(args.task_number) - ord('A')))
    #     __import__('pprint').pprint(self._api.get_contest_tasks(172)[0])

    def init(self, args):
        tasks = [task.id for task in self._api.get_contest_tasks(args.contest_id)]
        tests = [[{'stdin': y.input, 'stdout': y.output} for y in self._api.get_contest_task(args.contest_id, task).samples] for task in range(len(tasks))]

        data = {
            'contest_id': args.contest_id,
            'tasks': tasks,
            'tests': tests
        }

        with open('.sortme.json', 'w') as file:
            json.dump(data, file, indent=4)

    def test(self, args):
        dim = lambda x: f'{colorama.Style.DIM}{x}{colorama.Style.NORMAL}'
        bright = lambda x: f'{colorama.Style.BRIGHT}{x}{colorama.Style.NORMAL}'

        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        if '.cpp' in args.filename:
            filename = args.filename
        else:
            filename = args.filename.upper() + '.cpp'
            if not os.path.isfile(filename):
                filename = filename.lower()

        if not os.path.isfile(filename):
            print(f"Error! {filename} doesn't exist!", file=sys.stderr)
            exit(1)

        if args.task_id:
            if args.task_id.isnumeric():
                task_id = int(args.task_id)
            else:
                task_id = ord(args.task_id.upper()) - ord('A')
        else:
            task_id = ord(pathlib.Path(filename).stem.upper()) - ord('A')

        tests = data['tests'][task_id]

        test_filename = chr(task_id + ord('A')) + '.t'
        if not os.path.isfile(test_filename):
            test_filename = chr(task_id + ord('a')) + '.t'
        if not os.path.isfile(test_filename):
            test_filename = chr(task_id + ord('A')) + '.test'
        if not os.path.isfile(test_filename):
            test_filename = chr(task_id + ord('a')) + '.test'
        if not os.path.isfile(test_filename):
            test_filename = None

        if test_filename:
            with open(test_filename) as f:
                test_data = f.read().strip().split('\n\n\n')
            for test in test_data:
                t = test.split("\n\n")
                tests.append({'stdin': t[0].strip(), 'stdout': t[1].strip()})

        comp = subprocess.run(f'g++ -std=c++20 {filename} -o .a.out'.split())

        if comp.returncode:
            return

        for idx, test in enumerate(data['tests'][task_id]):
            pr = subprocess.Popen(['./.a.out'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            print(f'Тест {idx+1}: ', end='')
            output = pr.communicate(test['stdin'].encode('utf-8'))[0].decode('utf-8').strip()
            fail = True
            if test['stdout'].strip() == output:
                print(f'{colorama.Fore.GREEN}PASS{colorama.Style.RESET_ALL}')
                fail = False
            else:
                print(f'{colorama.Fore.RED}FAIL{colorama.Style.RESET_ALL}')
                print(bright('Входные данные:'), end='')
                printn(test['stdin'].strip())
                print(bright( 'Вывод:' ), end='')
                printn(output)
                print(bright( 'Ожидаемый вывод:' ), end='')
                printn(test['stdout'].strip())
            if idx+1 != len(data['tests'][task_id]) and fail:
                print()

        os.remove('.a.out')

    def submissions(self, args):
        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        if args.task_id.isnumeric():
            task_id = int(args.task_id)
            if task_id < len(data['tasks']):
                task_id = data['tasks'][task_id - 1]
        else:
            task_id = data['tasks'][ord(args.task_id.upper().replace(".CPP", "")) - ord('A')]

        if 'limit' in args:
            submissions = self._api.get_submission_history(data['contest_id'], task_id, limit=args.limit)
        else:
            submissions = self._api.get_submission_history(data['contest_id'], task_id)
        print(f"Тестов запущено: {submissions[0]}")
        PrettyPrinter.print_list(submissions[1])

    def contest(self, _):
        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        contest_info = self._api.get_contest(data['contest_id'])
        if contest_info["ends"] != -1:
            a = datetime.fromtimestamp(contest_info['ends']) - datetime.now()

            days, seconds = a.days, a.seconds
            hours = (seconds % 2160000) // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            end_time = colorama.Style.DIM
            if a.days > 0:
                end_time += f"{days}д. "
            end_time += f"{hours:02d}:{minutes:02d}:{seconds:02d}{colorama.Style.RESET_ALL}"
        else:
            end_time = f'{colorama.Fore.RED}Закончен{colorama.Style.RESET_ALL}'

        print(f"{contest_info['name'].replace('№', '№ ')}: {end_time}\n\nЗадачи:")
        for idx, task in enumerate(contest_info['tasks']):
            print(f"{colorama.Style.DIM}{chr(ord('A')+idx)}.{colorama.Style.RESET_ALL} {colorama.Style.BRIGHT}{task}{colorama.Style.RESET_ALL}")

        place = contest_info['place']
        place_color = colorama.Fore.BLACK + colorama.Back.YELLOW if place < 3 else colorama.Fore.YELLOW if place < 10 else colorama.Fore.GREEN if place < 50 else ''

        print(f"\nМесто в рейтинге: {place_color}{place}{colorama.Style.RESET_ALL}")

        print("Баллы: ",end='')
        result_string = ''
        solved_count = 0
        for result_with_time in contest_info['results']:
            result = result_with_time[0]
            if result == -1:
                result_string += f'{colorama.Style.DIM}-{colorama.Style.RESET_ALL}'
            elif result == 0:
                result_string += f'{colorama.Fore.RED}0{colorama.Style.RESET_ALL}'
            elif result == 100:
                result_string += f'{colorama.Fore.GREEN}100{colorama.Style.RESET_ALL}'
                solved_count += 1
            else:
                result_string += str(result)
                solved_count += 1
            result_string += ' '
        print(result_string)

        print('Решено задач:', solved_count)

    def code(self, args):
        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        if args.task_id.isnumeric():
            task_id = int(args.task_id)
            if task_id < len(data['tasks']):
                task_id = data['tasks'][task_id - 1]
        else:
            task_id = data['tasks'][ord(args.task_id.upper().replace(".CPP", "")) - ord('A')]

        subm = self._api.get_submission_info(data['contest_id'], task_id, args.submission_id)

        with open(".code_tmp.cpp", 'w') as code_file:
            code_file.write(subm['code'])

        subprocess.run('vim .code_tmp.cpp'.split())

        os.remove('.code_tmp.cpp')

    def info(self, args):
        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        if args.task_id.isnumeric():
            task_id = int(args.task_id)
            if task_id < len(data['tasks']):
                task_id = task_id - 1
        else:
            task_id = ord(args.task_id.upper().replace(".CPP", "")) - ord('A')

        task_info = self._api.get_contest_task(data['contest_id'], task_id)

        print_task(task_info)

    def stats(self, _):
        def bubble_sort(tasks: list[tuple[int, ContestTask]]): # i don't get python... at all... standard `sorted()` func just doesn't work...
            swaps = 1
            while swaps > 0:
                swaps = 0
                for i in range(len(tasks) - 1):
                    if tasks[i][1].solved_by < tasks[i+1][1].solved_by:
                        tasks[i], tasks[i+1] = tasks[i+1], tasks[i]
                        swaps += 1

        if not os.path.isfile('./.sortme.json'):
            print('Error! ".sortme.json" is missing! Run "sm init" to create it!', file=sys.stderr)
            exit(1)

        with open(".sortme.json") as datafile:
            data = json.load(datafile)

        dim = lambda x: f'{colorama.Style.DIM}{x}{colorama.Style.NORMAL}'
        bright = lambda x: f'{colorama.Style.BRIGHT}{x}{colorama.Style.NORMAL}'

        raw_tasks = self._api.get_contest_tasks(data['contest_id'])[:]
        tasks = list(zip(range(len(raw_tasks)), raw_tasks))
        bubble_sort(tasks)

        for idx, task in tasks:
            task_pretty_idx = chr(ord('A') + idx)
            print(f"{dim(task_pretty_idx)}. {task.name}: {bright(task.solved_by)}")


    def create(self, args):
        if not self._config.template_path and not args.template_path:
            print("Error! Template path missing!", file=sys.stderr)
        filename = args.task_id + '.cpp'
        template_path = cast(str, args.template_path) or cast(str, self._config.template_path)

        if (os.path.isfile(filename)):
            print("Error! File already exists!", file=sys.stderr)
            exit(1)

        if not os.path.isfile(template_path):
            print(f"Error! File {template_path} not found!", file=sys.stderr)
            exit(1)

        with open(template_path) as f:
            template = f.read()

        with open(filename, 'w') as f:
            f.write(template)


def main():
    api = ApiWorker()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    # fetch_parser = subparsers.add_parser('list')
    # fetch_parser.add_argument('object', choices=['c'])
    # fetch_parser.add_argument('task_number')
    # fetch_parser.set_defaults(callback=api.show)

    fetch_parser = subparsers.add_parser('init', help='Initialize the folder')
    fetch_parser.add_argument('contest_id', type=int, help='Contst id taken from the URL')
    fetch_parser.set_defaults(callback=api.init)

    push_parser = subparsers.add_parser('push', aliases=['p'], help='Push your solution to Sort-Me')
    push_parser.add_argument('filename', help='Filename or task id to push')
    push_parser.add_argument('-t', '--task-id', help='Optionally specify task id')
    push_parser.set_defaults(callback=api.push)

    push_parser = subparsers.add_parser('test', aliases=['t'], help='Test your solution with given tests')
    push_parser.add_argument('filename', help='Filename or task id to test')
    push_parser.add_argument('-t', '--task-id', help='Optionally specify task id')
    push_parser.set_defaults(callback=api.test)

    submission_parser = subparsers.add_parser('submissions', aliases=['sub'], help='List your submissions')
    submission_parser.add_argument('task_id', help='Task to list the submissions for')
    submission_parser.add_argument('--limit', type=int)
    submission_parser.set_defaults(callback=api.submissions)

    contest_parser = subparsers.add_parser('contest', aliases=['ct'], help='List contest info and your position in the raiting')
    contest_parser.set_defaults(callback=api.contest)

    stat_parser = subparsers.add_parser('stat', aliases=['st'], help='Show how many people have solved each task in the contest')
    stat_parser.set_defaults(callback=api.stats)

    code_parser = subparsers.add_parser('code', help='Pull your latest successful submission from Sort-Me')
    code_parser.add_argument('task_id', help='Task to pull the submission for')
    code_parser.add_argument('submission_id', type=int, nargs='?', help='Optionally specify which submission to pull (1-based)')
    code_parser.set_defaults(callback=api.code)

    info_parser = subparsers.add_parser('info', aliases=['i'], help='Print the problem description')
    info_parser.add_argument('task_id', help='Task to print')
    info_parser.set_defaults(callback=api.info)

    create_parser = subparsers.add_parser('create', aliases=['c'], help='Create a task with a predefined template')
    create_parser.add_argument('task_id', help='Task name to create')
    create_parser.add_argument('template_path', help='Optional path to template', nargs='?')
    create_parser.set_defaults(callback=api.create)

    args = parser.parse_args()
    args.callback(args)


if __name__ == "__main__":
    main()
