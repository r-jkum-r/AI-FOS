# Security Best Practices

## SIP Security

### 1. Authentication
```ini
# pjsip.conf
[endpoint-template](!)
auth=auth-template
send_rpid=yes
trust_id_inbound=no

[auth-template]
type=auth
auth_type=userpass
username=secure_user
password=STRONG_PASSWORD_HERE
```

### 2. TLS Encryption
```ini
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/asterisk/keys/asterisk.crt
priv_key_file=/etc/asterisk/keys/asterisk.key
ca_list_file=/etc/asterisk/keys/ca.crt
```

### 3. Firewall Rules
```bash
# Allow SIP
iptables -A INPUT -p udp --dport 5060 -j ACCEPT
iptables -A INPUT -p tcp --dport 5061 -j ACCEPT

# Allow RTP range
iptables -A INPUT -p udp --dport 10000:10100 -j ACCEPT

# Rate limiting
iptables -A INPUT -p udp --dport 5060 -m limit --limit 25/min -j ACCEPT
```

## API Security

### 1. Rate Limiting
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/call/initiate")
@limiter.limit("10/minute")
async def initiate_call():
    pass
```

### 2. Authentication
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/call/initiate")
async def initiate_call(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify JWT token
    pass
```

## Data Protection

### 1. Redis Security
```bash
# redis.conf
requirepass YOUR_STRONG_PASSWORD
rename-command CONFIG ""
rename-command FLUSHALL ""
```

### 2. Encryption at Rest
- Encrypt Redis persistence files
- Use encrypted volumes for model storage

### 3. Encryption in Transit
- TLS for all WebSocket connections
- SRTP for RTP audio streams

## Compliance

- GDPR: Delete call recordings after retention period
- PCI-DSS: No credit card data in voice streams
- HIPAA: Encrypt PHI if handling medical calls

## Monitoring

```python
# Log security events
logger.warning(f"Failed auth attempt from {ip_address}")
logger.info(f"Call initiated: {call_id} from {caller}")
```
