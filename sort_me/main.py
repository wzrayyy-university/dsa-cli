import base64
import json
import re
import time

from collections.abc import Generator

import requests
import websockets.sync.client

from .types import *
from .exceptions import RequestException, TooManyRequests

class AuthProvider:
    _session: requests.Session
    _phone_number: str

    def __init__(self, phone_number: str):
        self._session = requests.Session()
        self._phone_number = phone_number

    @staticmethod
    def _parse_telegram_html(html: str) -> TelegramResponse | None:
        match = re.search(r"tgAuthResult=(\w+)", html)
        assert match

        text = match.group(1)
        text += '=' * (len(text) % 3)

        return json.loads(base64.b64decode(text)) if match else None

    def auth(self):
        telegram_response = self._authorize_telegram()
        if not telegram_response:
            raise RuntimeError('Unable to log into telegram!')

        return self._authorize_sortme(telegram_response)

    def _authorize_telegram(self):
        REQUEST_PARAMS = {
            'bot_id': "1756957630",
            'origin': 'https://sort-me.org',
            'request_access': "true",
            'return_to': 'https://sort-me.org/',
        }

        self._session.get('https://oauth.telegram.org/auth', params=REQUEST_PARAMS)
        self._session.post("https://oauth.telegram.org/auth/request", data={'phone': self._phone_number}, params=REQUEST_PARAMS)

        while not self._session.post('https://oauth.telegram.org/auth/login', params=REQUEST_PARAMS).json():
            time.sleep(0.5)
        self._session.get("https://oauth.telegram.org/auth", params=REQUEST_PARAMS)

        return self._parse_telegram_html(self._session.get("https://oauth.telegram.org/auth/push", params=REQUEST_PARAMS).text)

    def _authorize_sortme(self, telegram_response: TelegramResponse) -> str:
        a = requests.post("https://api.sort-me.org/oauth?provider=telegram", json=telegram_response)
        return a.json()['token']


class SortMeAPI:
    _api_key: str
    client: ...

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _make_request(self, request_method: RequestMethod, method: str, *args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = f'Bearer {self._api_key}'

        r = requests.request(request_method, f'https://api.sort-me.org/{method}', *args, **kwargs)

        if r.status_code > 300:
            if r.status_code == 429:
                raise TooManyRequests(r.text, r.status_code)
            raise RequestException(r.json()['error'], r.status_code)

        return r

    def get_contests(self) -> list[VerboseContestInfo]:
        contests: list[UpcomingContest] = self._make_request('GET', 'GetUpcomingContests').json()
        return [self._make_request('GET', 'getContestById', params={"id": contest['id']}).json() for contest in contests]

    def get_contest_tasks(self, contest_id: int) -> list[ContestTask]:
        raw = self._make_request('GET', 'getContestTasks', params={'id': contest_id}).json()
        return list(map(ContestTask.from_dict, raw['tasks']))

    def get_contest_task(self, contest_id: int, idx: int) -> ContestTask:
        raw = self._make_request('GET', 'getContestTasks', params={'id': contest_id}).json()
        return ContestTask.from_dict(raw['tasks'][idx])

    def get_task_stats(self, task_id: int) -> Generator[int | BaseSubmission, None, None]:
        with websockets.sync.client.connect(f"wss://api.sort-me.org/ws/submission?id={task_id}&token={self._api_key}") as websocket:
            for message in map(str, websocket):
                if message.isnumeric():
                    yield int(message)
                else:
                    yield json.loads(message)

    def get_submission_history(self, contest_id: int, task_id: int, limit = 0) -> tuple[int, list[ShortSubmission | ShortSubmissionBase]]:
        r = self._make_request('GET', 'getMySubmissionsByTask', params={'id': task_id, 'contestid': contest_id}).json()
        submissions: list[ShortSubmission | ShortSubmissionBase] = r['submissions']
        total_count: int = r['count']

        if total_count < 10:
            return total_count, submissions

        for count in range(10, total_count, 10): # you CAN NOT async this, offset is STRICTLY absolute, there is NO WAY to optimize this...
            raw = self._make_request('GET', 'getMySubmissionsByTask', params={
                'id': task_id,
                "offset": submissions[-1]['id'],
                'contestid': contest_id
            }).json()

            submissions.extend(raw['submissions'])

            if limit and limit < count:
                return total_count, submissions[:limit]

        return total_count, submissions

    def get_submission_info(self, contest_id: int, task_id: int, submission_id: int | None): # TODO: Typing
        id = -1

        if submission_id:
            id = self.get_submission_history(contest_id, task_id, limit=submission_id + 1)[1][submission_id]['id']
        else:
            submissions = self.get_submission_history(contest_id, task_id)[1]
            for submission in submissions:
                if 'total_points' in submission and submission['total_points'] == 100:
                    id = submission['id']
                    break

        r = self._make_request('GET', 'getSubmissionInfo', params={'id': id}).json()
        return r

    def get_contest(self, contest_id: int): # TODO: Typing
        r = self._make_request("GET", 'getContestTasks', params={'id': contest_id}).json()
        out = {
            'name': r['name'],
            'status': r['status'],
            'ends': r['ends'] if 'ends' in r else -1,
            'tasks': [task['name'] for task in r['tasks']],
        }

        # r = self._make_request('GET', 'getContestTable', params={'contestid': contest_id, 'page': 1, 'label': 0}).json()['you']
        # out.update({
        #     'place': r['place'],
        #     'results': r['results'],
        #     'sum': r['sum'],
        #     'time': r['time']
        # })

        return out

    def upload_code(self, code: str, contest_id: int | None, task_id: int, lang: Lang = 'c++') -> int:
        return self._make_request('POST', 'submit', json={
            "code": code,
            "contest_id": contest_id,
            "task_id": task_id,
            "lang": lang,
        }).json()['id']

