# TLS runtime for catalog tools

The catalog itself is JSON data. The check scripts contact GitHub through
aiogithubapi/aiohttp and `data-v2.hacs.xyz` through Requests. The operator-only
R2 upload uses a separate AWS CLI environment; it is not needed to check or
contribute a catalog change.

## Verified Python environments

The hash-locked script environment was tested on CPython 3.10.21 with OpenSSL
3.5.8, Requests 2.34.2, urllib3 2.8.0 and aiohttp 3.14.4. The separate upload lock
was tested on CPython 3.12.14 with OpenSSL 3.5.8 and AWS CLI 1.46.1, including its
bundled botocore transport. Their normal verified TLS contexts retain security
level 2 and require TLS 1.2 or newer. OpenSSL security level 2 rejects RSA/DH keys
shorter than 2048 bits and elliptic-curve keys shorter than 224 bits, including
certificate-chain keys.

On 2026-10-08, isolated loopback handshakes against those installed context
factories rejected a trusted RSA-1024 server certificate and accepted RSA-2048
and ECDSA P-256 certificates. The fixture CA was added only to those temporary
test contexts; no operator trust store or credential was accessed. This evidence
does not establish the behavior of every OS build or custom endpoint.

Check the interpreter which will actually execute the scripts:

```sh
python3 - <<'PYTHON'
import ssl
import sys
context = ssl.create_default_context()
print(sys.version)
print(ssl.OPENSSL_VERSION)
print(context.security_level, context.minimum_version.name)
if context.security_level < 2 or context.minimum_version < ssl.TLSVersion.TLSv1_2:
    raise SystemExit("Unsupported TLS policy: upgrade the runtime")
PYTHON
```

Repeat the runtime check in the separate Python 3.12 AWS CLI environment before
an operator uses it. Retain certificate and hostname verification. Do not set
`verify=False`, pass `--no-verify-ssl`, or lower OpenSSL's security level to accept
an old endpoint. Repair the endpoint certificate or upgrade the runtime instead.

## Operator integration boundary

The inherited upload workflows also invoke system `curl` for cache purges and
contain operator-configured endpoints and signing credentials. The Python tests
above do not validate that curl executable, an R2 endpoint, an HTTPS proxy, a
custom CA, or the origin/strength of supplied signing credentials. Before enabling
those integrations, independently verify their actual TLS backend, minimum-key
policy, certificate/hostname checks and HTTPS endpoint. Keep operator uploads
unused when that environment has not been validated. Local tests need none of
these credentials or integrations.

The project does not implement a cipher or generate operator keys. Use credentials
issued by the service and handle their rotation through the service's supported
procedure. Do not paste them into a report or public configuration. These are
scoped runtime requirements, not a claim of FIPS certification or completion of
every cryptographic assessment criterion.

References: [OpenSSL security levels](https://docs.openssl.org/3.5/man3/SSL_CTX_set_security_level/)
and [Python SSL contexts](https://docs.python.org/3.10/library/ssl.html#ssl.SSLContext).
