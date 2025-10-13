"""Main orchestration engine"""

import uuid
import re
from typing import List
from .models import Task, ExecutionResult, BackendType, Issue, Severity, CodeOutput
from .task_decomposer import TaskDecomposer
from .execution_router import ExecutionRouter
from .state_manager import StateManager
from .qa.analyzer import CodeAnalyzer
from .ever_thinker.improver import Improver
from .agents.registry import AgentRegistry


class Orchestrator:
    """Main orchestration engine with agent support"""

    def __init__(self, db_path: str = "moderator.db", agents_config: str = "agents.yaml"):
        self.decomposer = TaskDecomposer()
        self.router = ExecutionRouter()
        self.state = StateManager(db_path)
        self.analyzer = CodeAnalyzer()
        self.improver = Improver()

        # Agent registry for multi-agent improvement
        try:
            self.agents = AgentRegistry(agents_config)
        except FileNotFoundError:
            print(f"⚠️  Warning: agents.yaml not found. Agent-based improvement disabled.")
            self.agents = None

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

    def improve_iteratively(self, result: ExecutionResult, max_rounds: int = 5) -> List[ExecutionResult]:
        """Iterative improvement using specialized agents"""

        if not self.agents:
            print("⚠️  Agent system not available. Skipping iterative improvement.")
            return [result]

        rounds = [result]
        current_files = result.output.files

        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*60}")
            print(f"[Round {round_num}] Improvement Pass")
            print(f"{'='*60}\n")

            # Step 1: Multi-agent review
            print("[1] Running multi-agent review...")
            all_issues = []

            # General review
            try:
                review_prompt = "Review this code for issues. List specific problems with severity and location."
                general_issues = self.agents.reviewer.execute(review_prompt, context=current_files)
                all_issues.extend(self._parse_issues(general_issues, "general"))
            except Exception as e:
                print(f"  ⚠️  General review failed: {e}")

            # Security review
            try:
                security_issues = self.agents.security_reviewer.execute(
                    "Perform security audit. Find vulnerabilities.",
                    context=current_files
                )
                all_issues.extend(self._parse_issues(security_issues, "security"))
            except Exception as e:
                print(f"  ⚠️  Security review failed: {e}")

            # Performance review
            try:
                perf_issues = self.agents.performance_reviewer.execute(
                    "Analyze performance. Find bottlenecks and inefficiencies.",
                    context=current_files
                )
                all_issues.extend(self._parse_issues(perf_issues, "performance"))
            except Exception as e:
                print(f"  ⚠️  Performance review failed: {e}")

            print(f"  → Found {len(all_issues)} issue(s) across all reviewers\n")

            if not all_issues:
                print("  ✅ No issues found - code quality acceptable")
                break

            # Step 2: Prioritize issues
            print("[2] Prioritizing issues...")
            high_priority = [i for i in all_issues if i.severity.value in ['critical', 'high']]
            print(f"  → {len(high_priority)} high-priority issues to fix\n")

            if not high_priority:
                print("  → Only low-priority issues remain")
                break

            # Step 3: Fix issues
            print("[3] Applying fixes...")
            fixes_applied = 0

            for issue in high_priority[:3]:  # Fix top 3 per round
                fix_prompt = f"""Fix this issue:

Issue: {issue.description}
Location: {issue.location}
Severity: {issue.severity.value}

Make minimal changes to fix only this specific issue.
Return the complete modified files."""

                try:
                    fixed_files = self.agents.fixer.execute_with_files(
                        fix_prompt,
                        current_files
                    )
                    current_files = fixed_files
                    fixes_applied += 1
                    print(f"  ✓ Fixed: {issue.description}")
                except Exception as e:
                    print(f"  ✗ Failed to fix: {issue.description} - {e}")

            print(f"\n  → Applied {fixes_applied} fixes\n")

            # Step 4: Create round result
            new_result = ExecutionResult(
                task_id=result.task_id,
                execution_id=f"{result.execution_id}_r{round_num}",
                backend=result.backend,
                output=CodeOutput(
                    files=current_files,
                    metadata={"round": round_num, "fixes_applied": fixes_applied},
                    backend=result.backend.value if result.backend else "unknown"
                ),
                issues=all_issues,
                improvements=[],
                status="improved"
            )

            rounds.append(new_result)

            # Progress report
            print(f"[Progress] Round {round_num} complete:")
            print(f"  Issues: {len(rounds[-2].issues)} → {len(all_issues)}")
            print(f"  High-priority: {len([i for i in all_issues if i.severity.value in ['critical', 'high']])}")

        print(f"\n{'='*60}")
        print(f"✅ Improvement complete after {len(rounds)-1} rounds")
        print(f"{'='*60}\n")

        return rounds

    def _parse_issues(self, agent_response: str, category: str) -> List[Issue]:
        """Parse agent's issue list into Issue objects"""
        issues = []

        # Simple regex-based parsing
        # Look for patterns like: "CRITICAL: description" or "- HIGH: description (file.py:10)"
        lines = agent_response.split('\n')

        for line in lines:
            line = line.strip()

            # Try to match severity markers
            severity_match = re.search(r'\b(CRITICAL|HIGH|MEDIUM|LOW|INFO)\b', line, re.IGNORECASE)
            if not severity_match:
                continue

            severity_str = severity_match.group(1).lower()
            try:
                severity = Severity[severity_str.upper()]
            except KeyError:
                continue

            # Extract location if present (file.py:line)
            location_match = re.search(r'([a-zA-Z0-9_./]+\.py):?(\d+)?', line)
            location = location_match.group(0) if location_match else "unknown"

            # Extract description (everything after the severity marker)
            desc_start = severity_match.end()
            description = line[desc_start:].strip(' :-')

            if description:
                issues.append(Issue(
                    severity=severity,
                    category=category,
                    location=location,
                    description=description[:200],  # Truncate long descriptions
                    auto_fixable=severity.value in ['high', 'medium'],
                    confidence=0.8
                ))

        return issues
