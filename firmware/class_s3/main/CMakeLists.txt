idf_component_register(
    SRCS "main.c" "config.c" "mesh_master.c" "spi_master.c" "ota.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_wifi esp_event esp_netif esp_http_client esp_app_format
        esp_https_ota app_update esp_timer efuse protocol
        esp_driver_gpio esp_driver_spi
)
