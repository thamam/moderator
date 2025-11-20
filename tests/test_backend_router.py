"""
Tests for BackendRouter intelligent backend selection.

Test Coverage:
- Task classification for all supported task types
- Routing rules (default and custom)
- Backend initialization and caching
- End-to-end backend selection
- Error handling for unavailable backends
- Configuration validation
"""

import pytest
from src.execution.backend_router import BackendRouter, DEFAULT_ROUTING_RULES, CLASSIFICATION_KEYWORDS
from src.models import Task
from src.execution.models import ExecutionContext, IsolationLevel
from src.backend import Backend, CCPMBackend, ClaudeCodeBackend, TestMockBackend
from src.config_validator import ConfigValidationError


class TestTaskClassification:
    """Tests for task type classification from description/ACs."""

    def create_sample_task(self, description: str, acceptance_criteria: list[str] = None):
        """Helper to create a task with given description and ACs."""
        return Task(
            id="task_001",
            description=description,
            acceptance_criteria=acceptance_criteria or []
        )

    def test_classify_prototyping_task(self):
        """Test that tasks with 'create new' keywords classify as prototyping."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task(
            "Create new API endpoint from scratch",
            ["Implement REST endpoint"]
        )

        task_type = router._classify_task(task)
        assert task_type == "prototyping"

    def test_classify_refactoring_task(self):
        """Test that tasks with 'refactor' keywords classify as refactoring."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task(
            "Refactor authentication module",
            ["Improve code structure", "Simplify complex functions"]
        )

        task_type = router._classify_task(task)
        assert task_type == "refactoring"

    def test_classify_testing_task(self):
        """Test that tasks with 'test' keywords classify as testing."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task(
            "Write unit tests for auth module",
            ["Test coverage > 80%", "Add integration tests"]
        )

        task_type = router._classify_task(task)
        assert task_type == "testing"

    def test_classify_documentation_task(self):
        """Test that tasks with 'document' keywords classify as documentation."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task(
            "Document API endpoints",
            ["Add docstrings", "Write README"]
        )

        task_type = router._classify_task(task)
        assert task_type == "documentation"

    def test_classify_general_task(self):
        """Test that tasks with no keywords default to 'general'."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task(
            "Review and update configuration",
            ["Update config.yaml"]
        )

        task_type = router._classify_task(task)
        assert task_type == "general"

    def test_classify_with_explicit_type(self):
        """Test that explicit task_type in metadata overrides classification."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        # Task description says "testing" but metadata says "prototyping"
        task = self.create_sample_task("Write unit tests for module")
        task.metadata = {'task_type': 'prototyping'}

        task_type = router._classify_task(task)
        assert task_type == "prototyping"

    def test_classify_multiple_keywords(self):
        """Test that first matching keyword determines type."""
        config = {
            'gear3': {'backend_routing': {'default_backend': 'claude_code'}},
            'backend': {}
        }
        router = BackendRouter(config)

        # Has both "create new" (prototyping) and "write tests" (testing)
        task = self.create_sample_task(
            "Create new module and write tests for it"
        )

        task_type = router._classify_task(task)
        # Should match first keyword found (order determined by CLASSIFICATION_KEYWORDS)
        assert task_type in ["prototyping", "testing"]


class TestRoutingRules:
    """Tests for routing rules engine."""

    def create_sample_config(self, custom_rules: dict = None):
        """Helper to create config with optional custom rules."""
        config = {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'claude_code',
                    'rules': custom_rules or {}
                }
            },
            'backend': {
                'ccpm': {'api_key': 'test-key'},
                'claude_code': {},
                'test_mock': {}
            }
        }
        return config

    def test_default_routing_rules(self):
        """Test that default rules route tasks correctly."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        # Test all default mappings
        assert router._apply_routing_rules("prototyping") == "ccpm"
        assert router._apply_routing_rules("refactoring") == "claude_code"
        assert router._apply_routing_rules("testing") == "claude_code"
        assert router._apply_routing_rules("documentation") == "claude_code"
        assert router._apply_routing_rules("general") == "claude_code"

    def test_custom_routing_rules(self):
        """Test that custom rules override default rules."""
        custom_rules = {
            "prototyping": "test_mock",  # Override default (ccpm)
            "testing": "ccpm"  # Override default (claude_code)
        }
        config = self.create_sample_config(custom_rules)
        router = BackendRouter(config)

        # Custom rules should override
        assert router._apply_routing_rules("prototyping") == "test_mock"
        assert router._apply_routing_rules("testing") == "ccpm"

        # Non-overridden rules should use defaults
        assert router._apply_routing_rules("refactoring") == "claude_code"

    def test_routing_rule_fallback(self):
        """Test that unknown task type falls back to default backend."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        # Unknown task type should use default
        backend_type = router._apply_routing_rules("unknown_type")
        assert backend_type == "claude_code"


class TestBackendInitialization:
    """Tests for backend initialization and caching."""

    def create_sample_config(self):
        """Helper to create valid config."""
        return {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'claude_code'
                }
            },
            'backend': {
                'ccpm': {'api_key': 'test-key'},
                'claude_code': {},
                'test_mock': {}
            }
        }

    def test_backend_initialization_ccpm(self):
        """Test initializing CCPMBackend with config."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        backend = router._initialize_backend("ccpm")
        assert isinstance(backend, CCPMBackend)

    def test_backend_initialization_claude_code(self):
        """Test initializing ClaudeCodeBackend."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        backend = router._initialize_backend("claude_code")
        assert isinstance(backend, ClaudeCodeBackend)

    def test_backend_initialization_test_mock(self):
        """Test initializing TestMockBackend."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        backend = router._initialize_backend("test_mock")
        assert isinstance(backend, TestMockBackend)

    def test_backend_caching(self):
        """Test that backends are cached and reused."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        # Initialize same backend twice
        backend1 = router._initialize_backend("ccpm")
        backend2 = router._initialize_backend("ccpm")

        # Should return same cached instance
        assert backend1 is backend2

    def test_lazy_initialization(self):
        """Test that backends are only created when requested."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        # Cache should be empty initially
        assert len(router._backend_cache) == 0

        # Initialize one backend
        router._initialize_backend("ccpm")

        # Only requested backend should be in cache
        assert len(router._backend_cache) == 1
        assert "ccpm" in router._backend_cache
        assert "claude_code" not in router._backend_cache

    def test_backend_initialization_failure(self):
        """Test handling of backend initialization failure."""
        config = {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'test_mock'
                }
            },
            'backend': {}
        }
        router = BackendRouter(config)

        # Initializing unknown backend should fallback to default
        backend = router._initialize_backend("unknown_backend")
        assert isinstance(backend, TestMockBackend)


class TestBackendSelection:
    """Tests for end-to-end backend selection."""

    def create_sample_task(self, description: str):
        """Helper to create a task."""
        return Task(
            id="task_001",
            description=description,
            acceptance_criteria=[]
        )

    def create_sample_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_001",
            working_directory="/tmp/project",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

    def create_sample_config(self):
        """Helper to create valid config."""
        return {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'claude_code',
                    'rules': {
                        'prototyping': 'ccpm'
                    }
                }
            },
            'backend': {
                'ccpm': {'api_key': 'test-key'},
                'claude_code': {},
                'test_mock': {}
            }
        }

    def test_select_backend_end_to_end(self):
        """Test complete flow from task to backend instance."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        task = self.create_sample_task("Create new API endpoint")
        context = self.create_sample_context()

        backend = router.select_backend(task, context)

        # Should classify as prototyping and route to CCPM
        assert isinstance(backend, CCPMBackend)

    def test_select_backend_with_context(self):
        """Test that context is passed correctly (though not currently used)."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        task = self.create_sample_task("Refactor auth module")
        context = self.create_sample_context()

        backend = router.select_backend(task, context)

        # Should classify as refactoring and route to Claude Code
        assert isinstance(backend, ClaudeCodeBackend)

    def test_select_backend_returns_cached_instance(self):
        """Test that select_backend reuses cached backends."""
        config = self.create_sample_config()
        router = BackendRouter(config)

        task1 = self.create_sample_task("Create new endpoint")
        task2 = self.create_sample_task("Implement from scratch")
        context = self.create_sample_context()

        # Both tasks should route to same backend type
        backend1 = router.select_backend(task1, context)
        backend2 = router.select_backend(task2, context)

        # Should return cached instance
        assert backend1 is backend2


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def create_sample_task(self, description: str):
        """Helper to create a task."""
        return Task(
            id="task_001",
            description=description,
            acceptance_criteria=[]
        )

    def create_sample_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_001",
            working_directory="/tmp/project",
            git_branch="main",
            state_dir="/tmp/state"
        )

    def test_fallback_to_default_backend(self):
        """Test fallback to default when preferred backend unavailable."""
        config = {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'test_mock',
                    'rules': {
                        'prototyping': 'invalid_backend'
                    }
                }
            },
            'backend': {
                'test_mock': {}
            }
        }
        router = BackendRouter(config)

        task = self.create_sample_task("Create new feature")
        context = self.create_sample_context()

        # Should fallback to test_mock
        backend = router.select_backend(task, context)
        assert isinstance(backend, TestMockBackend)

    def test_missing_default_backend_config(self):
        """Test handling of missing backend configuration."""
        config = {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'missing_backend'
                }
            },
            'backend': {}
        }
        router = BackendRouter(config)

        task = self.create_sample_task("General task")
        context = self.create_sample_context()

        # Should raise RuntimeError when no fallback available
        with pytest.raises(RuntimeError, match="Failed to initialize backend"):
            router.select_backend(task, context)


class TestConfigurationValidation:
    """Tests for configuration validation."""

    def test_valid_configuration_loads(self):
        """Test that valid configuration is accepted."""
        config = {
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'claude_code',
                    'rules': {
                        'prototyping': 'ccpm'
                    }
                }
            },
            'backend': {
                'ccpm': {'api_key': 'test'},
                'claude_code': {}
            }
        }

        # Should not raise exception
        router = BackendRouter(config)
        assert router._default_backend == 'claude_code'

    def test_missing_backend_routing_section(self):
        """Test that missing backend_routing section uses safe defaults."""
        config = {
            'gear3': {},
            'backend': {}
        }

        # Should use default values without error
        router = BackendRouter(config)
        assert router._default_backend == 'claude_code'

    def test_custom_rules_override_defaults(self):
        """Test that custom rules properly override default rules."""
        config = {
            'gear3': {
                'backend_routing': {
                    'default_backend': 'test_mock',
                    'rules': {
                        'prototyping': 'test_mock',
                        'refactoring': 'test_mock'
                    }
                }
            },
            'backend': {
                'test_mock': {}
            }
        }

        router = BackendRouter(config)

        # Custom rules should override defaults
        assert router._routing_rules['prototyping'] == 'test_mock'
        assert router._routing_rules['refactoring'] == 'test_mock'

        # Non-overridden rules should use defaults
        assert router._routing_rules['testing'] == DEFAULT_ROUTING_RULES['testing']
