# Common protocol library — included by all firmware projects
idf_component_register(
    SRCS "protocol.c" "spi_link.c"
    INCLUDE_DIRS "."
)
