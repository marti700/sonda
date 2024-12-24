#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

// UART defines
// By default the stdout UART is `uart0`, so we will use the second one
#define UART_ID uart1
#define BAUD_RATE 9600

// Use pins 4 and 5 for UART1
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define UART_TX_PIN 4
#define UART_RX_PIN 5

int main()
{
    stdio_init_all();

    // Set up our UART
    uart_init(UART_ID, BAUD_RATE);
    // Set the TX and RX pins by using the function select on the GPIO
    // Set datasheet for more information on function select
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);


    // For more examples of UART use see
    int c = 5;
    char str[20];
    while (true) {
        printf("Hello, world!\n");
        sprintf(str, "Sent %d\n", c);
	    // Send out a string, with CR/LF conversions
        uart_puts(UART_ID, str);
        sleep_ms(500);
        if (c == 100)
        {
            c == 0;
        }
        c++;
    }
}