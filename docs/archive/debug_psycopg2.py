try:
    import psycopg2
    print(f"Success: psycopg2 version {psycopg2.__version__}")
except ImportError as e:
    print(f"Error: {e}")
    import sys
    print(sys.path)
