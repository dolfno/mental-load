import json
import logging
import os
from datetime import date, datetime
from typing import Any

from openai import OpenAI

from src.domain import (
    RecurrencePattern,
    RecurrenceType,
    Urgency,
    TimeOfDay,
    calculate_urgency,
)
from src.application import (
    TaskRepository,
    MemberRepository,
    CompletionRepository,
    NoteRepository,
    CreateTask,
    CompleteTask,
    DeactivateTask,
    GetAllTasks,
    GetNote,
    UpdateNote,
    GetAllMembers,
    GetCompletionHistory,
    TaskWithUrgency,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Aivin, a helpful AI assistant for a household task management app. You help users manage their household chores and tasks through natural language conversation.

You have access to tools that let you interact with the app. Use them to fulfill user requests.

When listing tasks, format them clearly. When performing actions, confirm what you did.

For task creation, you need at minimum a name and recurrence type. If the user doesn't specify recurrence, ask them or default to "eenmalig" (one-time).

Available recurrence types: daily, weekly, biweekly, monthly, quarterly, yearly, eenmalig (one-time).
For weekly tasks, days are 0=Monday through 6=Sunday.

Today's date is {today}.

Keep responses concise and helpful. Respond in the same language the user writes in."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all active household tasks with their urgency and due dates",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new household task",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the task",
                    },
                    "recurrence_type": {
                        "type": "string",
                        "enum": ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly", "eenmalig"],
                        "description": "How often the task recurs",
                    },
                    "recurrence_days": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "For weekly/biweekly tasks, which days (0=Mon, 6=Sun)",
                    },
                    "recurrence_interval": {
                        "type": "integer",
                        "description": "Interval for recurrence (e.g., every 2 weeks). Defaults to 1.",
                    },
                    "next_due": {
                        "type": "string",
                        "description": "Next due date in YYYY-MM-DD format",
                    },
                    "assigned_to_name": {
                        "type": "string",
                        "description": "Name of the household member to assign the task to",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the task",
                    },
                },
                "required": ["name", "recurrence_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed by its name or ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Name (or partial name) of the task to complete",
                    },
                },
                "required": ["task_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete (deactivate) a task by its name",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Name (or partial name) of the task to delete",
                    },
                },
                "required": ["task_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_members",
            "description": "List all household members",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_notes",
            "description": "Get the shared household notepad content",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_notes",
            "description": "Update the shared household notepad content",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "New content for the notepad",
                    },
                },
                "required": ["content"],
            },
        },
    },
]


def _find_task_by_name(tasks: list[TaskWithUrgency], name: str) -> TaskWithUrgency | None:
    """Find a task by exact or partial name match (case-insensitive)."""
    name_lower = name.lower()
    # Try exact match first
    for twu in tasks:
        if twu.task.name.lower() == name_lower:
            return twu
    # Try partial match
    for twu in tasks:
        if name_lower in twu.task.name.lower():
            return twu
    return None


class LLMService:
    def __init__(
        self,
        task_repo: TaskRepository,
        member_repo: MemberRepository,
        completion_repo: CompletionRepository,
        note_repo: NoteRepository,
    ):
        self.task_repo = task_repo
        self.member_repo = member_repo
        self.completion_repo = completion_repo
        self.note_repo = note_repo

        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """Execute a tool call and return the result as a string."""
        try:
            if name == "list_tasks":
                return self._list_tasks()
            elif name == "create_task":
                return self._create_task(args)
            elif name == "complete_task":
                return self._complete_task(args)
            elif name == "delete_task":
                return self._delete_task(args)
            elif name == "list_members":
                return self._list_members()
            elif name == "get_notes":
                return self._get_notes()
            elif name == "update_notes":
                return self._update_notes(args)
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
        except Exception as e:
            logger.exception("Tool execution error: %s", name)
            return json.dumps({"error": str(e)})

    def _list_tasks(self) -> str:
        use_case = GetAllTasks(self.task_repo)
        tasks = use_case.execute(active_only=True)
        result = []
        for twu in tasks:
            task = twu.task
            member_name = None
            if task.assigned_to_id:
                member = self.member_repo.get_by_id(task.assigned_to_id)
                if member:
                    member_name = member.name
            result.append({
                "id": task.id,
                "name": task.name,
                "urgency": twu.calculated_urgency.value,
                "next_due": task.next_due.isoformat() if task.next_due else None,
                "assigned_to": member_name,
                "recurrence": task.recurrence.type.value,
                "description": task.description,
            })
        return json.dumps(result)

    def _create_task(self, args: dict[str, Any]) -> str:
        recurrence_type = RecurrenceType(args["recurrence_type"])
        recurrence_days = None
        if "recurrence_days" in args and args["recurrence_days"]:
            recurrence_days = tuple(args["recurrence_days"])

        recurrence = RecurrencePattern(
            type=recurrence_type,
            days=recurrence_days,
            interval=args.get("recurrence_interval", 1),
        )

        assigned_to_id = None
        if "assigned_to_name" in args and args["assigned_to_name"]:
            member = self.member_repo.get_by_name(args["assigned_to_name"])
            if member:
                assigned_to_id = member.id

        next_due = None
        if "next_due" in args and args["next_due"]:
            next_due = date.fromisoformat(args["next_due"])

        use_case = CreateTask(self.task_repo)
        task = use_case.execute(
            name=args["name"],
            recurrence=recurrence,
            next_due=next_due,
            assigned_to_id=assigned_to_id,
            description=args.get("description"),
        )
        return json.dumps({"success": True, "task_id": task.id, "name": task.name})

    def _complete_task(self, args: dict[str, Any]) -> str:
        use_case_get = GetAllTasks(self.task_repo)
        tasks = use_case_get.execute(active_only=True)
        twu = _find_task_by_name(tasks, args["task_name"])
        if not twu:
            return json.dumps({"error": f"Task not found: {args['task_name']}"})

        use_case = CompleteTask(self.task_repo, self.completion_repo)
        result = use_case.execute(task_id=twu.task.id)
        if result is None:
            return json.dumps({"error": "Failed to complete task"})
        task, _ = result
        return json.dumps({"success": True, "name": task.name, "next_due": task.next_due.isoformat() if task.next_due else None})

    def _delete_task(self, args: dict[str, Any]) -> str:
        use_case_get = GetAllTasks(self.task_repo)
        tasks = use_case_get.execute(active_only=True)
        twu = _find_task_by_name(tasks, args["task_name"])
        if not twu:
            return json.dumps({"error": f"Task not found: {args['task_name']}"})

        use_case = DeactivateTask(self.task_repo)
        success = use_case.execute(task_id=twu.task.id)
        return json.dumps({"success": success, "name": twu.task.name})

    def _list_members(self) -> str:
        use_case = GetAllMembers(self.member_repo)
        members = use_case.execute()
        return json.dumps([{"id": m.id, "name": m.name} for m in members])

    def _get_notes(self) -> str:
        use_case = GetNote(self.note_repo)
        note = use_case.execute()
        if note is None:
            return json.dumps({"content": ""})
        return json.dumps({"content": note.content, "updated_at": note.updated_at.isoformat()})

    def _update_notes(self, args: dict[str, Any]) -> str:
        use_case = UpdateNote(self.note_repo)
        note = use_case.execute(content=args["content"])
        return json.dumps({"success": True, "updated_at": note.updated_at.isoformat()})

    def chat(self, messages: list[dict[str, str]]) -> str:
        """Send messages to the LLM and process any tool calls.
        Returns the assistant's text response."""
        if not self.client:
            return "AI chat is not configured. Please set the LLM_API_KEY environment variable."

        system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(today=date.today().isoformat()),
        }

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[system_message] + messages,
            tools=TOOLS,
        )

        message = response.choices[0].message

        # Process tool calls in a loop (LLM may call multiple tools)
        max_iterations = 10
        iteration = 0
        conversation = [system_message] + messages

        while message.tool_calls and iteration < max_iterations:
            iteration += 1
            conversation.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                result = self._execute_tool(func_name, func_args)

                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation,
                tools=TOOLS,
            )
            message = response.choices[0].message

        return message.content or ""
