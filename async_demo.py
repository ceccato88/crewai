#!/usr/bin/env python3
"""
Demo das Capacidades Assíncronas do Sistema Multimodal CrewAI

Este script demonstra como usar kickoff_async() para execução paralela
de múltiplas crews multimodais, comparando performance com execução sequencial.
"""

import os
import sys
import asyncio
import time
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from src.generic_mm_project.crew import GenericMMCrew

os.makedirs("output", exist_ok=True)


async def run_single_async(query: str, label: str = "") -> tuple:
    """
    Executa uma única crew assincronamente e mede o tempo.
    """
    start_time = time.time()
    result = await GenericMMCrew().crew().kickoff_async(inputs={"query": query})
    end_time = time.time()
    
    return {
        "label": label or query[:50],
        "query": query,
        "result": result.raw,
        "time": end_time - start_time
    }


def run_single_sync(query: str, label: str = "") -> tuple:
    """
    Executa uma única crew sincronamente e mede o tempo.
    """
    start_time = time.time()
    result = GenericMMCrew().crew().kickoff(inputs={"query": query})
    end_time = time.time()
    
    return {
        "label": label or query[:50],
        "query": query,
        "result": result.raw,
        "time": end_time - start_time
    }


async def parallel_execution_demo():
    """
    Demonstra execução paralela de múltiplas crews.
    """
    print("🚀 DEMO: Execução Paralela de Crews Multimodais\n")
    
    queries = [
        ("Analise os aspectos textuais do documento", "Análise Textual"),
        ("Foque na análise visual das imagens", "Análise Visual"),
        ("Extraia insights principais do documento", "Insights Gerais"),
        ("Compare dados quantitativos e qualitativos", "Comparação de Dados")
    ]
    
    print(f"📋 Executando {len(queries)} análises em paralelo...")
    
    # Execução paralela
    start_time = time.time()
    tasks = [
        run_single_async(query, label) 
        for query, label in queries
    ]
    results = await asyncio.gather(*tasks)
    parallel_time = time.time() - start_time
    
    print(f"✅ Execução paralela completada em {parallel_time:.2f}s\n")
    
    # Mostrar resultados
    for i, result in enumerate(results, 1):
        print(f"🔍 {result['label']}:")
        print(f"   Tempo: {result['time']:.2f}s")
        print(f"   Preview: {result['result'][:100]}...\n")
    
    return results, parallel_time


async def sequential_vs_parallel_comparison():
    """
    Compara execução sequencial vs paralela.
    """
    print("⚡ COMPARAÇÃO: Sequencial vs Paralelo\n")
    
    queries = [
        "Analise o documento principal",
        "Descreva as imagens encontradas",
        "Extraia conclusões gerais"
    ]
    
    # Execução Sequencial
    print("🔄 Executando sequencialmente...")
    seq_start = time.time()
    seq_results = []
    for i, query in enumerate(queries, 1):
        print(f"   Crew {i}/{len(queries)}...")
        result = await run_single_async(query, f"Seq-{i}")
        seq_results.append(result)
    seq_time = time.time() - seq_start
    
    print(f"✅ Sequencial: {seq_time:.2f}s\n")
    
    # Execução Paralela
    print("⚡ Executando em paralelo...")
    par_start = time.time()
    tasks = [run_single_async(query, f"Par-{i+1}") for i, query in enumerate(queries)]
    par_results = await asyncio.gather(*tasks)
    par_time = time.time() - par_start
    
    print(f"✅ Paralelo: {par_time:.2f}s\n")
    
    # Comparação
    speedup = seq_time / par_time if par_time > 0 else 0
    efficiency = (speedup / len(queries)) * 100
    
    print("📊 RESULTADOS:")
    print(f"   Tempo Sequencial: {seq_time:.2f}s")
    print(f"   Tempo Paralelo:   {par_time:.2f}s")
    print(f"   Speedup:          {speedup:.2f}x")
    print(f"   Eficiência:       {efficiency:.1f}%")
    print(f"   Redução de Tempo: {((seq_time - par_time) / seq_time * 100):.1f}%\n")
    
    return seq_results, par_results, speedup


async def mixed_workload_demo():
    """
    Demonstra workload misto com diferentes tipos de análise.
    """
    print("🔀 DEMO: Workload Misto (Texto + Visual + Coordenação)\n")
    
    workloads = [
        ("Foque apenas na análise textual detalhada", "📝 Texto Heavy"),
        ("Analise apenas os aspectos visuais das imagens", "🖼️ Visual Heavy"),
        ("Coordene texto e imagem para insights integrados", "🔗 Multimodal Heavy"),
        ("Faça uma análise rápida e superficial", "⚡ Light Task")
    ]
    
    print("🎯 Executando workloads variados simultaneamente...")
    
    start_time = time.time()
    tasks = [run_single_async(query, label) for query, label in workloads]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"✅ Todos os workloads completados em {total_time:.2f}s\n")
    
    # Análise de performance por tipo
    for result in results:
        task_type = result['label'].split()[1]
        print(f"{result['label']: <20} | {result['time']:.2f}s | {len(result['result'])} chars")
    
    print(f"\n🎪 Performance média: {sum(r['time'] for r in results) / len(results):.2f}s por task")
    
    return results


async def stress_test_demo():
    """
    Teste de stress com muitas crews simultâneas.
    """
    print("💪 STRESS TEST: Múltiplas Crews Simultâneas\n")
    
    num_crews = 6
    base_queries = [
        "Analise documento {i}",
        "Descreva imagens {i}",
        "Extraia insights {i}",
        "Compare dados {i}",
        "Sintetize informações {i}",
        "Gere relatório {i}"
    ]
    
    queries = [query.format(i=i+1) for i, query in enumerate(base_queries)]
    
    print(f"🚀 Lançando {num_crews} crews simultaneamente...")
    print("⚠️  Isso pode sobrecarregar a API - use com moderação!")
    
    start_time = time.time()
    
    # Execução em lotes para evitar sobrecarga
    batch_size = 3
    all_results = []
    
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]
        print(f"   Batch {i//batch_size + 1}: {len(batch)} crews...")
        
        tasks = [run_single_async(query, f"Stress-{i+j+1}") for j, query in enumerate(batch)]
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)
        
        # Pequena pausa entre batches
        await asyncio.sleep(1)
    
    total_time = time.time() - start_time
    
    print(f"✅ Stress test completado: {len(all_results)} crews em {total_time:.2f}s")
    print(f"📊 Throughput: {len(all_results) / total_time:.2f} crews/segundo\n")
    
    return all_results


async def main_demo():
    """
    Função principal que executa todas as demonstrações.
    """
    print("=" * 70)
    print("🎯 DEMO COMPLETO: CrewAI Multimodal Assíncrono")
    print("=" * 70)
    print()
    
    demos = [
        ("Execução Paralela Básica", parallel_execution_demo),
        ("Comparação Sequencial vs Paralelo", sequential_vs_parallel_comparison),
        ("Workload Misto", mixed_workload_demo),
        ("Stress Test (Opcional)", stress_test_demo)
    ]
    
    results = {}
    
    for name, demo_func in demos:
        print(f"\n{'=' * 50}")
        print(f"🎪 {name}")
        print(f"{'=' * 50}")
        
        try:
            if name == "Stress Test (Opcional)":
                choice = input("Executar stress test? (pode ser lento) [y/N]: ")
                if choice.lower() != 'y':
                    print("⏭️ Pulando stress test...")
                    continue
            
            result = await demo_func()
            results[name] = result
            print(f"✅ {name} concluído!")
            
        except Exception as e:
            print(f"❌ Erro em {name}: {e}")
    
    print(f"\n{'=' * 70}")
    print("🎉 DEMO CONCLUÍDO - CrewAI Assíncrono Multimodal Funcional!")
    print(f"{'=' * 70}")
    
    return results


if __name__ == "__main__":
    print("🚀 Iniciando Demo das Capacidades Assíncronas...")
    print("⚡ Pressione Ctrl+C para interromper a qualquer momento\n")
    
    try:
        # Verificar argumentos
        if len(sys.argv) > 1:
            if sys.argv[1] == "--quick":
                # Demo rápido
                asyncio.run(parallel_execution_demo())
            elif sys.argv[1] == "--compare":
                # Apenas comparação
                asyncio.run(sequential_vs_parallel_comparison())
            elif sys.argv[1] == "--stress":
                # Apenas stress test
                asyncio.run(stress_test_demo())
            else:
                print("Opções: --quick, --compare, --stress")
        else:
            # Demo completo
            asyncio.run(main_demo())
            
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")