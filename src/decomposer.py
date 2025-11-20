"""
Task decomposition module responsible for breaking down high-level requirements into executable tasks.
"""

# src/decomposer.py

import re
import uuid
from .models import Task, TaskStatus


class ProjectType:
    """Enum-like class for project types"""
    CLI = "cli"
    SCRIPT = "script"
    LIBRARY = "library"
    WEB_APP = "web_app"
    DATA_PROCESSING = "data_processing"


class SimpleDecomposer:
    """Breaks requirements into tasks using templates with intelligent project type detection"""

    # Template for CLI applications
    CLI_TEMPLATE = [
        {
            "description": "Set up project structure and dependencies",
            "criteria": [
                "Directory structure created",
                "Dependencies file (requirements.txt/package.json) created",
                "Entry point script created"
            ]
        },
        {
            "description": "Implement argument parsing and user interaction",
            "criteria": [
                "Command-line argument parsing implemented",
                "Help text and usage information provided",
                "Input validation in place"
            ]
        },
        {
            "description": "Implement core CLI functionality",
            "criteria": [
                "Main business logic implemented",
                "Output formatting complete",
                "Error handling and user feedback in place"
            ]
        },
        {
            "description": "Add tests and documentation",
            "criteria": [
                "Unit tests for core functions",
                "CLI integration tests",
                "README with usage examples"
            ]
        }
    ]

    # Template for simple scripts
    SCRIPT_TEMPLATE = [
        {
            "description": "Set up project structure",
            "criteria": [
                "Main script file created",
                "Dependencies documented if any",
                "Configuration handled"
            ]
        },
        {
            "description": "Implement main script logic",
            "criteria": [
                "Core functionality implemented",
                "Input/output handling complete",
                "Error handling in place"
            ]
        },
        {
            "description": "Add tests and documentation",
            "criteria": [
                "Unit tests for main functions",
                "README with usage instructions",
                "Example usage provided"
            ]
        }
    ]

    # Template for libraries/packages
    LIBRARY_TEMPLATE = [
        {
            "description": "Set up library structure and packaging",
            "criteria": [
                "Package structure created (__init__.py, etc.)",
                "setup.py or pyproject.toml configured",
                "Dependencies specified"
            ]
        },
        {
            "description": "Implement core library functionality",
            "criteria": [
                "Public API defined",
                "Core modules implemented",
                "Type hints added"
            ]
        },
        {
            "description": "Add comprehensive tests",
            "criteria": [
                "Unit tests for all public functions",
                "Edge cases covered",
                "Test coverage meets standards"
            ]
        },
        {
            "description": "Add documentation and examples",
            "criteria": [
                "API documentation complete",
                "README with quick start guide",
                "Usage examples provided"
            ]
        }
    ]

    # Template for data processing projects
    DATA_PROCESSING_TEMPLATE = [
        {
            "description": "Set up project structure and data handling",
            "criteria": [
                "Directory structure created",
                "Dependencies specified (pandas, numpy, etc.)",
                "Data input/output paths configured"
            ]
        },
        {
            "description": "Implement data loading and validation",
            "criteria": [
                "Data loading functions implemented",
                "Input validation in place",
                "Data schema defined"
            ]
        },
        {
            "description": "Implement core data processing logic",
            "criteria": [
                "Data transformation complete",
                "Processing pipeline implemented",
                "Output generation working"
            ]
        },
        {
            "description": "Add tests and documentation",
            "criteria": [
                "Unit tests with sample data",
                "Data validation tests",
                "README with data format documentation"
            ]
        }
    ]

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

    # Keywords for project type detection
    PROJECT_TYPE_KEYWORDS = {
        ProjectType.CLI: [
            r'\bcli\b', r'\bcommand[- ]?line\b', r'\bterminal\b', r'\bconsole\b',
            r'\bargparse\b', r'\bclick\b', r'\btyper\b', r'\bargument\b',
            r'\binteractive\b.*\bprompt\b', r'\bshell\b'
        ],
        ProjectType.WEB_APP: [
            r'\bapi\b', r'\bweb\b', r'\bserver\b', r'\brest\b', r'\bhttp\b',
            r'\bendpoint\b', r'\bflask\b', r'\bdjango\b', r'\bfastapi\b',
            r'\brouter?\b', r'\bwebsite\b', r'\bweb\s*app\b', r'\bbackend\b',
            r'\bfrontend\b', r'\bdatabase\b', r'\bauth\b'
        ],
        ProjectType.LIBRARY: [
            r'\blibrary\b', r'\bpackage\b', r'\bmodule\b', r'\bsdk\b',
            r'\bpip\s*install\b', r'\bimport\b', r'\breusable\b',
            r'\bframework\b'
        ],
        ProjectType.DATA_PROCESSING: [
            r'\bdata\b', r'\bcsv\b', r'\bjson\s*file\b', r'\bprocess\b',
            r'\bparse\b', r'\betl\b', r'\bpandas\b', r'\banalyze\b',
            r'\btransform\b', r'\bpipeline\b', r'\bdataset\b'
        ],
        ProjectType.SCRIPT: [
            r'\bscript\b', r'\bsimple\b', r'\bquick\b', r'\bautomate\b',
            r'\btask\b', r'\butility\b'
        ]
    }

    # Template mapping
    TEMPLATES = {
        ProjectType.CLI: CLI_TEMPLATE,
        ProjectType.WEB_APP: WEB_APP_TEMPLATE,
        ProjectType.LIBRARY: LIBRARY_TEMPLATE,
        ProjectType.DATA_PROCESSING: DATA_PROCESSING_TEMPLATE,
        ProjectType.SCRIPT: SCRIPT_TEMPLATE
    }

    def detect_project_type(self, requirements: str) -> str:
        """
        Detect project type based on keyword analysis of requirements.

        Uses weighted scoring - each keyword match adds to the score.
        Returns the project type with highest score, defaulting to SCRIPT.
        """
        requirements_lower = requirements.lower()
        scores = {ptype: 0 for ptype in self.PROJECT_TYPE_KEYWORDS}

        for project_type, patterns in self.PROJECT_TYPE_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, requirements_lower):
                    scores[project_type] += 1

        # Get project type with highest score
        max_score = max(scores.values())

        # If no keywords matched, default to SCRIPT for simple tasks
        if max_score == 0:
            return ProjectType.SCRIPT

        # Return highest scoring type (with priority order for ties)
        priority_order = [
            ProjectType.WEB_APP,      # Highest priority for ties
            ProjectType.CLI,
            ProjectType.LIBRARY,
            ProjectType.DATA_PROCESSING,
            ProjectType.SCRIPT        # Lowest priority
        ]

        for ptype in priority_order:
            if scores[ptype] == max_score:
                return ptype

        return ProjectType.SCRIPT

    def decompose(self, requirements: str) -> list[Task]:
        """
        Decompose requirements into tasks.

        For Gear 1: Use template-based decomposition with project type detection.
        Future: Use LLM-based decomposition.
        """
        # Detect project type and select appropriate template
        project_type = self.detect_project_type(requirements)
        template = self.TEMPLATES[project_type]

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

    def get_project_type_for_requirements(self, requirements: str) -> str:
        """
        Public method to get detected project type for given requirements.
        Useful for debugging and testing.
        """
        return self.detect_project_type(requirements)