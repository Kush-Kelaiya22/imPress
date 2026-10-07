/**
 * @file input.c
 * @brief Button input with debounce and interrupt handling.
 */

#include "input.h"
#include "config.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "driver/gpio.h"

static const char *TAG = "input";

static const gpio_num_t s_buttons[] = {
    PIN_BTN_1, PIN_BTN_2, PIN_BTN_3, PIN_BTN_4, PIN_BTN_CONFIRM
};
#define NUM_BUTTONS (sizeof(s_buttons) / sizeof(s_buttons[0]))

static input_cb_t s_callback;
static QueueHandle_t s_gpio_queue;
static int s_last_button = -1;
static int s_active_count = 0;
/* Which s_buttons[] entries got a valid gpio_config. Pins the flash bus owns
 * (GPIO6-11 on QIO-flash ESP32) fail config — touching them deadlocks the
 * flash lock. Never read or IRQ a pin slot that isn't active. */
static bool s_buttons_active[NUM_BUTTONS];

static void IRAM_ATTR gpio_isr_handler(void *arg)
{
    int btn = (int)(intptr_t)arg;
    xQueueSendFromISR(s_gpio_queue, &btn, NULL);
}

static void input_task(void *arg)
{
    int btn;
    while (1) {
        if (xQueueReceive(s_gpio_queue, &btn, pdMS_TO_TICKS(100))) {
            /* Debounce: wait and re-check */
            vTaskDelay(pdMS_TO_TICKS(DEBOUNCE_MS));

            if (btn >= 0 && btn < (int)NUM_BUTTONS && s_buttons_active[btn] &&
                gpio_get_level(s_buttons[btn]) == 0) {  /* active low */
                s_last_button = btn;
                ESP_LOGI(TAG, "Button %d pressed", btn);
                if (s_callback) {
                    s_callback(btn);
                }
            }
        }
    }
}

int input_init(input_cb_t callback)
{
    s_callback = callback;
    s_gpio_queue = xQueueCreate(16, sizeof(int));

    /* Configure button GPIOs */
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_NEGEDGE,  /* interrupt on falling edge */
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
    };

    esp_err_t isr_err = gpio_install_isr_service(0);
    if (isr_err != ESP_OK && isr_err != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "gpio_install_isr_service: %s", esp_err_to_name(isr_err));
    }

    for (int i = 0; i < (int)NUM_BUTTONS; i++) {
        io_conf.pin_bit_mask = (1ULL << s_buttons[i]);
        /* A pin claimed by another peripheral (e.g. the QIO flash bus on some
         * ESP32 modules) makes gpio_config block; skip it instead of wedging
         * app_main's boot path. */
        if (gpio_config(&io_conf) != ESP_OK ||
            gpio_isr_handler_add(s_buttons[i], gpio_isr_handler,
                                 (void *)(intptr_t)i) != ESP_OK) {
            ESP_LOGW(TAG, "Button %d (GPIO%d) unavailable — skipping", i, s_buttons[i]);
            continue;
        }
        s_buttons_active[i] = true;
        s_active_count++;
    }

#if STUDENT_HAS_LED
    gpio_reset_pin(PIN_LED_STATUS);
    gpio_set_direction(PIN_LED_STATUS, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_LED_STATUS, 1);  /* LED on = initialized */
#endif

    xTaskCreate(input_task, "input_task", 2048, NULL, 5, NULL);
    ESP_LOGI(TAG, "Input initialized, %d/%d buttons active",
             s_active_count, (int)NUM_BUTTONS);
    return 0;
}

bool input_is_button_pressed(int button)
{
    if (button < 0 || button >= (int)NUM_BUTTONS) return false;
    if (!s_buttons_active[button]) return false;   /* flash-claimed pin reads low — don't trust */
    return gpio_get_level(s_buttons[button]) == 0;
}

int input_get_last_button(void)
{
    return s_last_button;
}
