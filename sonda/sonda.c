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


uint32_t measure_pulse_duration(uint32_t timeout_us) {

    // sometimes gpio_get(ECHO_PIN) == (1|0) will miss
    // when the echo pin goes high/low the elapsed_time
    // variable is here to break out of the loop after the
    // specified timeout_us passes
    uint32_t pulse_start, pulse_end, elapsed_time;


    // Wait for the pulse to start, with timeout
    pulse_start = time_us_32();
    while (gpio_get(ECHO_PIN) == 0) {
        elapsed_time = time_us_32() - pulse_start;
        if (elapsed_time > timeout_us) {
            return 0; // Timeout
        }
    }

    // Wait for the pulse to end, with timeout
    while (gpio_get(ECHO_PIN) == 1) {
        elapsed_time = time_us_32() - pulse_start;
        if (elapsed_time > timeout_us) {
            return 0; // Timeout
        }

        pulse_end = time_us_32();
    }

    return pulse_end - pulse_start;
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
        // max time the echo pin will be on in theory is 23400 us
        // because the JSN sensor can measure up to 400 cm so:
        //t = (400cm) / (34300 cm/s) = 0.01166180 seconds
        // but you have to multiply that by two because the sonic burst
        // goes and travels back when it colide with an object so
        // the total time is around 0.023323 seconds which is equal to
        // approximately 23300 us
        uint32_t pulse_duration = measure_pulse_duration(23500);
        float dist = measure_distance_cm(pulse_duration);

        sprintf(str, "Sent %f\n", dist);
        uart_puts(UART_ID, str);

        sleep_ms(1000);

    }
}