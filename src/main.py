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
from crew import GenericMMCrew

os.makedirs("output", exist_ok=True)


async def run_async(question: str):
    """
    Executa a crew assincronamente com a pergunta fornecida.
    """
    result = await GenericMMCrew().crew().kickoff_async(inputs={"query": question})
    return result


def run(question: str):
    """
    Executa a crew sincronamente com a pergunta fornecida.
    """
    result = GenericMMCrew().crew().kickoff(inputs={"query": question})
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
        GenericMMCrew().crew().kickoff_async(inputs={"query": question}) 
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
