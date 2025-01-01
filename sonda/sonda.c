#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

// UART defines
#define UART_ID uart1
#define BAUD_RATE 9600

// UART pins
#define UART_TX_PIN 4
#define UART_RX_PIN 5

// Utrasonic Sensor pins
#define TRIGER_PIN 16
#define ECHO_PIN 17

// Number of measurements to take each second
#define NUM_MEASUREMENTS 10

// API functions
void uart_init_and_configure();
void uart_send_float(float value);
float measure_distance_cm();

int main()
{
    stdio_init_all();

    uart_init_and_configure();

    gpio_init(TRIGER_PIN);
    gpio_set_dir(TRIGER_PIN, GPIO_OUT);
    gpio_init(ECHO_PIN);
    gpio_set_dir(ECHO_PIN, GPIO_IN);

    while (true)
    {
        uart_send_float(measure_distance_cm());
        sleep_ms(1000);
    }
}

void uart_init_and_configure()
{
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
}

void uart_send_float(float value)
{
    char str[20];
    sprintf(str, "%.2f\n", value);
    uart_puts(UART_ID, str);
}

void trigger_pulse()
{
    gpio_put(TRIGER_PIN, 1);
    sleep_us(20);
    gpio_put(TRIGER_PIN, 0);
}

uint32_t measure_pulse_duration(uint32_t timeout_us)
{

    // sometimes gpio_get(ECHO_PIN) == (1|0) will miss
    // when the echo pin goes high/low the elapsed_time
    // variable is here to break out of the loop after the
    // specified timeout_us passes. Otherwise the program will
    // enter an infinete loop that will prevent it to continue
    // execution
    uint32_t pulse_start, pulse_end, elapsed_time;

    // Wait for the pulse to start, with timeout
    pulse_start = time_us_32();
    while (gpio_get(ECHO_PIN) == 0)
    {
        elapsed_time = time_us_32() - pulse_start;
        if (elapsed_time > timeout_us)
        {
            return 0; // Timeout
        }
    }

    // Wait for the pulse to end, with timeout
    while (gpio_get(ECHO_PIN) == 1)
    {
        elapsed_time = time_us_32() - pulse_start;
        if (elapsed_time > timeout_us)
        {
            return 0; // Timeout
        }
        pulse_end = time_us_32();
    }

    return pulse_end - pulse_start;
}

float measure_distance_cm()
{
    const float speed_of_sound = 34300.0f;
    trigger_pulse();
    // max time the echo pin will be on in theory is 23400 us
    // because the JSN sensor can measure up to 400 cm so:
    // t = (400cm) / (34300 cm/s) = 0.01166180 seconds
    // but you have to multiply that by two because the sonic burst
    // goes and travels back when it colide with an object so
    // the total time is around 0.023323 seconds which is equal to
    // approximately 23300 us
    uint32_t pulse_duration = measure_pulse_duration(23500);
    return (pulse_duration * speed_of_sound) / 2 / 1000000.0f;
}
