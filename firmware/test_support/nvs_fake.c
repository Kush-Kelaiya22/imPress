/* In-memory NVS fake for firmware host tests. Single namespace (the firmware
 * uses one per project), string and u8 values, open-handle leak counting.
 * Include path must provide the project's idf_stubs.h (types + prototypes). */
#include <stdlib.h>
#include <string.h>
#include "idf_stubs.h"
#include "nvs_fake.h"

#define MAX_KEYS 32
static struct { char key[16]; char str[160]; int is_u8; uint32_t num; int used; } s_kv[MAX_KEYS];
static int s_open;
static esp_err_t s_init_result;

void nvs_wipe(void) { memset(s_kv, 0, sizeof s_kv); s_open = 0; s_init_result = ESP_OK; }
void nvs_fail_next_init(int err) { s_init_result = err; }
int  nvs_open_handles(void) { return s_open; }

static int find(const char *k)
{
    for (int i = 0; i < MAX_KEYS; i++) if (s_kv[i].used && strcmp(s_kv[i].key, k) == 0) return i;
    return -1;
}
static int slot(const char *k)
{
    int i = find(k);
    if (i >= 0) return i;
    for (i = 0; i < MAX_KEYS; i++) if (!s_kv[i].used) { s_kv[i].used = 1; snprintf(s_kv[i].key, sizeof s_kv[i].key, "%s", k); return i; }
    abort();
}
const char *nvs_stored_str(const char *k) { int i = find(k); return (i < 0 || s_kv[i].is_u8) ? NULL : s_kv[i].str; }

esp_err_t nvs_flash_init(void) { esp_err_t r = s_init_result; s_init_result = ESP_OK; return r; }
esp_err_t nvs_flash_erase(void) { memset(s_kv, 0, sizeof s_kv); return ESP_OK; }
esp_err_t nvs_open(const char *ns, nvs_open_mode_t m, nvs_handle_t *h) { (void)ns; (void)m; *h = 1; s_open++; return ESP_OK; }
void      nvs_close(nvs_handle_t h) { (void)h; s_open--; }
esp_err_t nvs_commit(nvs_handle_t h) { (void)h; return ESP_OK; }
esp_err_t nvs_get_str(nvs_handle_t h, const char *k, char *out, size_t *len)
{
    (void)h;
    int i = find(k);
    if (i < 0 || s_kv[i].is_u8) return ESP_ERR_NVS_NOT_FOUND;
    size_t need = strlen(s_kv[i].str) + 1;
    if (!out) { *len = need; return ESP_OK; }
    if (*len < need) return ESP_ERR_INVALID_ARG;
    memcpy(out, s_kv[i].str, need);
    *len = need;
    return ESP_OK;
}
esp_err_t nvs_set_str(nvs_handle_t h, const char *k, const char *v) { (void)h; int i = slot(k); s_kv[i].is_u8 = 0; snprintf(s_kv[i].str, sizeof s_kv[i].str, "%s", v); return ESP_OK; }
#define NUM_GET(name, T) esp_err_t name(nvs_handle_t h, const char *k, T *o) \
    { (void)h; int i = find(k); if (i < 0 || !s_kv[i].is_u8) return ESP_ERR_NVS_NOT_FOUND; *o = (T)s_kv[i].num; return ESP_OK; }
#define NUM_SET(name, T) esp_err_t name(nvs_handle_t h, const char *k, T v) \
    { (void)h; int i = slot(k); s_kv[i].is_u8 = 1; s_kv[i].num = (uint32_t)v; return ESP_OK; }
NUM_GET(nvs_get_u8, uint8_t)   NUM_SET(nvs_set_u8, uint8_t)
NUM_GET(nvs_get_u16, uint16_t) NUM_SET(nvs_set_u16, uint16_t)
NUM_GET(nvs_get_i32, int32_t)  NUM_SET(nvs_set_i32, int32_t)
esp_err_t nvs_erase_key(nvs_handle_t h, const char *k) { (void)h; int i = find(k); if (i < 0) return ESP_ERR_NVS_NOT_FOUND; s_kv[i].used = 0; return ESP_OK; }
