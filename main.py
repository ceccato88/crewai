
#!/usr/bin/env python
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generic_mm_project.main import run

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Resuma o Documento 1 e descreva sua imagem."
    run(q)
