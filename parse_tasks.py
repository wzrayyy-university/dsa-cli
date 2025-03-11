import os
from typing import cast
from sort_me.main import SortMeAPI
from sort_me.types import ContestTask

api = SortMeAPI("TOKEN")

contests = [103, 102, 105, 112, 115, 121, 124, 139, 144, 145, 159, 160, 300, 301]

def get_id(contest: dict, task: ContestTask):
    contest['tasks'] = cast(list[str], contest['tasks'])
    return chr(ord('A') + contest['tasks'].index(task.name))

for contest_id in contests:
    contest = api.get_contest(contest_id)
    tasks = api.get_contest_tasks(contest_id)

    contest_name = contest['name']
    try:
        os.mkdir(contest_name)
    except Exception:
        pass

    for task in tasks:
        out = ''
        out += '# ' + task.name + '\n'
        out += task.main_description + '\n\n'
        out += '## Входные данные\n'
        out += task.in_description + '\n'
        out += '## Выходные данные\n'
        out += task.out_description + '\n'

        out += '|STDIN|STDOUT|\n|---|---|\n'

        for sample in task.samples:
            out += f"|{sample.input.replace('\n', '<br>')}|{sample.output.replace('\n', '<br>')}|\n"

        if task.comment:
            out += '## Примечание\n\n' + task.comment + '\n'

        task_id = get_id(contest, task)
        with open(contest_name + '/' + task_id + '. ' + ' '.join(task.name.replace('\n', ' ').split(' ')) + '.md', 'w') as f:
            f.write(out.strip() + '\n')
