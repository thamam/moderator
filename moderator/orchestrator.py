"""Main orchestration engine"""

import uuid
from typing import List
from .models import Task, ExecutionResult, BackendType
from .task_decomposer import TaskDecomposer
from .execution_router import ExecutionRouter
from .state_manager import StateManager
from .qa.analyzer import CodeAnalyzer
from .ever_thinker.improver import Improver


class Orchestrator:
    """Main orchestration engine"""

    def __init__(self, db_path: str = "moderator.db"):
        self.decomposer = TaskDecomposer()
        self.router = ExecutionRouter()
        self.state = StateManager(db_path)
        self.analyzer = CodeAnalyzer()
        self.improver = Improver()

    def execute(self, request: str) -> ExecutionResult:
        """Execute a request end-to-end"""

        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        print(f"\n{'='*60}")
        print(f"🚀 Moderator Execution: {execution_id}")
        print(f"{'='*60}")
        print(f"Request: {request}\n")

        # Create execution record
        self.state.create_execution(execution_id, request)

        try:
            # Step 1: Decompose request into tasks
            print("[Step 1] Decomposing request into tasks...")
            tasks = self.decomposer.decompose(request)
            print(f"  → Created {len(tasks)} task(s)\n")

            # For now, handle single task (no parallel execution yet)
            task = tasks[0]
            self.state.create_task(task, execution_id)

            # Step 2: Execute task
            print(f"[Step 2] Executing task: {task.id}")
            output = self.router.execute_task(task)
            print(f"  → Generated {len(output.files)} file(s)")
            print(f"  → Execution time: {output.execution_time:.2f}s\n")

            # Step 3: Analyze code
            print("[Step 3] Analyzing generated code...")
            issues = self.analyzer.analyze(output)
            print(f"  → Found {len(issues)} issue(s)")
            for issue in issues:
                print(f"    - [{issue.severity.value.upper()}] {issue.description}")
            print()

            # Step 4: Identify improvements
            print("[Step 4] Identifying improvements...")
            improvements = self.improver.identify_improvements(output, issues)
            print(f"  → Identified {len(improvements)} improvement(s)")
            for imp in improvements[:3]:  # Show top 3
                print(f"    - [Priority {imp.priority}] {imp.description}")
            print()

            # Create result
            result = ExecutionResult(
                task_id=task.id,
                execution_id=execution_id,
                backend=task.assigned_backend,
                output=output,
                issues=issues,
                improvements=improvements,
                status="success"
            )

            # Step 5: Save results
            print("[Step 5] Saving results to database...")
            self.state.save_result(result)
            self.state.update_execution_status(execution_id, "completed")
            print(f"  → Saved to database\n")

            # Summary
            print(f"{'='*60}")
            print("✅ Execution Summary:")
            print(f"{'='*60}")
            print(f"Execution ID: {execution_id}")
            print(f"Files Generated: {len(output.files)}")
            print(f"Issues Found: {len(issues)}")
            print(f"  - Critical: {sum(1 for i in issues if i.severity.value == 'critical')}")
            print(f"  - High: {sum(1 for i in issues if i.severity.value == 'high')}")
            print(f"  - Medium: {sum(1 for i in issues if i.severity.value == 'medium')}")
            print(f"Improvements Queued: {len(improvements)}")
            print(f"Status: {result.status}")
            print(f"{'='*60}\n")

            return result

        except Exception as e:
            print(f"\n❌ Execution failed: {str(e)}\n")
            self.state.update_execution_status(execution_id, "failed")
            raise
