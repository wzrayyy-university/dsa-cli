from typing import Literal, TypeAlias, TypedDict
from dataclasses import dataclass

Lang: TypeAlias = Literal["python", "pypy", "c++", "golang", "haskell", "java", "rust", "c", "nodejs", "csharp"]

_Json: TypeAlias = dict[str, "_Json"] | list["_Json"] | str | int | float | bool | None

RequestMethod: TypeAlias = Literal['POST', 'GET']

class FailedTestResponse(TypedDict):
    n: int
    verdict: Literal[1, 2, 3, 4, 5]
    verdict_text: str
    milliseconds: int
    partial_score: int

class TelegramResponse(TypedDict):
    id: int
    first_name: str
    last_name: str
    username: str
    photo_url: str
    auth_date: int
    hash: str

class SubmissionSubTask(TypedDict):
    skipped: bool
    points: int
    failed_tests: list[FailedTestResponse] | None
    worst_time: int

class BaseSubmission(TypedDict):
    completed: bool
    compiler_log: str
    shown_verdict: Literal[1, 2, 3, 4, 5]
    shown_verdict_text: str
    total_points: int
    subtasks: list[SubmissionSubTask] | None

class FailedSubmission(BaseSubmission):
    shown_test: int

class VerboseSubmission(BaseSubmission):
    code: str
    submited_at: int

class ShortSubmissionBase(TypedDict):
    id: int
    shown_verdict: int
    shown_verdict_text: str

class ShortSubmission(ShortSubmissionBase):
    shown_test: int
    total_points: int

@dataclass
class _BaseContest(TypedDict):
    id: int
    name: str
    starts: int
    ends: int

class UpcomingContest(_BaseContest):
    org_name: str
    running: bool
    registration_opened: bool
    ended: bool

class VerboseContestInfo(_BaseContest):
    description: str
    register_starts: int
    register_ends: int
    participants_count: int
    rules: str
    registered: bool
    now: int
    is_admin: bool

@dataclass
class ContestTaskSample:
    input: str
    output: str

    @classmethod
    def from_dict(cls, data):
        return cls(input=data['in'], output=data.get('out') or '')

@dataclass
class ContestTaskSubtask:
    num: int
    points: int
    description: str
    subtask_rating_system: int
    tests_count: int
    necessary_subtasks: list[int] | None = None

@dataclass
class ContestTask:
    id: int
    name: str
    main_description: str
    in_description: str
    out_description: str
    category: int
    difficulty: int
    solved_by: int
    samples: list[ContestTaskSample]
    on_moderation: bool
    visibility: int
    is_admin: bool
    admins: list[int]
    tests_updated: int
    time_limit_milliseconds: int
    memory_limit_megabytes: int
    rating_system_type: int
    comment: str | None = None
    subtasks: list[ContestTaskSubtask] | None = None
    rating_system: str | None = None

    @classmethod
    def from_dict(cls, data):
        if 'subtasks' in data:
            data['subtasks'] = [ContestTaskSubtask(**subtask) for subtask in data['subtasks']]
        data['samples'] = [ContestTaskSample.from_dict(sample) for sample in data['samples']]

        return cls(**data)

class SubmissionHistory(TypedDict):
    count: int
    submissions: list[ShortSubmission | ShortSubmissionBase]

@dataclass
class ContestInfoNew:
    name: str
    status: str
    ends: int


@dataclass
class Config:
    api_key: str
    naming_convention: str
    phone_number: str
