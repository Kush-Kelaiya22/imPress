/* Host test for main/ota_logic.c: the C6 OTA client's decisions. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_logic.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define RUN(t) do { t(); printf("ok   %s\n", #t); } while (0)

#define HASH "9620E47584A943C0CD817C5AEFDE497497816738983EECEEA139F537E0F158A0"

static void test_parse_offer(void)
{
    ota_offer_t o;
    CHECK(ota_parse_check("{\"update_available\":true,\"version\":\"2.2.0\",\"sha256\":\"" HASH "\","
                          "\"size\":1124032,\"deployment_id\":7,\"ota_status\":\"precheck\"}", &o) == 0);
    CHECK(o.available && strcmp(o.version, "2.2.0") == 0 && o.size == 1124032 && o.deployment_id == 7);
    CHECK(strlen(o.sha256) == 64 && o.sha256[0] == '9' && o.sha256[4] == 'e');   /* lower-cased */
}

static void test_nothing_offered(void)
{
    ota_offer_t o;
    CHECK(ota_parse_check("{\"update_available\":false,\"version\":\"\"}", &o) == 0 && !o.available);
}

static void test_unverifiable_offers_are_refused(void)
{
    ota_offer_t o;
    const char *bad[] = {
        "not json", "[1,2]", NULL,
        "{\"update_available\":true,\"version\":\"2.2.0\",\"size\":10}",                       /* no hash */
        "{\"update_available\":true,\"version\":\"2.2.0\",\"sha256\":\"abc\",\"size\":10}",    /* short hash */
        "{\"update_available\":true,\"version\":\"1\",\"sha256\":\"" HASH "\",\"size\":10}",  /* not X.Y.Z */
        "{\"update_available\":true,\"version\":\"2..0\",\"sha256\":\"" HASH "\",\"size\":10}",
        "{\"update_available\":true,\"version\":\"2.2.0\",\"sha256\":\"" HASH "\",\"size\":0}",
        "{\"update_available\":true,\"version\":\"2.2.0\",\"sha256\":\"" HASH "\"}",          /* no size */
    };
    for (size_t i = 0; i < sizeof bad / sizeof bad[0]; i++) {
        CHECK(ota_parse_check(bad[i], &o) == -1);
        CHECK(!o.available);
    }
}

static void test_digest_comparison(void)
{
    uint8_t d[32];
    for (int i = 0; i < 32; i++) d[i] = (uint8_t)(i * 7);
    char hex[65];
    for (int i = 0; i < 32; i++) snprintf(hex + 2 * i, 3, "%02X", d[i]);
    CHECK(ota_digest_matches(d, hex));
    hex[63] = hex[63] == '0' ? '1' : '0';
    CHECK(!ota_digest_matches(d, hex));
    CHECK(!ota_digest_matches(d, "") && !ota_digest_matches(d, NULL));
}

static void test_prompt_routing(void)
{
    const char *me = "48:F6:EE:00:00:01";
    struct { const char *json; ota_prompt_target_t want; } cases[] = {
        {"{\"device_type\":\"c6\",\"mac_address\":\"48:f6:ee:00:00:01\",\"version\":\"2.2.0\"}", OTA_PROMPT_SELF},
        {"{\"device_type\":\"c6\",\"mac_address\":\"48:F6:EE:00:00:02\"}", OTA_PROMPT_OTHER},   /* another C6 */
        {"{\"device_type\":\"c6\"}", OTA_PROMPT_OTHER},
        {"{\"device_type\":\"s3\",\"mac_address\":\"a1b2c3d4e5f6\"}", OTA_PROMPT_S3},
        {"{\"version\":\"1.2.0\"}", OTA_PROMPT_S3},                                            /* pre-v2.1 */
        {"{\"device_type\":\"student\"}", OTA_PROMPT_OTHER},
    };
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i++) {
        cJSON *p = cJSON_Parse(cases[i].json);
        CHECK(ota_prompt_target(p, me) == cases[i].want);
        cJSON_Delete(p);
    }
    CHECK(ota_prompt_target(NULL, me) == OTA_PROMPT_OTHER);
}

int main(void)
{
    RUN(test_parse_offer);
    RUN(test_nothing_offered);
    RUN(test_unverifiable_offers_are_refused);
    RUN(test_digest_comparison);
    RUN(test_prompt_routing);
    puts("PASS test_ota_logic");
    return 0;
}
