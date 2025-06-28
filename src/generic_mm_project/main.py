#!/usr/bin/env python
import os, sys
from generic_mm_project.crew import GenericMMCrew

os.makedirs("output", exist_ok=True)

def run(question: str):
    result = GenericMMCrew().crew().kickoff(inputs={"query": question})
    print("\n=== RESPOSTA FINAL ===\n")
    print(result.raw)
    print("\nRelatório em: output/report.md")

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Resuma o Documento 1 e descreva sua imagem."
    run(q)
