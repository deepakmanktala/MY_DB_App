"""
Shared test helper: embedded throwaway certs for the test suite.

These are NOT the real Exasol credentials. They're a self-signed cert
pair used only by the local mock TLS servers in system_test.py,
failure_test.py, and aggressive_test.py. Embedding them as constants
means the tests run on any platform with no OpenSSL CLI dependency.

The cert is valid for ~10 years from its generation date in May 2026,
so it should outlast the practical lifetime of this repo.
"""
from __future__ import annotations

from pathlib import Path


# Self-signed cert + key for CN=localhost, valid 2026-2036.
# Generated with:
#   openssl req -x509 -nodes -newkey rsa:2048 \
#     -keyout key -out cert -days 3650 \
#     -subj "/CN=localhost" \
#     -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
TEST_SERVER_PEM = """\
-----BEGIN PRIVATE KEY-----
MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQC+yPR6eienHBW8
HORfLY08GhPfiyG2HTuHdsADNpQCxhL0XWEPwXZxLDNeScFe/QXHzL7SZdnmQk+Y
GLGeNcBVa5lryVdpOaTSQeU46hNA9qRwWJW1+jAZRNNH+JO4UTkaY4wViL4ZqkmR
r9wqguz6k99dCH6/kSgJGT2Cpquaewm+mHQ/2ouPP4SlWsZbDEXpKnaouTy7cjAf
XPpoc+WdQvm6vUbxQ7THq0nLNhb+KKmuzoL7cX5iYLJLZ5SokNqDyZabBB+ZyGf6
lVQmrqFNNUAnqgZFvvupSxJRi7rSwElj9SOG9YilsFivNq+9tg1Y0J57jwbhDbsp
wBqFEp87AgMBAAECgf8iR/mmCE0XufQt2QMwFv9JzWXExTtJffc0YCIgca4m0XCW
eDD4o8qki0yvpJEagFyJikC/jY2Z0lB7A/TmeMIWlz76HzOVtMXpAe4uS+EpyyfB
CCneiRYbdEKCrCfe9rlMBJcnR2rhMbgGdZMaEGyEmg2Iqf4cbfjDqcVjtI8hMqsf
YRpN8jjdoV33Gl/akaUl3l3dGDigHpemXtj2ikkVp8DNglY2r13HzcDYZ8uGtWD3
/0du5HfEuM0u9LnQHD7WRrm8rd2pQxuX9inZMvrHz/15I+vD6dtUeHt9WsgMfdR2
Ef9RiAgcTTqwflqv9T33oOClchEl4Hb6hC+6TmECgYEA4EgrS8vKks5TcQqivZ0L
x1NPfWuVsS+VCLP/jfbE0hAnrVSFzcpHAs5Ee/4xTV45+aayld0TfyXCxYPupweX
4xpI3MMrMKqZdNJJH4e1iV23/ZPT5Eeb1J/oQbruMOLdIArReHpOotEx/bQrMKaJ
hllOK/7+CeFSLj3IbCD3UcMCgYEA2cQS3EzVY4oXTYHXiPuI2TRjPYLra7Z9VTl8
C/qoIMUWouTB070gbJnYs+2GygFN0zgajB1praVM1wua0xbA/UU1P1WYXFg1zQD0
g5djyiK7wPzZgSBzKz83Vl/e0Aoxv99Cge3iKpr8dtsyNbxkkotcWrJroKcAfQfm
ETTX7SkCgYAu9235pWd6brKSjYOe6XA6AXw363uhazFubSMq+24j/zYP2g9bFOzh
7Yfx3z070muZmAr1zyHyElpDOmmTmMd5y1tOv6AfxNn12MNvUt/1MCcDdx18RHKh
iAr/GMIggqGDwEA1Vod5GQ267yvMOFO8Sp9QH0nbj8/B1zZNTmn8OQKBgCF6/9tX
BMfVB1gnSlgJNDUQ1OE0K7XXzNU5jVTaKNdA9gX9Xb+MKFwKG0MulbahFLIQwiQg
sYq9C19UrW0e5nUKGvGt20r3VO4741wH/pOpW2yEc3xi3NIdWgixnLQnnRZ+4N7R
ECC0y3QKp2GToXLWclCPdfSxOGYAvOKQWVJhAoGAFezKCy2b2ilmcQp4+64biWUC
JcFfKkY5EqlW8dZAmrrjS+2e3Q4WSTdKJX7RMqW0dpGaCPM7V5bGARpmzmeuqBc+
PUJJHcPlsOYrFVyAMwmRSKfRCwaE4HYnaUS1DCBhLGku61ZKqPdaAIcbgEWdQ/v+
ug7yyWoosUaT/FdE44w=
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIDJTCCAg2gAwIBAgIUPIITGnOlDcn8Dcf9LPxHtVFWoxkwDQYJKoZIhvcNAQEL
BQAwFDESMBAGA1UEAwwJbG9jYWxob3N0MB4XDTI2MDUwODA2MjAxNVoXDTM2MDUw
NTA2MjAxNVowFDESMBAGA1UEAwwJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEF
AAOCAQ8AMIIBCgKCAQEAvsj0enonpxwVvBzkXy2NPBoT34shth07h3bAAzaUAsYS
9F1hD8F2cSwzXknBXv0Fx8y+0mXZ5kJPmBixnjXAVWuZa8lXaTmk0kHlOOoTQPak
cFiVtfowGUTTR/iTuFE5GmOMFYi+GapJka/cKoLs+pPfXQh+v5EoCRk9gqarmnsJ
vph0P9qLjz+EpVrGWwxF6Sp2qLk8u3IwH1z6aHPlnUL5ur1G8UO0x6tJyzYW/iip
rs6C+3F+YmCyS2eUqJDag8mWmwQfmchn+pVUJq6hTTVAJ6oGRb77qUsSUYu60sBJ
Y/UjhvWIpbBYrzavvbYNWNCee48G4Q27KcAahRKfOwIDAQABo28wbTAdBgNVHQ4E
FgQUoSEdgcnyACufpLvr2xVtWRiR+vowHwYDVR0jBBgwFoAUoSEdgcnyACufpLvr
2xVtWRiR+vowDwYDVR0TAQH/BAUwAwEB/zAaBgNVHREEEzARgglsb2NhbGhvc3SH
BH8AAAEwDQYJKoZIhvcNAQELBQADggEBAGU6f4ANtE4P1q22N5XkOz19nWv4XIyE
q/ZcnDBz6bGkvl6BP60t5rgVIZ2L0pCIy8+Y0gJDdG22JQUOkrm9agNGcZyzf2QS
Tnu7UkoT25nWNIC6tHhAWgh90MAbCrlSmto3q2JXf+3naLTVzLzzZgjp8DE5jaqM
oiU7TtyocaeFZ8XlEVBt53Z/MZv2rXvOyest2PWFcBUwbuGLrrb4UI+qjdv+uNE0
6Ur9+imoykhxne3e5mEA2wqcpdxTmajSZCysBdxf3HG1wQkz+WfQnFMVMwDACkqp
NKEeSaQEXT2VI5iYBFjGI5Pt+vizGy6ihJGm99LZuEwa9RUzws9XIys=
-----END CERTIFICATE-----
"""


def write_test_server_pem(workdir: Path) -> tuple[Path, Path]:
    """
    Write the embedded test server cert+key pair to disk.

    Returns (cert_path, key_path). Both are the same combined PEM file
    because Python's ssl.load_cert_chain accepts a combined file.
    """
    pem_path = workdir / "test_server.pem"
    pem_path.write_text(TEST_SERVER_PEM)
    return pem_path, pem_path


def write_test_client_pem(workdir: Path) -> Path:
    """
    Write a test client PEM. The mock servers don't verify client
    identity, so we reuse the same cert+key as the server. This avoids
    needing a second cert and works on any platform.
    """
    pem_path = workdir / "test_client.pem"
    pem_path.write_text(TEST_SERVER_PEM)
    return pem_path
