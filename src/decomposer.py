"""
Task decomposition module responsible for breaking down high-level requirements into executable tasks.
"""

# src/decomposer.py

import uuid
from .models import Task, TaskStatus

class SimpleDecomposer:
    """Breaks requirements into tasks using templates"""

    # Template for web application projects
    WEB_APP_TEMPLATE = [
        {
            "description": "Set up project structure and dependencies",
            "criteria": [
                "Directory structure created",
                "Dependencies file (requirements.txt/package.json) created",
                "Basic configuration files present"
            ]
        },
        {
            "description": "Implement core data models and database schema",
            "criteria": [
                "Data models defined",
                "Database schema created",
                "Basic CRUD operations work"
            ]
        },
        {
            "description": "Create main application logic and API endpoints",
            "criteria": [
                "API endpoints implemented",
                "Business logic complete",
                "Error handling in place"
            ]
        },
        {
            "description": "Add tests and documentation",
            "criteria": [
                "Unit tests added",
                "Integration tests added",
                "README with usage instructions",
                "API documentation"
            ]
        }
    ]

    def decompose(self, requirements: str) -> list[Task]:
        """
        Decompose requirements into tasks.

        For Gear 1: Use simple template-based decomposition.
        Future: Use LLM-based decomposition.
        """

        # For now, use generic template
        # TODO: Add project type detection
        template = self.WEB_APP_TEMPLATE

        tasks = []
        for i, task_template in enumerate(template, 1):
            task_id = f"task_{i:03d}_{uuid.uuid4().hex[:6]}"

            # Augment description with requirements context
            description = f"{task_template['description']}. Context: {requirements}"

            task = Task(
                id=task_id,
                description=description,
                acceptance_criteria=task_template['criteria'],
                status=TaskStatus.PENDING
            )
            tasks.append(task)

        return tasks