"""
Supervisor agent for human-like oversight of orchestration.

Provides automated assessment, risk evaluation, and suggestions
using an LLM to simulate experienced tech lead judgment.
"""

import os
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic

from .state import SupervisorDecision


# System prompts for different review types

SUPERVISOR_SYSTEM_PROMPT = """You are an experienced Tech Lead reviewing AI-generated code and project plans.

Your role is to provide human-like oversight by:
1. Evaluating quality and completeness
2. Identifying potential risks and issues
3. Suggesting improvements
4. Deciding whether to approve, reject, or escalate

You should be:
- Thorough but not overly critical
- Practical and focused on real issues
- Clear in your reasoning
- Decisive with confidence scores

Always respond with a JSON object containing:
{
    "decision": "approve" | "reject" | "suggest_improvement" | "escalate",
    "confidence": <0-100>,
    "reasoning": "<clear explanation>",
    "suggestions": ["<improvement 1>", "<improvement 2>", ...],
    "risks": ["<risk 1>", "<risk 2>", ...]
}"""


DECOMPOSITION_REVIEW_PROMPT = """Review this task decomposition for the following requirements:

REQUIREMENTS:
{requirements}

DECOMPOSED TASKS:
{tasks}

Evaluate:
1. Coverage: Do tasks cover all requirements?
2. Granularity: Are tasks appropriately sized (not too big or small)?
3. Dependencies: Are tasks in logical order?
4. Clarity: Are task descriptions clear and actionable?
5. Acceptance Criteria: Are criteria specific and testable?

Provide your assessment as JSON."""


PR_REVIEW_PROMPT = """Review this task completion:

TASK:
{task}

PR URL: {pr_url}
FILES GENERATED: {files}

Evaluate:
1. Completion: Does the work appear to satisfy acceptance criteria?
2. Quality: Are files properly structured and named?
3. Risks: Any obvious issues or concerns?

Note: You cannot see the actual code content, only metadata.
Be conservative with confidence if information is limited.

Provide your assessment as JSON."""


class SupervisorAgent:
    """
    LLM-powered supervisor for orchestration oversight.

    Provides automated review and decision-making to simulate
    human tech lead judgment.
    """

    def __init__(self, config: dict):
        """
        Initialize supervisor agent.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Get supervisor config
        langgraph_config = config.get("langgraph", {})
        supervisor_config = langgraph_config.get("supervisor", {})

        # Model configuration
        self.model_name = supervisor_config.get("model", "claude-sonnet-4-20250514")
        self.temperature = supervisor_config.get("temperature", 0.3)
        self.max_tokens = supervisor_config.get("max_tokens", 1024)

        # Thresholds
        self.confidence_threshold = supervisor_config.get("confidence_threshold", 70)

        # Initialize LLM
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.llm = ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=api_key,
            )
        else:
            self.llm = None

    def _call_llm(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Call the LLM and parse response as JSON.

        Args:
            system_prompt: System message content
            user_prompt: User message content

        Returns:
            Parsed JSON response
        """
        if not self.llm:
            # Fallback when no API key - auto-approve with low confidence
            return {
                "decision": "approve",
                "confidence": 50,
                "reasoning": "No API key configured - using default approval",
                "suggestions": [],
                "risks": ["Supervisor not configured - manual review recommended"],
            }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Parse JSON from response
        # Handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "decision": "escalate",
                "confidence": 30,
                "reasoning": f"Failed to parse LLM response: {content[:200]}",
                "suggestions": ["Manual review required"],
                "risks": ["LLM response parsing failed"],
            }

    def review_decomposition(
        self,
        requirements: str,
        tasks: list[dict],
    ) -> SupervisorDecision:
        """
        Review task decomposition quality.

        Args:
            requirements: Original requirements
            tasks: Decomposed tasks

        Returns:
            SupervisorDecision with assessment
        """
        # Format tasks for prompt
        tasks_str = "\n\n".join([
            f"Task {i+1}: {t['id']}\n"
            f"Description: {t['description']}\n"
            f"Acceptance Criteria:\n" + "\n".join(f"  - {c}" for c in t['acceptance_criteria'])
            for i, t in enumerate(tasks)
        ])

        prompt = DECOMPOSITION_REVIEW_PROMPT.format(
            requirements=requirements,
            tasks=tasks_str,
        )

        result = self._call_llm(SUPERVISOR_SYSTEM_PROMPT, prompt)

        return SupervisorDecision(
            decision=result.get("decision", "approve"),
            confidence=result.get("confidence", 50),
            reasoning=result.get("reasoning", "No reasoning provided"),
            suggestions=result.get("suggestions", []),
            risks_identified=result.get("risks", []),
        )

    def review_pr(
        self,
        task: dict,
        pr_url: str | None,
    ) -> SupervisorDecision:
        """
        Review PR/task completion.

        Args:
            task: Task that was executed
            pr_url: URL of the created PR

        Returns:
            SupervisorDecision with assessment
        """
        # Format task for prompt
        task_str = (
            f"ID: {task['id']}\n"
            f"Description: {task['description']}\n"
            f"Acceptance Criteria:\n" + "\n".join(f"  - {c}" for c in task['acceptance_criteria'])
        )

        prompt = PR_REVIEW_PROMPT.format(
            task=task_str,
            pr_url=pr_url or "Not created",
            files=", ".join(task.get('files_generated', [])) or "None",
        )

        result = self._call_llm(SUPERVISOR_SYSTEM_PROMPT, prompt)

        return SupervisorDecision(
            decision=result.get("decision", "approve"),
            confidence=result.get("confidence", 50),
            reasoning=result.get("reasoning", "No reasoning provided"),
            suggestions=result.get("suggestions", []),
            risks_identified=result.get("risks", []),
        )

    def assess_risk(
        self,
        context: dict,
    ) -> SupervisorDecision:
        """
        General risk assessment for any context.

        Args:
            context: Context information to assess

        Returns:
            SupervisorDecision with risk assessment
        """
        prompt = f"""Assess the risks in this context:

{json.dumps(context, indent=2)}

Focus on:
1. Security risks
2. Quality risks
3. Technical debt
4. Missing requirements

Provide your assessment as JSON."""

        result = self._call_llm(SUPERVISOR_SYSTEM_PROMPT, prompt)

        return SupervisorDecision(
            decision=result.get("decision", "approve"),
            confidence=result.get("confidence", 50),
            reasoning=result.get("reasoning", "No reasoning provided"),
            suggestions=result.get("suggestions", []),
            risks_identified=result.get("risks", []),
        )

    def suggest_improvements(
        self,
        tasks: list[dict],
        completed_work: dict,
    ) -> list[str]:
        """
        Suggest improvements for completed work.

        Args:
            tasks: All tasks in the project
            completed_work: Summary of completed work

        Returns:
            List of improvement suggestions
        """
        prompt = f"""Based on this completed work, suggest improvements:

TASKS COMPLETED:
{json.dumps(tasks, indent=2)}

WORK SUMMARY:
{json.dumps(completed_work, indent=2)}

Suggest 3-5 concrete improvements that would enhance:
1. Code quality
2. Test coverage
3. Documentation
4. Performance
5. Security

Return as JSON with "suggestions" array."""

        result = self._call_llm(SUPERVISOR_SYSTEM_PROMPT, prompt)

        return result.get("suggestions", [])


class MockSupervisorAgent(SupervisorAgent):
    """
    Mock supervisor for testing without LLM calls.
    """

    def __init__(self, config: dict):
        """Initialize mock supervisor."""
        self.config = config
        self.llm = None
        self.mock_responses: list[dict] = []
        self._response_index = 0

    def set_mock_responses(self, responses: list[dict]) -> None:
        """
        Set mock responses for testing.

        Args:
            responses: List of response dictionaries
        """
        self.mock_responses = responses
        self._response_index = 0

    def _call_llm(self, system_prompt: str, user_prompt: str) -> dict:
        """Return mock response instead of calling LLM."""
        if self.mock_responses and self._response_index < len(self.mock_responses):
            response = self.mock_responses[self._response_index]
            self._response_index += 1
            return response

        # Default mock response
        return {
            "decision": "approve",
            "confidence": 85,
            "reasoning": "Mock approval for testing",
            "suggestions": [],
            "risks": [],
        }
