/**
 * @file student_set.h
 * @brief Set of students currently on the classroom mesh (C6 side).
 *
 * Maintained from STUDENT_JOIN / STUDENT_LEAVE events relayed by the S3.
 * The S3 sends no LEAVE when it reboots (its routing table is simply gone),
 * so the set is cleared when the S3 heartbeat's uptime goes backwards.
 * Pure C, no ESP-IDF: host-tested in test_host/test_student_set.c.
 * Not thread-safe: owned by the spi2http task; others read the count only.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define STUDENT_SET_MAX     300   /* matches the S3's MESH_MAX_STUDENTS */
#define STUDENT_ENROLL_LEN  10

typedef struct {
    char     enroll[STUDENT_SET_MAX][STUDENT_ENROLL_LEN + 1];
    int      count;
    bool     root_seen;
    uint32_t root_uptime_s;
} student_set_t;

void student_set_init(student_set_t *s);

/** @return true if newly added (false: empty, already present, or full). */
bool student_set_join(student_set_t *s, const char *enroll);

/** @return true if it was present and is now removed. */
bool student_set_leave(student_set_t *s, const char *enroll);

/** Feed the S3 heartbeat uptime. @return true if the S3 rebooted and the set was cleared. */
bool student_set_root_uptime(student_set_t *s, uint32_t uptime_s);

static inline int student_set_count(const student_set_t *s) { return s->count; }
