/*
 * UART.h
 *
 * Created: 2022-05-10 오전 11:14:09
 * Author : LEEHUIDO
 */ 
#ifndef UART_h
#define UART_h

#include <stdio.h>


void UART0_init(long baud);
void UART0_putchar(unsigned char c);
void UART0_p_putchar(unsigned char c, FILE * stream);
void UART0_puts(char *c);
unsigned char UART0_getchar(char *c);
void UART0_GPS_send(char* s);
void UART0_IMU_send(float _heading);
char hex2ascii(unsigned char a);
char UART0_gets(void);
char UART0_parsing(char *s);

#endif
