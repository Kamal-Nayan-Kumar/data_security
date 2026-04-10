import sqlite3
import yaml
import hashlib

# 1. Hardcoded Secrets (Caught by Secret Scanner)
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
DB_PASSWORD = "super_secret_database_password_123"

def get_user_data(user_input):
    # 2. SQL Injection Vulnerability (Caught by Static Analyzer)
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # DANGEROUS: String concatenation in SQL query
    query = "SELECT * FROM users WHERE username = '" + user_input + "'"
    cursor.execute(query)
    
    # ALSO DANGEROUS: f-string SQL query
    f_query = f"SELECT * FROM users WHERE id = {user_input}"
    
    return cursor.fetchall()

def parse_config(yaml_string):
    # 3. Unsafe Deserialization (Caught by Static Analyzer)
    # yaml.load() is dangerous without SafeLoader
    config = yaml.load(yaml_string)
    return config

def hash_password(password):
    # 4. Weak Cryptography (Caught by Static Analyzer)
    # MD5 is cryptographically broken and should not be used for passwords
    return hashlib.md5(password.encode()).hexdigest()

def run_dynamic_math(math_expression):
    # 5. Arbitrary Code Execution (Caught by Static Analyzer)
    # eval() is extremely dangerous with user input
    return eval(math_expression)
