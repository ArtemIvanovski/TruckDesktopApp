#!/usr/bin/env python3

"""
Простой лаунчер для тестирования алгоритма упаковки
"""

import sys


def main():
    print("Запуск тестера алгоритма упаковки...")
    print()

    try:
        from algorithm_tester import AlgorithmTester
        tester = AlgorithmTester()
        tester.run_test()
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что все файлы находятся в одной папке")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
