# src/main.py
import os
import sys
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from crew import MultimodalAnalysisCrew

os.makedirs("output", exist_ok=True)


async def run_async(question: str):
    """
    Executa a crew assincronamente com a pergunta fornecida.
    """
    result = await MultimodalAnalysisCrew().crew().kickoff_async(inputs={"query": question})
    return result

async def run_parallel_agents(question: str):
    """
    Executa análise textual e visual em paralelo, depois coordena.
    """
    crew_instance = MultimodalAnalysisCrew()
    
    # Cria crews separadas para execução paralela
    from crewai import Crew, Process
    
    # Crew só para análise textual
    text_crew = Crew(
        agents=[crew_instance.text_researcher()],
        tasks=[crew_instance.text_analysis_task()],
        process=Process.sequential,
        verbose=True
    )
    
    # Crew só para análise visual  
    visual_crew = Crew(
        agents=[crew_instance.image_analyst()],
        tasks=[crew_instance.visual_analysis_task()],
        process=Process.sequential,
        verbose=True
    )
    
    # Executa as duas crews em paralelo
    print("🚀 Executando análise textual e visual em paralelo...")
    text_result, visual_result = await asyncio.gather(
        text_crew.kickoff_async(inputs={"query": question}),
        visual_crew.kickoff_async(inputs={"query": question})
    )
    
    # Agora executa a coordenação com os resultados
    coordination_crew = Crew(
        agents=[crew_instance.coordinator()],
        tasks=[crew_instance.coordination_task()],
        process=Process.sequential,
        verbose=True
    )
    
    print("🔄 Integrando resultados...")
    final_result = await coordination_crew.kickoff_async(inputs={
        "query": question,
        "text_analysis": text_result.raw,
        "visual_analysis": visual_result.raw
    })
    
    return final_result


def run(question: str):
    """
    Executa a crew sincronamente com a pergunta fornecida.
    """
    result = MultimodalAnalysisCrew().crew().kickoff(inputs={"query": question})
    print("\n=== RESPOSTA FINAL ===\n")
    print(result.raw)
    print("\nRelatório em: output/multimodal_report.md")
    return result


async def run_multiple_queries_async(questions: list):
    """
    Executa múltiplas queries de forma assíncrona e paralela.
    """
    print(f"\n=== Executando {len(questions)} queries em paralelo ===")
    start_time = time.time()
    
    # Cria corrotinas para execução concorrente
    tasks = [
        MultimodalAnalysisCrew().crew().kickoff_async(inputs={"query": question}) 
        for question in questions
    ]
    
    # Aguarda todas as crews terminarem
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"\n=== Todas as queries completadas em {end_time - start_time:.2f} segundos ===")
    
    return results


async def demo_async_capabilities():
    """
    Demonstra as capacidades assíncronas do sistema multimodal.
    """
    print("=== DEMO: Capacidades Assíncronas CrewAI Multimodal ===\n")
    
    # Execução única assíncrona
    print("1. Execução Assíncrona Única:")
    start_time = time.time()
    result = await run_async("Resuma o Documento 1 e suas imagens")
    end_time = time.time()
    print(f"Tempo: {end_time - start_time:.2f}s")
    print("Resultado:", result.raw[:200] + "..." if len(result.raw) > 200 else result.raw)
    
    # Múltiplas execuções paralelas
    print("\n2. Múltiplas Execuções Paralelas:")
    questions = [
        "Resuma o Documento 1",
        "Analise as imagens do documento", 
        "Quais são os principais insights visuais?"
    ]
    
    results = await run_multiple_queries_async(questions)
    
    for i, (question, result) in enumerate(zip(questions, results), 1):
        print(f"\nQuery {i}: {question}")
        print(f"Resultado: {result.raw[:150]}..." if len(result.raw) > 150 else result.raw)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Resuma o Documento 1 e descreva sua imagem."
    
    # Verifica se deve executar demo assíncrono
    if "--async-demo" in sys.argv:
        asyncio.run(demo_async_capabilities())
    elif "--parallel" in sys.argv:
        async def main():
            result = await run_parallel_agents(q)
            print("\n=== RESPOSTA FINAL (PARALELO) ===\n")
            print(result.raw)
            print("\nRelatório em: output/multimodal_report.md")
        asyncio.run(main())
    elif "--async" in sys.argv:
        async def main():
            result = await run_async(q)
            print("\n=== RESPOSTA FINAL (ASYNC) ===\n")
            print(result.raw)
            print("\nRelatório em: output/multimodal_report.md")
        asyncio.run(main())
    else:
        # Execução síncrona padrão
        run(q)
