/* Host tests for class_c6/main/config.c — runtime config = Kconfig defaults
 * overlaid by NVS, so gateways can be re-provisioned without reflashing.
 * Run: ./run_config.sh */
#include <string.h>
#include "config.h"
#include "nvs_fake.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define RUN(t) do { nvs_wipe(); memset(&g_cfg, 0, sizeof g_cfg); t(); printf("ok   %s\n", #t); } while (0)

static void test_first_boot_uses_and_persists_kconfig(void)
{
    init_nvs_config();
    CHECK(strcmp(g_cfg.wifi_ssid, CONFIG_WIFI_SSID) == 0);
    CHECK(strcmp(g_cfg.backend_host, CONFIG_BACKEND_HOST) == 0 && g_cfg.backend_port == CONFIG_BACKEND_PORT);
    CHECK(g_cfg.class_id == 0 && g_cfg.batch_max == CONFIG_BATCH_MAX_SIZE);
    CHECK(strcmp(nvs_stored_str(NVS_KEY_API_KEY), CONFIG_DEVICE_API_KEY) == 0);   /* persisted for later edits */
    CHECK(nvs_open_handles() == 0);
}

static void test_nvs_values_override_kconfig_on_later_boots(void)
{
    init_nvs_config();                                   /* first boot */
    nvs_handle_t h;
    nvs_open("impress", NVS_READWRITE, &h);
    nvs_set_str(h, NVS_KEY_WIFI_SSID, "school-wifi");
    nvs_set_str(h, NVS_KEY_BACKEND_H, "10.0.0.5");
    nvs_set_u16(h, NVS_KEY_BACKEND_P, 8443);
    nvs_set_str(h, NVS_KEY_API_KEY, "per-site-key");
    nvs_close(h);
    memset(&g_cfg, 0, sizeof g_cfg);
    init_nvs_config();                                   /* reboot */
    CHECK(strcmp(g_cfg.wifi_ssid, "school-wifi") == 0);
    CHECK(strcmp(g_cfg.backend_host, "10.0.0.5") == 0 && g_cfg.backend_port == 8443);
    CHECK(strcmp(g_cfg.api_key, "per-site-key") == 0);
    CHECK(strcmp(g_cfg.wifi_pass, CONFIG_WIFI_PASSWORD) == 0);     /* untouched keys keep defaults */
}

static void test_bad_overrides_fall_back_to_defaults(void)
{
    init_nvs_config();
    nvs_handle_t h;
    nvs_open("impress", NVS_READWRITE, &h);
    nvs_set_str(h, NVS_KEY_BACKEND_H, "");                           /* empty string */
    nvs_set_u16(h, NVS_KEY_BACKEND_P, 0);                            /* port 0 */
    char huge[150];
    memset(huge, 'h', sizeof huge - 1);
    huge[sizeof huge - 1] = '\0';
    nvs_set_str(h, NVS_KEY_WIFI_SSID, huge);                         /* longer than the 33-byte field */
    nvs_close(h);
    init_nvs_config();
    CHECK(strcmp(g_cfg.backend_host, CONFIG_BACKEND_HOST) == 0);
    CHECK(g_cfg.backend_port == CONFIG_BACKEND_PORT);
    CHECK(strcmp(g_cfg.wifi_ssid, CONFIG_WIFI_SSID) == 0);           /* ignored, no overflow */
}

static void test_backend_assigned_class_id_survives_reboot(void)
{
    init_nvs_config();
    nvs_save_class_id(42);
    CHECK(g_cfg.class_id == 42);
    memset(&g_cfg, 0, sizeof g_cfg);
    init_nvs_config();
    CHECK(g_cfg.class_id == 42);
    CHECK(nvs_open_handles() == 0);
}

static void test_boot_count_increments_once_per_boot(void)
{
    init_nvs_config();
    CHECK(g_cfg.boot_count == 1);
    for (int i = 0; i < 2; i++) {
        memset(&g_cfg, 0, sizeof g_cfg);
        init_nvs_config();
    }
    CHECK(g_cfg.boot_count == 3);                        /* persisted, so it survives reboots (#39) */
    CHECK(nvs_open_handles() == 0);
}

static void test_nvs_layout_change_is_recovered(void)
{
    nvs_fail_next_init(ESP_ERR_NVS_NO_FREE_PAGES);
    init_nvs_config();                                   /* erase + re-init, then defaults */
    CHECK(strcmp(g_cfg.wifi_ssid, CONFIG_WIFI_SSID) == 0);
}

int main(void)
{
    RUN(test_first_boot_uses_and_persists_kconfig);
    RUN(test_nvs_values_override_kconfig_on_later_boots);
    RUN(test_bad_overrides_fall_back_to_defaults);
    RUN(test_backend_assigned_class_id_survives_reboot);
    RUN(test_boot_count_increments_once_per_boot);
    RUN(test_nvs_layout_change_is_recovered);
    puts("PASS test_c6_config");
    return 0;
}
