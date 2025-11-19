"""
Task decomposition module responsible for breaking down high-level requirements into executable tasks.
"""

# src/decomposer.py

import re
import uuid
import subprocess
import json
import re
import tempfile
from pathlib import Path
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

class AgentDecomposer:
    """
    AI-powered task decomposer that uses Claude Code to intelligently break down requirements.

    This decomposer spawns a Claude agent to:
    1. Analyze the requirements deeply
    2. Design an appropriate task breakdown specific to the problem
    3. Generate tasks with acceptance criteria tailored to the actual solution

    Falls back to SimpleDecomposer on failure for reliability.
    """

    # System prompt for decomposition
    DECOMPOSITION_PROMPT = '''You are an expert software architect and project planner. Your task is to analyze the given requirements and break them down into a sequence of executable development tasks.

IMPORTANT GUIDELINES:
1. Create 3-6 tasks that logically build on each other
2. Each task should be independently completable and testable
3. Tasks should follow a natural development progression (setup → core logic → features → polish)
4. Acceptance criteria should be specific and verifiable
5. Consider error handling, edge cases, and testing requirements

OUTPUT FORMAT:
You MUST respond with ONLY valid JSON in exactly this format (no markdown, no explanation):

{
  "tasks": [
    {
      "description": "Clear description of what this task accomplishes",
      "acceptance_criteria": [
        "First specific, testable criterion",
        "Second specific, testable criterion",
        "Third specific, testable criterion"
      ]
    }
  ]
}

REQUIREMENTS TO ANALYZE:
'''

    def __init__(self, cli_path: str = "claude", timeout_s: int = 180):
        """
        Initialize AgentDecomposer.

        Args:
            cli_path: Path to claude CLI executable (default: "claude" in PATH)
            timeout_s: Timeout in seconds for CLI execution (default: 180 = 3 minutes)
        """
        self.cli_path = cli_path
        self.timeout_s = timeout_s
        self._fallback_decomposer = SimpleDecomposer()

    def decompose(self, requirements: str) -> list[Task]:
        """
        Decompose requirements into tasks using Claude Code AI.

        Args:
            requirements: High-level project requirements

        Returns:
            List of Task objects with intelligent breakdown and acceptance criteria
        """
        print(f"[AGENT_DECOMPOSER] Analyzing requirements with Claude...")

        try:
            # Check if Claude CLI is available
            if not self._health_check():
                print("[AGENT_DECOMPOSER] Claude CLI not available, falling back to template-based decomposition")
                return self._fallback_decomposer.decompose(requirements)

            # Build the full prompt
            full_prompt = self.DECOMPOSITION_PROMPT + requirements

            # Execute Claude CLI
            result = self._execute_claude(full_prompt)

            # Parse the response
            tasks = self._parse_response(result, requirements)

            if tasks:
                print(f"[AGENT_DECOMPOSER] Successfully created {len(tasks)} intelligent tasks")
                return tasks
            else:
                print("[AGENT_DECOMPOSER] Failed to parse response, falling back to template-based decomposition")
                return self._fallback_decomposer.decompose(requirements)

        except Exception as e:
            print(f"[AGENT_DECOMPOSER] Error during AI decomposition: {str(e)}")
            print("[AGENT_DECOMPOSER] Falling back to template-based decomposition")
            return self._fallback_decomposer.decompose(requirements)

    def _execute_claude(self, prompt: str) -> str:
        """
        Execute Claude CLI with the given prompt.

        Args:
            prompt: The full prompt to send to Claude

        Returns:
            Claude's response text

        Raises:
            RuntimeError: If CLI execution fails
        """
        # Use a temporary directory for Claude to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[AGENT_DECOMPOSER] Executing Claude CLI (timeout: {self.timeout_s}s)")

            result = subprocess.run(
                [self.cli_path, "--print", "--dangerously-skip-permissions", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                cwd=temp_dir
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            return result.stdout

    def _parse_response(self, response: str, requirements: str) -> list[Task] | None:
        """
        Parse Claude's JSON response into Task objects.

        Args:
            response: Raw response from Claude CLI
            requirements: Original requirements (for context in descriptions)

        Returns:
            List of Task objects, or None if parsing fails
        """
        try:
            # Try to extract JSON from the response
            # Claude might include markdown code blocks or extra text
            json_str = self._extract_json(response)

            if not json_str:
                print("[AGENT_DECOMPOSER] No valid JSON found in response")
                return None

            data = json.loads(json_str)

            if "tasks" not in data or not isinstance(data["tasks"], list):
                print("[AGENT_DECOMPOSER] Invalid JSON structure: missing 'tasks' array")
                return None

            tasks = []
            for i, task_data in enumerate(data["tasks"], 1):
                # Validate task structure
                if "description" not in task_data:
                    print(f"[AGENT_DECOMPOSER] Task {i} missing 'description' field")
                    continue

                if "acceptance_criteria" not in task_data:
                    print(f"[AGENT_DECOMPOSER] Task {i} missing 'acceptance_criteria' field")
                    # Use default criteria if missing
                    task_data["acceptance_criteria"] = [
                        "Task completed successfully",
                        "Code is functional and tested"
                    ]

                # Ensure acceptance_criteria is a list
                criteria = task_data["acceptance_criteria"]
                if isinstance(criteria, str):
                    criteria = [criteria]
                elif not isinstance(criteria, list):
                    criteria = ["Task completed successfully"]

                # Generate unique task ID
                task_id = f"task_{i:03d}_{uuid.uuid4().hex[:6]}"

                # Create task with requirements context
                description = f"{task_data['description']}. Context: {requirements}"

                task = Task(
                    id=task_id,
                    description=description,
                    acceptance_criteria=criteria,
                    status=TaskStatus.PENDING
                )
                tasks.append(task)

            if not tasks:
                print("[AGENT_DECOMPOSER] No valid tasks parsed from response")
                return None

            return tasks

        except json.JSONDecodeError as e:
            print(f"[AGENT_DECOMPOSER] JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            print(f"[AGENT_DECOMPOSER] Error parsing response: {str(e)}")
            return None

    def _extract_json(self, response: str) -> str | None:
        """
        Extract JSON from Claude's response, handling various formats.

        Claude might return:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON with surrounding text

        Args:
            response: Raw response text

        Returns:
            Extracted JSON string, or None if not found
        """
        # Try to find JSON in markdown code blocks first
        code_block_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                if '"tasks"' in match:
                    return match.strip()

        # Try to find JSON object using brace matching
        # Find first { that contains "tasks"
        if '"tasks"' in response:
            # Find all opening braces
            start_idx = None
            for i, char in enumerate(response):
                if char == '{':
                    # Check if this brace leads to "tasks"
                    remaining = response[i:]
                    if '"tasks"' in remaining:
                        start_idx = i
                        break

            if start_idx is not None:
                # Match braces to find the end
                brace_count = 0
                for i in range(start_idx, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return response[start_idx:i+1]

        # Last resort: try the entire response if it looks like JSON
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            return stripped

        return None

    def _health_check(self) -> bool:
        """
        Check if Claude Code CLI is available.

        Returns:
            True if CLI is installed and accessible
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


class MockAgentDecomposer:
    """
    TEST INFRASTRUCTURE ONLY - Mock version of AgentDecomposer for testing.

    Returns predictable, deterministic task breakdowns without calling Claude CLI.
    Use this in tests to avoid:
    - Expensive API calls
    - Non-deterministic outputs
    - Network dependencies
    - Slow test execution
    """

    def __init__(self, cli_path: str = "claude", timeout_s: int = 180):
        """Initialize mock decomposer (params ignored, kept for interface compatibility)."""
        self.cli_path = cli_path
        self.timeout_s = timeout_s

    def decompose(self, requirements: str) -> list[Task]:
        """
        Generate mock intelligent task breakdown.

        Creates tasks that appear intelligently decomposed but are actually
        pre-defined for testing purposes.

        Args:
            requirements: High-level project requirements

        Returns:
            List of Task objects with mock intelligent breakdown
        """
        print(f"[MOCK_AGENT_DECOMPOSER] Generating mock task breakdown")

        # Analyze requirements for keyword-based customization
        req_lower = requirements.lower()

        # Customize tasks based on keywords in requirements
        if "api" in req_lower or "endpoint" in req_lower:
            tasks_data = self._api_project_tasks()
        elif "cli" in req_lower or "command" in req_lower:
            tasks_data = self._cli_project_tasks()
        elif "web" in req_lower or "frontend" in req_lower:
            tasks_data = self._web_project_tasks()
        else:
            tasks_data = self._generic_project_tasks()

        tasks = []
        for i, task_data in enumerate(tasks_data, 1):
            task_id = f"task_{i:03d}_{uuid.uuid4().hex[:6]}"
            description = f"{task_data['description']}. Context: {requirements}"

            task = Task(
                id=task_id,
                description=description,
                acceptance_criteria=task_data['criteria'],
                status=TaskStatus.PENDING
            )
            tasks.append(task)

        print(f"[MOCK_AGENT_DECOMPOSER] Created {len(tasks)} mock tasks")
        return tasks

    def _api_project_tasks(self) -> list[dict]:
        """Return tasks for API-style projects."""
        return [
            {
                "description": "Set up project structure with FastAPI/Flask and dependencies",
                "criteria": [
                    "Project directory structure created",
                    "requirements.txt with web framework dependencies",
                    "Configuration files for development and production"
                ]
            },
            {
                "description": "Implement data models and database schema",
                "criteria": [
                    "SQLAlchemy/Pydantic models defined",
                    "Database migrations created",
                    "Model validation tests pass"
                ]
            },
            {
                "description": "Create API endpoints with request/response handling",
                "criteria": [
                    "CRUD endpoints implemented",
                    "Input validation in place",
                    "Error responses follow REST conventions"
                ]
            },
            {
                "description": "Add authentication and authorization",
                "criteria": [
                    "JWT or session-based auth implemented",
                    "Protected routes require authentication",
                    "Role-based access control working"
                ]
            },
            {
                "description": "Write tests and API documentation",
                "criteria": [
                    "Unit tests for all endpoints",
                    "Integration tests for workflows",
                    "OpenAPI/Swagger documentation generated"
                ]
            }
        ]

    def _cli_project_tasks(self) -> list[dict]:
        """Return tasks for CLI-style projects."""
        return [
            {
                "description": "Set up CLI framework with argument parsing",
                "criteria": [
                    "Click/argparse configured",
                    "Help text and usage documentation",
                    "Version command working"
                ]
            },
            {
                "description": "Implement core business logic",
                "criteria": [
                    "Main functionality implemented",
                    "Error handling for edge cases",
                    "Input validation complete"
                ]
            },
            {
                "description": "Add commands and subcommands",
                "criteria": [
                    "All required commands implemented",
                    "Command options and flags working",
                    "Interactive prompts where needed"
                ]
            },
            {
                "description": "Implement output formatting and file I/O",
                "criteria": [
                    "Multiple output formats (text, JSON, table)",
                    "File reading/writing operations",
                    "Progress indicators for long operations"
                ]
            },
            {
                "description": "Add tests and user documentation",
                "criteria": [
                    "Unit tests for all commands",
                    "README with installation and usage",
                    "Example commands documented"
                ]
            }
        ]

    def _web_project_tasks(self) -> list[dict]:
        """Return tasks for web frontend projects."""
        return [
            {
                "description": "Set up frontend build tooling and dependencies",
                "criteria": [
                    "Package.json with dependencies",
                    "Build configuration (Vite/Webpack)",
                    "Development server working"
                ]
            },
            {
                "description": "Create component structure and routing",
                "criteria": [
                    "Component hierarchy established",
                    "Client-side routing configured",
                    "Layout components created"
                ]
            },
            {
                "description": "Implement UI components and styling",
                "criteria": [
                    "All required UI components built",
                    "Responsive design implemented",
                    "Consistent styling/theming"
                ]
            },
            {
                "description": "Add state management and API integration",
                "criteria": [
                    "State management solution implemented",
                    "API calls with error handling",
                    "Loading states and optimistic updates"
                ]
            },
            {
                "description": "Write tests and optimize performance",
                "criteria": [
                    "Component tests with testing library",
                    "E2E tests for critical flows",
                    "Bundle size optimization"
                ]
            }
        ]

    def _generic_project_tasks(self) -> list[dict]:
        """Return tasks for generic projects."""
        return [
            {
                "description": "Initialize project structure and configuration",
                "criteria": [
                    "Project directory structure created",
                    "Dependencies file created",
                    "Configuration files in place"
                ]
            },
            {
                "description": "Implement core data models and utilities",
                "criteria": [
                    "Data structures defined",
                    "Helper functions implemented",
                    "Basic validation in place"
                ]
            },
            {
                "description": "Build main application logic",
                "criteria": [
                    "Primary features implemented",
                    "Error handling complete",
                    "Edge cases covered"
                ]
            },
            {
                "description": "Add user interface or entry point",
                "criteria": [
                    "Main entry point working",
                    "User interactions handled",
                    "Output formatting complete"
                ]
            },
            {
                "description": "Create tests and documentation",
                "criteria": [
                    "Unit tests for core logic",
                    "Integration tests for workflows",
                    "README with usage instructions"
                ]
            }
        ]
