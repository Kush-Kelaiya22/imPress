idf_component_register(
    SRCS "main.c" "config.c" "spi_slave.c" "wifi_client.c" "ws_client.c" "ws_command.c" "student_set.c" "ota.c" "ota_logic.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_wifi esp_event esp_netif esp_http_client esp-tls esp_app_format app_update mbedtls spi_flash
        esp_websocket_client espressif__cjson protocol
        esp_timer esp_system efuse esp_adc heap
        esp_driver_gpio esp_driver_spi
)

# Backend over TLS with a site CA (#66): embed certs/backend_ca.pem
if(CONFIG_BACKEND_TLS_CA_FILE)
    target_add_binary_data(${COMPONENT_LIB} "${PROJECT_DIR}/certs/backend_ca.pem" TEXT)
endif()

# A TLS image on the backend's default plain-HTTP port is almost always a
# misconfiguration: the server only serves HTTPS when started with a
# certificate, usually on 443 (#132).
if(CONFIG_BACKEND_TLS AND CONFIG_BACKEND_PORT EQUAL 8000)
    message(WARNING "BACKEND_TLS is on but BACKEND_PORT is 8000: the backend serves HTTPS there only "
                    "when started with IMPRESS_SSL_CERTFILE/KEYFILE. See docs/guides/troubleshooting.md.")
endif()
