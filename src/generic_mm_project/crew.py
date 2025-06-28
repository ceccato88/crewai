import yaml
import pathlib
from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from .upstash_vector_tool import UpstashVectorSearchTool

ROOT = pathlib.Path(__file__).parent
AGENTS = yaml.safe_load((ROOT/"config/agents.yaml").read_text())
TASKS  = yaml.safe_load((ROOT/"config/tasks.yaml").read_text())

search_tool = UpstashVectorSearchTool()

@CrewBase
class GenericMMCrew:
    agents: List[Agent]
    tasks:  List[Task]

    @agent
    def text_researcher(self):
        return Agent(config=AGENTS["text_researcher"], tools=[search_tool])

    @agent
    def image_analyst(self):
        return Agent(config=AGENTS["image_analyst"])

    @task
    def search_task(self):
        return Task(config=TASKS["search_task"])

    @task
    def visual_task(self):
        return Task(config=TASKS["visual_task"], output_file="output/report.md")

    @crew
    def crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
