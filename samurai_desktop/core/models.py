from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ProjectType(Enum):
    SOFTWARE = "software"
    PRODUCTION = "production"
    RESEARCH = "research"


class ProjectStatus(Enum):
    SEED = "seed"
    SPROUT = "sprout"
    TREE = "tree"
    BLOOM = "bloom"


class EntryColor(Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class TaskStatus(Enum):
    IN_WORK = "in_work"
    IN_TEST = "in_test"


class TestMark(Enum):
    NONE = "none"
    GREEN = "green"
    RED = "red"
    BLUE = "blue"


class EcoType(Enum):
    NEW = "new"
    INTEGRATION = "integration"


@dataclass
class Project:
    title: str
    project_type: ProjectType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    date_created: datetime = field(default_factory=datetime.now)
    date_launched: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.SEED
    file_path: str = ""


@dataclass
class IdeaEntry:
    project_id: str
    theme: ProjectType
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_received: datetime = field(default_factory=datetime.now)
    color: EntryColor = EntryColor.RED
    phase: int = 0


@dataclass
class MVPTask:
    project_id: str
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.IN_WORK
    test_mark: TestMark = TestMark.NONE
    order: int = 0


@dataclass
class EcoEntry:
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    source_project_id: Optional[str] = None
    date_received: datetime = field(default_factory=datetime.now)
    entry_type: EcoType = EcoType.NEW
    result: str = ""


@dataclass
class TreeProject:
    project_id: str
    checklists: list = field(default_factory=list)
    keys_tools: list = field(default_factory=list)
    finance_data: dict = field(default_factory=dict)
    stability_achieved: bool = False
    eco_sent: bool = False


@dataclass
class ChatSession:
    entry_id: str
    prompt_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phase: int = 1
    messages: list = field(default_factory=list)
    is_complete: bool = False
    revision_used: bool = False


@dataclass
class User:
    login: str
    password_hash: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))