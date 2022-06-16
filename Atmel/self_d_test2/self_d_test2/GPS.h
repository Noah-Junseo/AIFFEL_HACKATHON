/*
 * GPS.h
 *
 * Created: 2022-05-11 오후 9:34:14
 * Author : LEEHUIDO
 */ 
#ifndef GPS_h
#define GPS_h

void GPS_UART2_init(long baud);
unsigned char GPS_UART2_getchar(char *c);
void GPS_UART2_putchar(unsigned char c);
char GPS_UART2_gets(void);
char GPS_parsing(char *s);
unsigned char atohex(char hexadecimal);
long atoi_(char*s);

#endif