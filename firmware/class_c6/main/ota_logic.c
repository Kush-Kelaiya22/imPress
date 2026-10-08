#include "ota_logic.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

static bool is_semver(const char *v)
{
    int dots = 0;
    if (!v || !*v) return false;
    for (const char *p = v; *p; p++) {
        if (*p == '.') {
            if (p == v || p[1] == '\0' || p[-1] == '.') return false;
            dots++;
        } else if (!isdigit((unsigned char)*p)) {
            return false;
        }
    }
    return dots == 2;
}

static bool is_hex64(const char *s)
{
    if (!s || strlen(s) != 64) return false;
    for (const char *p = s; *p; p++) {
        if (!isxdigit((unsigned char)*p)) return false;
    }
    return true;
}

int ota_parse_check(const char *json, ota_offer_t *out)
{
    memset(out, 0, sizeof(*out));
    cJSON *root = json ? cJSON_Parse(json) : NULL;
    if (!cJSON_IsObject(root)) {
        cJSON_Delete(root);
        return -1;
    }
    int rc = 0;
    out->available = cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(root, "update_available"));
    if (out->available) {
        const cJSON *v = cJSON_GetObjectItemCaseSensitive(root, "version");
        const cJSON *h = cJSON_GetObjectItemCaseSensitive(root, "sha256");
        const cJSON *n = cJSON_GetObjectItemCaseSensitive(root, "size");
        const cJSON *d = cJSON_GetObjectItemCaseSensitive(root, "deployment_id");
        if (cJSON_IsString(v) && is_semver(v->valuestring) && strlen(v->valuestring) < sizeof(out->version)
            && cJSON_IsString(h) && is_hex64(h->valuestring)
            && cJSON_IsNumber(n) && n->valuedouble > 0 && n->valuedouble < 64.0 * 1024 * 1024) {
            snprintf(out->version, sizeof(out->version), "%s", v->valuestring);
            for (int i = 0; i < 64; i++) out->sha256[i] = (char)tolower((unsigned char)h->valuestring[i]);
            out->size = (uint32_t)n->valuedouble;
            out->deployment_id = cJSON_IsNumber(d) ? d->valueint : 0;
        } else {
            out->available = false;       /* never install something we can't verify */
            rc = -1;
        }
    }
    cJSON_Delete(root);
    return rc;
}

bool ota_digest_matches(const uint8_t digest[32], const char *hex)
{
    if (!is_hex64(hex)) return false;
    char mine[65];
    for (int i = 0; i < 32; i++) snprintf(mine + 2 * i, 3, "%02x", digest[i]);
    return strcasecmp(mine, hex) == 0;
}

ota_prompt_target_t ota_prompt_target(const cJSON *payload, const char *my_mac)
{
    if (!cJSON_IsObject(payload)) return OTA_PROMPT_OTHER;
    const cJSON *type = cJSON_GetObjectItemCaseSensitive(payload, "device_type");
    const cJSON *mac = cJSON_GetObjectItemCaseSensitive(payload, "mac_address");
    if (!cJSON_IsString(type)) return OTA_PROMPT_S3;
    if (strcmp(type->valuestring, "s3") == 0) return OTA_PROMPT_S3;
    if (strcmp(type->valuestring, "c6") == 0 && cJSON_IsString(mac) && my_mac
        && strcasecmp(mac->valuestring, my_mac) == 0) {
        return OTA_PROMPT_SELF;
    }
    return OTA_PROMPT_OTHER;
}
