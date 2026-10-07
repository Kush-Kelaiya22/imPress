idf_component_register(
    SRCS "main.c" "config.c" "mesh_espnow.c" "display.c" "input.c" "enroll.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_wifi esp_event esp_netif esp_hw_support
        efuse protocol esp_driver_gpio esp_driver_i2c
)
