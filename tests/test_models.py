"""
Test module for data models (ProjectPhase, ProjectState, Task).

Tests for Gear 3 Story 1.1: Extend Project State Model with Gear 3 Phases
"""

import pytest
from src.models import ProjectPhase, ProjectState, Task, TaskStatus, WorkLogEntry


class TestProjectPhase:
    """Tests for ProjectPhase enum including Gear 3 phases."""

    def test_all_gear_2_phases_exist(self):
        """Verify all Gear 1-2 phases remain unchanged (AC #2)."""
        assert hasattr(ProjectPhase, 'INITIALIZING')
        assert hasattr(ProjectPhase, 'DECOMPOSING')
        assert hasattr(ProjectPhase, 'EXECUTING')
        assert hasattr(ProjectPhase, 'COMPLETED')
        assert hasattr(ProjectPhase, 'FAILED')

        # Verify values unchanged
        assert ProjectPhase.INITIALIZING.value == "initializing"
        assert ProjectPhase.DECOMPOSING.value == "decomposing"
        assert ProjectPhase.EXECUTING.value == "executing"
        assert ProjectPhase.COMPLETED.value == "completed"
        assert ProjectPhase.FAILED.value == "failed"

    def test_gear_3_phases_exist(self):
        """Verify IMPROVEMENT and MONITORING phases exist (AC #1)."""
        assert hasattr(ProjectPhase, 'IMPROVEMENT')
        assert hasattr(ProjectPhase, 'MONITORING')
        assert ProjectPhase.IMPROVEMENT.value == "improvement"
        assert ProjectPhase.MONITORING.value == "monitoring"

    def test_phase_enum_values_are_strings(self):
        """Verify all phase values are strings for JSON serialization."""
        for phase in ProjectPhase:
            assert isinstance(phase.value, str)

    def test_phase_values_are_lowercase(self):
        """Verify phase values follow lowercase convention."""
        for phase in ProjectPhase:
            assert phase.value == phase.value.lower()


class TestProjectStateSerialization:
    """Tests for ProjectState serialization with Gear 3 phases."""

    def test_serialize_project_with_improvement_phase(self):
        """Test saving state with IMPROVEMENT phase (AC #4)."""
        project = ProjectState(
            project_id="test_gear3_001",
            requirements="Test Gear 3 requirements",
            phase=ProjectPhase.IMPROVEMENT
        )

        data = project.to_dict()

        assert data['phase'] == "improvement"
        assert data['project_id'] == "test_gear3_001"

    def test_serialize_project_with_monitoring_phase(self):
        """Test saving state with MONITORING phase (AC #4)."""
        project = ProjectState(
            project_id="test_gear3_002",
            requirements="Test monitoring",
            phase=ProjectPhase.MONITORING
        )

        data = project.to_dict()

        assert data['phase'] == "monitoring"

    def test_deserialize_old_gear_2_state_file(self):
        """Test loading Gear 2 state file without new phases (AC #4 - backward compat)."""
        # Simulate old Gear 2 state file JSON
        old_state_data = {
            'project_id': 'gear2_project',
            'requirements': 'Old gear 2 requirements',
            'phase': 'completed',  # Old phase value
            'tasks': [],
            'current_task_index': 0,
            'require_approval': True,
            'created_at': '2024-01-01T00:00:00',
            'completed_at': None
        }

        # Should load without errors
        project = ProjectState.from_dict(old_state_data)

        assert project.phase == ProjectPhase.COMPLETED
        assert project.project_id == 'gear2_project'

    def test_deserialize_gear_3_state_with_improvement(self):
        """Test loading Gear 3 state file with IMPROVEMENT phase (AC #4)."""
        gear3_state_data = {
            'project_id': 'gear3_project',
            'requirements': 'Gear 3 requirements',
            'phase': 'improvement',  # New phase value
            'tasks': [],
            'current_task_index': 0,
            'require_approval': True,
            'created_at': '2024-11-05T00:00:00',
            'completed_at': None
        }

        project = ProjectState.from_dict(gear3_state_data)

        assert project.phase == ProjectPhase.IMPROVEMENT
        assert project.project_id == 'gear3_project'

    def test_deserialize_gear_3_state_with_monitoring(self):
        """Test loading Gear 3 state file with MONITORING phase (AC #4)."""
        gear3_state_data = {
            'project_id': 'gear3_monitor',
            'requirements': 'Monitoring test',
            'phase': 'monitoring',  # New phase value
            'tasks': [],
            'current_task_index': 0,
            'require_approval': True,
            'created_at': '2024-11-05T00:00:00',
            'completed_at': None
        }

        project = ProjectState.from_dict(gear3_state_data)

        assert project.phase == ProjectPhase.MONITORING

    def test_round_trip_serialization_with_new_phases(self):
        """Test save → load → save cycle preserves new phases (AC #4)."""
        original = ProjectState(
            project_id="roundtrip_test",
            requirements="Test round-trip",
            phase=ProjectPhase.IMPROVEMENT
        )

        # Serialize
        data = original.to_dict()
        phase_value_original = data['phase']  # Store before from_dict modifies it

        # Deserialize (NOTE: from_dict modifies input dict in place)
        restored = ProjectState.from_dict(data)

        # Re-serialize
        data2 = restored.to_dict()

        # Compare original serialized value with re-serialized value
        assert phase_value_original == data2['phase']
        assert restored.phase == ProjectPhase.IMPROVEMENT
        assert data2['phase'] == "improvement"


class TestPhaseTransitions:
    """Tests for phase transition semantics (AC #3)."""

    def test_can_assign_improvement_phase(self):
        """Test COMPLETED → IMPROVEMENT transition works (AC #3)."""
        project = ProjectState(
            project_id="transition_test_1",
            requirements="Test transition",
            phase=ProjectPhase.COMPLETED
        )

        # Transition to IMPROVEMENT
        project.phase = ProjectPhase.IMPROVEMENT

        assert project.phase == ProjectPhase.IMPROVEMENT

    def test_can_assign_monitoring_phase(self):
        """Test IMPROVEMENT → MONITORING transition works (AC #3)."""
        project = ProjectState(
            project_id="transition_test_2",
            requirements="Test transition",
            phase=ProjectPhase.IMPROVEMENT
        )

        # Transition to MONITORING
        project.phase = ProjectPhase.MONITORING

        assert project.phase == ProjectPhase.MONITORING

    def test_can_cycle_completed_to_improvement(self):
        """Test improvement cycle: COMPLETED ↔ IMPROVEMENT (AC #3)."""
        project = ProjectState(
            project_id="cycle_test",
            requirements="Test improvement cycle",
            phase=ProjectPhase.COMPLETED
        )

        # Cycle: COMPLETED → IMPROVEMENT → COMPLETED
        project.phase = ProjectPhase.IMPROVEMENT
        assert project.phase == ProjectPhase.IMPROVEMENT

        project.phase = ProjectPhase.COMPLETED
        assert project.phase == ProjectPhase.COMPLETED

    def test_all_gear_2_phase_transitions_still_work(self):
        """Verify existing Gear 2 phase transitions unchanged (AC #2)."""
        project = ProjectState(
            project_id="gear2_flow",
            requirements="Test Gear 2 flow",
            phase=ProjectPhase.INITIALIZING
        )

        # Gear 2 flow: INITIALIZING → DECOMPOSING → EXECUTING → COMPLETED
        project.phase = ProjectPhase.DECOMPOSING
        assert project.phase == ProjectPhase.DECOMPOSING

        project.phase = ProjectPhase.EXECUTING
        assert project.phase == ProjectPhase.EXECUTING

        project.phase = ProjectPhase.COMPLETED
        assert project.phase == ProjectPhase.COMPLETED


class TestBackwardCompatibility:
    """Additional backward compatibility tests (AC #4)."""

    def test_old_state_missing_new_fields_loads_correctly(self):
        """Test old state files with minimal fields still load."""
        minimal_old_state = {
            'project_id': 'minimal',
            'requirements': 'minimal req',
            'phase': 'decomposing',
            'tasks': [],
            'current_task_index': 0,
            'created_at': '2024-01-01T00:00:00'
            # Missing: require_approval, completed_at (should use defaults)
        }

        project = ProjectState.from_dict(minimal_old_state)

        assert project.phase == ProjectPhase.DECOMPOSING
        assert project.require_approval is True  # Default value
        assert project.completed_at is None  # Default value


class TestWorkLogEntry:
    """Tests for WorkLogEntry with Gear 3 event_type field (Story 1.2)."""

    def test_work_log_entry_without_event_type(self):
        """Test WorkLogEntry without event_type (Gear 2 compatibility)."""
        entry = WorkLogEntry(
            level="INFO",
            component="test_component",
            action="test_action",
            details={"key": "value"}
        )

        assert entry.event_type is None  # Default value for backward compatibility
        assert entry.component == "test_component"
        assert entry.action == "test_action"

    def test_work_log_entry_with_event_type(self):
        """Test WorkLogEntry with event_type (Gear 3 structured logging)."""
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_cycle_start",
            details={"cycle_number": 1},
            event_type="improvement_cycle_start"
        )

        assert entry.event_type == "improvement_cycle_start"
        assert entry.component == "ever_thinker"
        assert entry.details["cycle_number"] == 1

    def test_work_log_entry_serialization_with_event_type(self):
        """Test to_dict() includes event_type field (Gear 3)."""
        entry = WorkLogEntry(
            level="INFO",
            component="qa_manager",
            action="qa_scan_complete",
            details={"issues_found": 5},
            event_type="qa_scan_complete"
        )

        entry_dict = entry.to_dict()

        assert "event_type" in entry_dict
        assert entry_dict["event_type"] == "qa_scan_complete"
        assert entry_dict["component"] == "qa_manager"
        assert entry_dict["details"]["issues_found"] == 5

    def test_work_log_entry_serialization_without_event_type(self):
        """Test to_dict() works without event_type (Gear 2 compatibility)."""
        entry = WorkLogEntry(
            level="INFO",
            component="test",
            action="test_action"
        )

        entry_dict = entry.to_dict()

        assert "event_type" in entry_dict  # Field exists
        assert entry_dict["event_type"] is None  # But value is None for Gear 2 logs
