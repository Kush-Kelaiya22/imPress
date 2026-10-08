idf_component_register(
    SRCS "main.c" "config.c" "spi_slave.c" "wifi_client.c" "ws_client.c" "ws_command.c" "student_set.c" "ota.c" "ota_logic.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_wifi esp_event esp_netif esp_http_client esp_app_format app_update mbedtls
        esp_websocket_client espressif__cjson protocol
        esp_timer esp_system efuse esp_adc heap
        esp_driver_gpio esp_driver_spi
)

# Backend over TLS with a site CA (#66): embed certs/backend_ca.pem
if(CONFIG_BACKEND_TLS_CA_FILE)
    target_add_binary_data(${COMPONENT_LIB} "${PROJECT_DIR}/certs/backend_ca.pem" TEXT)
endif()
