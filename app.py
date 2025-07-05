import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2 # For PostgreSQL connection

app = Flask(__name__)

# --- Database Configuration ---
# Get database connection details from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost') # 'localhost' for local testing without Docker Compose
DB_NAME = os.getenv('DB_NAME', 'todo_db')
DB_USER = os.getenv('DB_USER', 'todo_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'todo_password')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        # In a real app, you might want more robust error handling / retry logic
        return None

def init_db():
    """Initializes the database by creating the 'todos' table if it doesn't exist."""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    task TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            if conn: conn.close()
    else:
        print("Could not connect to database for initialization.")


@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()
    if not conn:
        # Handle cases where DB is not available
        return "Database connection error. Please check backend services.", 500

    if request.method == 'POST':
        task = request.form['task']
        if not task:
            return "Task cannot be empty!", 400
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO todos (task) VALUES (%s)", (task,))
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"Error inserting task: {e}")
            conn.rollback() # Rollback on error
        finally:
            conn.close()
        return redirect(url_for('index'))
    else: # GET request
        todos = []
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, task, created_at FROM todos ORDER BY created_at DESC;")
            todos = cur.fetchall()
            cur.close()
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            todos = [] # Return empty list on error
        finally:
            conn.close()
        return render_template('index.html', todos=todos)

# Run this only when app.py is executed directly (not imported)
if __name__ == '__main__':
    # Initialize DB table on startup (or you can do this via an init script in docker-entrypoint-initdb.d for DB)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
