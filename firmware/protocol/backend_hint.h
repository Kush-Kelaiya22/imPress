/**
 * @file backend_hint.h
 * @brief Turn a failed connection to the backend into an actionable message (#132).
 *
 * "esp-tls: select() timeout" says nothing about the cause. What matters to
 * the person at the classroom is which of three things went wrong:
 *   - the backend's port could not be reached at all (wrong address, server
 *     bound to 127.0.0.1, firewall): the TCP connect timed out or was refused;
 *   - TCP worked but TLS failed (plain-HTTP server, wrong port, certificate
 *     that doesn't match the host or the embedded CA);
 *   - the backend answered but refused the device (bad key).
 *
 * Pure C, host-tested (test_host/test_backend_hint.c). Inputs are what both
 * esp_http_client and esp_websocket_client expose after a failure.
 */
#pragma once

#include <errno.h>
#include <stdbool.h>

typedef enum {
    BACKEND_FAIL_UNREACHABLE,   /* TCP connect timed out / host or network unreachable */
    BACKEND_FAIL_REFUSED,       /* nothing listens on that port */
    BACKEND_FAIL_TLS,           /* TCP up, TLS handshake failed */
    BACKEND_FAIL_REJECTED,      /* HTTP/WS answered 401/403 */
    BACKEND_FAIL_OTHER,
} backend_fail_t;

/**
 * @param connect_timed_out  ESP_ERR_ESP_TLS_CONNECTION_TIMEOUT / "select() timeout" seen
 * @param sock_errno         esp_transport sock errno, or 0
 * @param tls_stack_err      mbedTLS error from the handshake, or 0
 * @param http_status        status/handshake code the server sent, or 0
 */
static inline backend_fail_t backend_classify(bool connect_timed_out, int sock_errno,
                                              int tls_stack_err, int http_status)
{
    if (http_status == 401 || http_status == 403) return BACKEND_FAIL_REJECTED;
    if (sock_errno == ECONNREFUSED) return BACKEND_FAIL_REFUSED;
    if (connect_timed_out || sock_errno == ETIMEDOUT || sock_errno == EHOSTUNREACH
        || sock_errno == ENETUNREACH) {
        return BACKEND_FAIL_UNREACHABLE;
    }
    if (tls_stack_err != 0) return BACKEND_FAIL_TLS;
    return BACKEND_FAIL_OTHER;
}

/** One line for the serial log; `tls` = this image uses https/wss. */
static inline const char *backend_hint(backend_fail_t f, bool tls)
{
    switch (f) {
    case BACKEND_FAIL_UNREACHABLE:
        return "backend unreachable: is it running and listening on the network "
               "(IMPRESS_HOST=0.0.0.0, not 127.0.0.1), and is the port open in the "
               "host firewall? Check from a laptop on the same Wi-Fi: curl <url>/health";
    case BACKEND_FAIL_REFUSED:
        return "connection refused: nothing listens on that port (check BACKEND_PORT "
               "and IMPRESS_PORT)";
    case BACKEND_FAIL_TLS:
        return tls ? "TLS handshake failed: the server must serve HTTPS on this port with a "
                     "certificate for this host name (or IP) from the trusted CA"
                   : "unexpected TLS error on a plain-HTTP image";
    case BACKEND_FAIL_REJECTED:
        /* HTTP: the key. Class WebSocket: the key, or the gateway is not linked
         * to the class it joins (#121, #159). */
        return "backend refused the device: a wrong or reset device key (re-register with the "
               "site key), or, for the class WebSocket, this gateway is not linked to that class "
               "(Admin > Modules > link, or CONFIG_CLASS_SESSION_ID)";
    default:
        return "see the error above";
    }
}
