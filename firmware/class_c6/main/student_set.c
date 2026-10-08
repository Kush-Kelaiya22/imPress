#include "student_set.h"

#include <string.h>

void student_set_init(student_set_t *s)
{
    memset(s, 0, sizeof(*s));
}

/* Enrollment fields come off the radio: never trust a NUL terminator. */
static int find(const student_set_t *s, const char *enroll)
{
    for (int i = 0; i < s->count; i++) {
        if (strncmp(s->enroll[i], enroll, STUDENT_ENROLL_LEN) == 0) {
            return i;
        }
    }
    return -1;
}

bool student_set_join(student_set_t *s, const char *enroll)
{
    if (!enroll || !enroll[0] || find(s, enroll) >= 0 || s->count >= STUDENT_SET_MAX) {
        return false;
    }
    size_t n = strnlen(enroll, STUDENT_ENROLL_LEN);
    memcpy(s->enroll[s->count], enroll, n);
    s->enroll[s->count][n] = '\0';
    s->count++;
    return true;
}

bool student_set_leave(student_set_t *s, const char *enroll)
{
    int i = enroll ? find(s, enroll) : -1;
    if (i < 0) {
        return false;
    }
    s->count--;
    memcpy(s->enroll[i], s->enroll[s->count], sizeof(s->enroll[i]));  /* order is irrelevant */
    memset(s->enroll[s->count], 0, sizeof(s->enroll[s->count]));
    return true;
}

bool student_set_root_uptime(student_set_t *s, uint32_t uptime_s)
{
    bool rebooted = s->root_seen && uptime_s < s->root_uptime_s;
    s->root_seen = true;
    s->root_uptime_s = uptime_s;
    if (rebooted) {
        s->count = 0;
        memset(s->enroll, 0, sizeof(s->enroll));
    }
    return rebooted;
}
