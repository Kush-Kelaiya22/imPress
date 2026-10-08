/**
 * @file backend_tls.h
 * @brief How the hub and the gateway reach the backend: HTTP or HTTPS (#66).
 *
 * Kconfig (each project's "Backend Server" menu):
 *   BACKEND_TLS            https:// and wss:// instead of http:// and ws://
 *   BACKEND_TLS_CRT_BUNDLE trust public CAs (ESP-IDF certificate bundle),
 *                          e.g. a Let's Encrypt certificate on the server
 *   BACKEND_TLS_CA_FILE    trust only the CA in firmware/<project>/certs/backend_ca.pem
 *                          (a private CA or the server's self-signed certificate),
 *                          embedded in the image at build time
 *
 * Every esp_http_client / esp_websocket_client config that talks to the
 * backend goes through BACKEND_TLS_APPLY(); test_device_tls.py checks that.
 * ESP-IDF only (not part of the host-tested protocol code).
 */
#pragma once

#include "sdkconfig.h"

#if CONFIG_BACKEND_TLS
#  define BACKEND_HTTP_SCHEME "https"
#  define BACKEND_WS_SCHEME   "wss"
#  if CONFIG_BACKEND_TLS_CA_FILE
extern const char backend_ca_pem_start[] asm("_binary_backend_ca_pem_start");
#    define BACKEND_TLS_APPLY(cfg) do { (cfg).cert_pem = backend_ca_pem_start; } while (0)
#  else
#    include "esp_crt_bundle.h"
#    define BACKEND_TLS_APPLY(cfg) do { (cfg).crt_bundle_attach = esp_crt_bundle_attach; } while (0)
#  endif
#else
#  define BACKEND_HTTP_SCHEME "http"
#  define BACKEND_WS_SCHEME   "ws"
#  define BACKEND_TLS_APPLY(cfg) do { (void)(cfg); } while (0)
#endif
