user_input = "' OR 1=1 --"

query = "SELECT * FROM users WHERE username = '" + user_input + "'"

print(query)