"""
Backend routing for intelligent backend selection based on task characteristics.

This module implements rule-based routing that automatically selects the optimal
backend for each task type:
- Prototyping tasks → CCPMBackend (rapid code generation)
- Refactoring tasks → ClaudeCodeBackend (iterative improvements)
- Testing tasks → ClaudeCodeBackend (test generation quality)
- Documentation tasks → ClaudeCodeBackend (documentation quality)
- General tasks → Configured default backend

Example:
    >>> from src.execution.backend_router import BackendRouter
    >>> from src.models import Task
    >>> from src.execution.models import ExecutionContext
    >>>
    >>> config = {
    >>>     'gear3': {
    >>>         'backend_routing': {
    >>>             'enabled': True,
    >>>             'default_backend': 'claude_code',
    >>>             'rules': {
    >>>                 'prototyping': 'ccpm',
    >>>                 'refactoring': 'claude_code'
    >>>             }
    >>>         }
    >>>     },
    >>>     'backend': {
    >>>         'ccpm': {'api_key': 'your-key'},
    >>>         'claude_code': {}
    >>>     }
    >>> }
    >>>
    >>> router = BackendRouter(config)
    >>> task = Task(
    >>>     id="task_001",
    >>>     description="Create new API endpoint from scratch",
    >>>     acceptance_criteria=["Implement REST endpoint"]
    >>> )
    >>> backend = router.select_backend(task, context)
    >>> # Returns CCPMBackend (matched "prototyping" keywords)
"""

from typing import Dict, Optional
from src.models import Task
from src.execution.models import ExecutionContext
from src.backend import Backend, CCPMBackend, ClaudeCodeBackend, TestMockBackend


# Default routing rules mapping task types to backend types
DEFAULT_ROUTING_RULES = {
    "prototyping": "ccpm",
    "refactoring": "claude_code",
    "testing": "claude_code",
    "documentation": "claude_code",
    "general": "default"  # Uses configured default_backend
}

# Keywords for task type classification
CLASSIFICATION_KEYWORDS = {
    "prototyping": [
        "create new", "implement from scratch", "scaffold",
        "prototype", "build new", "new feature", "new component"
    ],
    "refactoring": [
        "refactor", "restructure", "improve", "clean up",
        "optimize", "reorganize", "simplify"
    ],
    "testing": [
        "write tests", "test coverage", "unit test",
        "integration test", "add tests", "test suite"
    ],
    "documentation": [
        "document", "add docs", "write readme",
        "api docs", "documentation", "docstring"
    ]
}


class BackendRouter:
    """
    Routes tasks to optimal backends based on task type classification.

    The BackendRouter analyzes task descriptions and acceptance criteria to
    determine the task type, then applies routing rules to select the most
    appropriate backend for execution.

    Attributes:
        config: Full configuration dictionary
        _backend_cache: Cache of initialized backend instances
        _routing_rules: Merged default and custom routing rules
        _default_backend: Fallback backend type when routing fails

    Example:
        >>> router = BackendRouter(config)
        >>> backend = router.select_backend(task, context)
        >>> result = backend.execute(task.description, context.working_directory)
    """

    def __init__(self, config: dict):
        """
        Initialize BackendRouter with configuration.

        Args:
            config: Full configuration dictionary with gear3.backend_routing section

        Raises:
            ConfigurationError: If backend_routing configuration is invalid
        """
        self.config = config
        self._backend_cache: Dict[str, Backend] = {}

        # Load routing configuration
        routing_config = config.get('gear3', {}).get('backend_routing', {})

        # Set default backend (fallback for unknown task types)
        self._default_backend = routing_config.get('default_backend', 'claude_code')

        # Merge custom rules with defaults
        self._routing_rules = DEFAULT_ROUTING_RULES.copy()
        custom_rules = routing_config.get('rules', {})
        self._routing_rules.update(custom_rules)

        # Replace 'default' placeholder with actual default backend
        for task_type, backend_type in self._routing_rules.items():
            if backend_type == 'default':
                self._routing_rules[task_type] = self._default_backend

    def select_backend(self, task: Task, context: ExecutionContext) -> Backend:
        """
        Select optimal backend for task execution.

        Analyzes the task to determine its type, applies routing rules, and
        returns an initialized backend instance ready for execution.

        Args:
            task: Task to execute (with description and acceptance criteria)
            context: Execution context for task

        Returns:
            Backend instance ready for task execution

        Raises:
            ConfigurationError: If backend initialization fails due to missing config
            RuntimeError: If no suitable backend can be found or initialized

        Example:
            >>> task = Task(
            ...     id="task_001",
            ...     description="Refactor authentication module",
            ...     acceptance_criteria=["Improve code structure"]
            ... )
            >>> backend = router.select_backend(task, context)
            >>> # Returns ClaudeCodeBackend (matched "refactoring")
        """
        # Step 1: Classify task type
        task_type = self._classify_task(task)

        # Step 2: Apply routing rules to get backend type
        backend_type = self._apply_routing_rules(task_type)

        # Step 3: Initialize and return backend instance
        backend = self._initialize_backend(backend_type)

        # Log routing decision (simple console output)
        print(f"[BackendRouter] Task {task.id} ({task_type}) → {backend_type} backend")

        return backend

    def _classify_task(self, task: Task) -> str:
        """
        Classify task type from description and acceptance criteria.

        Scans task description and acceptance criteria for classification keywords
        to determine the task type. Supports explicit task type hints via metadata.

        Args:
            task: Task to classify

        Returns:
            Task type string: "prototyping", "refactoring", "testing",
            "documentation", or "general"

        Example:
            >>> task = Task(
            ...     id="task_001",
            ...     description="Write unit tests for auth module",
            ...     acceptance_criteria=["Test coverage > 80%"]
            ... )
            >>> router._classify_task(task)
            'testing'
        """
        # Check for explicit task type hint in metadata (optional)
        if hasattr(task, 'metadata') and task.metadata:
            explicit_type = task.metadata.get('task_type')
            if explicit_type in CLASSIFICATION_KEYWORDS:
                return explicit_type

        # Combine task description and acceptance criteria for analysis
        text_to_analyze = task.description.lower()
        if hasattr(task, 'acceptance_criteria'):
            for criterion in task.acceptance_criteria:
                text_to_analyze += " " + criterion.lower()

        # Check each task type's keywords
        for task_type, keywords in CLASSIFICATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_to_analyze:
                    return task_type

        # Default to general if no keywords matched
        return "general"

    def _apply_routing_rules(self, task_type: str) -> str:
        """
        Apply routing rules to determine backend type.

        Maps task type to backend type using configured routing rules.
        Falls back to default backend if task type not in rules.

        Args:
            task_type: Classified task type string

        Returns:
            Backend type string: "ccpm", "claude_code", "test_mock"

        Example:
            >>> router._apply_routing_rules("prototyping")
            'ccpm'
            >>> router._apply_routing_rules("unknown_type")
            'claude_code'  # Falls back to default
        """
        # Get backend type from routing rules
        backend_type = self._routing_rules.get(task_type, self._default_backend)

        return backend_type

    def _initialize_backend(self, backend_type: str) -> Backend:
        """
        Initialize and cache backend instance.

        Checks cache first, initializes new backend if not cached. Handles
        backend initialization failures gracefully with fallback to default.

        Args:
            backend_type: Backend type string ("ccpm", "claude_code", "test_mock")

        Returns:
            Initialized Backend instance

        Raises:
            ConfigurationError: If backend configuration is missing or invalid
            RuntimeError: If backend initialization fails and no fallback available

        Example:
            >>> backend = router._initialize_backend("ccpm")
            >>> # Returns cached CCPMBackend instance on subsequent calls
        """
        # Check cache first
        if backend_type in self._backend_cache:
            return self._backend_cache[backend_type]

        # Initialize new backend based on type
        try:
            backend = self._create_backend_instance(backend_type)

            # Cache for reuse
            self._backend_cache[backend_type] = backend

            return backend

        except Exception as e:
            # Log initialization failure (simple console output)
            print(f"[BackendRouter] ERROR: Failed to initialize {backend_type} backend: {e}")

            # Try fallback to default backend if not already trying default
            if backend_type != self._default_backend:
                print(f"[BackendRouter] Falling back to default backend: {self._default_backend}")
                return self._initialize_backend(self._default_backend)

            # No fallback available, raise error
            raise RuntimeError(
                f"Failed to initialize backend '{backend_type}' and no fallback available"
            ) from e

    def _create_backend_instance(self, backend_type: str) -> Backend:
        """
        Create new backend instance with configuration.

        Helper method that instantiates the appropriate backend class
        with configuration from config.yaml.

        Args:
            backend_type: Backend type string

        Returns:
            New Backend instance

        Raises:
            ConfigurationError: If backend config missing or invalid
            ValueError: If backend_type is unknown
        """
        # Get backend-specific configuration
        backend_config = self.config.get('backend', {}).get(backend_type, {})

        # Create appropriate backend instance
        if backend_type == "ccpm":
            api_key = backend_config.get('api_key')
            if not api_key:
                # For testing, allow missing API key with warning
                print("[BackendRouter] WARNING: CCPM backend missing api_key in configuration")
            return CCPMBackend(api_key=api_key)

        elif backend_type == "claude_code":
            return ClaudeCodeBackend()

        elif backend_type == "test_mock":
            return TestMockBackend()

        else:
            raise ValueError(
                f"Unknown backend type '{backend_type}'. "
                f"Supported types: ccpm, claude_code, test_mock"
            )
