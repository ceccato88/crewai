# src/generic_mm_project/crew.py
import os
import pathlib
from typing import List

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from services.vector.upstash_vector_tool import UpstashVectorSearchTool

ROOT = pathlib.Path(__file__).parent
AGENTS = yaml.safe_load((ROOT / "config/agents.yaml").read_text())
TASKS = yaml.safe_load((ROOT / "config/tasks.yaml").read_text())

search_tool = UpstashVectorSearchTool()


@CrewBase
class GenericMMCrew:
    agents: List[Agent]
    tasks: List[Task]

    @agent
    def text_researcher(self):
        agent_config = AGENTS["text_researcher"].copy()
        agent_config["tools"] = [search_tool]
        return Agent(**agent_config)

    @agent
    def image_analyst(self):
        return Agent(**AGENTS["image_analyst"])

    @agent
    def coordinator(self):
        return Agent(**AGENTS["coordinator"])

    @task
    def text_analysis_task(self):
        task_config = TASKS["text_analysis_task"].copy()
        task_config["agent"] = self.text_researcher()
        return Task(**task_config)

    @task
    def visual_analysis_task(self):
        task_config = TASKS["visual_analysis_task"].copy()
        task_config["agent"] = self.image_analyst()
        return Task(**task_config)

    @task
    def coordination_task(self):
        task_config = TASKS["coordination_task"].copy()
        task_config["agent"] = self.coordinator()
        task_config["context"] = [self.text_analysis_task(), self.visual_analysis_task()]
        task_config["output_file"] = "output/multimodal_report.md"
        return Task(**task_config)

    @crew
    def crew(self):
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.hierarchical,
            manager_llm="openai/gpt-4o",
            verbose=True
        )
