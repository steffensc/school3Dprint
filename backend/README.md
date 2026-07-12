```
curl -X POST http://192.168.178.90:8080/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "P-bHfPRFTO_4uvZh"}' \
     -c cookies.txt
```

```
curl -X POST http://192.168.178.90:8080/api/auth/change-password \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"current_password": "P-bHfPRFTO_4uvZh", "new_password": "abcd1234"}'
```

```
curl -X POST http://192.168.178.90:8080/api/auth/change-password \
     -H "Content-Type: application/json" \
     -H "X-CSRF-Token: j0KGWpg855Ws6XveNlXuYFV6Brl95rcNYeeyN3pQ3rw" \
     -b cookies.txt \
     -d '{"current_password": "P-bHfPRFTO_4uvZh", "new_password": "abcd1234"}'
```