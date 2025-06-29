# src/generic_mm_project/crew.py
from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from services.vector.upstash_vector_tool import UpstashVectorSearchTool

@CrewBase
class MultimodalAnalysisCrew:
    """Crew for multimodal document analysis combining text and visual insights"""
    
    agents: List[Agent]
    tasks: List[Task]
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def text_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['text_researcher'],
            tools=[UpstashVectorSearchTool()],
            verbose=True
        )

    @agent
    def image_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['image_analyst'],
            tools=[UpstashVectorSearchTool()],
            verbose=True
        )

    @agent
    def coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['coordinator'],
            verbose=True
        )

    @task
    def text_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['text_analysis_task']
        )

    @task
    def visual_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['visual_analysis_task']
        )

    @task
    def coordination_task(self) -> Task:
        return Task(
            config=self.tasks_config['coordination_task'],
            context=[self.text_analysis_task(), self.visual_analysis_task()],
            output_file="output/multimodal_report.md"
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.text_researcher(), self.image_analyst(), self.coordinator()],
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
