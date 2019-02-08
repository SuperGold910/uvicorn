import contextlib
import sys
import tempfile
import threading
import time
import warnings
from functools import partialmethod

import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning
from uvicorn.config import Config
from uvicorn.main import Server

CERTIFICATE = b"""-----BEGIN CERTIFICATE-----
MIIEaDCCAtCgAwIBAgIRAPeU748qfVOTZJ7rj5DupbowDQYJKoZIhvcNAQELBQAw
fTEeMBwGA1UEChMVbWtjZXJ0IGRldmVsb3BtZW50IENBMSkwJwYDVQQLDCBmcmFp
cjUwMEBmcmFpcjUwMC1QcmVjaXNpb24tNTUyMDEwMC4GA1UEAwwnbWtjZXJ0IGZy
YWlyNTAwQGZyYWlyNTAwLVByZWNpc2lvbi01NTIwMB4XDTE5MDEwOTIwMzQ1N1oX
DTI5MDEwOTIwMzQ1N1owVDEnMCUGA1UEChMebWtjZXJ0IGRldmVsb3BtZW50IGNl
cnRpZmljYXRlMSkwJwYDVQQLDCBmcmFpcjUwMEBmcmFpcjUwMC1QcmVjaXNpb24t
NTUyMDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALahGo80UFExe7Iv
jPDulPP9Vu3mPVW/4XhrvmbwjHPSXk6nvK34kdDmGsS/UVgtSMH+sdMNFavkhyK/
b6PW5dPy+febfxlnaOkrZ5ptYx5IG1l/CNY/QDpQKGljW9YGQDV2t9apgKgT1/Ob
JIKf/rfd2o94iyxlrRnbXXidyMa1E6loo1AzzaN/g17dnblIL7ZCZtflgbsgnytw
UtwS92kTsvMHvuzM7Paz2M0xx+RNtQ2rq51fwph55gn7HLlBFEbkrMsfFj7hEquC
vJYvyrIEvaQLMyIOf+6/OgmrG9Z5ioMV4WAW9FLSuzXuuJruQc7FwQl4XIuE8d0M
jPjRfIcCAwEAAaOBizCBiDAOBgNVHQ8BAf8EBAMCBaAwEwYDVR0lBAwwCgYIKwYB
BQUHAwEwDAYDVR0TAQH/BAIwADAfBgNVHSMEGDAWgBTfMtd0Al3Ly09elEje6jyl
b3EQmjAyBgNVHREEKzApgglsb2NhbGhvc3SHBAAAAACHBH8AAAGHEAAAAAAAAAAA
AAAAAAAAAAEwDQYJKoZIhvcNAQELBQADggGBADLu7RSMVnUiRNyTqIM3aMmkUXmL
xSPB/SZRifqVwmp9R6ygAZWzC7Lw5BpX2WCde1jqWJZw1AjYbe4w5i8e9jaiUyYZ
eaLuQN7/+dyWeMIfFKx7thDxmati+OkSJSoojROA1v4NY7QAIM6ycfFkwTBRokPz
42srfR+XXrvdNmBRqjpvpr48SAn44uvqAkVr3kNgqs1xycPgjsFvMO7qZlU6w/ev
/7QFUgtyZS/Saa4s3yRXHZ++g3SpPinrzf8VqmovL/MoaqB/tYVjOA/1B3QAkli6
DIl+99eKANlqARXzMeXvgLpcg+1oAw0hYjFpCtqKhovhQzqN6KlAbmJ9JWTk35x8
81nOERZH5dh6JZoHzaaB/ZMEjWkmHnyi4bf5dXiPLzfXJslbQKHhnSt4nfZiSodS
brUVv/sux119zyUPe9iA6NNPFS/No1XOKcHrG19jiXTq/HIdJRoIrN6eRJDTRVK1
HyJ6uTvTJDu4ceBp2J1gz7R5opWbGyytDGg3Tw==
-----END CERTIFICATE-----
"""

PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC2oRqPNFBRMXuy
L4zw7pTz/Vbt5j1Vv+F4a75m8Ixz0l5Op7yt+JHQ5hrEv1FYLUjB/rHTDRWr5Ici
v2+j1uXT8vn3m38ZZ2jpK2eabWMeSBtZfwjWP0A6UChpY1vWBkA1drfWqYCoE9fz
mySCn/633dqPeIssZa0Z2114ncjGtROpaKNQM82jf4Ne3Z25SC+2QmbX5YG7IJ8r
cFLcEvdpE7LzB77szOz2s9jNMcfkTbUNq6udX8KYeeYJ+xy5QRRG5KzLHxY+4RKr
gryWL8qyBL2kCzMiDn/uvzoJqxvWeYqDFeFgFvRS0rs17ria7kHOxcEJeFyLhPHd
DIz40XyHAgMBAAECggEAZ1q7Liob/icz6r5wU/WhhIduB8qSEZI65qyLH7Sot+9p
Abh51jbjRsbChXAEeBOAppEeT+OKzTHSrH6MjrtSa+WJQ3DTuCvGupae1k1rl7qV
B8wV0zIOhjHQ/PuHAJOfCOK73ZclwXkhcLLvMaGcRLAgPaupj6GnGggEWPtqodDo
qBOcixT3/lMW5M1GklkqJqbD8g8qcx7SFBwORJjpwVX84Ynnursu0ZvTfK/CzZTk
D5t/UXyRV5Y5QBkzKIKzC0qUHv4eMIqkzlPBYx2PnAgrHokOm9/RS28yKT2DVPhw
t311ZM6+Z5AxfKamARWZbZdC8RG5Qo0ujLmgogNn2QKBgQDsqpwO+/yJlvF81nf9
0Ye5o0OdOdD5q1ra46PyhQ56hIC5cRZx3s3E9hUFDcot81qj9nMTpSGJL5J6GqAY
W7p3PbpYxT27MDjthgHHcZy7hu1M9no65ZAK1ElxVhKMgl89RQu/HQoa6Uh3qjbF
X0edTBTBJoGOYQ1lVaoL8s307QKBgQDFjGtEKubolZ0OqFb361fDcYs0RDKNlNxy
RIMM6Dhl0tgGHxNFuFNlLdjKyPEltfNaK0L0W3i3Ndf5sUlr2MuXYgO6RRqWo/D2
Tr2/jd6gsVKLK871WD7IS5SbCirCwuEsZQsZ2J2TWECoPqc8L3iZwyW6VGRkIW+K
o2Sl7P4cwwKBgQCnhAt6P7p82S6NInFEY28iYwGU5DuavUNN9BszqiKZbfh/SiCM
8RvM8jHmpeAZrkrWC7dgjF20cMvJSddP5n2RsUuZUeNj/7oLxfK0bSJ3SgXlmADk
d2EBiUmCw13VvuISyDCMUc25Rq5YpU6nXc2e9R8rqEnDscZ9l6kJVA+b8QKBgBAZ
coB6spjP4J3aMERCJMPj1AFtcWVCdXjGhpudrUL3HO3ayHpNHFbJlrpoB+cX3f5C
OlGpxru/optRzHcCkw0CSuV6TkFqmO+p2SLsT/Fuohh/eH1cNLmkFzdPa861jR5O
GcqAcc8ZSSOs/3oTMFPvqHp3+DqE0w9MY552Ivt7AoGATtJkMAg9M4U/5qIsCbRz
LplSCRvcarrg+czXW1re6y117rVjRHPCHgT//azsBDER0WpWSGv7XEnZwnz8U6Cn
FCXoiqqEJuD2wLwQlhb7QVXYTMdCwfPj5WV7ARJO1N4ty3g8x+jnTQCVoMpdhgxC
Sflxx+6bI4XMh0AsZhgtdW4=
-----END PRIVATE KEY-----
"""


@contextlib.contextmanager
def no_ssl_verification(session=requests.Session):
    old_request = session.request
    session.request = partialmethod(old_request, verify=False)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        yield

    session.request = old_request


@pytest.fixture(scope="function")
def create_certfile_and_keyfile(request):

    certfile = tempfile.NamedTemporaryFile(suffix=".pem")
    certfile.write(CERTIFICATE)
    certfile.seek(0)

    keyfile = tempfile.NamedTemporaryFile(suffix=".pem")
    keyfile.write(PRIVATE_KEY)
    keyfile.seek(0)

    def remove_files():
        certfile.close()
        keyfile.close()

    request.addfinalizer(remove_files)

    return certfile, keyfile


def test_run(create_certfile_and_keyfile):

    if sys.platform.startswith("win"):
        pytest.skip("Skipping SSL test on Windows for now :(")

    certfile, keyfile = create_certfile_and_keyfile

    class App:
        def __init__(self, scope):
            if scope["type"] != "http":
                raise Exception()

        async def __call__(self, receive, send):
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b"", "more_body": False})

    class CustomServer(Server):
        def install_signal_handlers(self):
            pass

    config = Config(
        app=App,
        loop="asyncio",
        limit_max_requests=1,
        ssl_keyfile=keyfile.name,
        ssl_certfile=certfile.name,
    )
    server = CustomServer(config=config)
    thread = threading.Thread(target=server.run)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    with no_ssl_verification():
        response = requests.get("https://127.0.0.1:8000")
    assert response.status_code == 204
    thread.join()
