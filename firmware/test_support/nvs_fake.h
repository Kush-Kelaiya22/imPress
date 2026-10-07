/* In-memory NVS fake shared by firmware host tests (test_support/nvs_fake.c).
 * Declares the IDF NVS API subset the firmware uses plus test controls. */
#pragma once

#include <stddef.h>
#include <stdint.h>

/* Test controls */
void        nvs_wipe(void);                         /* empty storage, reset counters */
void        nvs_fail_next_init(int esp_err);        /* next nvs_flash_init() returns this */
int         nvs_open_handles(void);                 /* open - close (leak detector) */
const char *nvs_stored_str(const char *key);        /* NULL if absent */
