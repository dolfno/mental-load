"""Task importer to parse tasks.md and import into database."""

import re
from pathlib import Path

from src.domain import Task, RecurrencePattern, RecurrenceType, TimeOfDay
from src.infrastructure import get_database, SQLiteTaskRepository


def parse_recurrence(recurrence_str: str) -> RecurrencePattern | None:
    """Parse a Dutch recurrence string into a RecurrencePattern."""
    if not recurrence_str or not recurrence_str.strip():
        return None

    s = recurrence_str.strip().lower()

    # Continuous
    if s == "continu":
        return RecurrencePattern(type=RecurrenceType.CONTINUOUS)

    # Daily with time of day
    if s == "elke ochtend":
        return RecurrencePattern(type=RecurrenceType.DAILY, time_of_day=TimeOfDay.MORNING)
    if s == "elke avond":
        return RecurrencePattern(type=RecurrenceType.DAILY, time_of_day=TimeOfDay.EVENING)

    # Daily
    if s in ("elke dag", "dagelijks"):
        return RecurrencePattern(type=RecurrenceType.DAILY)

    # Every X days
    match = re.match(r"elke (\w+) dag(?:en)?", s)
    if match:
        num_map = {"twee": 2, "drie": 3, "vier": 4, "vijf": 5}
        num = num_map.get(match.group(1), 2)
        return RecurrencePattern(type=RecurrenceType.DAILY, interval=num)

    # Biweekly
    if s in ("elke twee weken", "elke 2 weken", "om de twee weken", "om de week"):
        interval = 1 if "om de week" in s else 2
        return RecurrencePattern(type=RecurrenceType.BIWEEKLY if interval == 2 else RecurrenceType.WEEKLY)

    # Weekly with specific days
    day_map = {
        "maandag": 0, "ma": 0,
        "dinsdag": 1, "di": 1,
        "woensdag": 2, "wo": 2,
        "donderdag": 3, "do": 3,
        "vrijdag": 4, "vr": 4,
        "zaterdag": 5, "za": 5,
        "zondag": 6, "zo": 6,
    }

    # Check for specific day patterns like "Zondag" or "Ma do"
    found_days = []
    for day_name, day_num in day_map.items():
        if day_name in s:
            found_days.append(day_num)

    if found_days and not any(x in s for x in ["keer per", "elke"]):
        return RecurrencePattern(type=RecurrenceType.WEEKLY, days=tuple(sorted(set(found_days))))

    # X times per week
    match = re.match(r"(\d+)\s*keer\s*per\s*week", s)
    if match:
        times = int(match.group(1))
        return RecurrencePattern(type=RecurrenceType.WEEKLY, interval=times)

    # Weekly
    if s in ("elke week", "wekelijks"):
        return RecurrencePattern(type=RecurrenceType.WEEKLY)

    # Monthly
    if s in ("elke maand", "maandelijks"):
        return RecurrencePattern(type=RecurrenceType.MONTHLY)

    # Every X months
    match = re.match(r"elke (\w+) maand(?:en)?", s)
    if match:
        num_map = {"twee": 2, "drie": 3, "vier": 4, "zes": 6}
        num = num_map.get(match.group(1), 1)
        return RecurrencePattern(type=RecurrenceType.MONTHLY, interval=num)

    # Quarterly
    if "kwartaal" in s:
        return RecurrencePattern(type=RecurrenceType.QUARTERLY)

    # X times per year
    match = re.match(r"(\d+)\s*keer\s*per\s*jaar", s)
    if match:
        times = int(match.group(1))
        return RecurrencePattern(type=RecurrenceType.YEARLY, interval=times)

    # Every X weeks
    match = re.match(r"om de (\w+) weken?", s)
    if match:
        num_map = {"paar": 2, "twee": 2, "drie": 3}
        num = num_map.get(match.group(1), 2)
        if num == 2:
            return RecurrencePattern(type=RecurrenceType.BIWEEKLY)
        return RecurrencePattern(type=RecurrenceType.WEEKLY, interval=num)

    # Every X months pattern
    match = re.match(r"elke (\d+) weken?", s)
    if match:
        weeks = int(match.group(1))
        if weeks == 2:
            return RecurrencePattern(type=RecurrenceType.BIWEEKLY)
        return RecurrencePattern(type=RecurrenceType.WEEKLY, interval=weeks)

    # Day patterns with time
    if "avond" in s:
        found_days = []
        for day_name, day_num in day_map.items():
            if day_name in s:
                found_days.append(day_num)
        if found_days:
            return RecurrencePattern(
                type=RecurrenceType.WEEKLY,
                days=tuple(sorted(set(found_days))),
                time_of_day=TimeOfDay.EVENING,
            )

    # Default: assume weekly if nothing else matches
    return None


def parse_tasks_md(filepath: str) -> list[tuple[str, RecurrencePattern | None]]:
    """Parse tasks.md file and return list of (name, recurrence) tuples."""
    tasks = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("|") and "---" in line:
            continue
        if line.startswith("| Wat"):
            continue

        # Parse markdown table row
        if line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                name = parts[1]
                recurrence_str = parts[2]
                if name:
                    recurrence = parse_recurrence(recurrence_str)
                    tasks.append((name, recurrence))

    return tasks


def import_tasks(filepath: str, db_path: str = "aivin.db") -> int:
    """Import tasks from tasks.md into the database."""
    from src.infrastructure.database import Database, set_database

    db = Database(db_path)
    set_database(db)
    task_repo = SQLiteTaskRepository(db)

    # Get existing task names to avoid duplicates
    existing_tasks = {t.name for t in task_repo.get_all(active_only=False)}

    tasks = parse_tasks_md(filepath)
    imported = 0

    for name, recurrence in tasks:
        if name in existing_tasks:
            print(f"Skipping existing task: {name}")
            continue

        if recurrence is None:
            # Default to continuous for tasks without recurrence
            recurrence = RecurrencePattern(type=RecurrenceType.CONTINUOUS)

        task = Task(
            id=None,
            name=name,
            recurrence=recurrence,
        )
        task_repo.save(task)
        imported += 1
        print(f"Imported: {name}")

    return imported


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Find tasks.md
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    tasks_file = project_root / "tasks.md"

    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found")
        sys.exit(1)

    # Use the database in the backend directory
    db_path = str(backend_dir / "aivin.db")

    print(f"Importing tasks from {tasks_file}")
    print(f"Database: {db_path}")

    count = import_tasks(str(tasks_file), db_path)
    print(f"\nImported {count} tasks")
