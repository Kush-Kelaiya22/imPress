/* Host test for main/student_set.c: the C6's online-student set. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "student_set.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)
#define RUN(t) do { t(); printf("ok   %s\n", #t); } while (0)

static student_set_t g;

static void test_join_leave_counts(void)
{
    student_set_init(&g);
    CHECK(student_set_join(&g, "ABCDE12345"));
    CHECK(!student_set_join(&g, "ABCDE12345"));          /* duplicate join: still one */
    CHECK(student_set_join(&g, "ZZZZZ00001"));
    CHECK(student_set_count(&g) == 2);
    CHECK(student_set_leave(&g, "ABCDE12345"));
    CHECK(!student_set_leave(&g, "ABCDE12345"));         /* already gone */
    CHECK(!student_set_leave(&g, "NOTPRESENT"));
    CHECK(student_set_count(&g) == 1);
    CHECK(student_set_leave(&g, "ZZZZZ00001") && student_set_count(&g) == 0);
}

static void test_heartbeats_do_not_count_students(void)
{
    /* v2 incremented the count on every heartbeat; uptime updates must not. */
    student_set_init(&g);
    student_set_join(&g, "ABCDE12345");
    for (uint32_t t = 5; t < 500; t += 5) CHECK(!student_set_root_uptime(&g, t));
    CHECK(student_set_count(&g) == 1);
}

static void test_s3_reboot_clears_set(void)
{
    student_set_init(&g);
    CHECK(!student_set_root_uptime(&g, 1000));           /* first heartbeat: nothing to compare */
    student_set_join(&g, "ABCDE12345");
    student_set_join(&g, "ZZZZZ00001");
    CHECK(!student_set_root_uptime(&g, 1005));
    CHECK(student_set_root_uptime(&g, 3));               /* uptime went backwards: S3 rebooted */
    CHECK(student_set_count(&g) == 0);
    CHECK(student_set_join(&g, "ABCDE12345"));           /* students rejoin normally */
}

static void test_capacity_and_bad_input(void)
{
    student_set_init(&g);
    char id[16];
    for (int i = 0; i < STUDENT_SET_MAX; i++) {
        snprintf(id, sizeof id, "S%09d", i);
        CHECK(student_set_join(&g, id));
    }
    CHECK(!student_set_join(&g, "OVERFLOW01"));          /* full: refused, no overflow */
    CHECK(student_set_count(&g) == STUDENT_SET_MAX);
    CHECK(!student_set_join(&g, "") && !student_set_join(&g, NULL));
    CHECK(!student_set_leave(&g, NULL));

    /* 11 bytes with no NUL (as a corrupt radio payload could deliver) */
    student_set_init(&g);
    char raw[11];
    memset(raw, 'Q', sizeof raw);
    CHECK(student_set_join(&g, raw));
    CHECK(strlen(g.enroll[0]) == STUDENT_ENROLL_LEN);
    CHECK(student_set_leave(&g, raw));
}

int main(void)
{
    RUN(test_join_leave_counts);
    RUN(test_heartbeats_do_not_count_students);
    RUN(test_s3_reboot_clears_set);
    RUN(test_capacity_and_bad_input);
    puts("PASS test_student_set");
    return 0;
}
