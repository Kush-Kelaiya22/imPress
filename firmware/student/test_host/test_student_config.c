/* Host tests for student/main/config.c — the student's identity store.
 *
 * The enrollment number is the student's ONLY identity on the mesh and in the
 * backend, so its rules are core logic: exact format (10 alphanumerics, same
 * as the backend), the 0000000000 placeholder means "unprovisioned",
 * set-once semantics, explicit clear for re-provisioning, survives reboot.
 * NVS is an in-memory fake; "reboot" = re-running init_student_profile().
 * Run: ./run.sh
 */
#include <string.h>
#include "config.h"
#include "nvs_fake.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define RUN(t) do { nvs_wipe(); t(); printf("ok   %s\n", #t); } while (0)

/* ── Tests ──────────────────────────────────────────────────────────── */

static void test_first_boot_is_unprovisioned_placeholder(void)
{
    init_student_profile();
    CHECK(strcmp(g_student.enrollment, DEFAULT_ENROLLMENT) == 0);
    CHECK(!student_has_identity());
    CHECK(strcmp(nvs_stored_str(NVS_KEY_ENROLL), DEFAULT_ENROLLMENT) == 0);
    CHECK(nvs_open_handles() == 0);                          /* no leaked handles */
}

static void test_format_rules_match_backend(void)
{
    init_student_profile();
    const char *bad[] = { "", "ABC", "ABCDE123456", "ABCDE-1234", "ABCDE 1234", "ABCDE1234\n", DEFAULT_ENROLLMENT };
    for (size_t i = 0; i < sizeof bad / sizeof bad[0]; i++) {
        CHECK(student_set_enrollment(bad[i]) == ESP_ERR_INVALID_ARG);
    }
    CHECK(student_set_enrollment(NULL) == ESP_ERR_INVALID_ARG);
    CHECK(!student_has_identity());
    CHECK(student_set_enrollment("abcDE12345") == ESP_OK);   /* mixed case accepted, as backend */
    CHECK(student_has_identity());
}

static void test_identity_is_set_once_and_survives_reboot(void)
{
    init_student_profile();
    CHECK(student_set_enrollment("ABCDE12345") == ESP_OK);
    CHECK(student_set_enrollment("ZZZZZ99999") == ESP_ERR_INVALID_STATE);  /* no silent overwrite */
    CHECK(student_set_enrollment("ABCDE12345") == ESP_OK);                 /* same value: idempotent */
    memset(&g_student, 0, sizeof g_student);
    init_student_profile();                                                /* reboot */
    CHECK(strcmp(g_student.enrollment, "ABCDE12345") == 0 && student_has_identity());
    CHECK(nvs_open_handles() == 0);
}

static void test_clear_allows_reprovisioning(void)
{
    init_student_profile();
    student_set_enrollment("ABCDE12345");
    student_clear_enrollment();
    CHECK(!student_has_identity() && nvs_stored_str(NVS_KEY_ENROLL) == NULL);
    CHECK(student_set_enrollment("ZZZZZ99999") == ESP_OK);
    CHECK(strcmp(nvs_stored_str(NVS_KEY_ENROLL), "ZZZZZ99999") == 0);
}

static void test_server_profile_push_respects_identity(void)
{
    init_student_profile();
    student_update_profile("ABCDE12345", "Asha Rao", "B.Tech", "asha@x.io");
    CHECK(strcmp(g_student.enrollment, "ABCDE12345") == 0 && g_student.provisioned);
    CHECK(strcmp(nvs_stored_str(NVS_KEY_NAME), "Asha Rao") == 0);
    /* A push can't replace an existing identity, nor install an invalid one. */
    student_update_profile("ZZZZZ99999", NULL, NULL, NULL);
    student_update_profile("bad", NULL, NULL, NULL);
    CHECK(strcmp(g_student.enrollment, "ABCDE12345") == 0);
    /* Long profile fields are truncated safely, never overflow. */
    char longname[200];
    memset(longname, 'n', sizeof longname - 1);
    longname[sizeof longname - 1] = '\0';
    student_update_profile(NULL, longname, NULL, NULL);
    CHECK(strlen(g_student.name) == NVS_NAME_LEN - 1);
    CHECK(nvs_open_handles() == 0);
}

static void test_nvs_version_change_erases_and_recovers(void)
{
    nvs_set_str(1, NVS_KEY_ENROLL, "ABCDE12345");
    nvs_fail_next_init(ESP_ERR_NVS_NEW_VERSION_FOUND);      /* partition layout changed */
    init_student_profile();
    CHECK(!student_has_identity());                     /* erased → back to placeholder */
}

static void test_oversized_stored_value_is_ignored(void)
{
    nvs_set_str(1, NVS_KEY_INIT, "");
    nvs_set_u8(1, NVS_KEY_INIT, 1);
    nvs_set_str(1, NVS_KEY_ENROLL, "THIS-VALUE-IS-FAR-TOO-LONG-FOR-THE-BUFFER");
    init_student_profile();
    CHECK(strcmp(g_student.enrollment, DEFAULT_ENROLLMENT) == 0);   /* default kept, no overflow */
}

int main(void)
{
    RUN(test_first_boot_is_unprovisioned_placeholder);
    RUN(test_format_rules_match_backend);
    RUN(test_identity_is_set_once_and_survives_reboot);
    RUN(test_clear_allows_reprovisioning);
    RUN(test_server_profile_push_respects_identity);
    RUN(test_nvs_version_change_erases_and_recovers);
    RUN(test_oversized_stored_value_is_ignored);
    puts("PASS test_student_config");
    return 0;
}
