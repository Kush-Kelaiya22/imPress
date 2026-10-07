/**
 * @file display.c
 * @brief OLED display driver (SSD1306, 128x64, I2C) for the student module.
 *
 * Uses the ESP-IDF v6.x i2c_master driver (the legacy driver/i2c.h API was
 * removed in IDF v6.1). Text is rendered from a real 5x7 ASCII font into a
 * local framebuffer, which is flushed to the panel in one transaction.
 */

#include "display.h"
#include "config.h"

#include <string.h>
#include <stdio.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/i2c_master.h"

static const char *TAG = "display";

/* SSD1306 I2C address */
#define SSD1306_ADDR    0x3C
#define SSD1306_WIDTH   128
#define SSD1306_HEIGHT  64
#define SSD1306_PAGES   (SSD1306_HEIGHT / 8)   /* 8 pages */

#define I2C_TIMEOUT_MS  50

static bool s_initialized = false;
static i2c_master_bus_handle_t s_bus;
static i2c_master_dev_handle_t s_dev;
static uint8_t s_framebuffer[SSD1306_WIDTH * SSD1306_PAGES];  /* 1024 bytes */

/* ── Low-level I2C ─────────────────────────────────────────────────── */

static void ssd1306_write(const uint8_t *buf, size_t len)
{
    /* SSD1306 control byte is the first byte: 0x00 = command, 0x40 = data */
    if (i2c_master_transmit(s_dev, buf, len, I2C_TIMEOUT_MS) != ESP_OK) {
        ESP_LOGW(TAG, "I2C write failed (%u bytes)", (unsigned)len);
    }
}

static void ssd1306_cmd(uint8_t cmd)
{
    uint8_t data[2] = {0x00, cmd};  /* Co=0, D/C#=0 */
    ssd1306_write(data, sizeof(data));
}

static void ssd1306_data(const uint8_t *data, size_t len)
{
    /* Prepend 0x40 (Co=0, D/C#=1) and chunk to fit a 128-byte payload. */
    uint8_t buf[129];
    buf[0] = 0x40;
    while (len > 0) {
        size_t chunk = len > 128 ? 128 : len;
        memcpy(&buf[1], data, chunk);
        ssd1306_write(buf, chunk + 1);
        data += chunk;
        len -= chunk;
    }
}

static void ssd1306_init_sequence(void)
{
    ssd1306_cmd(0xAE);  /* display off */
    ssd1306_cmd(0x20);  /* memory mode */
    ssd1306_cmd(0x00);  /* horizontal addressing */
    ssd1306_cmd(0xD5);  /* clock divide */
    ssd1306_cmd(0x80);
    ssd1306_cmd(0xA8);  /* multiplex ratio */
    ssd1306_cmd(0x3F);  /* 64 rows */
    ssd1306_cmd(0xD3);  /* display offset */
    ssd1306_cmd(0x00);
    ssd1306_cmd(0x40);  /* start line = 0 */
    ssd1306_cmd(0x8D);  /* charge pump */
    ssd1306_cmd(0x14);  /* enable */
    ssd1306_cmd(0xA1);  /* segment re-map */
    ssd1306_cmd(0xC8);  /* COM scan direction */
    ssd1306_cmd(0xDA);  /* COM pins */
    ssd1306_cmd(0x12);
    ssd1306_cmd(0x81);  /* contrast */
    ssd1306_cmd(0xCF);
    ssd1306_cmd(0xD9);  /* pre-charge */
    ssd1306_cmd(0xF1);
    ssd1306_cmd(0xDB);  /* VCOMH deselect */
    ssd1306_cmd(0x40);
    ssd1306_cmd(0xA4);  /* display from RAM */
    ssd1306_cmd(0xA6);  /* normal display (not inverted) */
    ssd1306_cmd(0xAF);  /* display on */
}

/* ── 5x7 ASCII font (column-major, LSB = top row) ──────────────────── */

/* Covers ASCII 32 (space) through 126 ('~'): 95 glyphs x 5 columns. */
static const uint8_t FONT5X7[95][5] = {
    {0x00, 0x00, 0x00, 0x00, 0x00}, /* space */
    {0x00, 0x00, 0x5F, 0x00, 0x00}, /* ! */
    {0x00, 0x07, 0x00, 0x07, 0x00}, /* " */
    {0x14, 0x7F, 0x14, 0x7F, 0x14}, /* # */
    {0x24, 0x2A, 0x7F, 0x2A, 0x12}, /* $ */
    {0x23, 0x13, 0x08, 0x64, 0x62}, /* % */
    {0x36, 0x49, 0x55, 0x22, 0x50}, /* & */
    {0x00, 0x05, 0x03, 0x00, 0x00}, /* ' */
    {0x00, 0x1C, 0x22, 0x41, 0x00}, /* ( */
    {0x00, 0x41, 0x22, 0x1C, 0x00}, /* ) */
    {0x14, 0x08, 0x3E, 0x08, 0x14}, /* * */
    {0x08, 0x08, 0x3E, 0x08, 0x08}, /* + */
    {0x00, 0x50, 0x30, 0x00, 0x00}, /* , */
    {0x08, 0x08, 0x08, 0x08, 0x08}, /* - */
    {0x00, 0x60, 0x60, 0x00, 0x00}, /* . */
    {0x20, 0x10, 0x08, 0x04, 0x02}, /* / */
    {0x3E, 0x51, 0x49, 0x45, 0x3E}, /* 0 */
    {0x00, 0x42, 0x7F, 0x40, 0x00}, /* 1 */
    {0x42, 0x61, 0x51, 0x49, 0x46}, /* 2 */
    {0x21, 0x41, 0x45, 0x4B, 0x31}, /* 3 */
    {0x18, 0x14, 0x12, 0x7F, 0x10}, /* 4 */
    {0x27, 0x45, 0x45, 0x45, 0x39}, /* 5 */
    {0x3C, 0x4A, 0x49, 0x49, 0x30}, /* 6 */
    {0x01, 0x71, 0x09, 0x05, 0x03}, /* 7 */
    {0x36, 0x49, 0x49, 0x49, 0x36}, /* 8 */
    {0x06, 0x49, 0x49, 0x29, 0x1E}, /* 9 */
    {0x00, 0x36, 0x36, 0x00, 0x00}, /* : */
    {0x00, 0x56, 0x36, 0x00, 0x00}, /* ; */
    {0x08, 0x14, 0x22, 0x41, 0x00}, /* < */
    {0x14, 0x14, 0x14, 0x14, 0x14}, /* = */
    {0x00, 0x41, 0x22, 0x14, 0x08}, /* > */
    {0x02, 0x01, 0x51, 0x09, 0x06}, /* ? */
    {0x32, 0x49, 0x79, 0x41, 0x3E}, /* @ */
    {0x7E, 0x11, 0x11, 0x11, 0x7E}, /* A */
    {0x7F, 0x49, 0x49, 0x49, 0x36}, /* B */
    {0x3E, 0x41, 0x41, 0x41, 0x22}, /* C */
    {0x7F, 0x41, 0x41, 0x22, 0x1C}, /* D */
    {0x7F, 0x49, 0x49, 0x49, 0x41}, /* E */
    {0x7F, 0x09, 0x09, 0x09, 0x01}, /* F */
    {0x3E, 0x41, 0x49, 0x49, 0x7A}, /* G */
    {0x7F, 0x08, 0x08, 0x08, 0x7F}, /* H */
    {0x00, 0x41, 0x7F, 0x41, 0x00}, /* I */
    {0x20, 0x40, 0x41, 0x3F, 0x01}, /* J */
    {0x7F, 0x08, 0x14, 0x22, 0x41}, /* K */
    {0x7F, 0x40, 0x40, 0x40, 0x40}, /* L */
    {0x7F, 0x02, 0x0C, 0x02, 0x7F}, /* M */
    {0x7F, 0x04, 0x08, 0x10, 0x7F}, /* N */
    {0x3E, 0x41, 0x41, 0x41, 0x3E}, /* O */
    {0x7F, 0x09, 0x09, 0x09, 0x06}, /* P */
    {0x3E, 0x41, 0x51, 0x21, 0x5E}, /* Q */
    {0x7F, 0x09, 0x19, 0x29, 0x46}, /* R */
    {0x46, 0x49, 0x49, 0x49, 0x31}, /* S */
    {0x01, 0x01, 0x7F, 0x01, 0x01}, /* T */
    {0x3F, 0x40, 0x40, 0x40, 0x3F}, /* U */
    {0x1F, 0x20, 0x40, 0x20, 0x1F}, /* V */
    {0x3F, 0x40, 0x38, 0x40, 0x3F}, /* W */
    {0x63, 0x14, 0x08, 0x14, 0x63}, /* X */
    {0x07, 0x08, 0x08, 0x08, 0x07}, /* Y */
    {0x61, 0x51, 0x49, 0x45, 0x43}, /* Z */
    {0x00, 0x7F, 0x41, 0x41, 0x00}, /* [ */
    {0x02, 0x04, 0x08, 0x10, 0x20}, /* backslash */
    {0x00, 0x41, 0x41, 0x7F, 0x00}, /* ] */
    {0x04, 0x02, 0x01, 0x02, 0x04}, /* ^ */
    {0x40, 0x40, 0x40, 0x40, 0x40}, /* _ */
    {0x00, 0x01, 0x02, 0x04, 0x00}, /* ` */
    {0x20, 0x54, 0x54, 0x54, 0x78}, /* a */
    {0x7F, 0x48, 0x44, 0x44, 0x38}, /* b */
    {0x38, 0x44, 0x44, 0x44, 0x20}, /* c */
    {0x38, 0x44, 0x44, 0x48, 0x7F}, /* d */
    {0x38, 0x54, 0x54, 0x54, 0x18}, /* e */
    {0x08, 0x7E, 0x09, 0x01, 0x02}, /* f */
    {0x0C, 0x52, 0x52, 0x52, 0x3E}, /* g */
    {0x7F, 0x08, 0x04, 0x04, 0x78}, /* h */
    {0x00, 0x44, 0x7D, 0x40, 0x00}, /* i */
    {0x20, 0x40, 0x44, 0x3D, 0x00}, /* j */
    {0x7F, 0x10, 0x28, 0x44, 0x00}, /* k */
    {0x00, 0x41, 0x7F, 0x40, 0x00}, /* l */
    {0x7C, 0x04, 0x18, 0x04, 0x78}, /* m */
    {0x7C, 0x08, 0x04, 0x04, 0x78}, /* n */
    {0x38, 0x44, 0x44, 0x44, 0x38}, /* o */
    {0x7C, 0x14, 0x14, 0x14, 0x08}, /* p */
    {0x08, 0x14, 0x14, 0x18, 0x7C}, /* q */
    {0x7C, 0x08, 0x04, 0x04, 0x08}, /* r */
    {0x48, 0x54, 0x54, 0x54, 0x20}, /* s */
    {0x04, 0x3F, 0x44, 0x40, 0x20}, /* t */
    {0x3C, 0x40, 0x40, 0x20, 0x7C}, /* u */
    {0x1C, 0x20, 0x40, 0x20, 0x1C}, /* v */
    {0x3C, 0x40, 0x30, 0x40, 0x3C}, /* w */
    {0x44, 0x28, 0x10, 0x28, 0x44}, /* x */
    {0x0C, 0x50, 0x50, 0x50, 0x3C}, /* y */
    {0x44, 0x64, 0x54, 0x4C, 0x44}, /* z */
    {0x00, 0x08, 0x36, 0x41, 0x00}, /* { */
    {0x00, 0x00, 0x7F, 0x00, 0x00}, /* | */
    {0x00, 0x41, 0x36, 0x08, 0x00}, /* } */
    {0x08, 0x08, 0x2A, 0x1C, 0x08}, /* ~ */
};

/* ── Framebuffer rendering ─────────────────────────────────────────── */

/**
 * @brief Draw one character at page row @p page, column @p x.
 *        Each glyph is 5 columns + 1 blank column of spacing.
 */
static void draw_char(int x, int page, char c, bool invert)
{
    if (page < 0 || page >= SSD1306_PAGES) return;
    if (x < 0 || x + 5 > SSD1306_WIDTH) return;

    /* Map to the font table; anything outside 32..126 renders as '?'. */
    int idx = (unsigned char)c - 32;
    if (idx < 0 || idx >= (int)(sizeof(FONT5X7) / sizeof(FONT5X7[0]))) {
        idx = '?' - 32;
    }

    for (int col = 0; col < 5; col++) {
        uint8_t bits = FONT5X7[idx][col];
        if (invert) bits = ~bits;
        s_framebuffer[(page * SSD1306_WIDTH) + x + col] = bits;
    }
    /* Inter-character spacing column. */
    s_framebuffer[(page * SSD1306_WIDTH) + x + 5] = invert ? 0xFF : 0x00;
}

/**
 * @brief Draw a NUL-terminated string starting at column @p x on @p page.
 *        Stops at the panel edge rather than wrapping.
 */
static void draw_string(int x, int page, const char *s, bool invert)
{
    if (!s) return;
    while (*s && x + 6 <= SSD1306_WIDTH) {
        draw_char(x, page, *s, invert);
        x += 6;
        s++;
    }
}

/**
 * @brief Redraw the framebuffer onto the panel (full 128x64 refresh).
 */
static void display_flush(void)
{
    /* Full-window update: columns 0..127, pages 0..7 */
    ssd1306_cmd(0x21);
    ssd1306_cmd(0);
    ssd1306_cmd(SSD1306_WIDTH - 1);
    ssd1306_cmd(0x22);
    ssd1306_cmd(0);
    ssd1306_cmd(SSD1306_PAGES - 1);
    ssd1306_data(s_framebuffer, sizeof(s_framebuffer));
}

/* ── Public API ────────────────────────────────────────────────────── */

int display_init(void)
{
    if (s_initialized) return 0;

    if (!STUDENT_HAS_DISPLAY) {
        ESP_LOGW(TAG, "No display fitted — skipping SSD1306/I2C init");
        return -1;
    }

    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t err = i2c_new_master_bus(&bus_cfg, &s_bus);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "i2c_new_master_bus failed: %s", esp_err_to_name(err));
        return -1;
    }

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = SSD1306_ADDR,
        .scl_speed_hz = I2C_FREQ_HZ,
    };
    err = i2c_master_bus_add_device(s_bus, &dev_cfg, &s_dev);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "i2c_master_bus_add_device failed: %s", esp_err_to_name(err));
        i2c_del_master_bus(s_bus);
        return -1;
    }

    ssd1306_init_sequence();
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    display_flush();

    s_initialized = true;
    ESP_LOGI(TAG, "SSD1306 ready (SDA=%d SCL=%d)", PIN_I2C_SDA, PIN_I2C_SCL);
    return 0;
}

void display_clear(void)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    display_flush();
}

void display_show_text(const char *line1, const char *line2, const char *line3)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    if (line1) draw_string(0, 0, line1, false);
    if (line2) draw_string(0, 2, line2, false);
    if (line3) draw_string(0, 4, line3, false);
    display_flush();
}

void display_show_status(const char *status, int battery_pct)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));

    /* Status line, then a battery readout on the next text row. */
    if (status) draw_string(0, 0, status, false);

    char batt[24];
    snprintf(batt, sizeof(batt), "BAT %d%%", battery_pct);
    draw_string(0, 2, batt, false);

    display_flush();
}

void display_show_question(const char *question, const char *options[],
                           int num_options, int selected)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));

    /* Question on page 0, then up to 6 option rows. */
    if (question) draw_string(0, 0, question, false);

    for (int i = 0; i < num_options && i < 6; i++) {
        int page = 2 + i;
        bool sel = (i == selected);
        char line[24];
        snprintf(line, sizeof(line), "%c %s",
                 sel ? '>' : ' ', options[i] ? options[i] : "");
        /* Invert the selected row so it reads as highlighted. */
        draw_string(0, page, line, sel);
    }

    display_flush();
}

void display_show_result(const char *text)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    if (text) draw_string(0, 3, text, false);
    display_flush();
}

void display_show_waiting(const char *message)
{
    display_clear();
    display_show_text("WAITING...", message, NULL);
}

void display_show_provision_state(const char *title, const char *id,
                                  int cursor, const char *hint)
{
    if (!s_initialized) return;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));

    if (title) draw_string(0, 0, title, false);

    /* Ten ID slots, centered; the active cursor slot is inverted. */
    int x = (SSD1306_WIDTH - 10 * 6) / 2;
    for (int i = 0; i < 10; i++) {
        char c = (id && id[i]) ? id[i] : '_';
        draw_char(x, 2, c, (i == cursor));
        x += 6;
    }

    if (hint) draw_string(0, 6, hint, false);
    display_flush();
}

void display_deinit(void)
{
    if (!s_initialized) return;
    /* Blank the panel so stale content doesn't linger after shutdown. */
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    display_flush();
    ssd1306_cmd(0xAE);  /* display off */

    if (s_dev) {
        i2c_master_bus_rm_device(s_dev);
        s_dev = NULL;
    }
    if (s_bus) {
        i2c_del_master_bus(s_bus);
        s_bus = NULL;
    }
    s_initialized = false;
}
