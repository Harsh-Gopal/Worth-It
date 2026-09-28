import psycopg2
conn = psycopg2.connect("postgres://postgres:postgres@localhost:5432/postgres")
cur = conn.cursor()
try:
    cur.execute("CREATE TABLE test (id int); CREATE TABLE test2 (id int);")
    conn.commit()
    print("Success!")
except Exception as e:
    print(e)
