/* Host tests for backend_hint.h (#132). */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "backend_hint.h"

int main(void)
{
    /* The field log (#132): select() timeout, tls_error_code=0, handshake 0, errno 5. */
    assert(backend_classify(true, EIO, 0, 0) == BACKEND_FAIL_UNREACHABLE);
    assert(backend_classify(false, ETIMEDOUT, 0, 0) == BACKEND_FAIL_UNREACHABLE);
    assert(backend_classify(false, EHOSTUNREACH, 0, 0) == BACKEND_FAIL_UNREACHABLE);
    assert(backend_classify(false, ENETUNREACH, 0, 0) == BACKEND_FAIL_UNREACHABLE);
    assert(backend_classify(false, ECONNREFUSED, 0, 0) == BACKEND_FAIL_REFUSED);
    /* TCP connected, then mbedTLS failed (e.g. HTTPS client against a plain-HTTP server). */
    assert(backend_classify(false, 0, -0x7280, 0) == BACKEND_FAIL_TLS);
    assert(backend_classify(false, 0, 0, 401) == BACKEND_FAIL_REJECTED);
    assert(backend_classify(true, 0, 0, 403) == BACKEND_FAIL_REJECTED);     /* an answer beats a guess */
    assert(backend_classify(false, 0, 0, 0) == BACKEND_FAIL_OTHER);

    assert(strstr(backend_hint(BACKEND_FAIL_UNREACHABLE, true), "0.0.0.0"));
    assert(strstr(backend_hint(BACKEND_FAIL_UNREACHABLE, false), "firewall"));
    assert(strstr(backend_hint(BACKEND_FAIL_TLS, true), "HTTPS"));
    assert(strstr(backend_hint(BACKEND_FAIL_REFUSED, false), "BACKEND_PORT"));
    /* #159: a gateway refused for its class link must not be told only about its key */
    assert(strstr(backend_hint(BACKEND_FAIL_REJECTED, false), "device key"));
    assert(strstr(backend_hint(BACKEND_FAIL_REJECTED, false), "not linked to that class"));
    puts("PASS test_backend_hint");
    return 0;
}
