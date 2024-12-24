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

#define TRIGER_PIN 16
#define ECHO_PIN 17

uint32_t pulse_start, pulse_end;

void trigger_pulse()
{
    gpio_put(TRIGER_PIN, 1);
    sleep_us(20);
    gpio_put(TRIGER_PIN, 0);
}


uint32_t measure_pulse_duration() {

    uint32_t start, end;

    // Wait for the pulse to start
    while (gpio_get(ECHO_PIN) == 0) {
        start = time_us_32() ;
    }

    // Wait for the pulse to end
    while (gpio_get(ECHO_PIN) == 1) {
        end = time_us_32();
    }

    return end - start;
}

float measure_distance_cm(uint32_t pulse_duration)
{
    // speed of sound in cm/s
    const float speed_of_sound = 34300.0f;
    // 1000000.0f converts from micrometers so cm
    return (pulse_duration * speed_of_sound) / 2 / 1000000.0f;
}


int main()
{
    stdio_init_all();

    // Set up our UART
    uart_init(UART_ID, BAUD_RATE);
    // Set the TX and RX pins by using the function select on the GPIO
    // Set datasheet for more information on function select
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    // int c = 5;
    char str[20];
    gpio_init(TRIGER_PIN);
    gpio_set_dir(TRIGER_PIN, GPIO_OUT);
    gpio_init(ECHO_PIN);
    gpio_set_dir(ECHO_PIN, GPIO_IN);

    while (true) {
        trigger_pulse();
        uint32_t pulse_duration = measure_pulse_duration(23500);
        float dist = measure_distance_cm(pulse_duration);

        sprintf(str, "Sent %f\n", dist);
        uart_puts(UART_ID, str);

        sleep_ms(1000);
    }
}