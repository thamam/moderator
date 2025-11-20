"""
Tests for SequentialExecutor.

This module tests the SequentialExecutor implementation that provides
backward compatibility with Gear 2 mode while implementing the TaskExecutor
interface.
"""

import pytest
from src.execution.sequential_executor import SequentialExecutor
from src.execution.backend_router import BackendRouter
from src.execution.models import ExecutionContext, IsolationLevel, TaskResult
from src.backend import Backend, TestMockBackend
from src.models import Task


class TestSequentialExecutorInitialization:
    """Test SequentialExecutor initialization and validation."""

    def test_init_with_backend_router_only(self):
        """Test initialization with only BackendRouter."""
        config = {
            'backend': {'type': 'test_mock'},
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'test_mock',
                    'rules': {}
                }
            }
        }
        router = BackendRouter(config)

        executor = SequentialExecutor(backend_router=router)

        assert executor._backend_router is router
        assert executor._default_backend is None

    def test_init_with_default_backend_only(self):
        """Test initialization with only default backend."""
        backend = TestMockBackend()

        executor = SequentialExecutor(default_backend=backend)

        assert executor._backend_router is None
        assert executor._default_backend is backend

    def test_init_with_both_router_and_default(self):
        """Test initialization with both router and default backend."""
        config = {
            'backend': {'type': 'test_mock'},
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'test_mock',
                    'rules': {}
                }
            }
        }
        router = BackendRouter(config)
        backend = TestMockBackend()

        executor = SequentialExecutor(backend_router=router, default_backend=backend)

        assert executor._backend_router is router
        assert executor._default_backend is backend

    def test_init_with_neither_raises_error(self):
        """Test initialization without router or backend raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SequentialExecutor(backend_router=None, default_backend=None)

        assert "requires either backend_router or default_backend" in str(exc_info.value)


class TestSequentialExecutorExecution:
    """Test SequentialExecutor task execution."""

    def test_execute_single_task_with_default_backend(self):
        """Test executing a single task with default backend."""
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        task = Task(
            id="task_001",
            description="Test task",
            acceptance_criteria=["Works"]
        )
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks([task], context)

        assert len(results) == 1
        assert results[0].task.id == "task_001"
        assert results[0].success

    def test_execute_multiple_tasks_sequentially(self):
        """Test executing multiple tasks in sequential order."""
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=["AC1"]),
            Task(id="task_002", description="Task 2", acceptance_criteria=["AC2"]),
            Task(id="task_003", description="Task 3", acceptance_criteria=["AC3"])
        ]
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks(tasks, context)

        assert len(results) == 3
        assert results[0].task.id == "task_001"
        assert results[1].task.id == "task_002"
        assert results[2].task.id == "task_003"
        # TestMockBackend returns successful results
        assert all(r.success for r in results)

    def test_execute_tasks_with_backend_router(self):
        """Test executing tasks with BackendRouter selection."""
        config = {
            'backend': {'type': 'test_mock'},
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'test_mock',
                    'rules': {}
                }
            }
        }
        router = BackendRouter(config)
        executor = SequentialExecutor(backend_router=router)

        task = Task(
            id="task_001",
            description="Create new prototype feature",
            acceptance_criteria=["Works"]
        )
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks([task], context)

        assert len(results) == 1
        assert results[0].task.id == "task_001"

    def test_execute_empty_task_list(self):
        """Test executing empty task list returns empty results."""
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks([], context)

        assert results == []


class TestSequentialExecutorBackendSelection:
    """Test backend selection logic."""

    def test_backend_selection_prefers_router(self):
        """Test that router is used when both router and default are available."""
        config = {
            'backend': {'type': 'test_mock'},
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'test_mock',
                    'rules': {}
                }
            }
        }
        router = BackendRouter(config)
        default_backend = TestMockBackend()
        executor = SequentialExecutor(backend_router=router, default_backend=default_backend)

        task = Task(
            id="task_001",
            description="Test task",
            acceptance_criteria=["Works"]
        )
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        # _select_backend is private but we can test via execute_tasks
        results = executor.execute_tasks([task], context)

        # If router was used, task was routed successfully
        assert len(results) == 1
        assert results[0].success

    def test_backend_selection_uses_default_when_no_router(self):
        """Test that default backend is used when router unavailable."""
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        task = Task(
            id="task_001",
            description="Test task",
            acceptance_criteria=["Works"]
        )
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks([task], context)

        assert len(results) == 1
        assert results[0].success


class TestSequentialExecutorTaskOrder:
    """Test that tasks are executed in the correct order."""

    def test_tasks_executed_in_input_order(self):
        """Test that tasks are executed in the same order as input."""
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        tasks = [
            Task(id=f"task_{i:03d}", description=f"Task {i}", acceptance_criteria=["AC"])
            for i in range(10)
        ]
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks(tasks, context)

        # Check results are in same order as input
        assert len(results) == len(tasks)
        for i, result in enumerate(results):
            assert result.task.id == f"task_{i:03d}"

    def test_results_maintain_task_order_even_with_failures(self):
        """Test that results maintain order even if some tasks fail."""
        # Note: TestMockBackend doesn't fail, but we test the structure
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=["AC1"]),
            Task(id="task_002", description="Task 2", acceptance_criteria=["AC2"]),
            Task(id="task_003", description="Task 3", acceptance_criteria=["AC3"])
        ]
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks(tasks, context)

        # Results should be in same order as tasks
        assert [r.task.id for r in results] == ["task_001", "task_002", "task_003"]


class TestSequentialExecutorGear2Compatibility:
    """Test backward compatibility with Gear 2 mode."""

    def test_gear2_mode_sequential_execution(self):
        """Test Gear 2 mode: sequential execution with default backend."""
        # Gear 2 mode: No router, just default backend
        backend = TestMockBackend()
        executor = SequentialExecutor(default_backend=backend)

        tasks = [
            Task(id="task_001", description="Implement feature", acceptance_criteria=["Works"]),
            Task(id="task_002", description="Write tests", acceptance_criteria=["Tests pass"])
        ]
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks(tasks, context)

        # All tasks executed sequentially with same backend
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_gear3_mode_with_routing(self):
        """Test Gear 3 mode: sequential execution with backend routing."""
        config = {
            'backend': {'type': 'test_mock'},
            'gear3': {
                'backend_routing': {
                    'enabled': True,
                    'default_backend': 'test_mock',
                    'rules': {
                        'prototyping': 'test_mock',
                        'refactoring': 'test_mock'
                    }
                }
            }
        }
        router = BackendRouter(config)
        executor = SequentialExecutor(backend_router=router)

        tasks = [
            Task(id="task_001", description="Create new prototype", acceptance_criteria=["Works"]),
            Task(id="task_002", description="Refactor code", acceptance_criteria=["Clean"])
        ]
        context = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/test",
            git_branch="main",
            state_dir="/tmp/test_state",
            isolation_level=IsolationLevel.NONE
        )

        results = executor.execute_tasks(tasks, context)

        # Tasks routed to appropriate backends and executed
        assert len(results) == 2
        assert all(r.success for r in results)
