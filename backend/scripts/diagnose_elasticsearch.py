import sys
import os

# Добавляем путь к backend в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.elasticsearch_utils import diagnose_index

def main():
    diagnose_index()

if __name__ == "__main__":
    main()
