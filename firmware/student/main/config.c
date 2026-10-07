/**
 * @file config.c
 * @brief Student module identity/profile — NVS persistence.
 *
 * The student ESP32 stores the full student profile the server pushed to it,
 * but transmits ONLY the enrollment number over the mesh. All identity data
 * lives in NVS so an OTA update never loses it.
 */

#include "config.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"

#include <string.h>

static const char *TAG = "student_cfg";

student_profile_t g_student;

static void _read_str(nvs_handle_t h, const char *key, char *buf, size_t sz)
{
    size_t len = 0;
    if (nvs_get_str(h, key, NULL, &len) == ESP_OK && len > 0 && len <= sz) {
        nvs_get_str(h, key, buf, &sz);
    }
}

/* ── Enrollment validation ──────────────────────────────────────────── */

static bool _is_enroll_char(char c)
{
    return (c >= '0' && c <= '9') ||
           (c >= 'A' && c <= 'Z') ||
           (c >= 'a' && c <= 'z');
}

/**
 * @brief Strict format check: exactly 10 alphanumeric chars (matches the
 *        backend's ENROLL_RE = "^[A-Za-z0-9]{10}$").
 */
static bool _enrollment_is_valid(const char *enroll)
{
    if (!enroll) {
        return false;
    }
    size_t n = strlen(enroll);
    if (n != 10) {
        return false;
    }
    for (size_t i = 0; i < n; i++) {
        if (!_is_enroll_char(enroll[i])) {
            return false;
        }
    }
    return true;
}

void init_student_profile(void)
{
    /* Defaults (safety net — replaced by NVS). */
    snprintf(g_student.enrollment, sizeof(g_student.enrollment), "%s", DEFAULT_ENROLLMENT);
    g_student.name[0]    = '\0';
    g_student.program[0] = '\0';
    g_student.email[0]   = '\0';
    g_student.provisioned = false;

    /* NVS must be initialized before we can read/write it. */
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        ESP_LOGE(TAG, "NVS open failed");
        return;
    }

    /* First boot: write the placeholder so provisioning can edit it later. */
    uint8_t init_flag = 0;
    if (nvs_get_u8(h, NVS_KEY_INIT, &init_flag) != ESP_OK || init_flag != 1) {
        ESP_LOGI(TAG, "First boot — writing placeholder enrollment");
        nvs_set_str(h, NVS_KEY_ENROLL, g_student.enrollment);
        nvs_set_u8(h, NVS_KEY_INIT, 1);
        nvs_commit(h);
    }

    _read_str(h, NVS_KEY_ENROLL, g_student.enrollment, sizeof(g_student.enrollment));
    _read_str(h, NVS_KEY_NAME, g_student.name, sizeof(g_student.name));
    _read_str(h, NVS_KEY_PROGRAM, g_student.program, sizeof(g_student.program));
    _read_str(h, NVS_KEY_EMAIL, g_student.email, sizeof(g_student.email));

    g_student.provisioned = (g_student.name[0] != '\0');
    nvs_close(h);

    ESP_LOGI(TAG, "Student identity: enrollment=%s profile=%s",
             g_student.enrollment,
             g_student.provisioned ? "cached" : "pending-server-push");
}

/**
 * @brief Update the locally cached profile (called when server pushes data).
 *        Enrollment may be updated here too, but NEVER transmitted as identity
 *        beyond the enrollment number itself.
 */
void student_update_profile(const char *enroll, const char *name,
                            const char *program, const char *email)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    if (enroll && enroll[0]) {
        /* Enrollment may only be set when it is valid AND it never overwrites
         * an already-provisioned identity (set-once semantics). */
        if (_enrollment_is_valid(enroll) &&
            strcmp(enroll, DEFAULT_ENROLLMENT) != 0) {
            if (!student_has_identity() ||
                strcmp(g_student.enrollment, enroll) == 0) {
                snprintf(g_student.enrollment, sizeof(g_student.enrollment),
                         "%s", enroll);
                nvs_set_str(h, NVS_KEY_ENROLL, g_student.enrollment);
            } else {
                ESP_LOGW(TAG, "Ignored server-pushed enrollment '%s' — "
                              "identity already set to '%s'",
                         enroll, g_student.enrollment);
            }
        } else {
            ESP_LOGW(TAG, "Ignored server-pushed invalid enrollment '%s'",
                     enroll);
        }
    }
    if (name && name[0]) {
        snprintf(g_student.name, sizeof(g_student.name), "%s", name);
        nvs_set_str(h, NVS_KEY_NAME, g_student.name);
    }
    if (program && program[0]) {
        snprintf(g_student.program, sizeof(g_student.program), "%s", program);
        nvs_set_str(h, NVS_KEY_PROGRAM, g_student.program);
    }
    if (email && email[0]) {
        snprintf(g_student.email, sizeof(g_student.email), "%s", email);
        nvs_set_str(h, NVS_KEY_EMAIL, g_student.email);
    }
    nvs_set_u8(h, NVS_KEY_INIT, 1);
    g_student.provisioned = true;
    nvs_commit(h);
    nvs_close(h);
    ESP_LOGI(TAG, "Profile updated: enrollment=%s", g_student.enrollment);
}

/* ── Identity lifecycle ─────────────────────────────────────────────── */

bool student_has_identity(void)
{
    return _enrollment_is_valid(g_student.enrollment) &&
           strcmp(g_student.enrollment, DEFAULT_ENROLLMENT) != 0;
}

int student_set_enrollment(const char *enroll)
{
    if (!_enrollment_is_valid(enroll) ||
        strcmp(enroll, DEFAULT_ENROLLMENT) == 0) {
        ESP_LOGW(TAG, "Rejected enrollment '%s' (need exactly 10 "
                      "alphanumeric chars)", enroll ? enroll : "(null)");
        return ESP_ERR_INVALID_ARG;
    }

    /* Set-once: never silently overwrite an already-provisioned identity. */
    if (student_has_identity() &&
        strcmp(g_student.enrollment, enroll) != 0) {
        ESP_LOGW(TAG, "Refusing to overwrite identity '%s' with '%s'",
                 g_student.enrollment, enroll);
        return ESP_ERR_INVALID_STATE;
    }

    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        ESP_LOGE(TAG, "NVS open failed in set_enrollment");
        return ESP_FAIL;
    }
    snprintf(g_student.enrollment, sizeof(g_student.enrollment), "%s", enroll);
    nvs_set_str(h, NVS_KEY_ENROLL, g_student.enrollment);
    nvs_commit(h);
    nvs_close(h);
    ESP_LOGI(TAG, "Identity set: enrollment=%s", g_student.enrollment);
    return ESP_OK;
}

void student_clear_enrollment(void)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        nvs_erase_key(h, NVS_KEY_ENROLL);
        nvs_commit(h);
        nvs_close(h);
    }
    g_student.enrollment[0] = '\0';
    ESP_LOGW(TAG, "Identity cleared — device will re-provision on next boot");
}